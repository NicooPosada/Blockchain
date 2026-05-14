//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract CFP {
    // Evento que se emite cuando alguien registra una propuesta
    event ProposalRegistered(
        bytes32 proposal,
        address sender,
        uint256 blockNumber
    );

    // Estructura que representa una propuesta
    struct ProposalData {
        address sender;
        uint256 blockNumber;
        uint256 timestamp;
    }

    // Mapping para almacenar datos de propuestas
    mapping(bytes32 => ProposalData) private _proposalData;

    // Lista de propuestas registradas
    bytes32[] private _proposals;

    // Timestamp del cierre
    uint256 private closingTimeValue;

    // Identificador del llamado
    bytes32 private callIdValue;

    // Dirección del creador
    address private creatorValue;

    // Devuelve los datos asociados con una propuesta
    function proposalData(
        bytes32 proposal
    ) public view returns (ProposalData memory) {
        return _proposalData[proposal];
    }

    // Devuelve la propuesta que está en la posición `index` de la lista de propuestas registradas
    function proposals(uint index) public view returns (bytes32) {
        return _proposals[index];
    }

    // Timestamp del cierre de la recepción de propuestas
    function closingTime() public view returns (uint256) {
        return closingTimeValue;
    }

    // Identificador de este llamado
    function callId() public view returns (bytes32) {
        return callIdValue;
    }

    // Creador de este llamado
    function creator() public view returns (address) {
        return creatorValue;
    }

    /** Construye un llamado con un identificador y un tiempo de cierre.
     *  Si el `timestamp` del bloque actual es mayor o igual al tiempo de cierre especificado,
     *  revierte con el mensaje "El cierre de la convocatoria no puede estar en el pasado".
     */
    constructor(bytes32 _callId, uint256 _closingTime) {
        require(
            block.timestamp < _closingTime,
            "El cierre de la convocatoria no puede estar en el pasado"
        );

        callIdValue = _callId;
        closingTimeValue = _closingTime;
        creatorValue = msg.sender;
    }

    // Devuelve la cantidad de propuestas presentadas
    function proposalCount() public view returns (uint256) {
        return _proposals.length;
    }

    /** Permite registrar una propuesta espec.
     *  Registra al emisor del mensaje como emisor de la propuesta.
     *  Si el timestamp del bloque actual es mayor que el del cierre del llamado,
     *  revierte con el error "Convocatoria cerrada"
     *  Si ya se ha registrado una propuesta igual, revierte con el mensaje
     *  "La propuesta ya ha sido registrada"
     *  Emite el evento `ProposalRegistered`
     */
    function registerProposal(bytes32 proposal) public {
        require(block.timestamp <= closingTimeValue, "Convocatoria cerrada");

        require(
            _proposalData[proposal].timestamp == 0,
            "La propuesta ya ha sido registrada"
        );

        _proposalData[proposal] = ProposalData({
            sender: msg.sender,
            blockNumber: block.number,
            timestamp: block.timestamp
        });

        _proposals.push(proposal);

        emit ProposalRegistered(proposal, msg.sender, block.number);
    }

    /** Permite registrar una propuesta especificando un emisor.
     *  Sólo puede ser ejecutada por el creador del llamado. Si no es así, revierte
     *  con el mensaje "Solo el creador puede hacer esta llamada"
     *  Si el timestamp del bloque actual es mayor que el del cierre del llamado,
     *  revierte con el error "Convocatoria cerrada"
     *  Si ya se ha registrado una propuesta igual, revierte con el mensaje
     *  "La propuesta ya ha sido registrada"
     *  Emite el evento `ProposalRegistered`
     */
    function registerProposalFor(bytes32 proposal, address sender) public {
        require(
            msg.sender == creatorValue,
            "Solo el creador puede hacer esta llamada"
        );

        require(block.timestamp <= closingTimeValue, "Convocatoria cerrada");

        require(
            _proposalData[proposal].timestamp == 0,
            "La propuesta ya ha sido registrada"
        );

        _proposalData[proposal] = ProposalData({
            sender: sender,
            blockNumber: block.number,
            timestamp: block.timestamp
        });

        _proposals.push(proposal);

        emit ProposalRegistered(proposal, sender, block.number);
    }

    /** Devuelve el timestamp en el que se ha registrado una propuesta.
     *  Si la propuesta no está registrada, devuelve cero.
     */
    function proposalTimestamp(
        bytes32 proposal
    ) public view returns (uint256) {
        return _proposalData[proposal].timestamp;
    }
}