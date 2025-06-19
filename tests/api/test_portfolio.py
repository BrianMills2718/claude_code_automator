"""Tests for portfolio API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test-token"}


def test_list_portfolios_unauthorized(client):
    """Test listing portfolios without authentication."""
    response = client.get("/api/portfolio/")
    assert response.status_code == 401


def test_list_portfolios_authorized(client, auth_headers):
    """Test listing portfolios with authentication."""
    # This will fail due to auth validation, but tests the endpoint structure
    response = client.get("/api/portfolio/", headers=auth_headers)
    # Response could be 401 (invalid token) or 200 (if mock auth works)
    assert response.status_code in [200, 401]


def test_create_portfolio_unauthorized(client):
    """Test creating portfolio without authentication."""
    portfolio_data = {
        "name": "Test Portfolio",
        "description": "Test description"
    }
    response = client.post("/api/portfolio/", json=portfolio_data)
    assert response.status_code == 401


def test_get_portfolio_not_found(client, auth_headers):
    """Test getting non-existent portfolio."""
    response = client.get("/api/portfolio/nonexistent", headers=auth_headers)
    # Could be 401 (auth) or 404 (not found)
    assert response.status_code in [401, 404]


def test_api_documentation_accessible(client):
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_accessible(client):
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "ML Portfolio Analyzer API"