import bcrypt

salt = bcrypt.gensalt()


def hash_password(password: str):
    password: bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password, salt)

    return hashed


w = "eraergstgsrde"
hashed = hash_password(w)
print(bcrypt.checkpw("eraergstgsrde".encode("utf-8"), hashed))