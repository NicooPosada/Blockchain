#!/usr/bin/env python3

import argparse
import sys
import os
from web3 import Web3

DEFAULT_WEB3_URI = "~/blockchain-iua/bfatest/node/geth.ipc"

def connect(uri):
    uri = os.path.expanduser(uri)
    w3 = Web3(Web3.IPCProvider(uri))
    
    if not w3.is_connected():
        print("Error: No se pudo conectar al nodo", file=sys.stderr)
        sys.exit(1)
    
    return w3


def balance(account, unit):
    w3 = connect(args.uri)

    try:
        balance_wei = w3.eth.get_balance(account)
        balance_converted = w3.from_wei(balance_wei, unit)
        print(f"Balance de {account}: {balance_converted} {unit}")
    except Exception as e:
        print(f"Error al obtener balance: {e}", file=sys.stderr)
        sys.exit(1)


def transfer(src, dst, amount, unit):
    w3 = connect(args.uri)

    try:
        # Convertir a wei
        value = w3.to_wei(amount, unit)

        password = input(f"Ingrese password para {src}: ")

        # Desbloquear cuenta
        w3.geth.personal.unlock_account(src, password)

        # Crear transacción
        tx = {
            "from": src,
            "to": dst,
            "value": value
        }

        # Enviar transacción
        tx_hash = w3.eth.send_transaction(tx)

        print("Transferencia enviada!")
        print("Hash:", tx_hash.hex())

    except Exception as e:
        print(f"Error en la transferencia: {e}", file=sys.stderr)
        sys.exit(1)


def accounts():
    w3 = connect(args.uri)

    try:
        accs = w3.eth.accounts
        if not accs:
            print("No hay cuentas en el nodo")
        else:
            print("Cuentas:")
            for acc in accs:
                print(acc)
    except Exception as e:
        print(f"Error al listar cuentas: {e}", file=sys.stderr)
        sys.exit(1)


def address(x):
    if x[:2] == '0x' or x[:2] == '0X':
        try:
            b = bytes.fromhex(x[2:])
            if len(b) == 20:
                return x
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"Invalid address: '{x}'")                                                                                        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        f"""Maneja los fondos de una cuenta en una red ethereum.
        Permite consultar el balance y realizar transferencias. Por defecto, intenta conectarse mediante '{DEFAULT_WEB3_URI}'""")

    parser.add_argument("--uri", help="URI para la conexión con geth", default=DEFAULT_WEB3_URI)

    subparsers = parser.add_subparsers(title="command", dest="command")
    subparsers.required = True

    parser_balance = subparsers.add_parser("balance", help="Obtiene el balance de una cuenta")
    parser_balance.add_argument("--unit", choices=['wei', 'Kwei', 'Mwei', 'Gwei', 'microether', 'milliether','ether'], default='wei')
    parser_balance.add_argument("--account", "-a", type=address, required=True)

    parser_transfer = subparsers.add_parser("transfer", help="Transfiere fondos de una cuenta a otra")
    parser_transfer.add_argument("--from", type=address, required=True, dest='src')
    parser_transfer.add_argument("--to", type=address, required=True, dest='dst')
    parser_transfer.add_argument("--amount", type=int, required=True)
    parser_transfer.add_argument("--unit", choices=['wei', 'Kwei', 'Mwei', 'Gwei', 'microether', 'milliether','ether'], default='wei')

    parser_accounts = subparsers.add_parser("accounts", help="Lista las cuentas de un nodo")

    args = parser.parse_args()

    if args.command == "balance":
        balance(args.account, args.unit)
    elif args.command == "transfer":
        transfer(args.src, args.dst, args.amount, args.unit)
    elif args.command == "accounts":
        accounts()
    else:
        print(f"Comando desconocido: {args.command}", file=sys.stderr)
        sys.exit(1)