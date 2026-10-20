from datetime import datetime, timedelta, timezone

import jwt


DEMO_USER = {"username": "alice", "password": "CorrectHorseBatteryStaple!"}


def login(client):
    response = client.post("/auth/login", json=DEMO_USER)
    assert response.status_code == 200
    return response.get_json()["access_token"]


def test_login_returns_jwt(client):
    response = client.post("/auth/login", json=DEMO_USER)

    assert response.status_code == 200
    body = response.get_json()
    assert body["scheme"] == "Bearer"
    assert body["access_token"].count(".") == 2


def test_login_rejects_wrong_password(client):
    response = client.post(
        "/auth/login", json={"username": "alice", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Invalid credentials"}


def test_login_rejects_sql_injection(client):
    response = client.post(
        "/auth/login",
        json={"username": "alice' OR '1'='1", "password": "anything"},
    )

    assert response.status_code == 401


def test_data_requires_a_token(client):
    response = client.get("/api/data")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Bearer token required"}


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/api/data", headers={"Authorization": "Bearer not-a-valid-token"}
    )

    assert response.status_code == 401


def test_expired_token_is_rejected(app, client):
    now = datetime.now(timezone.utc)
    expired = jwt.encode(
        {
            "sub": "1",
            "username": "alice",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
        },
        app.config["JWT_SECRET"],
        algorithm="HS256",
    )

    response = client.get(
        "/api/data", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401


def test_authenticated_data_uses_parameterized_query(client):
    token = login(client)
    response = client.get(
        "/api/data", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.get_json()["username"] == "alice"
    assert len(response.get_json()["items"]) >= 2


def test_created_user_data_is_html_escaped(client):
    token = login(client)
    payload = {
        "title": '<script>alert("xss")</script>',
        "content": "<img src=x onerror=alert(1)>",
    }
    response = client.post(
        "/api/items",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    item = response.get_json()["item"]
    assert item["title"] == "&lt;script&gt;alert(&#34;xss&#34;)&lt;/script&gt;"
    assert item["content"] == "&lt;img src=x onerror=alert(1)&gt;"
    assert "<script>" not in response.get_data(as_text=True)

