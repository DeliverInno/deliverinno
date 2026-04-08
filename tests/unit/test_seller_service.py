"""Unit tests for seller service with mocks (no real DB)."""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from tests.unit.conftest import create_mock_row
from src.services import seller_service
from src.shared.models.seller import ProductCreate, ProductUpdate


class TestCreateProduct:
    def test_create_product_success(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.execute.return_value = mock_cursor

        payload = ProductCreate(
            name="Test Product",
            description="Test Desc",
            price=10.0,
            quantity=5,
        )

        result = seller_service.create_product(mock_conn, 1, payload)

        assert result["id"] == 1
        mock_conn.execute.assert_called_once()


class TestListProducts:
    def test_list_products_success(self, mock_conn):
        mock_row = create_mock_row({
            "id": 1,
            "name": "Product",
            "description": "Desc",
            "price": 10.0,
            "quantity": 5,
            "seller_id": 1,
        })

        mock_conn.execute.return_value.fetchall.return_value = [mock_row]

        result = seller_service.list_products(mock_conn, 1)

        assert len(result) == 1
        assert result[0].name == "Product"

    def test_list_products_empty(self, mock_conn):
        mock_conn.execute.return_value.fetchall.return_value = []

        result = seller_service.list_products(mock_conn, 1)

        assert result == []


class TestUpdateProduct:
    def test_update_product_success(self, mock_conn):
        mock_conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=create_mock_row({
                "id": 1,
                "seller_id": 1
            }))),
            MagicMock(),
        ]

        payload = ProductUpdate(name="Updated")

        result = seller_service.update_product(mock_conn, 1, 1, payload)

        assert result["status"] == "updated"

    def test_update_product_not_found(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None

        with pytest.raises(HTTPException) as exc:
            seller_service.update_product(mock_conn, 1, 1, ProductUpdate(name="x"))

        assert exc.value.status_code == 404

    def test_update_product_not_owner(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = create_mock_row({
            "id": 1,
            "seller_id": 2
        })

        with pytest.raises(HTTPException) as exc:
            seller_service.update_product(mock_conn, 1, 1, ProductUpdate(name="x"))

        assert exc.value.status_code == 403

    def test_update_product_empty_payload(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = create_mock_row({
            "id": 1,
            "seller_id": 1
        })

        with pytest.raises(HTTPException) as exc:
            seller_service.update_product(mock_conn, 1, 1, ProductUpdate())

        assert exc.value.status_code == 400


class TestDeleteProduct:
    def test_delete_product_success(self, mock_conn):
        mock_conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=create_mock_row({
                "id": 1,
                "seller_id": 1
            }))),
            MagicMock(),
        ]

        seller_service.delete_product(mock_conn, 1, 1)

        assert mock_conn.execute.call_count == 2

    def test_delete_product_not_found(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = None

        with pytest.raises(HTTPException) as exc:
            seller_service.delete_product(mock_conn, 1, 1)

        assert exc.value.status_code == 404

    def test_delete_product_not_owner(self, mock_conn):
        mock_conn.execute.return_value.fetchone.return_value = create_mock_row({
            "id": 1,
            "seller_id": 2
        })

        with pytest.raises(HTTPException) as exc:
            seller_service.delete_product(mock_conn, 1, 1)

        assert exc.value.status_code == 403
