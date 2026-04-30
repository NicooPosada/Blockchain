import json
import os
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Conexión al nodo
w3 = Web3(Web3.IPCProvider(os.path.expanduser("~/blockchain-iua/bfatest/node/geth.ipc")))

# Middleware POA (IMPORTANTÍSIMO)
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

if not w3.is_connected():
    print("Error conectando al nodo")
    exit(1)

# Leer JSON del contrato
with open("Stamper.json") as f:
    config = json.load(f)

abi = config["abi"]
address = config["networks"]["55555000000"]["address"]

# Crear objeto contrato
contract = w3.eth.contract(address=address, abi=abi)

# Hash de prueba (random o uno tuyo)
test_hash = "0x" + "0"*64  # hash dummy

# Llamada al contrato (NO gasta gas)
result = contract.functions.stamped(test_hash).call()

print("Resultado:")
print("Signer:", result[0])
print("Block:", result[1])
