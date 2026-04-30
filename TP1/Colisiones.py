from hashlib import sha256

email = "fposada183@alumnos.iua.edu.ar"
hashes = {}

i = 0

while True:

    msj = f"{email}{i}"

    h = sha256(msj.encode()).hexdigest()[:12]

    if h in hashes and hashes[h] != msj:
        print("-------------------")
        print("COLISION ENCONTRADA")
        print("-------------------")
        print("Mensaje 1: ", hashes[h])
        print("Mensaje 2: ", msj)
        print("Hash: ", h)
        break

    hashes[h] = msj
    i += 1