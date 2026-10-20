from flask import Blueprint, g, jsonify, request
from markupsafe import escape

from .auth import auth_required, issue_token
from .db import get_db
from .passwords import verify_password


api = Blueprint("api", __name__)


def _escaped(value):
    return str(escape(value))


@api.post("/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"error": "username and password must be strings"}), 400
    if not username or not password or len(password.encode("utf-8")) > 72:
        return jsonify({"error": "Invalid credentials"}), 401

    user = get_db().execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()

    if user is None or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify(
        {
            "access_token": issue_token(user["id"], user["username"]),
            "scheme": "Bearer",
        }
    )


@api.get("/api/data")
@auth_required
def data():
    rows = get_db().execute(
        """
        SELECT id, title, content, created_at
        FROM items
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (g.current_user["id"],),
    ).fetchall()

    items = [
        {
            "id": row["id"],
            "title": _escaped(row["title"]),
            "content": _escaped(row["content"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    return jsonify({"username": _escaped(g.current_user["username"]), "items": items})


@api.post("/api/items")
@auth_required
def create_item():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    content = body.get("content")

    if not isinstance(title, str) or not isinstance(content, str):
        return jsonify({"error": "title and content must be strings"}), 400
    title = title.strip()
    content = content.strip()
    if not title or not content or len(title) > 100 or len(content) > 500:
        return jsonify({"error": "title or content has an invalid length"}), 400

    database = get_db()
    cursor = database.execute(
        "INSERT INTO items (user_id, title, content) VALUES (?, ?, ?)",
        (g.current_user["id"], title, content),
    )
    database.commit()

    return (
        jsonify(
            {
                "item": {
                    "id": cursor.lastrowid,
                    "title": _escaped(title),
                    "content": _escaped(content),
                }
            }
        ),
        201,
    )

