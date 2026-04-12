"""Integration tests for seller API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
import uuid

client = TestClient(app)


def unique_username(prefix="user"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def seller_token():
    username = unique_username("seller")
    response = client.post("/auth/register", json={
        "username": username,
        "password": "pass1234",
        "role": "seller"
    })
    return response.json()["access_token"]


@pytest.fixture
def another_seller_token():
    username = unique_username("seller2")
    response = client.post("/auth/register", json={
        "username": username,
        "password": "pass1234",
        "role": "seller"
    })
    return response.json()["access_token"]


@pytest.fixture
def test_product(seller_token):
    response = client.post(
        "/seller/products",
        json={
            "name": "Test Product",
            "description": "Desc",
            "price": 10.0,
            "quantity": 5
        },
        headers={"Authorization": f"Bearer {seller_token}"}
    )
    return response.json()["id"]


class TestCreateProduct:
    def test_create_product_success(self, seller_token):
        response = client.post(
            "/seller/products",
            json={
                "name": "Product",
                "description": "Desc",
                "price": 10.0,
                "quantity": 5
            },
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        assert response.status_code == 201
        assert "id" in response.json()

    def test_create_product_unauthorized(self):
        response = client.post("/seller/products", json={})
        assert response.status_code == 403


class TestListProducts:
    def test_list_products_success(self, seller_token, test_product):
        response = client.get(
            "/seller/products",
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        assert response.status_code == 200
        products = response.json()
        assert len(products) >= 1
        assert any(p["id"] == test_product for p in products)

    def test_list_products_only_own(self, seller_token, another_seller_token):
        # product 1
        client.post(
            "/seller/products",
            json={"name": "A", "description": "x", "price": 1, "quantity": 1},
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        # product 2
        client.post(
            "/seller/products",
            json={"name": "B", "description": "x", "price": 1, "quantity": 1},
            headers={"Authorization": f"Bearer {another_seller_token}"}
        )

        response = client.get(
            "/seller/products",
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        products = response.json()
        assert len(products) == 1

    def test_list_products_unauthorized(self):
        response = client.get("/seller/products")
        assert response.status_code == 403


class TestUpdateProduct:
    def test_update_product_success(self, seller_token, test_product):
        response = client.put(
            f"/seller/products/{test_product}",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        assert response.status_code == 200
        assert response.json()["status"] == "updated"

    def test_update_product_not_found(self, seller_token):
        response = client.put(
            "/seller/products/99999",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        assert response.status_code == 404

    def test_update_product_not_owner(self, seller_token, another_seller_token, test_product):
        response = client.put(
            f"/seller/products/{test_product}",
            json={"name": "Hack"},
            headers={"Authorization": f"Bearer {another_seller_token}"}
        )

        assert response.status_code == 403

    def test_update_product_empty_payload(self, seller_token, test_product):
        response = client.put(
            f"/seller/products/{test_product}",
            json={},
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        assert response.status_code == 400

    def test_update_product_unauthorized(self, test_product):
        response = client.put(f"/seller/products/{test_product}", json={"name": "X"})
        assert response.status_code == 403


class TestDeleteProduct:
    def test_delete_product_success(self, seller_token):
        response = client.post(
            "/seller/products",
            json={"name": "ToDelete", "description": "x", "price": 1, "quantity": 1},
            headers={"Authorization": f"Bearer {seller_token}"}
        )
        product_id = response.json()["id"]

        response = client.delete(
            f"/seller/products/{product_id}",
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        assert response.status_code == 204

    def test_delete_product_not_found(self, seller_token):
        response = client.delete(
            "/seller/products/99999",
            headers={"Authorization": f"Bearer {seller_token}"}
        )

        assert response.status_code == 404

    def test_delete_product_not_owner(self, seller_token, another_seller_token, test_product):
        response = client.delete(
            f"/seller/products/{test_product}",
            headers={"Authorization": f"Bearer {another_seller_token}"}
        )

        assert response.status_code == 403

    def test_delete_product_unauthorized(self, test_product):
        response = client.delete(f"/seller/products/{test_product}")
        assert response.status_code == 403
