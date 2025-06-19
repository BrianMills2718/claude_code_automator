"""Tests for market data API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


def test_get_market_data_success(client):
    """Test getting market data for a valid symbol."""
    response = client.get("/api/market-data/AAPL")
    assert response.status_code == 200
    
    data = response.json()
    assert "symbol" in data
    assert "price" in data
    assert "change" in data
    assert "volume" in data
    assert data["symbol"] == "AAPL"


def test_get_market_data_unknown_symbol(client):
    """Test getting market data for unknown symbol."""
    response = client.get("/api/market-data/UNKNOWN")
    assert response.status_code == 200  # Returns generic data
    
    data = response.json()
    assert data["symbol"] == "UNKNOWN"
    assert data["price"] == 100.00  # Default price


def test_get_historical_data_success(client):
    """Test getting historical data."""
    response = client.get("/api/market-data/AAPL/historical?days=30")
    assert response.status_code == 200
    
    data = response.json()
    assert "symbol" in data
    assert "data" in data
    assert "start_date" in data
    assert "end_date" in data
    assert len(data["data"]) == 30


def test_get_historical_data_invalid_days(client):
    """Test historical data with invalid days parameter."""
    response = client.get("/api/market-data/AAPL/historical?days=500")
    assert response.status_code == 422  # Validation error


def test_market_data_response_structure(client):
    """Test market data response has correct structure."""
    response = client.get("/api/market-data/GOOGL")
    assert response.status_code == 200
    
    data = response.json()
    required_fields = ["symbol", "price", "change", "change_percent", 
                      "volume", "market_cap", "pe_ratio", "timestamp"]
    
    for field in required_fields:
        assert field in data
        assert data[field] is not None