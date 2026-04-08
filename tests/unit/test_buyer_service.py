"""Unit tests for buyer service with mocks (no real DB)."""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from tests.unit.conftest import create_mock_row

from src.services import buyer_service
from src.shared.models.buyer import AddToCartRequest


class TestListProducts:
    """Test list_products service."""

    def test_list_products_success(self, mock_conn):
        """Test listing products successfully."""
        mock_row1 = create_mock_row({
            "id": 1,
            "name": "Laptop",
            "description": "High-end",
            "price": 999.99,
            "quantity": 5,
            "seller_id": 1,
        })

        mock_row2 = create_mock_row({
            "id": 2,
            "name": "Mouse",
            "description": "Wireless",
            "price": 29.99,
            "quantity": 20,
            "seller_id": 1,
        })

        mock_conn.execute.return_value.fetchall.return_value = [
            mock_row1,
            mock_row2,
        ]

        result = buyer_service.list_products(mock_conn)

        assert len(result) == 2
        assert result[0].name == "Laptop"
        assert result[1].name == "Mouse"
        mock_conn.execute.assert_called_once()

    def test_list_products_empty(self, mock_conn):
        """Test listing products when none exist."""
        mock_conn.execute.return_value.fetchall.return_value = []
        result = buyer_service.list_products(mock_conn)
        assert result == []


class TestAddToCart:
    """Test add_to_cart service."""

    def test_add_to_cart_success(self, mock_conn):
        """Test adding to cart successfully."""
        mock_product = create_mock_row({"id": 1, "quantity": 10})
        mock_conn.execute.return_value.fetchone.return_value = mock_product

        payload = AddToCartRequest(product_id=1, quantity=2)
        result = buyer_service.add_to_cart(mock_conn, user_id=1, payload=payload)

        assert result["status"] == "ok"
        assert mock_conn.execute.call_count >= 2

    def test_add_to_cart_product_not_found(self, mock_conn):
        """Test adding non-existent product."""
        mock_conn.execute.return_value.fetchone.return_value = None
        payload = AddToCartRequest(product_id=999, quantity=1)

        with pytest.raises(HTTPException) as exc:
            buyer_service.add_to_cart(mock_conn, user_id=1, payload=payload)

        assert exc.value.status_code == 404

    def test_add_to_cart_insufficient_stock(self, mock_conn):
        """Test adding more than available stock."""
        mock_product = create_mock_row({"id": 1, "quantity": 5})
        mock_conn.execute.return_value.fetchone.return_value = mock_product

        payload = AddToCartRequest(product_id=1, quantity=10)

        with pytest.raises(HTTPException) as exc:
            buyer_service.add_to_cart(mock_conn, user_id=1, payload=payload)

        assert exc.value.status_code == 400

    def test_add_to_cart_updates_quantity(self, mock_conn):
        """Test that adding to cart decreases product quantity."""
        mock_product = create_mock_row({"id": 1, "quantity": 10})
        mock_conn.execute.return_value.fetchone.return_value = mock_product

        payload = AddToCartRequest(product_id=1, quantity=2)
        buyer_service.add_to_cart(mock_conn, user_id=1, payload=payload)

        calls = mock_conn.execute.call_args_list
        assert any("UPDATE products" in str(call) for call in calls)


class TestGetCart:
    """Test get_cart service."""

    def test_get_cart_with_items(self, mock_conn):
        """Test getting cart with items."""
        mock_row = create_mock_row({
            "product_id": 1,
            "name": "Laptop",
            "price": 999.99,
            "quantity": 2,
        })

        mock_conn.execute.return_value.fetchall.return_value = [mock_row]

        result = buyer_service.get_cart(mock_conn, user_id=1)

        assert len(result) == 1
        assert result[0].name == "Laptop"
        assert result[0].quantity == 2

    def test_get_cart_empty(self, mock_conn):
        """Test getting empty cart."""
        mock_conn.execute.return_value.fetchall.return_value = []
        result = buyer_service.get_cart(mock_conn, user_id=1)
        assert result == []

    def test_get_cart_multiple_items(self, mock_conn):
        """Test getting cart with multiple items."""
        mock_row1 = create_mock_row({
            "product_id": 1,
            "name": "Laptop",
            "price": 999.99,
            "quantity": 1,
        })

        mock_row2 = create_mock_row({
            "product_id": 2,
            "name": "Mouse",
            "price": 29.99,
            "quantity": 3,
        })

        mock_conn.execute.return_value.fetchall.return_value = [
            mock_row1,
            mock_row2,
        ]

        result = buyer_service.get_cart(mock_conn, user_id=1)

        assert len(result) == 2
        assert result[0].name == "Laptop"
        assert result[1].name == "Mouse"


