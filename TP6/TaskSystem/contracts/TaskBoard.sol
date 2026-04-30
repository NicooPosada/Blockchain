// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "./Task.sol";

/// @title Tablero de tareas
/// @notice Crea tareas, registra sus estados y mantiene listados por etapa.
contract TaskBoard is ITaskRegistry {

    enum Status { None, ToDo, InProgress, Done }

    struct TaskInfo {
        Status status;
        uint index;
    }

    // Listas por estado
    address[] private _todo;
    address[] private _inProgress;
    address[] private _done;

    // Registro de tareas
    mapping(address => TaskInfo) public tasks;

    // -------------------------
    // EVENTOS
    // -------------------------
    event TaskCreated(address taskAddress, address reporter, string description);
    event TaskMovedToInProgress(address taskAddress, uint256 index);
    event TaskMovedToDone(address taskAddress, uint256 index);

    // -------------------------
    // CREAR TAREA
    // -------------------------
    function createTask(string memory description) public returns (address) {
        Task task = new Task(description, msg.sender);

        address taskAddr = address(task);

        _todo.push(taskAddr);
        tasks[taskAddr] = TaskInfo(Status.ToDo, _todo.length - 1);

        emit TaskCreated(taskAddr, msg.sender, description);

        return taskAddr;
    }

    // -------------------------
    // GETTERS
    // -------------------------
    function todo(uint index) public view returns (address) {
        return _todo[index];
    }

    function inProgress(uint index) public view returns (address) {
        return _inProgress[index];
    }

    function done(uint index) public view returns (address) {
        return _done[index];
    }

    function todoCount() public view returns (uint256) {
        return _todo.length;
    }

    function inProgressCount() public view returns (uint256) {
        return _inProgress.length;
    }

    function doneCount() public view returns (uint256) {
        return _done.length;
    }

    // -------------------------
    // FILTROS POR ASSIGNEE
    // -------------------------
    function todoByAssignee(address worker) public view returns (address[] memory) {
        return _filterByAssignee(_todo, worker);
    }

    function inProgressByAssignee(address worker) public view returns (address[] memory) {
        return _filterByAssignee(_inProgress, worker);
    }

    function doneByAssignee(address worker) public view returns (address[] memory) {
        return _filterByAssignee(_done, worker);
    }

    function _filterByAssignee(address[] memory list, address worker) internal view returns (address[] memory) {
        uint count = 0;

        for (uint i = 0; i < list.length; i++) {
            if (Task(list[i]).assignee() == worker) {
                count++;
            }
        }

        address[] memory result = new address[](count);
        uint index = 0;

        for (uint i = 0; i < list.length; i++) {
            if (Task(list[i]).assignee() == worker) {
                result[index++] = list[i];
            }
        }

        return result;
    }

    // -------------------------
    // HELPERS (swap & pop)
    // -------------------------
    function _removeFromArray(address[] storage arr, uint index) internal {
        uint lastIndex = arr.length - 1;

        if (index != lastIndex) {
            address last = arr[lastIndex];
            arr[index] = last;
            tasks[last].index = index;
        }

        arr.pop();
    }

    // -------------------------
    // CALLBACKS DESDE TASK
    // -------------------------
    function taskStarted() public override {
        TaskInfo storage info = tasks[msg.sender];

        require(info.status != Status.None, "Tarea no registrada");
        require(info.status != Status.InProgress, "La tarea ya esta en progreso");
        require(info.status != Status.Done, "La tarea ya fue completada");

        // remover de todo
        _removeFromArray(_todo, info.index);

        // agregar a inProgress
        _inProgress.push(msg.sender);
        info.status = Status.InProgress;
        info.index = _inProgress.length - 1;

        emit TaskMovedToInProgress(msg.sender, info.index);
    }

    function taskCompleted() public override {
        TaskInfo storage info = tasks[msg.sender];

        require(info.status != Status.None, "Tarea no registrada");
        require(info.status != Status.Done, "La tarea ya fue completada");
        require(info.status == Status.InProgress, "La tarea no esta en progreso");

        // remover de inProgress
        _removeFromArray(_inProgress, info.index);

        // agregar a done
        _done.push(msg.sender);
        info.status = Status.Done;
        info.index = _done.length - 1;

        emit TaskMovedToDone(msg.sender, info.index);
    }
}