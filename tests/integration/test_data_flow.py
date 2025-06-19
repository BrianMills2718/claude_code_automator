import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Any, List

from src.processing.pipeline import DataPipeline
from src.storage.repository import DataRepository
from src.data_sources.yahoo_finance import YahooFinanceAdapter
from src.data_sources.base import MarketData


class TestDataFlowIntegration:
    """Test end-to-end data flow integration."""

    @pytest.mark.asyncio
    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_complete_data_flow(self, mock_redis: Any, mock_create_engine: Any, mock_ticker: Any, mock_yahoo_finance_data: Any) -> None:
        """Test complete data flow from fetch to storage."""
        # Setup Yahoo Finance mock
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_yahoo_finance_data
        mock_ticker.return_value = mock_ticker_instance
        
        # Setup database mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_session_maker = Mock(return_value=mock_session)
        
        # Setup cache mock
        mock_cache = Mock()
        mock_redis.return_value = mock_cache
        
        # Create components
        yahoo_adapter = YahooFinanceAdapter()
        pipeline = DataPipeline([yahoo_adapter])
        repository: DataRepository = DataRepository()
        repository.Session = mock_session_maker
        
        # Test data flow
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        # Verify fetch
        assert response.success is True
        assert response.data is not None and len(response.data) > 0
        
        # Test storage
        # Convert StockPrice to MarketData for repository
        market_data_list = [MarketData(
            symbol=stock.symbol,
            timestamp=stock.timestamp,
            open=stock.open,
            high=stock.high,
            low=stock.low,
            close=stock.close,
            volume=stock.volume,
            source=stock.source
        ) for stock in (response.data or [])]
        repository.save_market_data(market_data_list)
        
        # Verify storage calls
        assert mock_session.merge.call_count == len(response.data or [])
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_data_flow_with_repository_failure(self, mock_redis: Any, mock_create_engine: Any, sample_market_data: List[MarketData]) -> None:
        """Test data flow handling repository failures gracefully."""
        # Setup failing database
        mock_create_engine.side_effect = Exception("DB Connection Failed")
        mock_cache = Mock()
        mock_redis.return_value = mock_cache
        
        # Create repository (should handle failure gracefully)
        repository: DataRepository = DataRepository()
        
        # Test storage with failed repository
        repository.save_market_data(sample_market_data)
        
        # Should not raise exception
        assert repository.engine is None
        assert repository.Session is None

    @pytest.mark.asyncio
    async def test_data_flow_with_pipeline_failure(self) -> None:
        """Test data flow handling pipeline failures."""
        # Create mock source that fails
        mock_source = Mock()
        mock_source.get_daily_prices = AsyncMock(side_effect=Exception("API Error"))
        
        pipeline = DataPipeline([mock_source])
        
        # Test fetch with failure
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        # Verify failure handling
        assert response.success is False
        assert response.error is not None

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_cache_integration(self, mock_redis: Any, mock_create_engine: Any, sample_market_data: List[MarketData]) -> None:
        """Test cache integration in data flow."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_cache.set_market_data = Mock()
        mock_redis.return_value = mock_cache
        
        # Create repository
        repository: DataRepository = DataRepository()
        repository.Session = mock_session_maker
        
        # Test saving with cache
        repository.save_market_data(sample_market_data)
        
        # Verify cache calls
        assert mock_cache.set_market_data.call_count == len(sample_market_data)

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_data_retrieval_integration(self, mock_redis: Any, mock_create_engine: Any, sample_market_data: List[MarketData]) -> None:
        """Test data retrieval integration."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Create mock database rows
        mock_rows = []
        for data in sample_market_data:
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
        repository: DataRepository = DataRepository()
        repository.Session = mock_session_maker
        
        # Test retrieval
        result = repository.get_market_data("AAPL")
        
        # Verify
        assert len(result) == len(sample_market_data)
        assert all(item.symbol == "AAPL" for item in result)