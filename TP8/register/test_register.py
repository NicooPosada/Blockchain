from eth_account import Account
from eth_account.messages import encode_defunct

FACTORY_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

account = Account.from_key(PRIVATE_KEY)

message = encode_defunct(
    hexstr=FACTORY_ADDRESS
)

signed = Account.sign_message(
    message,
    PRIVATE_KEY
)

print("address:", account.address)
print("signature:", signed.signature.hex())