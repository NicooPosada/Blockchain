#!/usr/bin/env python3

import argparse
import hashlib
import requests
import sys

API_URL = "http://127.0.0.1:5000"

# Calcular hash de archivo (SHA-256)
def file_hash(filename):
    try:
        with open(filename, "rb") as f:
            data = f.read()
            h = hashlib.sha256(data).hexdigest()
            return "0x" + h
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
        sys.exit(1)


# VERIFY
def verify(files):
    for file in files:
        h = file_hash(file)

        print(f"\nArchivo: {file}")
        print(f"Hash: {h}")

        try:
            r = requests.get(f"{API_URL}/stamped/{h}")

            if r.status_code == 200:
                data = r.json()
                print("Registrado!")
                print("Signer:", data["signer"])
                print("Block:", data["blockNumber"])

            elif r.status_code == 404:
                print("No registrado!")

            else:
                print("Error:", r.json())

        except Exception as e:
            print("Error conectando a la API:", e)


# STAMP
def stamp(files):
    for file in files:
        h = file_hash(file)

        print(f"\nArchivo: {file}")
        print(f"Hash: {h}")

        try:
            r = requests.post(
                f"{API_URL}/stamp",
                json={"hash": h}
            )

            if r.status_code == 201:
                data = r.json()
                print("Registrado correctamente!")
                print("TX:", data["transaction"])
                print("Block:", data["blockNumber"])

            elif r.status_code == 403:
                data = r.json()
                print("Ya estaba registrado!")
                print("Signer:", data["signer"])
                print("Block:", data["blockNumber"])

            else:
                print("Error:", r.json())

        except Exception as e:
            print("Error conectando a la API:", e)

# MAIN
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Cliente CLI para API Stamper")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # verify
    parser_verify = subparsers.add_parser("verify")
    parser_verify.add_argument("files", nargs="+", help="Archivos a verificar")

    # stamp
    parser_stamp = subparsers.add_parser("stamp")
    parser_stamp.add_argument("files", nargs="+", help="Archivos a registrar")

    args = parser.parse_args()

    if args.command == "verify":
        verify(args.files)

    elif args.command == "stamp":
        stamp(args.files)
