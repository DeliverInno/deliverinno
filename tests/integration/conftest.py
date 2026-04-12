"""Fixtures for integration tests with isolated test database."""

import tempfile
import pytest
import os

from src.api.dependencies import get_db_conn
from src.core.database import Database
from src.api.main import app


@pytest.fixture(scope="session", autouse=True)
def use_test_database():
    """
    Use isolated temp test database for all integration tests.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    test_db = Database(db_path)
    test_db.init_db()

    def override_get_db():
        with test_db.get_db() as conn:
            yield conn
    app.dependency_overrides[get_db_conn] = override_get_db

    yield
