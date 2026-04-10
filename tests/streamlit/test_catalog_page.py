import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch
from src.streamlit.config import API_URL


@pytest.fixture
def mock_products_response():
    return [
        {"id": 1, "name": "Laptop", "description": "Powerful machine",
            "quantity": 5, "price": 999.99, "seller_id": 10},
        {"id": 2, "name": "Mouse", "description": "Wireless",
            "quantity": 20, "price": 29.99, "seller_id": 10},
    ]


@patch("src.streamlit.buyer.buyer_catalog.requests.get")
def test_catalog_displays_products(mock_get, mock_products_response):
    mock_response = mock_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = mock_products_response

    at = AppTest.from_file("src/streamlit/buyer/buyer_catalog.py")
    at.run()

    assert not at.exception

    headers = [h.value for h in at.header]
    assert "Laptop" in headers
    assert "Mouse" in headers

    markdowns = [md.value for md in at.markdown if md.value]
    assert "### Powerful machine" in markdowns
    assert "#### Quantity: 5" in markdowns
    assert "## 999.99 $" in markdowns
    assert "### Wireless" in markdowns
    assert "#### Quantity: 20" in markdowns
    assert "## 29.99 $" in markdowns

    mock_get.assert_called_once_with(f"{API_URL}/buyer/products", timeout=5)


@patch("src.streamlit.buyer.buyer_catalog.requests.get")
def test_catalog_api_error(mock_get):
    mock_response = mock_get.return_value
    mock_response.status_code = 500

    at = AppTest.from_file("src/streamlit/buyer/buyer_catalog.py")
    at.run()

    assert any("Failed to load catalog" in err.value for err in at.error)


@patch("src.streamlit.buyer.buyer_catalog.requests.post")
@patch("src.streamlit.buyer.buyer_catalog.requests.get")
def test_add_to_cart(mock_get, mock_post, mock_products_response):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_products_response

    at = AppTest.from_file("src/streamlit/buyer/buyer_catalog.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    print(at._tree)

    quantity_input = at.number_input("num_1")
    quantity_input.set_value(3).run()

    mock_post.return_value.status_code = 201

    at.button("btn_1").click().run()

    assert len(at.toast) == 1


@patch("src.streamlit.buyer.buyer_catalog.requests.post")
@patch("src.streamlit.buyer.buyer_catalog.requests.get")
def test_add_to_cart_with_error(mock_get, mock_post, mock_products_response):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_products_response

    at = AppTest.from_file("src/streamlit/buyer/buyer_catalog.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    print(at._tree)

    quantity_input = at.number_input("num_1")
    quantity_input.set_value(3).run()

    mock_post.return_value.status_code = 400

    at.button("btn_1").click().run()

    assert at.error[0].value == "Not enough stock!"
