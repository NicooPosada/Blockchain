// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// Interfaz que debe implementar el tablero para recibir
// notificaciones de cambios de estado de una tarea.
interface ITaskRegistry {
    // Notifica al tablero que la tarea pasó a estado en progreso.
    function taskStarted() external;

    // Notifica al tablero que la tarea pasó a estado finalizada.
    function taskCompleted() external;
}

/// @title Tarea individual del sistema
contract Task {

    // =========================
    // STORAGE
    // =========================

    string private _description;
    address private _reporter;
    address private _assignee;
    address private _factory;

    bool private _started;
    bool private _completed;

    uint256 private _assignedAt;
    uint256 private _startedAt;
    uint256 private _completedAt;

    // =========================
    // EVENTS
    // =========================

    event TaskAssigned(address reporter, address assignee, uint256 timestamp);
    event TaskStarted(address assignee, uint256 timestamp);
    event TaskCompleted(address assignee, uint256 timestamp);

    // =========================
    // MODIFIERS
    // =========================

    modifier onlyReporter() {
        require(msg.sender == _reporter, "Solo el reporter puede realizar esta accion");
        _;
    }

    modifier onlyAssignee() {
        require(msg.sender == _assignee, "Solo el assignee puede realizar esta accion");
        _;
    }

    modifier isPending() {
        require(!_started, "La tarea ya ha comenzado");
        _;
    }

    modifier isInProgress() {
        require(_started && !_completed, "La tarea no esta en progreso");
        _;
    }

    // =========================
    // CONSTRUCTOR
    // =========================

    constructor(string memory description_, address reporter_) {
        _description = description_;
        _reporter = reporter_;
        _factory = msg.sender; // TaskBoard
    }

    // =========================
    // GETTERS
    // =========================

    function description() public view returns (string memory) {
        return _description;
    }

    function reporter() public view returns (address) {
        return _reporter;
    }

    function assignee() public view returns (address) {
        return _assignee;
    }

    function started() public view returns (bool) {
        return _started;
    }

    function completed() public view returns (bool) {
        return _completed;
    }

    function assignedAt() public view returns (uint256) {
        return _assignedAt;
    }

    function startedAt() public view returns (uint256) {
        return _startedAt;
    }

    function completedAt() public view returns (uint256) {
        return _completedAt;
    }

    // =========================
    // CORE LOGIC
    // =========================

    function assign(address worker) public onlyReporter isPending {
        _assignee = worker;
        _assignedAt = block.timestamp;

        emit TaskAssigned(_reporter, worker, block.timestamp);
    }

    function start() public onlyAssignee isPending {
        _started = true;
        _startedAt = block.timestamp;

        emit TaskStarted(_assignee, block.timestamp);

        ITaskRegistry(_factory).taskStarted();
    }

    function complete() public onlyAssignee isInProgress {
        _completed = true;
        _completedAt = block.timestamp;

        emit TaskCompleted(_assignee, block.timestamp);

        ITaskRegistry(_factory).taskCompleted();
    }
}