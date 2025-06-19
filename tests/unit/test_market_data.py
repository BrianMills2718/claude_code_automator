import pytest
from datetime import datetime
from src.data_sources.base import MarketData


def test_market_data_creation() -> None:
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


def test_market_data_dict_conversion() -> None:
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


def test_market_data_validation() -> None:
    """Test MarketData validation."""
    # Test invalid volume (should be int)
    with pytest.raises((ValueError, TypeError)):
        MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume="invalid",  # type: ignore[arg-type]
            source="test"
        )


def test_market_data_edge_cases() -> None:
    """Test MarketData edge cases."""
    # Test with zero values
    data = MarketData(
        symbol="TEST",
        timestamp=datetime(2023, 1, 1),
        open=0.0,
        high=0.0,
        low=0.0,
        close=0.0,
        volume=0,
        source="test"
    )
    assert data.volume == 0
    assert data.open == 0.0
    
    # Test with very large values
    data = MarketData(
        symbol="LARGE",
        timestamp=datetime(2023, 1, 1),
        open=99999.99,
        high=100000.00,
        low=99999.98,
        close=99999.99,
        volume=999999999,
        source="test"
    )
    assert data.volume == 999999999
    assert data.high == 100000.00


def test_market_data_string_representation() -> None:
    """Test MarketData string representation."""
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
    
    str_repr = str(data)
    assert "AAPL" in str_repr
    assert "100.0" in str_repr or "100" in str_repr