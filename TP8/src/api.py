"""Servidor API para TP8."""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from dateutil.parser import isoparse
from flask import Flask, jsonify, request
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

import messages

load_dotenv()

# -------------------------------------------------------------------
# Configuración inicial
# -------------------------------------------------------------------

app = Flask(__name__)

RPC_URL = "http://127.0.0.1:8545"

w3 = Web3(Web3.HTTPProvider(RPC_URL))

# Habilitar soporte mnemonic
Account.enable_unaudited_hdwallet_features()

MNEMONIC = os.getenv("CFP_MNEMONIC")
FACTORY_ADDRESS = os.getenv("CFP_FACTORY_ADDRESS")

if not MNEMONIC:
    raise ValueError("Falta CFP_MNEMONIC")

if not FACTORY_ADDRESS:
    raise ValueError("Falta CFP_FACTORY_ADDRESS")

# Cuenta principal del servidor (owner)
server_account = Account.from_mnemonic(
    MNEMONIC,
    account_path="m/44'/60'/0'/0/0"
)

# -------------------------------------------------------------------
# ABI
# -------------------------------------------------------------------

with open("config/config.json", "r", encoding="utf-8") as file:
    config = json.load(file)

FACTORY_ABI = config["CFPFactory"]
CFP_ABI = config["CFP"]

factory = w3.eth.contract(
    address=Web3.to_checksum_address(FACTORY_ADDRESS),
    abi=FACTORY_ABI
)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def response_error(message, code):
    """Genera respuesta de error."""
    return jsonify({"message": message}), code


def is_valid_address(address):
    """Verifica si una dirección Ethereum es válida."""
    return (
        isinstance(address, str)
        and Web3.is_address(address)
    )


def is_valid_hash(value):
    """Verifica si un hash hexadecimal es válido."""
    return (
        isinstance(value, str)
        and value.startswith("0x")
        and len(value) == 66
    )


def is_valid_signature(signature):
    """Verifica si una firma es válida."""
    return (
        isinstance(signature, str)
        and signature.startswith("0x")
        and len(signature) == 132
    )


def send_transaction(tx):

    tx["nonce"] = w3.eth.get_transaction_count(server_account.address)
    tx["gas"] = 3000000

    tx["maxPriorityFeePerGas"] = w3.to_wei(1, "gwei")
    tx["maxFeePerGas"] = w3.to_wei(3, "gwei")

    signed_tx = w3.eth.account.sign_transaction(
        tx,
        server_account.key
    )

    tx_hash = w3.eth.send_raw_transaction(
        signed_tx.raw_transaction
    )

    return w3.eth.wait_for_transaction_receipt(tx_hash)


# -------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------

@app.route("/contract-address", methods=["GET"])
def contract_address():
    """Devuelve dirección del contrato factory."""
    return jsonify({
        "address": FACTORY_ADDRESS
    }), 200


@app.route("/contract-owner", methods=["GET"])
def contract_owner():
    """Devuelve dirección del owner."""

    try:

        owner = factory.functions.owner().call()

        return jsonify({
            "address": owner
        }), 200

    except Exception:
        return response_error(
            messages.INTERNAL_ERROR,
            500
        )


@app.route("/authorized/<address>", methods=["GET"])
def authorized(address):
    """Indica si una dirección está autorizada."""

    try:

        if not is_valid_address(address):
            return response_error(
                messages.INVALID_ADDRESS,
                400
            )

        result = factory.functions.isAuthorized(
            Web3.to_checksum_address(address)
        ).call()

        return jsonify({
            "authorized": result
        }), 200

    except Exception:
        return response_error(
            messages.INTERNAL_ERROR,
            500
        )


