import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch
from src.streamlit.config import API_URL


@pytest.fixture
def mock_orders_response():
    return [
        {
            "id": 101,
            "total_amount": 1500.50,
            "status": "pending",
            "items": [
                {"product_id": 1, "quantity": 2, "price_at_time": 500.0, "name": "Laptop"},
                {"product_id": 2, "quantity": 1, "price_at_time": 500.5, "name": "Mouse"}
            ]
        },
        {
            "id": 102,
            "total_amount": 75.0,
            "status": "pending",
            "items": [
                {"product_id": 3, "quantity": 3, "price_at_time": 25.0, "name": "USB Cable"}
            ]
        }
    ]


@patch("src.streamlit.buyer.orders.requests.get")
def test_orders_displays_correctly(mock_get, mock_orders_response):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_orders_response

    at = AppTest.from_file("src/streamlit/buyer/orders.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    assert not at.exception

    headers = [h.value for h in at.header]
    assert "# 101" in headers
    assert "# 102" in headers

    markdowns = [md.value for md in at.markdown if md.value]
    assert "## Status: pending" in markdowns
    assert "## Status: pending" in markdowns
    assert "- Laptop x2 for 500.0$" in markdowns
    assert "- Mouse x1 for 500.5$" in markdowns
    assert "- USB Cable x3 for 25.0$" in markdowns

    mock_get.assert_called_once_with(
        f"{API_URL}/buyer/orders",
        headers={"Authorization": "Bearer fake_token"},
        timeout=5
    )


@patch("src.streamlit.buyer.orders.requests.get")
def test_orders_api_error(mock_get):
    mock_get.return_value.status_code = 500

    at = AppTest.from_file("src/streamlit/buyer/orders.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    assert at.error[0].value == "Failed to load orders. Server returned 500"


@patch("src.streamlit.buyer.orders.requests.get")
def test_orders_handles_connection_error(mock_get):
    mock_get.side_effect = Exception("Connection error")

    at = AppTest.from_file("src/streamlit/buyer/orders.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    assert "Connection error" in at.error[0].value
