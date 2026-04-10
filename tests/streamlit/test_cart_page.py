# tests/test_cart_page.py
import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch

from src.streamlit.config import API_URL


@pytest.fixture
def mock_cart_response():
    return [
        {"product_id": 1, "name": "Laptop", "quantity": 2, "price": 999.99},
        {"product_id": 2, "name": "Mouse", "quantity": 1, "price": 29.99}
    ]


@patch("src.streamlit.buyer.cart.requests.get")
def test_cart_displays_items(mock_get, mock_cart_response):
    mock_response = mock_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = mock_cart_response

    at = AppTest.from_file("src/streamlit/buyer/cart.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    assert not at.exception

    headers = [h.value for h in at.header]
    assert "Laptop" in headers
    assert "Mouse" in headers

    markdowns = [md.value for md in at.markdown if md.value]
    assert "#### Quantity: 2" in markdowns
    assert "### 999.99 $" in markdowns
    assert "#### Quantity: 1" in markdowns
    assert "### 29.99 $" in markdowns

    assert any(btn.label == "Make order" for btn in at.button)

    mock_get.assert_called_once_with(
        f"{API_URL}/buyer/cart",
        headers={"Authorization": "Bearer fake_token"},
        timeout=5
    )


@patch("src.streamlit.buyer.cart.requests.get")
@patch("src.streamlit.buyer.cart.requests.post")
def test_make_order(mock_post, mock_get, mock_cart_response):
    mock_response = mock_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = mock_cart_response

    at = AppTest.from_file("src/streamlit/buyer/cart.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    mock_post.return_value.status_code = 201

    at.button[0].click().run()

    assert at.toast[0].value == "Created order!"


@patch("src.streamlit.buyer.cart.requests.get")
@patch("src.streamlit.buyer.cart.requests.post")
def test_make_order_error_not_in_stock(mock_post, mock_get, mock_cart_response):
    mock_response = mock_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = mock_cart_response

    at = AppTest.from_file("src/streamlit/buyer/cart.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    mock_post.return_value.status_code = 400

    at.button[0].click().run()

    assert at.error[0].value == "Not enough stock!"


@patch("src.streamlit.buyer.cart.requests.get")
@patch("src.streamlit.buyer.cart.requests.post")
def test_make_order_error(mock_post, mock_get, mock_cart_response):
    mock_response = mock_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = mock_cart_response

    at = AppTest.from_file("src/streamlit/buyer/cart.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    mock_post.return_value.status_code = 500

    at.button[0].click().run()

    assert at.error[0].value == "Error: 500"


@patch("src.streamlit.buyer.cart.requests.get")
def test_cart_handles_api_error(mock_get):
    mock_response = mock_get.return_value
    mock_response.status_code = 500

    at = AppTest.from_file("src/streamlit/buyer/cart.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    assert any("Failed to load orders" in err.value for err in at.error)


@patch("src.streamlit.buyer.cart.requests.get")
def test_cart_handles_connection_exception(mock_get):
    mock_get.side_effect = Exception("Network down")

    at = AppTest.from_file("src/streamlit/buyer/cart.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    assert any("Connection error: Network down" in err.value for err in at.error)
