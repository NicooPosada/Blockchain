Trabajo Práctico 4

Descripción:
 Se implementó una API REST en Python que interactúa con un contrato inteligente en Ethereum,
junto con un cliente de línea de comandos para registrar y verificar hashes de archivos.

Arquitectura:
 Usuario → client.py → API (apiserver.py) → Smart Contract

Requisitos:
 - Python 3
 - Nodo Ethereum (geth)
 - Archivo `Stamper.json`
 - Keystore en `~/.ethereum/keystore`

Instalar dependencias:
 pip install flask web3 eth-account requests jsonschema

Ejecución:
1- Levantar nodo Ethereum:
    cd ~/blockchain-iua/bfatest
    geth -datadir node -config config.toml
2- Activar entorno Python (en otra terminal):
    cd ~/blockchain-iua/bfatest
    source web3py/bin/activate
3- Ejecutar la API:
    python3 apiserver.py
    Disponible en: [http://127.0.0.1:5000]
4- Ejecutar tests (otra terminal):
    cd ~/blockchain-iua/bfatest
    source web3py/bin/activate
    pytest test_apiserver.py
5- Usar Cliente CLI (otra terminal):
 Verificar archivo:
    python3 client.py verify archivo.txt
 Registrar archivos:
    python3 client.py stamp archivo.txt

Endpoints:

GET /stamped/<hash>

 - 200: devuelve signer y blockNumber
 - 404: no registrado
 - 400: hash inválido

POST /stamp

 - 201: registrado correctamente
 - 403: hash ya existe
 - 400: error en datos

Tests
 Archivo: `test_apiserver.py`

Ejecutar:
 pytest test_apiserver.py

Valida:

 - formatos de hash y firma
 - respuestas HTTP
 - registro y verificación
 - manejo de errores

Conclusión:
 Se desarrolló una solución completa para interactuar con un contrato en blockchain mediante una API REST,
 un cliente CLI y pruebas automatizadas.
