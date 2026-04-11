from datetime import datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.database import SECRET_KEY, ALGORITHM, Database


# Initialize database connection pool (singleton)
_db = Database(path="data/deliverinno.db")
_db.init_db()


def get_db_conn():
    """
    Get SQLite database connection from pool.

    Yields connection from context manager to ensure cleanup.
    Used in every endpoint that needs database access.
    """
    with _db.get_db() as conn:
        yield conn


def create_access_token(user_id: int, role: str) -> str:
    """
    Create JWT access token valid for 24 hours.

    Args:
        user_id: User's database ID
        role: User role (buyer or seller)

    Returns:
        JWT token string encoded with SECRET_KEY
    """
    # Create JWT payload with user info and expiration
    payload = {
        "sub": str(user_id),           # Subject: user ID
        "role": role,                  # User role for RBAC
        "exp": datetime.utcnow() + timedelta(hours=24),  # Expires in 24h
    }

    # Encode payload into JWT token using SECRET_KEY and ALGORITHM
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# HTTP Bearer authentication scheme
http_bearer = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)]
) -> dict:
    """
    Validate JWT token and extract user info.

    Called by FastAPI on every protected endpoint.
    Raises 401 if token invalid, expired, or missing.

    Returns:
        {"id": user_id, "role": user_role}
    """
    # Create exception template for invalid credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # STEP 1: Extract JWT token from Authorization header
        token = credentials.credentials

        # STEP 2: Decode JWT token using SECRET_KEY
        # Validates signature and checks expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # STEP 3: Extract user ID and role from payload
        user_id = payload.get("sub")
        role = payload.get("role")

        # STEP 4: Validate required fields present
        if user_id is None or role is None:
            raise credentials_exception

        # STEP 5: Convert user_id from string to int
        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError):
        # Token is invalid, expired, or malformed
        raise credentials_exception

    # Return authenticated user info
    return {"id": user_id, "role": role}


def require_buyer(user=Depends(get_current_user)) -> dict:
    """
    Enforce buyer role requirement.

    Add to endpoint signature to restrict access to buyers only.
    Returns 403 if user is not a buyer.

    Args:
        user: Current authenticated user from get_current_user

    Returns:
        User dict if role is buyer

    Raises:
        HTTPException 403: If user role is not buyer
    """
    # Check if user has buyer role
    if user["role"] != "buyer":
        # User is authenticated but lacks required role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Buyer role required",
        )
    return user


def require_seller(user=Depends(get_current_user)) -> dict:
    """
    Enforce seller role requirement.

    Add to endpoint signature to restrict access to sellers only.
    Returns 403 if user is not a seller.

    Args:
        user: Current authenticated user from get_current_user

    Returns:
        User dict if role is seller

    Raises:
        HTTPException 403: If user role is not seller
    """
    # Check if user has seller role
    if user["role"] != "seller":
        # User is authenticated but lacks required role
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller role required",
        )
    return user
