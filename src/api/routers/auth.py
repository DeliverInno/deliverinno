"""Auth endpoints: register and login."""

from sqlite3 import Connection
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_db_conn, create_access_token
from src.core.database import hash_password

TOKEN_TYPE = "bearer"  # nosec B105

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=4, max_length=128)
    role: Literal["buyer", "seller"]


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, conn: Connection = Depends(get_db_conn)):
    """Register new user."""
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (payload.username,),
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    password_hash = hash_password(payload.password)
    cursor = conn.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (payload.username, password_hash, payload.role),
    )
    user_id = cursor.lastrowid or 0
    user_id = int(user_id)

    token = create_access_token(user_id, payload.role)
    return {
        "access_token": token,
        "token_type": TOKEN_TYPE,
        "id": user_id,
        "username": payload.username,
        "role": payload.role,
    }


@router.post("/login")
def login_user(payload: LoginRequest, conn: Connection = Depends(get_db_conn)):
    """Login user."""
    user = conn.execute(
        "SELECT id, username, password, role FROM users WHERE username = ?",
        (payload.username,),
    ).fetchone()
    if not user or user["password"] != hash_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(user["id"], user["role"])
    return {
        "access_token": token,
        "token_type": TOKEN_TYPE,
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }
