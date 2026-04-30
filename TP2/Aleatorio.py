import requests

server = "https://cripto.iua.edu.ar/blockchain"
email = "fposada183@alumnos.iua.edu.ar"

a = 25214903917
b = 11
m = 1 << 48

def next_seed(seed):
    return (seed * a + b) & (m - 1)

def next_int(seed):
    return seed >> 16

response = requests.get(f"{server}/javarand/{email}/challenge")
x1 = int(response.text)
print("Primer número:", x1)

response = requests.get(f"{server}/javarand/{email}/challenge")
x2 = int(response.text)
print("Segundo número:", x2)

x1 &= 0xffffffff
x2 &= 0xffffffff

print("Buscando seed")

seed_found = None

for guess in range(1 << 16):

    seed = (x1 << 16) | guess

    next_s = next_seed(seed)

    if next_int(next_s) == x2:
        seed_found = next_s
        print("Seed encontrada:", seed)
        break

if seed_found is None:
    print("No se encontró seed")
    exit()

next_s = next_seed(seed_found)
prediction = next_int(next_s)

if prediction >= 2**31:
    prediction -= 2**32

print("Predicción:", prediction)

response = requests.post(
    f"{server}/javarand/{email}/answer",
    files={"number": str(prediction).encode()}
)

print("Status:", response.status_code)
print(response.text)