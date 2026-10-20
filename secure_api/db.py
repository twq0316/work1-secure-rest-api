import os
import sqlite3
from pathlib import Path

import click
from flask import current_app, g

from .passwords import hash_password


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_items_user_id ON items (user_id);
"""


def get_db():
    if "db" not in g:
        database_path = Path(current_app.config["DATABASE"])
        database_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_db(demo_username=None, demo_password=None):
    database = get_db()
    database.executescript(SCHEMA)

    username = demo_username or os.environ.get("DEMO_USERNAME", "alice")
    password = demo_password or os.environ.get(
        "DEMO_PASSWORD", "ChangeMe-OnlyForLocal-123!"
    )

    existing = database.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing is None:
        cursor = database.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        user_id = cursor.lastrowid
    else:
        user_id = existing["id"]

    item_count = database.execute(
        "SELECT COUNT(*) AS count FROM items WHERE user_id = ?", (user_id,)
    ).fetchone()["count"]
    if item_count == 0:
        database.executemany(
            "INSERT INTO items (user_id, title, content) VALUES (?, ?, ?)",
            [
                (user_id, "Welcome", "This record is visible only to its owner."),
                (user_id, "Security demo", "Try a script tag and inspect the escaped response."),
            ],
        )
    database.commit()


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("Database initialized and demo data seeded.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

