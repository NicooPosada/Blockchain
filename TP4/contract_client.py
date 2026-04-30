#!/usr/bin/env python3

import os
import json
import getpass
from web3 import Web3
from eth_account import Account

KEYSTORE_DIR = os.path.expanduser("~/.ethereum/keystore")
DEFAULT_WEB3_URI = os.path.expanduser("~/blockchain-iua/bfatest/node/geth.ipc")

# Cargar cuenta
def load_account():
    files = sorted(os.listdir(KEYSTORE_DIR))
    keystore_file = os.path.join(KEYSTORE_DIR, files[0])

    with open(keystore_file) as f:
        keystore = json.load(f)

    password = getpass.getpass("Password: ")
    private_key = Account.decrypt(keystore, password)
    account = Account.from_key(private_key)

    return account


# Conectar a web3
def connect():
    w3 = Web3(Web3.IPCProvider(DEFAULT_WEB3_URI))

    if not w3.is_connected():
        print("Error conectando al nodo")
        exit(1)

    return w3

# Cargar contrato
def load_contract(w3):
    with open("Stamper.json") as f:
        config = json.load(f)

    address = config["networks"]["55555000000"]["address"]
    abi = config["abi"]

    contract = w3.eth.contract(address=address, abi=abi)
    return contract


# Consultar stamped (CALL)
def stamped(contract, hash_value):
    result = contract.functions.stamped(hash_value).call()

    signer = result[0]
    block = result[1]

    print("Signer:", signer)
    print("Block:", block)


# Hacer stamp (TRANSACTION)
def stamp(w3, contract, account, private_key, hash_value):
    try:
        # Construir transacción
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

        print("TX enviada:", tx_hash.hex())

        # Esperar confirmación
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print("Bloque:", receipt.blockNumber)

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    w3 = connect()
    account = load_account()
    private_key = account.key

    contract = load_contract(w3)

    # PRUEBAS
    test_hash = "0x" + os.urandom(32).hex()

    print("\n--- Probando stamped ---")
    stamped(contract, test_hash)

    print("\n--- Probando stamp ---")
    stamp(w3, contract, account, private_key, test_hash)

