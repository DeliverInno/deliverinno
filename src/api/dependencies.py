import jwt
from datetime import datetime, timedelta
from typing import Generator
from sqlite3 import Connection
from fastapi import Depends, Header, HTTPException, status

from src.core.database import get_db, SECRET_KEY, ALGORITHM


def get_db_conn() -> Generator[Connection, None, None]:
    """FastAPI dependency for DB connection."""
    with get_db() as conn:
        yield conn


def create_access_token(user_id: int, role: str) -> str:
    """Create JWT token."""
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str | None = Header(default=None, alias="Authorization")) -> dict:
    """Verify JWT token from Authorization header."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )

    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        role = payload.get("role")
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        return {"id": user_id, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def require_buyer(user=Depends(verify_token)) -> dict:
    """Ensure user has buyer role."""
    if user["role"] != "buyer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Buyer role required",
        )
    return user


def require_seller(user=Depends(verify_token)) -> dict:
    """Ensure user has seller role."""
    if user["role"] != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller role required",
        )
    return user