class TestPlaceOrder:
    """Test place_order service."""

    def test_place_order_success(self, mock_conn):
        """Test placing order successfully."""
        mock_cart_row = create_mock_row({
            "product_id": 1,
            "quantity": 2,
            "price": 999.99,
            "name": "Laptop",
        })

        mock_order_row = create_mock_row({
            "product_id": 1,
            "quantity": 2,
            "price_at_time": 999.99,
            "name": "Laptop",
        })

        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1

        mock_conn.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[mock_cart_row])),
            mock_cursor,
            MagicMock(),
            MagicMock(),
            MagicMock(fetchall=MagicMock(return_value=[mock_order_row])),
        ]

        result = buyer_service.place_order(mock_conn, user_id=1)

        assert result.status == "pending"
        assert result.total_amount == 1999.98
        assert len(result.items) == 1

    def test_place_order_empty_cart(self, mock_conn):
        """Test placing order with empty cart."""
        mock_conn.execute.return_value.fetchall.return_value = []

        with pytest.raises(HTTPException) as exc:
            buyer_service.place_order(mock_conn, user_id=1)

        assert exc.value.status_code == 400

    def test_place_order_failed_insert(self, mock_conn):
        """Test placing order when insert fails."""
        mock_cart_row = create_mock_row({
            "product_id": 1,
            "quantity": 2,
            "price": 999.99,
            "name": "Laptop",
        })

        mock_cursor = MagicMock()
        mock_cursor.lastrowid = None

        mock_conn.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[mock_cart_row])),
            mock_cursor,
        ]

        with pytest.raises(HTTPException) as exc:
            buyer_service.place_order(mock_conn, user_id=1)

        assert exc.value.status_code == 500

    def test_place_order_multiple_items(self, mock_conn):
        """Test placing order with multiple items."""
        mock_cart_row1 = create_mock_row({
            "product_id": 1,
            "quantity": 1,
            "price": 999.99,
            "name": "Laptop",
        })

        mock_cart_row2 = create_mock_row({
            "product_id": 2,
            "quantity": 2,
            "price": 29.99,
            "name": "Mouse",
        })

        mock_order_row1 = create_mock_row({
            "product_id": 1,
            "quantity": 1,
            "price_at_time": 999.99,
            "name": "Laptop",
        })

        mock_order_row2 = create_mock_row({
            "product_id": 2,
            "quantity": 2,
            "price_at_time": 29.99,
            "name": "Mouse",
        })

        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1

        mock_conn.execute.side_effect = [
            MagicMock(
                fetchall=MagicMock(return_value=[mock_cart_row1, mock_cart_row2])
            ),
            mock_cursor,
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(
                fetchall=MagicMock(return_value=[mock_order_row1, mock_order_row2])
            ),
        ]

        result = buyer_service.place_order(mock_conn, user_id=1)

        assert result.status == "pending"
        assert result.total_amount == 1059.97
        assert len(result.items) == 2


class TestListOrders:
    """Test list_orders service."""

    def test_list_orders_success(self, mock_conn):
        """Test listing orders successfully."""
        mock_order = create_mock_row({
            "id": 1,
            "total_amount": 1999.98,
            "status": "pending",
        })

        mock_item = create_mock_row({
            "product_id": 1,
            "quantity": 2,
            "price_at_time": 999.99,
            "name": "Laptop",
        })

        mock_conn.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[mock_order])),
            MagicMock(fetchall=MagicMock(return_value=[mock_item])),
        ]

        result = buyer_service.list_orders(mock_conn, user_id=1)

        assert len(result) == 1
        assert result[0].status == "pending"
        assert len(result[0].items) == 1

    def test_list_orders_empty(self, mock_conn):
        """Test listing orders when none exist."""
        mock_conn.execute.return_value.fetchall.return_value = []
        result = buyer_service.list_orders(mock_conn, user_id=1)
        assert result == []

    def test_list_orders_multiple(self, mock_conn):
        """Test listing multiple orders."""
        mock_order1 = create_mock_row({
            "id": 1,
            "total_amount": 1999.98,
            "status": "pending",
        })

        mock_order2 = create_mock_row({
            "id": 2,
            "total_amount": 29.99,
            "status": "pending",
        })

        mock_item1 = create_mock_row({
            "product_id": 1,
            "quantity": 2,
            "price_at_time": 999.99,
            "name": "Laptop",
        })

        mock_item2 = create_mock_row({
            "product_id": 2,
            "quantity": 1,
            "price_at_time": 29.99,
            "name": "Mouse",
        })

        mock_conn.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[mock_order1, mock_order2])),
            MagicMock(fetchall=MagicMock(return_value=[mock_item1])),
            MagicMock(fetchall=MagicMock(return_value=[mock_item2])),
        ]

        result = buyer_service.list_orders(mock_conn, user_id=1)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
