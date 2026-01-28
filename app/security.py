import os
from cryptography.fernet import Fernet

FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    raise RuntimeError(
        "FERNET_KEY is missing. Generate one using Fernet.generate_key() "
        "and set it in your environment variables."
    )

fernet = Fernet(FERNET_KEY)


def encrypt_token(token: str) -> str:
    return fernet.encrypt(token.encode()).decode()


def decrypt_token(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()
