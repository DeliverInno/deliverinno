from fastapi.testclient import TestClient
from src.api.main import app
import uuid

client = TestClient(app)


def unique_username(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def test_register_and_login():
    username = unique_username("testuser")
    password = "testpass123"
    role = "buyer"

    # Register
    response = client.post("/auth/register", json={
        "username": username,
        "password": password,
        "role": role
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == username
    assert data["role"] == role
    assert "access_token" in data

    # Login
    response = client.post("/auth/login", json={
        "username": username,
        "password": password
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["role"] == role
    assert "access_token" in data


def test_register_duplicate():
    username = unique_username("dupuser")
    password = "testpass_dup"
    role = "buyer"

    # Register first time
    response = client.post("/auth/register", json={
        "username": username,
        "password": password,
        "role": role
    })
    assert response.status_code == 201

    # Register duplicate
    response = client.post("/auth/register", json={
        "username": username,
        "password": password,
        "role": role
    })
    assert response.status_code == 400
    assert "Username already exists" in response.text


def test_login_invalid():
    response = client.post("/auth/login", json={
        "username": unique_username("not_exist"),
        "password": "wrong"
    })
    assert response.status_code == 401
    assert "Invalid credentials" in response.text