@app.route("/register", methods=["POST"])
def register():
    """Registra y autoriza una cuenta."""

    try:

        if not request.is_json:
            return response_error(
                messages.INVALID_MIMETYPE,
                400
            )

        data = request.get_json()

        if "address" not in data or "signature" not in data:
            return response_error(
                messages.MISSING_FIELD,
                400
            )

        address = data["address"]
        signature = data["signature"]

        if not is_valid_address(address):
            return response_error(
                messages.INVALID_ADDRESS,
                400
            )

        if not is_valid_signature(signature):
            return response_error(
                messages.INVALID_SIGNATURE,
                400
            )

        signable = encode_defunct(
            hexstr=FACTORY_ADDRESS
        )

        try:

            recovered = Account.recover_message(
                signable,
                signature=signature
            )

        except Exception:
            return response_error(
                messages.INVALID_SIGNATURE,
                400
            )

        if recovered.lower() != address.lower():
            return response_error(
                messages.INVALID_SIGNATURE,
                400
            )

        already = factory.functions.isAuthorized(
            Web3.to_checksum_address(address)
        ).call()

        if already:
            return response_error(
                messages.ALREADY_AUTHORIZED,
                403
            )

        tx = factory.functions.authorize(
            Web3.to_checksum_address(address)
        ).build_transaction({
            "from": server_account.address
        })

        send_transaction(tx)

        return jsonify({
            "message": messages.OK
        }), 200

    except Exception as exc:

        print(exc)

        return response_error(
            messages.INTERNAL_ERROR,
            500
        )


@app.route("/create", methods=["POST"])
def create():
    """Crea un CFP."""

    try:

        if not request.is_json:
            return response_error(
                messages.INVALID_MIMETYPE,
                400
            )

        data = request.get_json()

        required = ["callId", "closingTime", "signature"]

        for field in required:

            if field not in data:
                return response_error(
                    messages.MISSING_FIELD,
                    400
                )

        call_id = data["callId"]
        closing_time = data["closingTime"]
        signature = data["signature"]

        if not is_valid_hash(call_id):
            return response_error(
                messages.INVALID_CALLID,
                400
            )

        if not is_valid_signature(signature):
            return response_error(
                messages.INVALID_SIGNATURE,
                400
            )

        try:

            closing_dt = isoparse(closing_time)

        except Exception:
            return response_error(
                messages.INVALID_TIME_FORMAT,
                400
            )

        closing_timestamp = int(
            closing_dt.timestamp()
        )

        if closing_timestamp <= int(datetime.now().timestamp()):
            return response_error(
                messages.INVALID_CLOSING_TIME,
                400
            )

        message = (
            bytes.fromhex(FACTORY_ADDRESS[2:])
            + bytes.fromhex(call_id[2:])
            + closing_timestamp.to_bytes(32, "big")
        )

        signable = encode_defunct(message)

        try:

            creator = Account.recover_message(
                signable,
                signature=signature
            )

        except Exception:
            return response_error(
                messages.INVALID_SIGNATURE,
                400
            )

        authorized_user = factory.functions.isAuthorized(
            Web3.to_checksum_address(creator)
        ).call()

        if not authorized_user:
            return response_error(
                messages.UNAUTHORIZED,
                403
            )

        existing = factory.functions.calls(
            call_id
        ).call()

        if existing[1] != "0x0000000000000000000000000000000000000000":
            return response_error(
                messages.ALREADY_CREATED,
                403
            )

        tx = factory.functions.createFor(
            call_id,
            closing_timestamp,
            Web3.to_checksum_address(creator)
        ).build_transaction({
            "from": server_account.address
        })

        send_transaction(tx)

        return jsonify({
            "message": messages.OK
        }), 201

    except Exception as exc:

        print(exc)

        return response_error(
            messages.INTERNAL_ERROR,
            500
        )


@app.route("/calls/<call_id>", methods=["GET"])
def calls(call_id):
    """Devuelve datos de un llamado."""

    try:

        if not is_valid_hash(call_id):
            return response_error(
                messages.INVALID_CALLID,
                400
            )

        data = factory.functions.calls(
            call_id
        ).call()

        creator = data[0]
        cfp = data[1]

        if cfp == "0x0000000000000000000000000000000000000000":
            return response_error(
                messages.CALLID_NOT_FOUND,
                404
            )

        return jsonify({
            "creator": creator,
            "cfp": cfp
        }), 200

    except Exception as exc:

        print(exc)

        return response_error(
            messages.INTERNAL_ERROR,
            500
        )


