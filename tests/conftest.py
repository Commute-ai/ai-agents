from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    Create a fresh test client for each test function.
    This ensures test isolation and prevents state leakage between tests.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def anyio_backend():
    """
    Configure pytest-asyncio to use asyncio backend for async tests.
    Required for FastAPI async route testing.
    """
    return "asyncio"
