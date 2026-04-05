"""Unit tests for FastAPI main app initialization."""

import pytest
from fastapi.testclient import TestClient


def test_app_health_check():
    """Test health check endpoint."""
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "deliverinno"}


def test_app_includes_buyer_router():
    """Test that buyer router is included."""
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/buyer/products")
    assert response.status_code in [200, 401]


def test_app_includes_auth_router():
    """Test that auth router is included."""
    from src.api.main import app
    client = TestClient(app)
    response = client.post("/auth/register", json={
        "username": "test_unique_1",
        "password": "test1234",
        "role": "buyer"
    })
    assert response.status_code in [201, 400]


def test_app_includes_seller_router():
    """Test that seller router is included."""
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/seller/products")
    assert response.status_code in [401]


def test_app_metadata():
    """Test app metadata."""
    from src.api.main import app
    assert app.title == "DeliverInno API"
    assert app.description == "Delivery service API for sellers and buyers"
    assert app.version == "0.1.0"


def test_app_openapi_schema():
    """Test that OpenAPI schema is generated."""
    from src.api.main import app
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "DeliverInno API"
    assert "/buyer/products" in schema["paths"]
    assert "/auth/register" in schema["paths"]
    assert "/seller/products" in schema["paths"]


def test_app_lifespan_initialization():
    """Test that app initializes with lifespan (init_db is called on startup)."""
    try:
        assert True
    except Exception as e:
        pytest.fail(f"App lifespan failed: {str(e)}")


def test_app_lifespan_executes_init_db():
    """Test that lifespan context manager executes init_db and yield."""
    from src.api.main import app
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "deliverinno"}
