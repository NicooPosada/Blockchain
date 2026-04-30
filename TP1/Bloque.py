import requests
import base64
from hashlib import sha256
from datetime import datetime

server = "https://cripto.iua.edu.ar/blockchain"
email = "fposada183@alumnos.iua.edu.ar"

response = requests.get(f"{server}/pow/{email}/blocks/latest")
block = base64.b64decode(response.content)

print("Longitud:", len(block))

block_number = int.from_bytes(block[:8], "big")
print("Número de bloque:", block_number)

timestamp = int.from_bytes(block[8:16], "big")
print("Timestamp:", timestamp)

date_and_time = datetime.fromtimestamp(timestamp)
print("Fecha y hora:", date_and_time)

msb_64_target = int.from_bytes(block[16:24], "big")

target = msb_64_target << 192
target_bytes = block[16:24] + b'\0'*24

print("Target:", target_bytes.hex())

new_block_number = block_number + 1
new_timestamp = int(datetime.now().timestamp())
new_target = block[16:24]

previous_block_hash = sha256(block).digest()
email_hash = sha256(email.encode("utf-8")).digest()

new_block = bytearray(96)

new_block[0:8] = new_block_number.to_bytes(8, "big")
new_block[8:16] = new_timestamp.to_bytes(8, "big")
new_block[16:24] = new_target
new_block[32:64] = previous_block_hash
new_block[64:96] = email_hash

print("Bloque base:", new_block.hex())

print("Minando bloque:")

nonce = 0

while True:

    new_block[24:32] = nonce.to_bytes(8, "big")

    new_hash = sha256(new_block).digest()

    if new_hash < target_bytes:
        print("Bloque encontrado!")
        print("Nonce:", nonce)
        print("Hash:", new_hash.hex())
        break

    nonce += 1

encoded_block = base64.b64encode(new_block)

response = requests.post(
    f"{server}/pow/{email}/blocks",
    files={"block": encoded_block}
)

print("Respuesta del servidor:", response.status_code)
print(response.text)