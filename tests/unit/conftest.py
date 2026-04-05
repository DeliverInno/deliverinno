"""Unit test fixtures with mocks."""

import pytest
from unittest.mock import MagicMock


class MockRow(dict):
    """Mock SQLite Row that supports dict() conversion."""
    def __getitem__(self, key):
        """Support both bracket and dict access."""
        return super().__getitem__(key)


@pytest.fixture
def mock_conn():
    """Mock database connection."""
    return MagicMock()


def create_mock_row(data: dict) -> MockRow:
    """Create a mock row that works with dict() conversion."""
    return MockRow(data)
