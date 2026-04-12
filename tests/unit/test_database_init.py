"""Tests for database initialization (init_db)."""

from src.core.database import Database


def test_init_db_creates_demo_users():
    """Test that demo users are created when DB is empty."""
    test_db = Database(":memory:")
    test_db.init_db()

    conn = test_db.get_connection()

    users = conn.execute("SELECT username FROM users").fetchall()
    usernames = {u["username"] for u in users}

    assert "demo_seller" in usernames
    assert "demo_buyer" in usernames

    conn.close()


def test_init_db_does_not_duplicate_demo_users():
    """Test that demo users are not duplicated if already exist."""
    test_db = Database(":memory:")

    # first init
    test_db.init_db()

    # second init (должно НЕ создать новых)
    test_db.init_db()

    conn = test_db.get_connection()

    users = conn.execute(
        "SELECT username, COUNT(*) as cnt FROM users GROUP BY username"
    ).fetchall()

    for row in users:
        assert row["cnt"] == 1  # каждый пользователь только один

    conn.close()
