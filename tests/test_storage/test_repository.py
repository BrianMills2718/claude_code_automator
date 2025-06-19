from typing import Any, List
from unittest.mock import Mock, patch

from src.storage.repository import DataRepository
from src.data_sources.base import MarketData


class TestDataRepository:
    """Test DataRepository functionality."""

    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    def test_repository_initialization_success(self, mock_redis: Any, mock_create_engine: Any) -> None:
        """Test successful repository initialization."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_cache = Mock()
        mock_redis.return_value = mock_cache
        
        # Create repository
        repo = DataRepository()
        
        # Verify initialization
        assert repo.engine is not None
        assert repo.Session is not None
        assert repo.cache is not None

    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    def test_repository_initialization_db_failure(self, mock_redis: Any, mock_create_engine: Any) -> None:
        """Test repository initialization with database failure."""
        # Setup mocks
        mock_create_engine.side_effect = Exception("DB Connection Failed")
        mock_cache = Mock()
        mock_redis.return_value = mock_cache
        
        # Create repository
        repo = DataRepository()
        
        # Verify graceful failure handling
        assert repo.engine is None
        assert repo.Session is None
        assert repo.cache is not None

    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    def test_repository_initialization_cache_failure(self, mock_redis: Any, mock_create_engine: Any) -> None:
        """Test repository initialization with cache failure."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_redis.side_effect = Exception("Redis Connection Failed")
        
        # Create repository
        repo = DataRepository()
        
        # Verify graceful failure handling
        assert repo.engine is not None
        assert repo.Session is not None
        assert repo.cache is None

    def test_save_market_data_no_database(self, sample_market_data: List[MarketData]) -> None:
        """Test saving market data when database is unavailable."""
        # Create repository with no database
        repo = DataRepository()
        repo.engine = None
        repo.Session = None
        repo.cache = None
        
        # Should not raise exception
        repo.save_market_data(sample_market_data)

    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    def test_save_market_data_success(self, mock_redis: Any, mock_create_engine: Any, sample_market_data: List[MarketData]) -> None:
        """Test successful market data saving."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_redis.return_value = mock_cache
        
        # Create repository and patch Session
        repo = DataRepository()
        repo.Session = mock_session_maker
        
        # Test saving
        repo.save_market_data(sample_market_data)
        
        # Verify calls
        assert mock_session.merge.call_count == len(sample_market_data)
        mock_session.commit.assert_called_once()

    def test_get_market_data_no_database(self) -> None:
        """Test getting market data when database is unavailable."""
        # Create repository with no database
        repo = DataRepository()
        repo.engine = None
        repo.Session = None
        repo.cache = None
        
        # Should return empty list
        result = repo.get_market_data("AAPL")
        assert result == []

    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    def test_get_market_data_success(self, mock_redis: Any, mock_create_engine: Any, sample_market_data: List[MarketData]) -> None:
        """Test successful market data retrieval."""
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
        
        mock_scalars = Mock()
        mock_scalars.return_value = mock_rows
        mock_execute_result = Mock()
        mock_execute_result.scalars.return_value = mock_rows
        mock_session.execute.return_value = mock_execute_result
        
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_cache.get_market_data.return_value = None  # Cache miss
        mock_redis.return_value = mock_cache
        
        # Create repository
        repo = DataRepository()
        repo.Session = mock_session_maker
        
        # Test retrieval
        result = repo.get_market_data("AAPL")
        
        # Verify results
        assert len(result) == len(sample_market_data)
        assert all(isinstance(item, MarketData) for item in result)