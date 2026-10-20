import os
import secrets
from pathlib import Path

from flask import Flask

from . import db
from .routes import api


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    configured_secret = os.environ.get("JWT_SECRET")
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "DATABASE_PATH", str(Path(app.instance_path) / "work1.sqlite")
        ),
        JWT_SECRET=configured_secret or secrets.token_hex(32),
        JWT_ALGORITHM="HS256",
        JWT_EXP_MINUTES=int(os.environ.get("JWT_EXP_MINUTES", "30")),
        BCRYPT_ROUNDS=int(os.environ.get("BCRYPT_ROUNDS", "12")),
        JSON_SORT_KEYS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(api)

    return app

