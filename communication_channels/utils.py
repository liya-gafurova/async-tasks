import secrets

import bcrypt

salt = bcrypt.gensalt()


def hash_password(password: str):
    password: bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password, salt)

    return hashed


def check_password(password, actual_password_hashed):
    return bcrypt.checkpw(password.encode("utf-8"), actual_password_hashed)


def generate_key():
    return secrets.token_hex(nbytes=16)