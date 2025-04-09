"""
Tests for the main FastAPI application setup.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Generator, Dict, Any, cast
from ..main import app

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Fixture providing a TestClient instance."""
    yield TestClient(app)

def test_app_title() -> None:
    """Test that the app has the correct title."""
    assert app.title == "Crypto Trading API"

def test_app_description() -> None:
    """Test that the app has the correct description."""
    assert app.description == "API for cryptocurrency trading and market data"

def test_app_version() -> None:
    """Test that the app has the correct version."""
    assert app.version == "1.0.0"

def test_cors_middleware() -> None:
    """Test that CORS middleware is properly configured."""
    middleware = [middleware for middleware in app.user_middleware]
    assert len(middleware) > 0
    assert any("CORSMiddleware" in str(m) for m in middleware)

def test_root_endpoint(client: TestClient) -> None:
    """Test that the root endpoint returns 404 (since we haven't defined a root route)."""
    response = client.get("/")
    assert response.status_code == 404

def test_openapi_docs(client: TestClient) -> None:
    """Test that the OpenAPI documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in cast(Dict[str, str], response.headers)["content-type"]

def test_openapi_json(client: TestClient) -> None:
    """Test that the OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert cast(Dict[str, str], response.headers)["content-type"] == "application/json" 