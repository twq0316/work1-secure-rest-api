import pytest

from secure_api import create_app
from secure_api.db import init_db


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.sqlite"),
            "JWT_SECRET": "test-only-secret-that-is-long-enough",
            "JWT_EXP_MINUTES": 30,
            "BCRYPT_ROUNDS": 4,
        }
    )
    with application.app_context():
        init_db(demo_username="alice", demo_password="CorrectHorseBatteryStaple!")
    yield application


@pytest.fixture
def client(app):
    return app.test_client()

