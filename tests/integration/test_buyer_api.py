"""Integration tests for buyer API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
import uuid


client = TestClient(app)


def unique_username(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def buyer_token():
    """Register and login buyer."""
    username = unique_username("buyer")
    response = client.post("/auth/register", json={
        "username": username,
        "password": "pass1234",
        "role": "buyer"
    })
    return response.json()["access_token"]


@pytest.fixture
def seller_token():
    """Register and login seller."""
    username = unique_username("seller")
    response = client.post("/auth/register", json={
        "username": username,
        "password": "pass1234",
        "role": "seller"
    })
    return response.json()["access_token"]


@pytest.fixture
def test_product(seller_token):
    """Create test product."""
    response = client.post(
        "/seller/products",
        json={
            "name": "Test Laptop",
            "description": "High-end test",
            "price": 999.99,
            "quantity": 5
        },
        headers={"Authorization": f"Bearer {seller_token}"}
    )
    return response.json()["id"]


class TestBuyerProductsEndpoint:
    """Test /buyer/products endpoint."""

    def test_list_products_success(self, test_product):
        """Test listing products successfully."""
        response = client.get("/buyer/products")
        assert response.status_code == 200
        products = response.json()
        assert len(products) > 0
        assert any(p["id"] == test_product for p in products)

    def test_list_products_returns_product_response_model(self, test_product):
        """Test that response matches ProductResponse model."""
        response = client.get("/buyer/products")
        products = response.json()
        product = products[0]
        assert "id" in product
        assert "name" in product
        assert "description" in product
        assert "price" in product
        assert "quantity" in product
        assert "seller_id" in product

    def test_list_products_only_positive_quantity(self, seller_token):
        """Test that only products with quantity > 0 are returned."""
        # Create product
        response = client.post(
            "/seller/products",
            json={
                "name": "Zero Qty Product",
                "description": "test",
                "price": 10.0,
                "quantity": 0
            },
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        product_id = response.json()["id"]

        # List products
        response = client.get("/buyer/products")
        products = response.json()
        assert not any(p["id"] == product_id for p in products)


class TestBuyerCartEndpoint:
    """Test /buyer/cart endpoints."""

    def test_add_to_cart_success(self, buyer_token, test_product):
        """Test adding product to cart."""
        response = client.post(
            "/buyer/cart",
            json={"product_id": test_product, "quantity": 2},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 201
        assert response.json()["status"] == "ok"

    def test_add_to_cart_unauthorized(self, test_product):
        """Test adding to cart without auth."""
        response = client.post(
            "/buyer/cart",
            json={"product_id": test_product, "quantity": 1}
        )
        assert response.status_code == 403

    def test_add_to_cart_product_not_found(self, buyer_token):
        """Test adding non-existent product."""
        response = client.post(
            "/buyer/cart",
            json={"product_id": 99999, "quantity": 1},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 404

    def test_add_to_cart_insufficient_stock(self, buyer_token, test_product):
        """Test adding more than available stock."""
        response = client.post(
            "/buyer/cart",
            json={"product_id": test_product, "quantity": 10},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 400

    def test_get_cart_empty(self, buyer_token):
        """Test getting empty cart."""
        response = client.get(
            "/buyer/cart",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_get_cart_with_items(self, buyer_token, test_product):
        """Test getting cart with items."""
        client.post(
            "/buyer/cart",
            json={"product_id": test_product, "quantity": 1},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        response = client.get(
            "/buyer/cart",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 1
        assert items[0]["product_id"] == test_product

    def test_get_cart_unauthorized(self):
        """Test getting cart without auth."""
        response = client.get("/buyer/cart")
        assert response.status_code == 403


class TestBuyerOrdersEndpoint:
    """Test /buyer/orders endpoints."""

    def test_place_order_success(self, buyer_token, test_product):
        """Test placing order successfully."""
        client.post(
            "/buyer/cart",
            json={"product_id": test_product, "quantity": 1},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        response = client.post(
            "/buyer/orders",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 201
        order = response.json()
        assert order["status"] == "pending"
        assert order["total_amount"] == 999.99
        assert len(order["items"]) == 1

    def test_place_order_empty_cart(self, buyer_token):
        """Test placing order with empty cart."""
        response = client.post(
            "/buyer/orders",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 400

    def test_place_order_clears_cart(self, buyer_token, test_product):
        """Test that placing order clears the cart."""
        client.post(
            "/buyer/cart",
            json={"product_id": test_product, "quantity": 1},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        client.post(
            "/buyer/orders",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        response = client.get(
            "/buyer/cart",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.json() == []

    def test_place_order_unauthorized(self, test_product):
        """Test placing order without auth."""
        response = client.post("/buyer/orders")
        assert response.status_code == 403

    def test_list_orders_empty(self, buyer_token):
        """Test listing orders when none exist."""
        response = client.get(
            "/buyer/orders",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_list_orders_with_orders(self, buyer_token, test_product):
        """Test listing orders with existing orders."""
        client.post(
            "/buyer/cart",
            json={"product_id": test_product, "quantity": 1},
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        client.post(
            "/buyer/orders",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        response = client.get(
            "/buyer/orders",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) == 1
        assert orders[0]["status"] == "pending"

    def test_list_orders_unauthorized(self):
        """Test listing orders without auth."""
        response = client.get("/buyer/orders")
        assert response.status_code == 403

    def test_list_orders_multiple(self, buyer_token, seller_token):
        """Test listing multiple orders."""
        # Create product
        response = client.post(
            "/seller/products",
            json={"name": "Product", "description": "test", "price": 50.0, "quantity": 10},
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        product_id = response.json()["id"]

        # Place 2 orders
        for _ in range(2):
            client.post(
                "/buyer/cart",
                json={"product_id": product_id, "quantity": 1},
                headers={"Authorization": f"Bearer {buyer_token}"}
            )
            client.post(
                "/buyer/orders",
                headers={"Authorization": f"Bearer {buyer_token}"}
            )

        response = client.get(
            "/buyer/orders",
            headers={"Authorization": f"Bearer {buyer_token}"}
        )
        orders = response.json()
        assert len(orders) == 2
