import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Tuple

from src.data_sources.alpha_vantage import AlphaVantageAdapter, TimeSeriesConfig
from src.data_sources.base import MarketData
from src.data_sources.exceptions import APIError, RateLimitError


class TestTimeSeriesConfig:
    """Unit tests for TimeSeriesConfig dataclass."""

    def test_time_series_config_creation(self) -> None:
        """Test TimeSeriesConfig creation."""
        config = TimeSeriesConfig(
            symbol="AAPL",
            timestamp_format="%Y-%m-%d",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            limit=100
        )
        
        assert config.symbol == "AAPL"
        assert config.timestamp_format == "%Y-%m-%d"
        assert config.start_date == date(2023, 1, 1)
        assert config.end_date == date(2023, 1, 31)
        assert config.limit == 100

    def test_time_series_config_minimal(self) -> None:
        """Test TimeSeriesConfig with minimal parameters."""
        config = TimeSeriesConfig(
            symbol="AAPL",
            timestamp_format="%Y-%m-%d"
        )
        
        assert config.symbol == "AAPL"
        assert config.timestamp_format == "%Y-%m-%d"
        assert config.start_date is None
        assert config.end_date is None
        assert config.limit is None


class TestAlphaVantageAdapter:
    """Unit tests for AlphaVantageAdapter."""

    @pytest.fixture
    def mock_settings(self) -> None:
        """Mock settings for testing."""
        with patch('src.data_sources.alpha_vantage.settings') as mock_settings:
            mock_settings.ALPHA_VANTAGE_API_KEY.get_secret_value.return_value = "test_api_key"
            mock_settings.ALPHA_VANTAGE_RATE_LIMIT = 5
            mock_settings.ALPHA_VANTAGE_RATE_LIMIT_WINDOW_MINUTES = 1
            mock_settings.ALPHA_VANTAGE_COMPACT_LIMIT_THRESHOLD = 100
            mock_settings.ALPHA_VANTAGE_DEFAULT_OUTPUTSIZE = "full"
            mock_settings.ALPHA_VANTAGE_DAILY_TIMESTAMP_FORMAT = "%Y-%m-%d"
            mock_settings.ALPHA_VANTAGE_INTRADAY_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
            yield mock_settings

    @pytest.fixture
    def adapter(self, mock_settings: Any) -> AlphaVantageAdapter:
        """Create AlphaVantageAdapter instance for testing."""
        with patch('src.data_sources.alpha_vantage.TimeSeries'):
            return AlphaVantageAdapter()

    def test_adapter_initialization_success(self, mock_settings: Any) -> None:
        """Test successful adapter initialization."""
        with patch('src.data_sources.alpha_vantage.TimeSeries') as mock_ts:
            adapter = AlphaVantageAdapter()
            assert hasattr(adapter, '_client')
            assert hasattr(adapter, '_request_times')
            assert hasattr(adapter, '_lock')
            mock_ts.assert_called_once_with(key="test_api_key")

    def test_adapter_initialization_no_api_key(self) -> None:
        """Test adapter initialization without API key."""
        with patch('src.data_sources.alpha_vantage.settings') as mock_settings:
            mock_settings.ALPHA_VANTAGE_API_KEY = None
            
            with pytest.raises(ValueError, match="ALPHA_VANTAGE_API_KEY is required"):
                AlphaVantageAdapter()

    def test_handle_api_error(self, adapter: AlphaVantageAdapter) -> None:
        """Test API error handling."""
        test_error = Exception("Test error")
        
        with pytest.raises(APIError, match="Alpha Vantage API error: Test error"):
            adapter._handle_api_error(test_error)

    def test_extract_price_fields(self, adapter: AlphaVantageAdapter) -> None:
        """Test price field extraction."""
        values = {
            '1. open': '100.50',
            '2. high': '105.75',
            '3. low': '99.25',
            '4. close': '102.00',
            '5. volume': '1500000'
        }
        
        result = adapter._extract_price_fields(values)
        
        assert result['open'] == 100.50
        assert result['high'] == 105.75
        assert result['low'] == 99.25
        assert result['close'] == 102.00
        assert result['volume'] == 1500000

    def test_parse_field_value(self, adapter: AlphaVantageAdapter) -> None:
        """Test field value parsing."""
        # Test float parsing
        assert adapter._parse_field_value("100.50", False) == 100.50
        
        # Test integer parsing for volume
        assert adapter._parse_field_value("1500000", True) == 1500000

    def test_create_market_data_from_values(self, adapter: AlphaVantageAdapter) -> None:
        """Test MarketData creation from values."""
        values = {
            '1. open': '100.50',
            '2. high': '105.75',
            '3. low': '99.25',
            '4. close': '102.00',
            '5. volume': '1500000'
        }
        
        timestamp = datetime(2023, 1, 1, 9, 30)
        result = adapter._create_market_data_from_values("AAPL", timestamp, values)
        
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        assert result.timestamp == timestamp
        assert result.open == 100.50
        assert result.high == 105.75
        assert result.low == 99.25
        assert result.close == 102.00
        assert result.volume == 1500000
        assert result.source == "alpha_vantage"

    def test_cleanup_old_requests(self, adapter: AlphaVantageAdapter) -> None:
        """Test cleanup of old request timestamps."""
        now = datetime.now()
        old_time = now - timedelta(minutes=2)
        recent_time = now - timedelta(seconds=30)
        
        adapter._request_times = [old_time, recent_time]
        adapter._cleanup_old_requests(now)
        
        # Old request should be removed
        assert len(adapter._request_times) == 1
        assert adapter._request_times[0] == recent_time

    def test_is_request_within_window(self, adapter: AlphaVantageAdapter) -> None:
        """Test request time window checking."""
        current_time = datetime.now()
        
        # Recent request should be within window
        recent_time = current_time - timedelta(seconds=30)
        assert adapter._is_request_within_window(current_time, recent_time)
        
        # Old request should be outside window
        old_time = current_time - timedelta(minutes=2)
        assert not adapter._is_request_within_window(current_time, old_time)

    def test_is_within_rate_limit(self, adapter: AlphaVantageAdapter) -> None:
        """Test rate limit checking."""
        now = datetime.now()
        
        # Empty request list should be within limit
        adapter._request_times = []
        assert adapter._is_within_rate_limit(now)
        
        # List below limit should be within limit
        adapter._request_times = [now - timedelta(seconds=30)] * 3
        assert adapter._is_within_rate_limit(now)
        
        # List at limit should exceed limit
        adapter._request_times = [now - timedelta(seconds=30)] * 5
        assert not adapter._is_within_rate_limit(now)

    @pytest.mark.asyncio
    async def test_manage_rate_limit_success(self, adapter: AlphaVantageAdapter) -> None:
        """Test successful rate limit management."""
        adapter._request_times = []
        
        await adapter._manage_rate_limit()
        
        # Should add current time to request list
        assert len(adapter._request_times) == 1

    @pytest.mark.asyncio
    async def test_manage_rate_limit_exceeded(self, adapter: AlphaVantageAdapter) -> None:
        """Test rate limit exceeded."""
        # Fill up the rate limit
        now = datetime.now()
        adapter._request_times = [now - timedelta(seconds=30)] * 5
        
        with pytest.raises(RateLimitError, match="Alpha Vantage rate limit exceeded"):
            await adapter._manage_rate_limit()

    @pytest.mark.asyncio
    async def test_execute_api_operation_success(self, adapter: AlphaVantageAdapter) -> None:
        """Test successful API operation execution."""
        def mock_operation() -> str:
            return "success"
        
        adapter._request_times = []  # Reset rate limit
        result = await adapter._execute_api_operation(mock_operation)
        
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_api_operation_error(self, adapter: AlphaVantageAdapter) -> None:
        """Test API operation with error."""
        def mock_operation() -> None:
            raise Exception("API Error")
        
        adapter._request_times = []  # Reset rate limit
        
        with pytest.raises(APIError, match="Alpha Vantage API error: API Error"):
            await adapter._execute_api_operation(mock_operation)

    def test_is_date_in_range(self, adapter: AlphaVantageAdapter) -> None:
        """Test date range checking."""
        timestamp = datetime(2023, 1, 15)
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 31)
        
        # Within range
        assert adapter._is_date_in_range(timestamp, start_date, end_date)
        
        # Before start date
        early_timestamp = datetime(2022, 12, 31)
        assert not adapter._is_date_in_range(early_timestamp, start_date, end_date)
        
        # After end date
        late_timestamp = datetime(2023, 2, 1)
        assert not adapter._is_date_in_range(late_timestamp, start_date, end_date)
        
        # No date restrictions
        assert adapter._is_date_in_range(timestamp, None, None)

    def test_process_time_series_data(self, adapter: AlphaVantageAdapter) -> None:
        """Test time series data processing."""
        data = {
            "2023-01-01": {
                '1. open': '100.00',
                '2. high': '105.00',
                '3. low': '99.00',
                '4. close': '102.00',
                '5. volume': '1000000'
            },
            "2023-01-02": {
                '1. open': '102.00',
                '2. high': '107.00',
                '3. low': '101.00',
                '4. close': '104.00',
                '5. volume': '1100000'
            }
        }
        
        config = TimeSeriesConfig(
            symbol="AAPL",
            timestamp_format="%Y-%m-%d"
        )
        
        result = adapter._process_time_series_data(data, config)
        
        assert len(result) == 2
        assert all(isinstance(item, MarketData) for item in result)
        assert result[0].symbol == "AAPL"
        assert result[0].source == "alpha_vantage"

    def test_process_time_series_data_with_date_filter(self, adapter: AlphaVantageAdapter) -> None:
        """Test time series data processing with date filtering."""
        data = {
            "2023-01-01": {
                '1. open': '100.00',
                '2. high': '105.00',
                '3. low': '99.00',
                '4. close': '102.00',
                '5. volume': '1000000'
            },
            "2023-01-15": {
                '1. open': '102.00',
                '2. high': '107.00',
                '3. low': '101.00',
                '4. close': '104.00',
                '5. volume': '1100000'
            }
        }
        
        config = TimeSeriesConfig(
            symbol="AAPL",
            timestamp_format="%Y-%m-%d",
            start_date=date(2023, 1, 10),
            end_date=date(2023, 1, 20)
        )
        
        result = adapter._process_time_series_data(data, config)
        
        # Should only include the second entry
        assert len(result) == 1
        assert result[0].timestamp == datetime(2023, 1, 15)

    def test_process_time_series_data_with_limit(self, adapter: AlphaVantageAdapter) -> None:
        """Test time series data processing with limit."""
        data = {
            f"2023-01-{i:02d}": {
                '1. open': '100.00',
                '2. high': '105.00',
                '3. low': '99.00',
                '4. close': '102.00',
                '5. volume': '1000000'
            } for i in range(1, 6)
        }
        
        config = TimeSeriesConfig(
            symbol="AAPL",
            timestamp_format="%Y-%m-%d",
            limit=3
        )
        
        result = adapter._process_time_series_data(data, config)
        
        # Should respect the limit
        assert len(result) == 3

    def test_get_outputsize_for_limit(self, adapter: AlphaVantageAdapter) -> None:
        """Test outputsize determination based on limit."""
        # Small limit should use compact
        assert adapter._get_outputsize_for_limit(50) == 'compact'
        
        # Large limit should use default
        assert adapter._get_outputsize_for_limit(200) == 'full'
        
        # No limit should use default
        assert adapter._get_outputsize_for_limit(None) == 'full'

    def test_format_symbol_match(self, adapter: AlphaVantageAdapter) -> None:
        """Test symbol search match formatting."""
        match = {
            '1. symbol': 'AAPL',
            '2. name': 'Apple Inc.',
            '3. type': 'Equity',
            '4. region': 'United States'
        }
        
        result = adapter._format_symbol_match(match)
        
        assert result['symbol'] == 'AAPL'
        assert result['name'] == 'Apple Inc.'
        assert result['type'] == 'Equity'
        assert result['region'] == 'United States'

    @pytest.mark.asyncio
    async def test_get_daily_prices(self, adapter: AlphaVantageAdapter) -> None:
        """Test daily price retrieval."""
        mock_data = {
            "2023-01-01": {
                '1. open': '100.00',
                '2. high': '105.00',
                '3. low': '99.00',
                '4. close': '102.00',
                '5. volume': '1000000'
            }
        }
        
        adapter._client.get_daily = Mock(return_value=(mock_data, {}))
        adapter._request_times = []  # Reset rate limit
        
        result = await adapter.get_daily_prices("AAPL")
        
        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert result[0].source == "alpha_vantage"

    @pytest.mark.asyncio
    async def test_get_intraday_prices(self, adapter: AlphaVantageAdapter) -> None:
        """Test intraday price retrieval."""
        mock_data = {
            "2023-01-01 09:30:00": {
                '1. open': '100.00',
                '2. high': '105.00',
                '3. low': '99.00',
                '4. close': '102.00',
                '5. volume': '1000000'
            }
        }
        
        adapter._client.get_intraday = Mock(return_value=(mock_data, {}))
        adapter._request_times = []  # Reset rate limit
        
        result = await adapter.get_intraday_prices("AAPL", interval=5)
        
        assert len(result) == 1
        assert result[0].symbol == "AAPL"
        assert result[0].source == "alpha_vantage"

    @pytest.mark.asyncio
    async def test_search_symbols(self, adapter: AlphaVantageAdapter) -> None:
        """Test symbol search."""
        mock_matches = [
            {
                '1. symbol': 'AAPL',
                '2. name': 'Apple Inc.',
                '3. type': 'Equity',
                '4. region': 'United States'
            }
        ]
        
        adapter._client.get_symbol_search = Mock(return_value=mock_matches)
        adapter._request_times = []  # Reset rate limit
        
        result = await adapter.search_symbols("AAPL")
        
        assert len(result) == 1
        assert result[0]['symbol'] == 'AAPL'
        assert result[0]['name'] == 'Apple Inc.'

    def test_create_api_operation(self, adapter: AlphaVantageAdapter) -> None:
        """Test API operation creation."""
        def mock_func() -> Tuple[str, Any]:
            return ("result", "metadata")
        
        operation = adapter._create_api_operation(mock_func)
        result = operation()
        
        # Should return the first element of tuple
        assert result == "result"

    def test_create_api_operation_non_tuple(self, adapter: AlphaVantageAdapter) -> None:
        """Test API operation creation with non-tuple result."""
        def mock_func() -> str:
            return "result"
        
        operation = adapter._create_api_operation(mock_func)
        result = operation()
        
        # Should return the result as-is
        assert result == "result"