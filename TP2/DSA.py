import requests
import base64
from hashlib import sha256

server = "https://cripto.iua.edu.ar/blockchain"
email = "fposada183@alumnos.iua.edu.ar"

def modinv(a, m):
    """Inverso modular usando pow"""
    return pow(a, -1, m)

def hash_msg(msg_bytes):
    """SHA-256 del mensaje"""
    return int.from_bytes(sha256(msg_bytes).digest(), 'big')

response = requests.get(f"{server}/dsa/{email}/public-key")
pub = response.json()

p = int(pub["P"])
q = int(pub["Q"])
g = int(pub["G"])
y = int(pub["Y"])

print("Clave pública obtenida")

signatures = {}

i = 0

print("Buscando firmas con mismo r")

while True:

    msg = f"mensaje_{i}".encode()
    msg_b64 = base64.b64encode(msg)

    response = requests.post(
        f"{server}/dsa/{email}/sign",
        files={"message": msg_b64}
    )

    data = response.json()
    r = int(data["r"])
    s = int(data["s"])

    if r in signatures:
        print("Reutilización de k detectada!")
        msg1, s1 = signatures[r]
        msg2, s2 = msg, s
        break

    signatures[r] = (msg, s)
    i += 1

h1 = hash_msg(msg1)
h2 = hash_msg(msg2)

k = ((h1 - h2) * modinv(s1 - s2, q)) % q

print("k encontrado:", k)

x = (modinv(r, q) * (k * s1 - h1)) % q

print("Clave privada encontrada:", x)

response = requests.post(
    f"{server}/dsa/{email}/answer",
    files={"private-key": str(x).encode()}
)

print("Status:", response.status_code)
print(response.text)