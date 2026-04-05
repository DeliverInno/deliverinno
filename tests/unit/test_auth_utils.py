import pytest
from src.api import dependencies
import jwt


def test_create_access_token_and_decode():
    token = dependencies.create_access_token(1, "buyer")
    payload = jwt.decode(token, dependencies.SECRET_KEY, algorithms=[dependencies.ALGORITHM])
    assert payload["sub"] == "1"
    assert payload["role"] == "buyer"


def test_require_buyer_and_seller():
    buyer = {"id": 1, "role": "buyer"}
    seller = {"id": 2, "role": "seller"}
    assert dependencies.require_buyer(buyer) == buyer
    assert dependencies.require_seller(seller) == seller
    with pytest.raises(Exception):
        dependencies.require_buyer(seller)
    with pytest.raises(Exception):
        dependencies.require_seller(buyer)
