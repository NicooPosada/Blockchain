#!/usr/bin/env python3

import os
import json
import getpass
from eth_account import Account

KEYSTORE_DIR = os.path.expanduser("~/.ethereum/keystore")


def load_first_account():
    # 1. Listar archivos del keystore
    files = sorted(os.listdir(KEYSTORE_DIR))

    if not files:
        print("No hay cuentas en el keystore")
        exit(1)

    # 2. Tomar el primero (orden lexicográfico)
    keystore_file = os.path.join(KEYSTORE_DIR, files[0])

    print(f"Usando keystore: {files[0]}")

    # 3. Leer archivo JSON
    with open(keystore_file) as f:
        keystore = json.load(f)

    # 4. Pedir contraseña (oculta)
    password = getpass.getpass("Ingrese contraseña: ")

    try:
        # 5. Desencriptar cuenta
        account = Account.decrypt(keystore, password)

        # 6. Obtener private key en formato hex
        private_key = account.hex()

        # 7. Obtener address
        addr = Account.from_key(private_key).address

        print("\nCuenta cargada correctamente")
        print("Address:", addr)
        print("Private key:", private_key)

        return private_key, addr

    except Exception as e:
        print("Error: contraseña incorrecta o archivo inválido")
        exit(1)


if __name__ == "__main__":
    load_first_account()
