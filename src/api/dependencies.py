from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta
from typing import Annotated, Generator
from sqlite3 import Connection
from fastapi import Depends, HTTPException, status

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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    return {"id": user_id, "role": role}


def require_buyer(user=Depends(get_current_user)) -> dict:
    """Ensure user has buyer role."""
    if user["role"] != "buyer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Buyer role required",
        )
    return user


def require_seller(user=Depends(get_current_user)) -> dict:
    """Ensure user has seller role."""
    if user["role"] != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller role required",
        )
    return user
