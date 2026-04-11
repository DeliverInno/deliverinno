from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.database import SECRET_KEY, ALGORITHM, Database


_db = Database(path="data/deliverinno.db")
_db.init_db()


def get_db_conn():
    with _db.get_db() as conn:
        yield conn


def create_access_token(user_id: int, role: str) -> str:
    """Create JWT token."""
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


http_bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
        user_id = int(user_id)
    except (jwt.InvalidTokenError, ValueError):
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
