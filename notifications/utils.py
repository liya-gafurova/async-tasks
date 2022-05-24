import secrets


def generate_key():
    return secrets.token_hex(16)
