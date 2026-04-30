#!/usr/bin/env python3

import os
import json
import getpass
from flask import Flask, request, jsonify
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

# Config
KEYSTORE_DIR = os.path.expanduser("~/.ethereum/keystore")
WEB3_URI = os.path.expanduser("~/blockchain-iua/bfatest/node/geth.ipc")

app = Flask(__name__)

# Cargar cuenta
def load_account():
    files = sorted(os.listdir(KEYSTORE_DIR))
    keystore_file = os.path.join(KEYSTORE_DIR, files[0])

    with open(keystore_file) as f:
        keystore = json.load(f)

    password = getpass.getpass("Password: ")
    private_key = Account.decrypt(keystore, password)
    account = Account.from_key(private_key)

    return account, private_key

# Validar firma
def is_valid_signature(hash_value, signature):
    if not signature.startswith("0x"):
        return False

    if len(signature) != 132:
        return False

    try:
        bytes.fromhex(signature[2:])
    except ValueError:
        return False

    try:
        msg = encode_defunct(hexstr=hash_value)
        Account.recover_message(msg, signature=signature)
    except Exception:
        return False

    return True

# Conectar nodo
w3 = Web3(Web3.IPCProvider(WEB3_URI))

if not w3.is_connected():
    print("Error conectando al nodo")
    exit(1)

# Cargar contrato
with open("Stamper.json") as f:
    config = json.load(f)

contract = w3.eth.contract(
    address=config["networks"]["55555000000"]["address"],
    abi=config["abi"]
)

# Cargar cuenta
account, private_key = load_account()

# ENDPOINT: GET /stamped/<hash>
@app.route("/stamped/<hash_value>", methods=["GET"])
def get_stamped(hash_value):

    # Validación de hash
    if not hash_value.startswith("0x") or len(hash_value) != 66:
        return jsonify({"message": "Invalid hash"}), 400

    try:
        result = contract.functions.stamped(hash_value).call()

        signer = result[0]
        block = result[1]

        if signer == "0x0000000000000000000000000000000000000000":
            return jsonify({"message": "Hash not found"}), 404

        return jsonify({
            "signer": signer,
            "blockNumber": block
        }), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 400

# ENDPOINT: POST /stamp
@app.route("/stamp", methods=["POST"])
def post_stamp():

    # Validar content-type
    if not request.is_json:
        return jsonify({"message": "Invalid content-type"}), 400

    # Validar JSON
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"message": "Invalid JSON"}), 400

    if data is None:
        return jsonify({"message": "Invalid JSON"}), 400

    hash_value = data.get("hash")
    signature = data.get("signature")

    # Validar hash
    if not hash_value or not hash_value.startswith("0x") or len(hash_value) != 66:
        return jsonify({"message": "Invalid hash"}), 400

    # Validar firma (si viene)
    if signature is not None:
        if not is_valid_signature(hash_value, signature):
            return jsonify({"message": "Invalid signature"}), 400

    try:
        # Construir transacción
        if signature:
            tx = contract.functions.stampSigned(hash_value, signature).build_transaction({
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "gasPrice": w3.eth.gas_price,
                "chainId": w3.eth.chain_id
            })
        else:
            tx = contract.functions.stamp(hash_value).build_transaction({
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "gasPrice": w3.eth.gas_price,
                "chainId": w3.eth.chain_id
            })

        # Firmar
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)

        # Enviar
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Esperar recibo
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 0:
            raise Exception("Transaction failed")

        return jsonify({
            "transaction": tx_hash.hex(),
            "blockNumber": receipt.blockNumber
        }), 201

    except Exception:

        # Caso hash ya registrado
        try:
            result = contract.functions.stamped(hash_value).call()
            signer = result[0]
            block = result[1]

            if signer != "0x0000000000000000000000000000000000000000":
                return jsonify({
                    "message": "Hash already stamped",
                    "signer": signer,
                    "blockNumber": block
                }), 403
        except:
            pass

        return jsonify({"message": "Transaction failed"}), 400

# MAIN
if __name__ == "__main__":
    app.run(debug=True)