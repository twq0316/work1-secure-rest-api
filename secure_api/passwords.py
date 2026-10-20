import bcrypt
from flask import current_app


def hash_password(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=current_app.config["BCRYPT_ROUNDS"]),
    ).decode("utf-8")


def verify_password(password, password_hash):
    return bcrypt.checkpw(
        password.encode("utf-8"), password_hash.encode("utf-8")
    )

