import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from typing import List

from src.processing.pipeline import DataPipeline
from src.data_sources.base import MarketData, DataSourceBase


class TestDataPipeline:
    """Unit tests for DataPipeline."""

    @pytest.fixture
    def sample_market_data(self) -> List[MarketData]:
        """Create sample market data for testing."""
        base_time = datetime(2023, 1, 1, 9, 30)
        return [
            MarketData(
                symbol="AAPL",
                timestamp=base_time,
                open=100.0,
                high=105.0,
                low=99.0,
                close=102.0,
                volume=1000000,
                source="test"
            ),
            MarketData(
                symbol="AAPL",
                timestamp=base_time.replace(hour=10),
                open=102.0,
                high=107.0,
                low=101.0,
                close=104.0,
                volume=1100000,
                source="test"
            )
        ]

    @pytest.fixture
    def mock_data_source(self, sample_market_data: List[MarketData]) -> Mock:
        """Create a mock data source."""
        mock_source = Mock(spec=DataSourceBase)
        mock_source.name = "test_source"
        mock_source.get_daily_prices = AsyncMock(return_value=sample_market_data)
        mock_source.get_intraday_prices = AsyncMock(return_value=sample_market_data)
        return mock_source

    def test_pipeline_initialization(self, mock_data_source: Mock) -> None:
        """Test pipeline initialization."""
        pipeline = DataPipeline([mock_data_source])
        
        assert len(pipeline.data_sources) == 1
        assert pipeline.data_sources[0] == mock_data_source

    def test_pipeline_initialization_empty(self) -> None:
        """Test pipeline initialization with empty sources."""
        pipeline = DataPipeline([])
        
        assert len(pipeline.data_sources) == 0

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, mock_data_source: Mock, sample_market_data: List[MarketData]) -> None:
        """Test successful data fetching."""
        pipeline = DataPipeline([mock_data_source])
        
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        assert response.success is True
        assert response.data is not None and len(response.data) == len(sample_market_data)
        mock_data_source.get_daily_prices.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_data_with_interval(self, mock_data_source: Mock, sample_market_data: List[MarketData]) -> None:
        """Test data fetching with intraday interval."""
        pipeline = DataPipeline([mock_data_source])
        
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5),
            interval=5
        )
        
        assert response.success is True
        mock_data_source.get_intraday_prices.assert_called_once_with(symbol="AAPL", interval=5)

    @pytest.mark.asyncio
    async def test_fetch_data_source_failure(self, mock_data_source: Mock) -> None:
        """Test data fetching with source failure."""
        mock_data_source.get_daily_prices.side_effect = Exception("API Error")
        
        pipeline = DataPipeline([mock_data_source])
        
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        assert response.success is False
        assert response.error is not None and "API Error" in response.error

    @pytest.mark.asyncio
    async def test_fetch_data_multiple_sources(self, sample_market_data: List[MarketData]) -> None:
        """Test data fetching with multiple sources."""
        # Create multiple mock sources
        mock_source1 = Mock(spec=DataSourceBase)
        mock_source1.name = "source1"
        mock_source1.get_daily_prices = AsyncMock(return_value=sample_market_data[:1])
        
        mock_source2 = Mock(spec=DataSourceBase)
        mock_source2.name = "source2"  
        mock_source2.get_daily_prices = AsyncMock(return_value=sample_market_data[1:])
        
        pipeline = DataPipeline([mock_source1, mock_source2])
        
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        assert response.success is True
        # Should get data from both sources
        assert response.data is not None and len(response.data) >= 1

    @pytest.mark.asyncio
    async def test_fetch_data_no_sources(self) -> None:
        """Test data fetching with no sources."""
        pipeline = DataPipeline([])
        
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        assert response.success is False
        assert response.error is not None and "No data sources" in response.error

    @pytest.mark.asyncio
    async def test_fetch_data_invalid_dates(self, mock_data_source: Mock) -> None:
        """Test data fetching with invalid date range."""
        pipeline = DataPipeline([mock_data_source])
        
        # End date before start date
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 5),  # Later date
            end_date=datetime(2023, 1, 1)    # Earlier date
        )
        
        assert response.success is False

    @pytest.mark.asyncio 
    async def test_fetch_data_empty_symbol(self, mock_data_source: Mock) -> None:
        """Test data fetching with empty symbol."""
        pipeline = DataPipeline([mock_data_source])
        
        response = await pipeline.fetch_data(
            symbol="",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        assert response.success is False

