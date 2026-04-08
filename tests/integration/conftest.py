"""Fixtures for integration tests with isolated test database."""

import pytest
import os
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def use_test_database():
    """
    Use isolated test database for all integration tests.
    Database is stored in data/test_deliverinno.db and cleaned up after tests.
    """
    test_db = Path(__file__).parent.parent.parent / "data" / "test_deliverinno.db"

    # Set DATABASE_PATH environment variable BEFORE importing database module
    os.environ["DATABASE_PATH"] = str(test_db)

    # Now initialize the test DB
    from src.core.database import init_db
    init_db()

    yield

    # Cleanup: delete test database after all tests
    if test_db.exists():
        test_db.unlink()
        print(f"Deleted test database: {test_db}")
