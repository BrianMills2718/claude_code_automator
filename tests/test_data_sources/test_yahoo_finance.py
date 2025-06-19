import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import date, datetime

from src.data_sources.yahoo_finance import YahooFinanceAdapter
from src.data_sources.exceptions import APIError


@pytest.fixture
def yahoo_adapter():
    """Create Yahoo Finance adapter for testing."""
    return YahooFinanceAdapter()


class TestYahooFinanceAdapter:
    """Test Yahoo Finance adapter functionality."""

    def test_create_market_data(self, yahoo_adapter):
        """Test market data creation from DataFrame row."""
        symbol = "AAPL"
        timestamp = datetime(2023, 1, 1, 9, 30)
        row = {
            'Open': 100.0,
            'High': 105.0,
            'Low': 99.0,
            'Close': 102.0,
            'Volume': 1000000
        }
        
        # Mock the timestamp
        mock_timestamp = Mock()
        mock_timestamp.to_pydatetime.return_value = timestamp
        
        market_data = yahoo_adapter._create_market_data(symbol, mock_timestamp, row)
        
        assert market_data.symbol == "AAPL"
        assert market_data.timestamp == timestamp
        assert market_data.open == 100.0
        assert market_data.high == 105.0
        assert market_data.low == 99.0
        assert market_data.close == 102.0
        assert market_data.volume == 1000000
        assert market_data.source == "yahoo_finance"

    @pytest.mark.asyncio
    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    async def test_get_daily_prices_success(self, mock_ticker, yahoo_adapter, mock_yahoo_finance_data):
        """Test successful daily price retrieval."""
        # Setup mock
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_yahoo_finance_data
        mock_ticker.return_value = mock_ticker_instance
        
        # Test
        result = await yahoo_adapter.get_daily_prices(
            "AAPL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 5)
        )
        
        # Verify
        assert len(result) == 5
        assert all(item.symbol == "AAPL" for item in result)
        assert all(item.source == "yahoo_finance" for item in result)
        mock_ticker.assert_called_once_with("AAPL")
        mock_ticker_instance.history.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    async def test_get_daily_prices_api_error(self, mock_ticker, yahoo_adapter):
        """Test API error handling in daily price retrieval."""
        # Setup mock to raise exception
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.side_effect = Exception("API Error")
        mock_ticker.return_value = mock_ticker_instance
        
        # Test
        with pytest.raises(APIError):
            await yahoo_adapter.get_daily_prices("AAPL")

    @pytest.mark.asyncio
    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    async def test_get_intraday_prices_success(self, mock_ticker, yahoo_adapter, mock_yahoo_finance_data):
        """Test successful intraday price retrieval."""
        # Setup mock
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_yahoo_finance_data
        mock_ticker.return_value = mock_ticker_instance
        
        # Test
        result = await yahoo_adapter.get_intraday_prices("AAPL", interval=5)
        
        # Verify
        assert len(result) == 5
        assert all(item.symbol == "AAPL" for item in result)
        mock_ticker_instance.history.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_symbols(self, yahoo_adapter):
        """Test symbol search functionality."""
        # Yahoo Finance adapter doesn't implement search
        # This should return empty list or raise NotImplementedError
        result = await yahoo_adapter.search_symbols("AAPL")
        assert isinstance(result, list)