@app.route("/closing-time/<call_id>", methods=["GET"])
def closing_time(call_id):
    """Devuelve closing time."""

    try:

        if not is_valid_hash(call_id):
            return response_error(
                messages.INVALID_CALLID,
                400
            )

        data = factory.functions.calls(
            call_id
        ).call()

        cfp_address = data[1]

        if cfp_address == "0x0000000000000000000000000000000000000000":
            return response_error(
                messages.CALLID_NOT_FOUND,
                404
            )

        cfp = w3.eth.contract(
            address=cfp_address,
            abi=CFP_ABI
        )

        timestamp = cfp.functions.closingTime().call()

        iso = datetime.fromtimestamp(
            timestamp
        ).astimezone().isoformat()

        return jsonify({
            "closingTime": iso
        }), 200

    except Exception as exc:

        print(exc)

        return response_error(
            messages.INTERNAL_ERROR,
            500
        )


@app.route("/register-proposal", methods=["POST"])
def register_proposal():
    """Registra una propuesta."""

    try:

        if not request.is_json:
            return response_error(
                messages.INVALID_MIMETYPE,
                400
            )

        data = request.get_json()

        required = ["callId", "proposal"]

        for field in required:
            if field not in data:
                return response_error(
                    messages.MISSING_FIELD,
                    400
                )

        call_id = data["callId"]
        proposal = data["proposal"]

        if not is_valid_hash(call_id):
            return response_error(
                messages.INVALID_CALLID,
                400
            )

        if not is_valid_hash(proposal):
            return response_error(
                messages.INVALID_PROPOSAL,
                400
            )

        call_data = factory.functions.calls(
            call_id
        ).call()

        cfp_address = call_data[1]

        if cfp_address == "0x0000000000000000000000000000000000000000":
            return response_error(
                messages.CALLID_NOT_FOUND,
                404
            )

        cfp = w3.eth.contract(
            address=cfp_address,
            abi=CFP_ABI
        )

        # Verificar si ya existe
        proposal_data = cfp.functions.proposalData(
            proposal
        ).call()

        if proposal_data[2] != 0:
            return response_error(
                messages.ALREADY_REGISTERED,
                403
            )

        tx = factory.functions.registerProposal(
            call_id,
            proposal
        ).build_transaction({
            "from": server_account.address
        })

        send_transaction(tx)

        return jsonify({
            "message": messages.OK
        }), 201

    except Exception as exc:
        print(exc)

        return response_error(
            messages.INTERNAL_ERROR,
            500
        )


@app.route("/proposal-data/<call_id>/<proposal>", methods=["GET"])
def proposal_data(call_id, proposal):
    """Devuelve información de una propuesta."""

    try:

        if not is_valid_hash(call_id):
            return response_error(
                messages.INVALID_CALLID,
                400
            )

        if not is_valid_hash(proposal):
            return response_error(
                messages.INVALID_PROPOSAL,
                400
            )

        call_data = factory.functions.calls(
            call_id
        ).call()

        cfp_address = call_data[1]

        if cfp_address == "0x0000000000000000000000000000000000000000":
            return response_error(
                messages.CALLID_NOT_FOUND,
                404
            )

        cfp = w3.eth.contract(
            address=cfp_address,
            abi=CFP_ABI
        )

        data = cfp.functions.proposalData(
            proposal
        ).call()

        sender = data[0]
        block_number = data[1]
        timestamp = data[2]

        if timestamp == 0:
            return response_error(
                messages.PROPOSAL_NOT_FOUND,
                404
            )

        iso = datetime.fromtimestamp(
            timestamp
        ).astimezone().isoformat()

        return jsonify({
            "sender": sender,
            "blockNumber": block_number,
            "timestamp": iso
        }), 200

    except Exception as exc:

        print(exc)

        return response_error(
            messages.INTERNAL_ERROR,
            500
        )


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )