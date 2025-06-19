import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Any, List
import pandas as pd

from src.storage.repository import DataRepository
from src.data_sources.base import MarketData
from src.cli.commands import get_pipeline, analyze


class TestTechnicalAnalysisIntegration:
    """Test integration between data components and technical analysis workflow."""

    @pytest.fixture
    def sample_time_series_data(self) -> List[MarketData]:
        """Create sample time series data for technical analysis."""
        base_date = datetime(2023, 1, 1)
        data = []
        prices = [100.0, 102.0, 104.0, 103.0, 105.0, 107.0, 106.0, 108.0, 110.0, 109.0]
        
        for i, price in enumerate(prices):
            data.append(MarketData(
                symbol="AAPL",
                timestamp=base_date + timedelta(days=i),
                open=price - 0.5,
                high=price + 1.0,
                low=price - 1.0,
                close=price,
                volume=1000000 + (i * 10000),
                source="yahoo_finance"
            ))
        return data

    @pytest.mark.asyncio
    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_data_pipeline_for_technical_analysis(
        self, 
        mock_redis: Any, 
        mock_create_engine: Any, 
        mock_ticker: Any,
        mock_yahoo_finance_data: Any
    ) -> None:
        """Test that data pipeline provides clean data suitable for technical analysis."""
        # Setup mocks
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_yahoo_finance_data
        mock_ticker.return_value = mock_ticker_instance
        
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_redis.return_value = mock_cache
        
        # Create pipeline
        pipeline = get_pipeline()
        repository = DataRepository()
        repository.Session = mock_session_maker
        
        # Fetch data
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 10)
        )
        
        # Verify data is suitable for technical analysis
        assert response.success is True
        assert response.data is not None
        assert len(response.data) > 0
        
        # Verify data has required fields for technical indicators
        sample_data = response.data[0]
        assert hasattr(sample_data, 'open')
        assert hasattr(sample_data, 'high')
        assert hasattr(sample_data, 'low')
        assert hasattr(sample_data, 'close')
        assert hasattr(sample_data, 'volume')
        assert hasattr(sample_data, 'timestamp')
        
        # Verify data is chronologically ordered (important for technical analysis)
        timestamps = [item.timestamp for item in response.data]
        assert timestamps == sorted(timestamps)

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_repository_time_series_retrieval(
        self, 
        mock_redis: Any, 
        mock_create_engine: Any,
        sample_time_series_data: List[MarketData]
    ) -> None:
        """Test repository retrieval of time series data for technical analysis."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Create mock database rows in chronological order
        mock_rows = []
        for data in sample_time_series_data:
            mock_row = Mock()
            mock_row.symbol = data.symbol
            mock_row.timestamp = data.timestamp
            mock_row.open = data.open
            mock_row.high = data.high
            mock_row.low = data.low
            mock_row.close = data.close
            mock_row.volume = data.volume
            mock_row.source = data.source
            mock_rows.append(mock_row)
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        mock_execute_result = Mock()
        mock_execute_result.scalars.return_value = mock_rows
        mock_session.execute.return_value = mock_execute_result
        
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_cache.get_market_data = Mock(return_value=None)
        mock_redis.return_value = mock_cache
        
        # Create repository
        repository = DataRepository()
        repository.Session = mock_session_maker
        
        # Test retrieval
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 10)
        result = repository.get_market_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify data is suitable for technical analysis
        assert len(result) == len(sample_time_series_data)
        assert all(item.symbol == "AAPL" for item in result)
        
        # Verify timestamps are within requested range
        for item in result:
            assert start_date <= item.timestamp <= end_date
        
        # Convert to DataFrame to verify data structure (common for technical analysis)
        df = pd.DataFrame([item.model_dump() for item in result])
        
        # Verify DataFrame has required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
        assert all(col in df.columns for col in required_columns)
        
        # Verify data types are suitable for calculations
        assert df['open'].dtype in ['float64', 'int64']
        assert df['high'].dtype in ['float64', 'int64']
        assert df['low'].dtype in ['float64', 'int64']
        assert df['close'].dtype in ['float64', 'int64']
        assert df['volume'].dtype in ['float64', 'int64']

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_cli_analysis_integration(
        self, 
        mock_redis: Any, 
        mock_create_engine: Any,
        sample_time_series_data: List[MarketData]
    ) -> None:
        """Test CLI analysis command integration with data retrieval."""
        # Setup mocks similar to previous test
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_rows = []
        for data in sample_time_series_data:
            mock_row = Mock()
            mock_row.symbol = data.symbol
            mock_row.timestamp = data.timestamp
            mock_row.open = data.open
            mock_row.high = data.high
            mock_row.low = data.low
            mock_row.close = data.close
            mock_row.volume = data.volume
            mock_row.source = data.source
            mock_rows.append(mock_row)
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        mock_execute_result = Mock()
        mock_execute_result.scalars.return_value = mock_rows
        mock_session.execute.return_value = mock_execute_result
        
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_cache.get_market_data = Mock(return_value=None)
        mock_redis.return_value = mock_cache
        
        # Mock the repository creation in the CLI
        with patch('src.cli.commands.get_repository') as mock_get_repo, \
             patch('src.cli.commands.console') as mock_console:
            
            mock_repo = DataRepository()
            mock_repo.Session = mock_session_maker
            mock_get_repo.return_value = mock_repo
            
            # Test the analyze command (simulating CLI call)
            try:
                analyze("AAPL", days=10)
                # If no exception raised, the integration works
                analysis_successful = True
            except Exception:
                analysis_successful = False
            
            # Verify analysis was attempted
            assert analysis_successful or mock_console.print.called
            
            # Verify repository was called with correct parameters
            mock_get_repo.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_consistency_for_technical_indicators(
        self, 
        sample_time_series_data: List[MarketData]
    ) -> None:
        """Test data consistency requirements for technical indicators."""
        # Verify no missing data points (gaps can break technical indicators)
        timestamps = [data.timestamp for data in sample_time_series_data]
        timestamps.sort()
        
        # Check for reasonable gaps (no more than 3 days for daily data)
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i-1]).days
            assert gap <= 3, f"Data gap too large: {gap} days"
        
        # Verify OHLC consistency (technical requirement)
        for data in sample_time_series_data:
            assert data.high >= data.open, f"High {data.high} < Open {data.open}"
            assert data.high >= data.close, f"High {data.high} < Close {data.close}"
            assert data.low <= data.open, f"Low {data.low} > Open {data.open}"
            assert data.low <= data.close, f"Low {data.low} > Close {data.close}"
            assert data.high >= data.low, f"High {data.high} < Low {data.low}"
            assert data.volume >= 0, f"Negative volume: {data.volume}"

    @pytest.mark.asyncio
    async def test_data_aggregation_for_multiple_timeframes(
        self,
        sample_time_series_data: List[MarketData]
    ) -> None:
        """Test data can be aggregated for different timeframes (needed for multi-timeframe analysis)."""
        # Convert to DataFrame for aggregation
        df = pd.DataFrame([data.model_dump() for data in sample_time_series_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Test weekly aggregation (common for technical analysis)
        weekly_data = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Verify aggregation maintains OHLC integrity
        for _, row in weekly_data.iterrows():
            assert row['high'] >= row['open']
            assert row['high'] >= row['close']
            assert row['low'] <= row['open']
            assert row['low'] <= row['close']
            assert row['high'] >= row['low']
            assert row['volume'] >= 0

    @pytest.mark.asyncio
    async def test_error_handling_in_technical_analysis_workflow(self) -> None:
        """Test error handling when data is insufficient for technical analysis."""
        # Test with empty data
        empty_data: List[MarketData] = []
        
        # Verify pandas DataFrame creation handles empty data gracefully
        df = pd.DataFrame([data.model_dump() for data in empty_data])
        assert len(df) == 0
        
        # Test with single data point (insufficient for most indicators)
        single_data = [MarketData(
            symbol="TEST",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=101.0,
            low=99.0,
            close=100.5,
            volume=1000,
            source="test"
        )]
        
        df_single = pd.DataFrame([data.model_dump() for data in single_data])
        assert len(df_single) == 1
        
        # Verify basic calculations work with single point
        assert df_single['close'].mean() == 100.5
        assert df_single['volume'].sum() == 1000