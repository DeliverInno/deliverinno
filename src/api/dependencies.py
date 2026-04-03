from typing import Generator
from sqlite3 import Connection
from fastapi import Depends, Header, HTTPException, status

from src.core.database import get_db


def get_db_conn() -> Generator[Connection, None, None]:
    """FastAPI dependency for DB connection."""
    with get_db() as conn:
        yield conn


def get_current_user(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
    conn: Connection = Depends(get_db_conn),
):
    """Resolve current user by X-User-Id header."""
    if x_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-User-Id")

    user = conn.execute("SELECT * FROM users WHERE id = ?", (x_user_id,)).fetchone()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")

    return user


def require_buyer(user=Depends(get_current_user)):
    """Ensure user has buyer role."""
    if user["role"] != "buyer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Buyer role required")
    return user
