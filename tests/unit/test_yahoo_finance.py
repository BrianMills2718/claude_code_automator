import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Any
import tenacity

from src.data_sources.yahoo_finance import YahooFinanceAdapter
from src.data_sources.base import MarketData


class TestYahooFinanceAdapter:
    """Unit tests for YahooFinanceAdapter."""

    @pytest.fixture
    def adapter(self) -> YahooFinanceAdapter:
        """Create a YahooFinanceAdapter instance."""
        return YahooFinanceAdapter()

    @pytest.fixture
    def mock_yfinance_data(self) -> Any:
        """Mock yfinance data."""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")
        
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        return pd.DataFrame({
            'Open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'High': [105.0, 106.0, 107.0, 108.0, 109.0],
            'Low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'Close': [102.0, 103.0, 104.0, 105.0, 106.0],
            'Volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        }, index=dates)

    def test_create_market_data(self, adapter: YahooFinanceAdapter) -> None:
        """Test market data creation from row data."""
        
        # Create a mock row
        row_data = {
            'Open': 100.0,
            'High': 105.0,
            'Low': 99.0,
            'Close': 102.0,
            'Volume': 1000000
        }
        
        timestamp = datetime(2023, 1, 1)
        result = adapter._create_market_data("AAPL", timestamp, row_data)
        
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        assert result.timestamp == timestamp
        assert result.open == 100.0
        assert result.high == 105.0
        assert result.low == 99.0
        assert result.close == 102.0
        assert result.volume == 1000000
        assert result.source == "yahoo_finance"

    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    @pytest.mark.asyncio
    async def test_get_daily_prices_success(self, mock_ticker: Mock, adapter: YahooFinanceAdapter, mock_yfinance_data: Any) -> None:
        """Test successful daily price retrieval."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_ticker_instance
        
        result = await adapter.get_daily_prices(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1).date(),
            end_date=datetime(2023, 1, 5).date()
        )
        
        assert len(result) == 5
        assert all(isinstance(item, MarketData) for item in result)
        assert result[0].symbol == "AAPL"
        assert result[0].source == "yahoo_finance"

    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    @pytest.mark.asyncio
    async def test_get_daily_prices_api_error(self, mock_ticker: Mock, adapter: YahooFinanceAdapter) -> None:
        """Test API error handling in daily price retrieval."""
        mock_ticker.side_effect = Exception("API Error")
        
        with pytest.raises(tenacity.RetryError):
            await adapter.get_daily_prices(
                symbol="AAPL",
                start_date=datetime(2023, 1, 1).date(),
                end_date=datetime(2023, 1, 5).date()
            )

    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    @pytest.mark.asyncio
    async def test_get_intraday_prices_success(self, mock_ticker: Mock, adapter: YahooFinanceAdapter, mock_yfinance_data: Any) -> None:
        """Test successful intraday price retrieval."""
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_yfinance_data
        mock_ticker.return_value = mock_ticker_instance
        
        result = await adapter.get_intraday_prices(symbol="AAPL", interval=5)
        
        assert len(result) == 5
        assert all(isinstance(item, MarketData) for item in result)
        assert result[0].symbol == "AAPL"

    @patch('src.data_sources.yahoo_finance.yf.Tickers')
    @pytest.mark.asyncio
    async def test_search_symbols(self, mock_tickers: Mock, adapter: YahooFinanceAdapter) -> None:
        """Test symbol search functionality."""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.ticker = 'AAPL'
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'quoteType': 'EQUITY',
            'exchange': 'NASDAQ'
        }
        
        mock_tickers_instance = Mock()
        mock_tickers_instance.tickers = [mock_ticker]
        mock_tickers.return_value = mock_tickers_instance
        
        result = await adapter.search_symbols("AAPL")
        
        assert len(result) == 1
        assert result[0]['symbol'] == 'AAPL'
        assert result[0]['name'] == 'Apple Inc.'

    def test_adapter_initialization(self, adapter: YahooFinanceAdapter) -> None:
        """Test adapter initialization."""
        assert hasattr(adapter, 'get_daily_prices')
        assert hasattr(adapter, 'get_intraday_prices')
        assert hasattr(adapter, 'search_symbols')

    def test_create_market_data_edge_cases(self, adapter: YahooFinanceAdapter) -> None:
        """Test market data creation edge cases."""
        
        # Test with zero volume
        row_data = {
            'Open': 100.0,
            'High': 105.0,
            'Low': 99.0,
            'Close': 102.0,
            'Volume': 0
        }
        
        timestamp = datetime(2023, 1, 1)
        result = adapter._create_market_data("TEST", timestamp, row_data)
        
        assert result.volume == 0

    def test_create_market_data_invalid_data(self, adapter: YahooFinanceAdapter) -> None:
        """Test market data creation with invalid data."""
        # Test with missing required fields
        row_data = {
            'Open': 100.0,
            # Missing other required fields
        }
        
        timestamp = datetime(2023, 1, 1)
        
        # Should handle missing data gracefully or raise appropriate error
        with pytest.raises((KeyError, ValueError, TypeError)):
            adapter._create_market_data("TEST", timestamp, row_data)