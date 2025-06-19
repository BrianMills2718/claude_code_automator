from datetime import datetime
from unittest.mock import patch

from src.storage.models import MarketDataModel


class TestMarketDataModel:
    """Unit tests for MarketDataModel."""

    def test_market_data_model_creation(self) -> None:
        """Test MarketDataModel creation."""
        model = MarketDataModel(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="yahoo_finance"
        )
        
        assert model.symbol == "AAPL"
        assert model.timestamp == datetime(2023, 1, 1, 9, 30)
        assert model.open == 100.0
        assert model.high == 105.0
        assert model.low == 99.0
        assert model.close == 102.0
        assert model.volume == 1000000
        assert model.source == "yahoo_finance"
        assert model.id is None  # Should be None before saving to DB

    def test_market_data_model_repr(self) -> None:
        """Test MarketDataModel string representation."""
        model = MarketDataModel(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="yahoo_finance"
        )
        
        repr_str = repr(model)
        assert "MarketData" in repr_str
        assert "AAPL" in repr_str
        assert "2023-01-01 09:30:00" in repr_str

    def test_market_data_model_table_name(self) -> None:
        """Test MarketDataModel table name."""
        assert MarketDataModel.__tablename__ == 'market_data'

    def test_market_data_model_columns(self) -> None:
        """Test MarketDataModel column definitions."""
        # Test that all expected columns exist
        columns = MarketDataModel.__table__.columns
        
        column_names = [col.name for col in columns]
        expected_columns = [
            'id', 'symbol', 'timestamp', 'open', 'high', 'low', 
            'close', 'volume', 'source', 'created_at'
        ]
        
        for expected_col in expected_columns:
            assert expected_col in column_names

    def test_market_data_model_primary_key(self) -> None:
        """Test MarketDataModel primary key."""
        id_column = MarketDataModel.__table__.columns['id']
        assert id_column.primary_key is True

    def test_market_data_model_nullable_constraints(self) -> None:
        """Test MarketDataModel nullable constraints."""
        columns = MarketDataModel.__table__.columns
        
        # These columns should not be nullable
        non_nullable_columns = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'source']
        for col_name in non_nullable_columns:
            assert columns[col_name].nullable is False

    def test_market_data_model_indexes(self) -> None:
        """Test MarketDataModel indexes."""
        columns = MarketDataModel.__table__.columns
        
        # Symbol and timestamp should be indexed
        assert columns['symbol'].index is True
        assert columns['timestamp'].index is True

    def test_market_data_model_unique_constraint(self) -> None:
        """Test MarketDataModel unique constraint."""
        constraints = MarketDataModel.__table__.constraints
        
        # Should have a unique constraint on symbol, timestamp, source
        unique_constraints = [c for c in constraints if hasattr(c, 'columns')]
        assert len(unique_constraints) > 0
        
        # Find the specific unique constraint
        target_constraint = None
        for constraint in unique_constraints:
            if hasattr(constraint, 'name') and constraint.name == 'uix_market_data_symbol_timestamp_source':
                target_constraint = constraint
                break
        
        assert target_constraint is not None

    def test_market_data_model_default_created_at(self) -> None:
        """Test MarketDataModel created_at default."""
        with patch('src.storage.models.datetime') as mock_datetime:
            mock_now = datetime(2023, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = mock_now
            
            # created_at should use the default function
            columns = MarketDataModel.__table__.columns
            created_at_column = columns['created_at']
            assert created_at_column.default is not None

    def test_market_data_model_edge_cases(self) -> None:
        """Test MarketDataModel edge cases."""
        # Test with minimum values
        model = MarketDataModel(
            symbol="A",  # Single character symbol
            timestamp=datetime(1970, 1, 1),  # Very old date
            open=0.01,  # Very small price
            high=0.01,
            low=0.01,
            close=0.01,
            volume=0,  # Zero volume
            source="test"
        )
        
        assert model.symbol == "A"
        assert model.volume == 0
        assert model.open == 0.01

    def test_market_data_model_large_values(self) -> None:
        """Test MarketDataModel with large values."""
        model = MarketDataModel(
            symbol="VERYLONGSYMBOL"[:10],  # Truncated to fit constraint
            timestamp=datetime(2099, 12, 31),  # Future date
            open=999999.99,  # Large price
            high=999999.99,
            low=999999.99,
            close=999999.99,
            volume=999999999999,  # Large volume
            source="very_long_source_name"[:20]  # Truncated to fit constraint
        )
        
        assert model.open == 999999.99
        assert model.volume == 999999999999

    def test_market_data_model_string_lengths(self) -> None:
        """Test MarketDataModel string field length constraints."""
        columns = MarketDataModel.__table__.columns
        
        # Symbol should have length constraint
        symbol_column = columns['symbol']
        assert hasattr(symbol_column.type, 'length')
        assert symbol_column.type.length == 10
        
        # Source should have length constraint
        source_column = columns['source']
        assert hasattr(source_column.type, 'length')
        assert source_column.type.length == 20

    def test_market_data_model_data_types(self) -> None:
        """Test MarketDataModel column data types."""
        columns = MarketDataModel.__table__.columns
        
        # Check specific column types
        assert str(columns['symbol'].type) == 'VARCHAR(10)'
        assert str(columns['source'].type) == 'VARCHAR(20)'
        assert 'INTEGER' in str(columns['id'].type)
        assert 'INTEGER' in str(columns['volume'].type)
        assert 'FLOAT' in str(columns['open'].type)
        assert 'DATETIME' in str(columns['timestamp'].type)

    def test_market_data_model_all_fields_set(self) -> None:
        """Test MarketDataModel with all fields explicitly set."""
        created_time = datetime(2023, 1, 1, 12, 0, 0)
        
        model = MarketDataModel(
            id=1,
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="yahoo_finance",
            created_at=created_time
        )
        
        assert model.id == 1
        assert model.created_at == created_time

    def test_market_data_model_comparison(self) -> None:
        """Test MarketDataModel comparison/equality."""
        model1 = MarketDataModel(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="yahoo_finance"
        )
        
        model2 = MarketDataModel(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="yahoo_finance"
        )
        
        # Objects should be different instances
        assert model1 is not model2
        
        # But should have the same data
        assert model1.symbol == model2.symbol
        assert model1.timestamp == model2.timestamp
        assert model1.open == model2.open