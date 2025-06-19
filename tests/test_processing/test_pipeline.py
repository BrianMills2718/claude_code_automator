import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, date

from src.processing.pipeline import DataPipeline
from src.data_sources.base import MarketData


@pytest.fixture
def mock_data_source():
    """Create mock data source."""
    source = Mock()
    source.get_daily_prices = AsyncMock()
    source.get_intraday_prices = AsyncMock()
    source.search_symbols = AsyncMock()
    return source


@pytest.fixture
def sample_pipeline_data():
    """Create sample data for pipeline testing."""
    return [
        MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
    ]


class TestDataPipeline:
    """Test DataPipeline functionality."""

    def test_pipeline_initialization(self, mock_data_source):
        """Test pipeline initialization with data sources."""
        pipeline = DataPipeline([mock_data_source])
        
        assert len(pipeline.data_sources) == 1
        assert pipeline.data_sources[0] == mock_data_source

    def test_pipeline_initialization_empty(self):
        """Test pipeline initialization with empty sources."""
        pipeline = DataPipeline([])
        
        assert len(pipeline.data_sources) == 0

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, mock_data_source, sample_pipeline_data):
        """Test successful data fetching."""
        # Setup mock
        mock_data_source.get_daily_prices.return_value = sample_pipeline_data
        
        pipeline = DataPipeline([mock_data_source])
        
        # Test
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        # Verify
        assert response.success is True
        assert len(response.data) == 1
        assert response.data[0].symbol == "AAPL"
        assert response.error is None

    @pytest.mark.asyncio
    async def test_fetch_data_with_interval(self, mock_data_source, sample_pipeline_data):
        """Test data fetching with intraday interval."""
        # Setup mock
        mock_data_source.get_intraday_prices.return_value = sample_pipeline_data
        
        pipeline = DataPipeline([mock_data_source])
        
        # Test
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5),
            interval=5
        )
        
        # Verify
        assert response.success is True
        mock_data_source.get_intraday_prices.assert_called_once_with("AAPL", 5, None)

    @pytest.mark.asyncio
    async def test_fetch_data_source_failure(self, mock_data_source):
        """Test data fetching with source failure."""
        # Setup mock to fail
        mock_data_source.get_daily_prices.side_effect = Exception("API Error")
        
        pipeline = DataPipeline([mock_data_source])
        
        # Test
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        # Verify
        assert response.success is False
        assert response.error is not None
        assert "API Error" in response.error

    @pytest.mark.asyncio
    async def test_fetch_data_multiple_sources(self, sample_pipeline_data):
        """Test data fetching with multiple sources."""
        # Create multiple mock sources
        source1 = Mock()
        source1.get_daily_prices = AsyncMock(return_value=sample_pipeline_data[:1])
        
        source2 = Mock()
        source2.get_daily_prices = AsyncMock(return_value=sample_pipeline_data[:1])
        
        pipeline = DataPipeline([source1, source2])
        
        # Test
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        # Verify
        assert response.success is True
        # Should combine data from both sources
        assert len(response.data) >= 1

    @pytest.mark.asyncio
    async def test_fetch_data_no_sources(self):
        """Test data fetching with no sources."""
        pipeline = DataPipeline([])
        
        # Test
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 5)
        )
        
        # Verify
        assert response.success is False
        assert "No data sources" in response.error