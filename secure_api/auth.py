from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from .db import get_db
from .passwords import verify_password


def issue_token(user_id, username):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=current_app.config["JWT_EXP_MINUTES"]),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")
        scheme, separator, token = authorization.partition(" ")
        if not separator or scheme.lower() != "bearer" or not token:
            return jsonify({"error": "Bearer token required"}), 401

        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
                options={"require": ["exp", "iat", "sub"]},
            )
            user_id = int(payload["sub"])
        except (jwt.PyJWTError, TypeError, ValueError):
            return jsonify({"error": "Invalid or expired token"}), 401

        user = get_db().execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user is None:
            return jsonify({"error": "Invalid or expired token"}), 401

        g.current_user = {"id": user["id"], "username": user["username"]}
        return view(*args, **kwargs)

    return wrapped

