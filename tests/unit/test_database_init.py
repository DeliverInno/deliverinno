"""Tests for database initialization (init_db)."""

import sqlite3

from src.core.database import init_db, DB_PATH


def remove_db():
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_init_db_creates_demo_users():
    """Test that demo users are created when DB is empty."""
    remove_db()

    # init DB
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    users = conn.execute("SELECT username FROM users").fetchall()
    usernames = {u["username"] for u in users}

    assert "demo_seller" in usernames
    assert "demo_buyer" in usernames

    conn.close()


def test_init_db_does_not_duplicate_demo_users():
    """Test that demo users are not duplicated if already exist."""
    remove_db()

    # first init
    init_db()

    # second init (должно НЕ создать новых)
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    users = conn.execute(
        "SELECT username, COUNT(*) as cnt FROM users GROUP BY username"
    ).fetchall()

    for row in users:
        assert row["cnt"] == 1  # каждый пользователь только один

    conn.close()
