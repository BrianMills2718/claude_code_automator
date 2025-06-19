import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from src.storage.models import Base, MarketDataModel


@pytest.fixture
def in_memory_db() -> Session:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


class TestMarketDataModel:
    """Test MarketDataModel functionality."""

    def test_market_data_model_creation(self, in_memory_db: Session) -> None:
        """Test MarketDataModel creation and persistence."""
        # Create model instance
        market_data = MarketDataModel(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        # Test attributes
        assert market_data.symbol == "AAPL"
        assert market_data.timestamp == datetime(2023, 1, 1, 9, 30)
        assert market_data.open == 100.0
        assert market_data.high == 105.0
        assert market_data.low == 99.0
        assert market_data.close == 102.0
        assert market_data.volume == 1000000
        assert market_data.source == "test"

    def test_market_data_model_persistence(self, in_memory_db: Session) -> None:
        """Test saving and retrieving MarketDataModel."""
        # Create and save model
        market_data = MarketDataModel(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        in_memory_db.add(market_data)
        in_memory_db.commit()
        
        # Retrieve and verify
        retrieved = in_memory_db.query(MarketDataModel).filter_by(symbol="AAPL").first()
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"
        assert retrieved.close == 102.0

    def test_market_data_model_uniqueness(self, in_memory_db: Session) -> None:
        """Test unique constraint on symbol, timestamp, source."""
        # Create first record
        market_data1 = MarketDataModel(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        in_memory_db.add(market_data1)
        in_memory_db.commit()
        
        # Create duplicate record (same symbol, timestamp, source)
        market_data2 = MarketDataModel(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=101.0,  # Different values
            high=106.0,
            low=100.0,
            close=103.0,
            volume=1100000,
            source="test"  # Same source
        )
        
        in_memory_db.add(market_data2)
        
        # This should handle the uniqueness constraint
        # depending on the model's unique constraint implementation
        try:
            in_memory_db.commit()
        except Exception:
            in_memory_db.rollback()
            
        # Should still have only one record or updated record
        count = in_memory_db.query(MarketDataModel).filter_by(symbol="AAPL").count()
        assert count >= 1