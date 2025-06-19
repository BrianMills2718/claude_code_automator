import pytest
from datetime import datetime, date
from typing import Dict, List, Optional
from abc import ABC

from src.data_sources.base import MarketData, DataSourceBase


class TestMarketData:
    """Unit tests for MarketData model."""

    def test_market_data_creation(self) -> None:
        """Test MarketData creation with valid data."""
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="yahoo_finance"
        )
        
        assert market_data.symbol == "AAPL"
        assert market_data.timestamp == datetime(2023, 1, 1, 9, 30)
        assert market_data.open == 100.0
        assert market_data.high == 105.0
        assert market_data.low == 99.0
        assert market_data.close == 102.0
        assert market_data.volume == 1000000
        assert market_data.source == "yahoo_finance"

    def test_market_data_model_config(self) -> None:
        """Test MarketData model configuration."""
        # Should allow arbitrary types
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        # Should not raise validation errors for datetime
        assert isinstance(market_data.timestamp, datetime)

    def test_market_data_validation(self) -> None:
        """Test MarketData field validation."""
        # All fields are required
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MarketData(  # type: ignore[call-arg]
                symbol="AAPL",
                # Missing required fields
            )

    def test_market_data_types(self) -> None:
        """Test MarketData field types."""
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.5,
            high=105.75,
            low=99.25,
            close=102.0,
            volume=1500000,
            source="test"
        )
        
        assert isinstance(market_data.symbol, str)
        assert isinstance(market_data.timestamp, datetime)
        assert isinstance(market_data.open, float)
        assert isinstance(market_data.high, float)
        assert isinstance(market_data.low, float)
        assert isinstance(market_data.close, float)
        assert isinstance(market_data.volume, int)
        assert isinstance(market_data.source, str)

    def test_market_data_edge_cases(self) -> None:
        """Test MarketData with edge case values."""
        # Zero volume
        market_data = MarketData(
            symbol="TEST",
            timestamp=datetime(2023, 1, 1),
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            volume=0,
            source="test"
        )
        assert market_data.volume == 0

        # Very small prices
        market_data = MarketData(
            symbol="PENNY",
            timestamp=datetime(2023, 1, 1),
            open=0.0001,
            high=0.0002,
            low=0.0001,
            close=0.0001,
            volume=1000000,
            source="test"
        )
        assert market_data.open == 0.0001

    def test_market_data_string_conversion(self) -> None:
        """Test MarketData string representation."""
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        str_repr = str(market_data)
        assert "AAPL" in str_repr
        assert "100.0" in str_repr

    def test_market_data_dict_conversion(self) -> None:
        """Test MarketData to dict conversion."""
        market_data = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        data_dict = market_data.model_dump()
        
        assert data_dict['symbol'] == "AAPL"
        assert data_dict['open'] == 100.0
        assert data_dict['volume'] == 1000000
        assert isinstance(data_dict['timestamp'], datetime)

    def test_market_data_equality(self) -> None:
        """Test MarketData equality comparison."""
        market_data1 = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        market_data2 = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        assert market_data1 == market_data2

    def test_market_data_inequality(self) -> None:
        """Test MarketData inequality comparison."""
        market_data1 = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        market_data2 = MarketData(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=101.0,  # Different price
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        assert market_data1 != market_data2


class TestDataSourceBase:
    """Unit tests for DataSourceBase abstract class."""

    def test_data_source_base_is_abstract(self) -> None:
        """Test DataSourceBase is abstract."""
        assert issubclass(DataSourceBase, ABC)
        
        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            DataSourceBase()  # type: ignore[abstract]

    def test_data_source_base_abstract_methods(self) -> None:
        """Test DataSourceBase has required abstract methods."""
        # Check that abstract methods are defined
        abstract_methods = DataSourceBase.__abstractmethods__
        expected_methods = {'get_daily_prices', 'get_intraday_prices', 'search_symbols'}
        
        assert abstract_methods == expected_methods

    def test_data_source_base_method_signatures(self) -> None:
        """Test DataSourceBase method signatures."""
        # Check get_daily_prices signature
        import inspect
        daily_sig = inspect.signature(DataSourceBase.get_daily_prices)
        daily_params = list(daily_sig.parameters.keys())
        assert 'self' in daily_params
        assert 'symbol' in daily_params
        assert 'start_date' in daily_params
        assert 'end_date' in daily_params
        
        # Check get_intraday_prices signature
        intraday_sig = inspect.signature(DataSourceBase.get_intraday_prices)
        intraday_params = list(intraday_sig.parameters.keys())
        assert 'self' in intraday_params
        assert 'symbol' in intraday_params
        assert 'interval' in intraday_params
        assert 'limit' in intraday_params
        
        # Check search_symbols signature
        search_sig = inspect.signature(DataSourceBase.search_symbols)
        search_params = list(search_sig.parameters.keys())
        assert 'self' in search_params
        assert 'query' in search_params

    def test_concrete_implementation_required(self) -> None:
        """Test that concrete implementations must implement all abstract methods."""
        
        # Class missing one abstract method should fail
        class IncompleteAdapter(DataSourceBase):
            async def get_daily_prices(self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[MarketData]:
                return []
            
            async def get_intraday_prices(self, symbol: str, interval: int = 5, limit: Optional[int] = None) -> List[MarketData]:
                return []
            
            # Missing search_symbols method
        
        with pytest.raises(TypeError):
            IncompleteAdapter()  # type: ignore[abstract]

    def test_complete_implementation_works(self) -> None:
        """Test that complete implementations can be instantiated."""
        
        class CompleteAdapter(DataSourceBase):
            async def get_daily_prices(self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[MarketData]:
                return []
            
            async def get_intraday_prices(self, symbol: str, interval: int = 5, limit: Optional[int] = None) -> List[MarketData]:
                return []
            
            async def search_symbols(self, query: str) -> List[Dict[str, str]]:
                return []
        
        # Should be able to instantiate
        adapter = CompleteAdapter()
        assert isinstance(adapter, DataSourceBase)

    @pytest.mark.asyncio
    async def test_complete_implementation_methods(self) -> None:
        """Test that complete implementations can call methods."""
        
        class TestAdapter(DataSourceBase):
            async def get_daily_prices(self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[MarketData]:
                return [MarketData(
                    symbol=symbol,
                    timestamp=datetime(2023, 1, 1),
                    open=100.0,
                    high=105.0,
                    low=99.0,
                    close=102.0,
                    volume=1000000,
                    source="test"
                )]
            
            async def get_intraday_prices(self, symbol: str, interval: int = 5, limit: Optional[int] = None) -> List[MarketData]:
                return []
            
            async def search_symbols(self, query: str) -> List[Dict[str, str]]:
                return [{'symbol': 'AAPL', 'name': 'Apple Inc.'}]
        
        adapter = TestAdapter()
        
        # Test daily prices
        daily_data = await adapter.get_daily_prices("AAPL")
        assert len(daily_data) == 1
        assert daily_data[0].symbol == "AAPL"
        
        # Test intraday prices
        intraday_data = await adapter.get_intraday_prices("AAPL")
        assert len(intraday_data) == 0
        
        # Test search
        search_results = await adapter.search_symbols("AAPL")
        assert len(search_results) == 1
        assert search_results[0]['symbol'] == "AAPL"