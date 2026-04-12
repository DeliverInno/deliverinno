import pytest
from streamlit.testing.v1 import AppTest
from unittest.mock import patch

from src.streamlit.config import API_URL


@pytest.fixture
def mock_session_state():
    return {"access_token": "fake_token"}


@patch("src.streamlit.seller.dashboard.requests.get")
def test_dashboard_displays_products(mock_get, mock_session_state):
    mock_response = mock_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": 1, "name": "Product A", "description": "Desc A",
            "quantity": 10, "price": 100, "seller_id": 1},
        {"id": 2, "name": "Product B", "description": "Desc B",
            "quantity": 5, "price": 200, "seller_id": 1},
    ]

    at = AppTest.from_file("src/streamlit/seller/dashboard.py")

    at.session_state["access_token"] = "fake_token"

    at.run()

    assert not at.exception
    headers = [head.value for head in at.header]
    assert "Product A" in headers
    assert "Product B" in headers
    markdown_texts = [md.value for md in at.markdown]
    assert "### Desc A" in markdown_texts
    assert "### Desc B" in markdown_texts

    mock_get.assert_called_once_with(
        f"{API_URL}/seller/products",
        headers={"Authorization": "Bearer fake_token"},
        timeout=5
    )

    assert any(ti.label == "Name" for ti in at.text_input)
    assert any(ti.label == "Description" for ti in at.text_input)
    assert any(ni.label == "Price" for ni in at.number_input)
    assert any(ni.label == "Quantity" for ni in at.number_input)
    assert any(btn.label == "Create" for btn in at.button)


@patch("src.streamlit.seller.dashboard.requests.get")
@patch("src.streamlit.seller.dashboard.requests.post")
def test_create_product_success(mock_post, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = []

    mock_post.return_value.status_code = 201

    at = AppTest.from_file("src/streamlit/seller/dashboard.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    at.text_input[0].input("New Product").run()
    at.text_input[1].input("New Description").run()
    at.number_input[0].set_value(99.99).run()
    at.number_input[1].set_value(5).run()

    create_btn = next(btn for btn in at.button if btn.label == "Create")
    create_btn.click().run()

    expected_json = {
        "name": "New Product",
        "description": "New Description",
        "price": 99.99,
        "quantity": 5
    }
    mock_post.assert_called_once_with(
        f"{API_URL}/seller/products",
        json=expected_json,
        headers={"Authorization": "Bearer fake_token"},
        timeout=5
    )

    assert at.toast[0].value == "Created product New Product"


@patch("src.streamlit.seller.dashboard.requests.get")
@patch("src.streamlit.seller.dashboard.requests.put")
def test_update_product_success(mock_put, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        {"id": 1, "name": "Old Name", "description": "Old Desc",
            "quantity": 10, "price": 50, "seller_id": 1}
    ]
    mock_put.return_value.status_code = 200

    at = AppTest.from_file("src/streamlit/seller/dashboard.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    print(at._tree)

    name_input = next((ti for ti in at.text_input if ti.label ==
                      "Name" and ti.value == "Old Name"), None)
    assert name_input is not None
    name_input.input("New Name").run()

    desc_input = next((ti for ti in at.text_input if ti.label ==
                      "Description" and ti.value == "Old Desc"), None)
    desc_input.input("New Desc").run()

    price_input = next((ni for ni in at.number_input if ni.label == "Price"), None)
    price_input.set_value(75.0).run()

    qt_input = next((ni for ni in at.number_input if ni.label == "Quantity"), None)
    qt_input.set_value(20).run()

    update_btn = next((btn for btn in at.button if btn.label == "Update"), None)
    update_btn.click().run()

    expected_json = {
        "name": "New Name",
        "description": "New Desc",
        "price": 75.0,
        "quantity": 20
    }
    mock_put.assert_called_once_with(
        f"{API_URL}/seller/products/1",
        json=expected_json,
        headers={"Authorization": "Bearer fake_token"},
        timeout=5
    )
    assert at.toast[0].value == "Updated product New Name"


@patch("src.streamlit.seller.dashboard.requests.get")
@patch("src.streamlit.seller.dashboard.requests.delete")
def test_delete_product_success(mock_delete, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        {"id": 1, "name": "Old Name", "description": "Old Desc",
            "quantity": 10, "price": 50, "seller_id": 1}
    ]
    mock_delete.return_value.status_code = 204

    at = AppTest.from_file("src/streamlit/seller/dashboard.py")
    at.session_state["access_token"] = "fake_token"
    at.run()

    at.button("del_1").click().run()

    mock_delete.assert_called_once_with(
        f"{API_URL}/seller/products/1",
        headers={"Authorization": "Bearer fake_token"},
        timeout=5
    )
    assert at.toast[0].value == "Removed product"
