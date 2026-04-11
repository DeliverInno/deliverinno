from fastapi.testclient import TestClient
from uuid import uuid4
from src.api.main import app

client = TestClient(app)


def register_user(username: str, password: str, role: str):
    """Helper to register a user and return the response."""
    payload = {"username": username, "password": password, "role": role}
    return client.post("/auth/register", json=payload)


def login_user(username: str, password: str):
    """Helper to log in a user and return the access token."""
    payload = {"username": username, "password": password}
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200, f"Login failed: {response.text}"
    # Assuming the response contains an 'access_token' field
    return response.json()["access_token"]


def test_complete_buyer_seller_flow():
    """
    End‑to‑end test covering:
    - Seller registration & product management
    - Buyer registration & shopping flow
    """
    # 1. Seller registration and product management
    seller_username = f"seller_{uuid4().hex[:8]}"
    seller_password = "seller123"
    register_response = register_user(seller_username, seller_password, "seller")
    assert register_response.status_code == 201

    seller_token = login_user(seller_username, seller_password)
    seller_headers = {"Authorization": f"Bearer {seller_token}"}

    # Create a product
    product_payload = {
        "name": "Test Laptop",
        "description": "High performance laptop",
        "price": 999.99,
        "quantity": 10,
    }
    create_response = client.post(
        "/seller/products", json=product_payload, headers=seller_headers
    )
    assert create_response.status_code == 201
    # Extract product ID from location header or response body (assuming body contains id)
    # The spec doesn't define the response body; we assume it returns the created product.
    # If it returns nothing, we need to list products to get the ID.
    # Let's list products to obtain the ID:
    list_response = client.get("/seller/products", headers=seller_headers)
    assert list_response.status_code == 200
    products = list_response.json()
    assert len(products) == 1
    product_id = products[0]["id"]
    assert products[0]["name"] == product_payload["name"]
    assert products[0]["quantity"] == product_payload["quantity"]

    # Update the product (increase price, reduce quantity)
    update_payload = {"price": 1099.99, "quantity": 5}
    update_response = client.put(
        f"/seller/products/{product_id}", json=update_payload, headers=seller_headers
    )
    assert update_response.status_code == 200

    # Verify update
    list_response = client.get("/seller/products", headers=seller_headers)
    updated_product = list_response.json()[0]
    assert updated_product["price"] == 1099.99
    assert updated_product["quantity"] == 5

    # 2. Buyer registration and shopping flow
    buyer_username = f"buyer_{uuid4().hex[:8]}"
    buyer_password = "buyer123"
    register_response = register_user(buyer_username, buyer_password, "buyer")
    assert register_response.status_code == 201

    buyer_token = login_user(buyer_username, buyer_password)
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

    # Buyer lists available products (should see the seller's product)
    products_response = client.get("/buyer/products")
    assert products_response.status_code == 200
    available_products = products_response.json()
    assert len(available_products) == 1
    assert available_products[0]["id"] == product_id
    assert available_products[0]["quantity"] == 5  # updated quantity

    # Add product to cart (quantity 2)
    add_to_cart_payload = {"product_id": product_id, "quantity": 2}
    cart_add_response = client.post(
        "/buyer/cart", json=add_to_cart_payload, headers=buyer_headers
    )
    assert cart_add_response.status_code == 201

    # Get cart contents
    cart_response = client.get("/buyer/cart", headers=buyer_headers)
    assert cart_response.status_code == 200
    cart_items = cart_response.json()
    assert len(cart_items) == 1
    assert cart_items[0]["product_id"] == product_id
    assert cart_items[0]["quantity"] == 2
    assert cart_items[0]["price"] == 1099.99

    # Verify product quantity decreased (from 5 to 3)
    products_response = client.get("/buyer/products")
    assert products_response.status_code == 200
    updated_available = products_response.json()[0]
    assert updated_available["quantity"] == 3

    # Place order
    place_order_response = client.post("/buyer/orders", headers=buyer_headers)
    assert place_order_response.status_code == 201
    order = place_order_response.json()
    assert order["total_amount"] == 2 * 1099.99  # 2199.98
    assert order["status"] == "pending"
    assert len(order["items"]) == 1
    assert order["items"][0]["product_id"] == product_id
    assert order["items"][0]["quantity"] == 2
    assert order["items"][0]["price_at_time"] == 1099.99

    # After placing order, cart should be empty
    cart_response = client.get("/buyer/cart", headers=buyer_headers)
    assert cart_response.status_code == 200
    assert cart_response.json() == []

    # Buyer order history
    orders_response = client.get("/buyer/orders", headers=buyer_headers)
    assert orders_response.status_code == 200
    orders = orders_response.json()
    assert len(orders) == 1
    assert orders[0]["id"] == order["id"]

    # 3. Seller deletes the product (cleanup)
    delete_response = client.delete(
        f"/seller/products/{product_id}", headers=seller_headers
    )
    assert delete_response.status_code == 204

    # Verify product no longer appears for buyer
    products_response = client.get("/buyer/products")
    assert products_response.status_code == 200
    assert products_response.json() == []


def test_cart_quantity_exceeds_inventory():
    """
    Edge case: buyer tries to add more than available quantity.
    Expected: 422 or appropriate error (depending on implementation).
    """
    # Setup: register seller, create product with quantity 1
    seller_username = f"seller_{uuid4().hex[:8]}"
    seller_password = "seller123"
    register_user(seller_username, seller_password, "seller")
    seller_token = login_user(seller_username, seller_password)
    seller_headers = {"Authorization": f"Bearer {seller_token}"}

    product_payload = {
        "name": "Limited Item",
        "price": 10.0,
        "quantity": 1,
    }
    create_response = client.post("/seller/products", json=product_payload, headers=seller_headers)
    assert create_response.status_code == 201
    # Get product ID
    list_resp = client.get("/seller/products", headers=seller_headers)
    product_id = list_resp.json()[0]["id"]

    # Register buyer
    buyer_username = f"buyer_{uuid4().hex[:8]}"
    buyer_password = "buyer123"
    register_user(buyer_username, buyer_password, "buyer")
    buyer_token = login_user(buyer_username, buyer_password)
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

    # Try to add quantity 2 (exceeds available 1)
    add_payload = {"product_id": product_id, "quantity": 2}
    response = client.post("/buyer/cart", json=add_payload, headers=buyer_headers)
    # Expect validation error (422) or a 400 Bad Request
    assert response.status_code == 422 or response.status_code == 400

    # Cart should remain empty
    cart_resp = client.get("/buyer/cart", headers=buyer_headers)
    assert cart_resp.json() == []

    # Cleanup: delete product
    client.delete(f"/seller/products/{product_id}", headers=seller_headers)


def test_unauthorized_access():
    """Ensure protected endpoints require authentication."""
    # /buyer/cart without token
    resp = client.get("/buyer/cart")
    assert resp.status_code == 403 or resp.status_code == 401

    # /seller/products without token
    resp = client.post("/seller/products", json={"name": "x", "price": 1, "quantity": 1})
    assert resp.status_code == 403 or resp.status_code == 401
