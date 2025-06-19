import pytest
from datetime import datetime
from src.data_sources.base import MarketData


def test_market_data_creation():
    """Test MarketData model creation."""
    data = MarketData(
        symbol="AAPL",
        timestamp=datetime(2023, 1, 1, 9, 30),
        open=100.0,
        high=105.0,
        low=99.0,
        close=102.0,
        volume=1000000,
        source="test"
    )
    
    assert data.symbol == "AAPL"
    assert data.timestamp == datetime(2023, 1, 1, 9, 30)
    assert data.open == 100.0
    assert data.high == 105.0
    assert data.low == 99.0
    assert data.close == 102.0
    assert data.volume == 1000000
    assert data.source == "test"


def test_market_data_dict_conversion():
    """Test MarketData conversion to dictionary."""
    data = MarketData(
        symbol="AAPL",
        timestamp=datetime(2023, 1, 1, 9, 30),
        open=100.0,
        high=105.0,
        low=99.0,
        close=102.0,
        volume=1000000,
        source="test"
    )
    
    data_dict = data.model_dump()
    assert isinstance(data_dict, dict)
    assert data_dict["symbol"] == "AAPL"
    assert data_dict["volume"] == 1000000


def test_market_data_validation():
    """Test MarketData validation."""
    # Test invalid volume (should be int)
    with pytest.raises(ValueError):
        MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume="invalid",  # Should be int
            source="test"
        )