import pytest
from src.api import dependencies
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from src.api.dependencies import get_current_user


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


@pytest.mark.asyncio
async def test_get_current_user_missing_fields():
    """Token without sub or role should raise 401."""
    # создаём токен вручную без role
    from src.api.dependencies import SECRET_KEY, ALGORITHM
    import jwt

    token = jwt.encode({"sub": "1"}, SECRET_KEY, algorithm=ALGORITHM)

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Invalid JWT should raise 401."""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid.token.here"
    )

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_user_id_cast():
    """Non-integer sub should trigger ValueError."""
    from src.api.dependencies import SECRET_KEY, ALGORITHM
    import jwt

    token = jwt.encode(
        {"sub": "not_an_int", "role": "buyer"},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token
    )

    with pytest.raises(HTTPException) as exc:
        await get_current_user(credentials)

    assert exc.value.status_code == 401
