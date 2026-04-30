#!/usr/bin/env python3

import argparse
from web3 import Web3
from web3.middleware.geth_poa import geth_poa_middleware


def address(x):
    if x[:2] == "0x" or x[:2] == "0X":
        try:
            b = bytes.fromhex(x[2:])
            if len(b) == 20:
                return x
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"Invalid address: '{x}'")


def shorten(addr):
    return addr[:8]


if __name__ == "__main__":

    DEFAULT_WEB3_URI = "~/blockchain-iua/bfatest/node/geth.ipc"

    parser = argparse.ArgumentParser()

    parser.add_argument("addresses", metavar="ADDRESS", type=address, nargs="*")
    parser.add_argument("--add", action="store_true", default=False)
    parser.add_argument("--first-block", "-f", type=int, default=0)
    parser.add_argument("--last-block", "-l", default="latest")
    parser.add_argument("--format", choices=["plain", "graphviz"], default="plain")
    parser.add_argument("--short", action="store_true")
    parser.add_argument("--uri", default=DEFAULT_WEB3_URI)

    args = parser.parse_args()

    # Conexión al nodo
    w3 = Web3(Web3.IPCProvider(args.uri))

    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    if not w3.is_connected():
        print("Error conectando al nodo")
        exit(1)

    # Determinar rango de bloques
    first_block = args.first_block

    if args.last_block == "latest":
        last_block = w3.eth.block_number
    else:
        last_block = int(args.last_block)

    # Direcciones a filtrar
    tracked = set(args.addresses)

    # Para graphviz
    if args.format == "graphviz":
        print("digraph Transfers {")

    # Recorrer bloques
    for i in range(first_block, last_block + 1):

        block = w3.eth.get_block(i, full_transactions=True)

        for tx in block.transactions:

            # Solo transferencias de ether
            if tx["value"] == 0:
                continue

            src = tx["from"]
            dst = tx["to"]
            value = w3.from_wei(tx["value"], "ether")

            # Filtro por direcciones
            if tracked:
                if src not in tracked and dst not in tracked:
                    continue

            # Opción --add
            if args.add:
                tracked.add(src)
                tracked.add(dst)

            # Opción --short
            if args.short:
                src_out = shorten(src)
                dst_out = shorten(dst)
            else:
                src_out = src
                dst_out = dst

            # Formato de salida
            if args.format == "plain":
                print(f"{src_out} -> {dst_out}: {value} ether ({i})")

            elif args.format == "graphviz":
                print(f"\"{src_out}\" -> \"{dst_out}\" [label=\"{value} ether ({i})\"]")

    if args.format == "graphviz":
        print("}")