import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator
from unittest.mock import Mock

from src.data_sources.base import MarketData

try:
    import pandas as pd  # type: ignore[import-untyped]
except ImportError:
    pd = None


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_market_data() -> List[MarketData]:
    """Create sample market data for testing."""
    base_time = datetime(2023, 1, 1, 9, 30)
    return [
        MarketData(
            symbol="AAPL",
            timestamp=base_time + timedelta(hours=i),
            open=100.0 + i,
            high=105.0 + i,
            low=99.0 + i,
            close=102.0 + i,
            volume=1000000 + i * 100,
            source="test"
        )
        for i in range(5)
    ]


@pytest.fixture
def mock_yahoo_finance_data() -> Any:
    """Mock Yahoo Finance API response data."""
    if pd is None:
        raise ImportError("pandas is required for mock_yahoo_finance_data fixture")
    
    dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
    return pd.DataFrame({
        'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
        'High': [105.0, 106.0, 107.0, 108.0, 109.0],
        'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
        'Close': [102.0, 103.0, 104.0, 105.0, 106.0],
        'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
    }, index=dates)


@pytest.fixture
def mock_alpha_vantage_data() -> Dict[str, Dict[str, Dict[str, str]]]:
    """Mock Alpha Vantage API response data."""
    return {
        'Time Series (Daily)': {
            '2023-01-01': {
                '1. open': '100.0',
                '2. high': '105.0',
                '3. low': '99.0',
                '4. close': '102.0',
                '5. volume': '1000000'
            },
            '2023-01-02': {
                '1. open': '101.0',
                '2. high': '106.0',
                '3. low': '100.0',
                '4. close': '103.0',
                '5. volume': '1100000'
            }
        }
    }


@pytest.fixture
def mock_search_results() -> List[Dict[str, str]]:
    """Mock symbol search results."""
    return [
        {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'type': 'Equity',
            'exchange': 'NASDAQ'
        },
        {
            'symbol': 'MSFT',
            'name': 'Microsoft Corporation',
            'type': 'Equity',
            'exchange': 'NASDAQ'
        }
    ]


@pytest.fixture
def mock_database_session() -> Mock:
    """Mock database session for testing."""
    session = Mock()
    session.merge = Mock()
    session.commit = Mock()
    session.execute = Mock()
    session.scalars = Mock()
    return session


@pytest.fixture
def mock_redis_cache() -> Mock:
    """Mock Redis cache for testing."""
    cache = Mock()
    cache.get = Mock(return_value=None)
    cache.set = Mock()
    cache.get_json = Mock(return_value=None)
    cache.set_json = Mock()
    return cache