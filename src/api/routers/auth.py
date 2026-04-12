from sqlite3 import Connection
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_db_conn, create_access_token
from src.core.database import hash_password

TOKEN_TYPE = "bearer"  # nosec B105

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """User registration request model."""
    username: str = Field(min_length=3, max_length=50, description="Unique username")
    password: str = Field(min_length=4, max_length=128, description="User password")
    role: Literal["buyer", "seller"] = Field(description="User role in system")


class LoginRequest(BaseModel):
    """User login request model."""
    username: str = Field(description="Registered username")
    password: str = Field(description="User password")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, conn: Connection = Depends(get_db_conn)):
    """
    Register new user.

    Returns: access_token, token_type, user_id, username, role
    Raises: 400 if username already exists
    """
    # STEP 1: Check if username already exists in database
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (payload.username,),
    ).fetchone()

    if existing:
        # Username is taken
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # STEP 2: Hash password using bcrypt
    password_hash = hash_password(payload.password)

    # STEP 3: Insert new user into database
    cursor = conn.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (payload.username, password_hash, payload.role),
    )
    user_id = cursor.lastrowid or 0
    user_id = int(user_id)

    # STEP 4: Generate JWT access token (valid for 24 hours)
    token = create_access_token(user_id, payload.role)

    # STEP 5: Return user info with token
    return {
        "access_token": token,
        "token_type": TOKEN_TYPE,
        "id": user_id,
        "username": payload.username,
        "role": payload.role,
    }


@router.post("/login")
def login_user(payload: LoginRequest, conn: Connection = Depends(get_db_conn)):
    """
    Login user.

    Returns: access_token, token_type, user_id, username, role
    Raises: 401 if credentials invalid
    """
    # STEP 1: Fetch user from database by username
    user = conn.execute(
        "SELECT id, username, password, role FROM users WHERE username = ?",
        (payload.username,),
    ).fetchone()

    # STEP 2: Verify user exists and password matches
    if not user or user["password"] != hash_password(payload.password):
        # Either user not found or password incorrect
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # STEP 3: Generate JWT access token (valid for 24 hours)
    token = create_access_token(user["id"], user["role"])

    # STEP 4: Return user info with token
    return {
        "access_token": token,
        "token_type": TOKEN_TYPE,
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }
