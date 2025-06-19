import pytest
from datetime import datetime
from pydantic import ValidationError

from src.processing.validation import (
    StockPrice,
    TimeSeriesRequest,
    SearchRequest,
    DataSourceResponse
)


class TestStockPrice:
    """Unit tests for StockPrice validation model."""

    def test_valid_stock_price(self) -> None:
        """Test valid stock price creation."""
        stock_price = StockPrice(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1, 9, 30),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="yahoo_finance"
        )
        
        assert stock_price.symbol == "AAPL"
        assert stock_price.timestamp == datetime(2023, 1, 1, 9, 30)
        assert stock_price.open == 100.0
        assert stock_price.high == 105.0
        assert stock_price.low == 99.0
        assert stock_price.close == 102.0
        assert stock_price.volume == 1000000
        assert stock_price.source == "yahoo_finance"

    def test_stock_price_high_validation(self) -> None:
        """Test high price validation."""
        # High less than low should fail
        with pytest.raises(ValidationError) as exc_info:
            StockPrice(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=98.0,  # High less than low
                low=99.0,
                close=100.0,
                volume=1000000,
                source="test"
            )
        assert "high must be greater than low" in str(exc_info.value)

    def test_stock_price_open_close_validation(self) -> None:
        """Test open and close price validation."""
        # Open price outside high-low range
        with pytest.raises(ValidationError) as exc_info:
            StockPrice(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                open=110.0,  # Above high
                high=105.0,
                low=99.0,
                close=102.0,
                volume=1000000,
                source="test"
            )
        assert "price must be within high-low range" in str(exc_info.value)

        # Close price outside high-low range
        with pytest.raises(ValidationError) as exc_info:
            StockPrice(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=105.0,
                low=99.0,
                close=97.0,  # Below low
                volume=1000000,
                source="test"
            )
        assert "price must be within high-low range" in str(exc_info.value)

    def test_stock_price_positive_validation(self) -> None:
        """Test positive price validation."""
        # Zero price should fail
        with pytest.raises(ValidationError):
            StockPrice(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                open=0.0,  # Zero not allowed
                high=105.0,
                low=99.0,
                close=102.0,
                volume=1000000,
                source="test"
            )

        # Negative price should fail
        with pytest.raises(ValidationError):
            StockPrice(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=-105.0,  # Negative not allowed
                low=99.0,
                close=102.0,
                volume=1000000,
                source="test"
            )

    def test_stock_price_volume_validation(self) -> None:
        """Test volume validation."""
        # Zero volume should be allowed
        stock_price = StockPrice(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=0,
            source="test"
        )
        assert stock_price.volume == 0

        # Negative volume should fail
        with pytest.raises(ValidationError):
            StockPrice(
                symbol="AAPL",
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=105.0,
                low=99.0,
                close=102.0,
                volume=-1000,  # Negative not allowed
                source="test"
            )

    def test_stock_price_symbol_validation(self) -> None:
        """Test symbol validation."""
        # Empty symbol should fail
        with pytest.raises(ValidationError):
            StockPrice(
                symbol="",  # Empty not allowed
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=105.0,
                low=99.0,
                close=102.0,
                volume=1000000,
                source="test"
            )

        # Long symbol should fail
        with pytest.raises(ValidationError):
            StockPrice(
                symbol="VERYLONGSYMBOL",  # Too long
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=105.0,
                low=99.0,
                close=102.0,
                volume=1000000,
                source="test"
            )


class TestTimeSeriesRequest:
    """Unit tests for TimeSeriesRequest validation model."""

    def test_valid_time_series_request(self) -> None:
        """Test valid time series request creation."""
        request = TimeSeriesRequest(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31),
            interval=5,
            limit=100
        )
        
        assert request.symbol == "AAPL"
        assert request.start_date == datetime(2023, 1, 1)
        assert request.end_date == datetime(2023, 1, 31)
        assert request.interval == 5
        assert request.limit == 100

    def test_time_series_request_minimal(self) -> None:
        """Test minimal time series request."""
        request = TimeSeriesRequest(symbol="AAPL", start_date=None, end_date=None, interval=None, limit=None)
        
        assert request.symbol == "AAPL"
        assert request.start_date is None
        assert request.end_date is None
        assert request.interval is None
        assert request.limit is None

    def test_time_series_request_date_validation(self) -> None:
        """Test date validation."""
        # End date before start date should fail
        with pytest.raises(ValidationError) as exc_info:
            TimeSeriesRequest(
                symbol="AAPL",
                start_date=datetime(2023, 1, 31),
                end_date=datetime(2023, 1, 1),  # Before start date
                interval=None,
                limit=None
            )
        assert "end_date must be after start_date" in str(exc_info.value)

    def test_time_series_request_interval_validation(self) -> None:
        """Test interval validation."""
        # Zero interval should fail
        with pytest.raises(ValidationError):
            TimeSeriesRequest(symbol="AAPL", start_date=None, end_date=None, interval=0, limit=None)

        # Large interval should fail
        with pytest.raises(ValidationError):
            TimeSeriesRequest(symbol="AAPL", start_date=None, end_date=None, interval=61, limit=None)

    def test_time_series_request_limit_validation(self) -> None:
        """Test limit validation."""
        # Zero limit should fail
        with pytest.raises(ValidationError):
            TimeSeriesRequest(symbol="AAPL", start_date=None, end_date=None, interval=None, limit=0)

        # Negative limit should fail
        with pytest.raises(ValidationError):
            TimeSeriesRequest(symbol="AAPL", start_date=None, end_date=None, interval=None, limit=-1)


class TestSearchRequest:
    """Unit tests for SearchRequest validation model."""

    def test_valid_search_request(self) -> None:
        """Test valid search request creation."""
        request = SearchRequest(query="AAPL", limit=10)
        
        assert request.query == "AAPL"
        assert request.limit == 10

    def test_search_request_minimal(self) -> None:
        """Test minimal search request."""
        request = SearchRequest(query="AAPL", limit=None)
        
        assert request.query == "AAPL"
        assert request.limit is None

    def test_search_request_query_validation(self) -> None:
        """Test query validation."""
        # Empty query should fail
        with pytest.raises(ValidationError):
            SearchRequest(query="", limit=None)

    def test_search_request_limit_validation(self) -> None:
        """Test limit validation."""
        # Zero limit should fail
        with pytest.raises(ValidationError):
            SearchRequest(query="AAPL", limit=0)

        # Negative limit should fail
        with pytest.raises(ValidationError):
            SearchRequest(query="AAPL", limit=-1)


class TestDataSourceResponse:
    """Unit tests for DataSourceResponse validation model."""

    def test_valid_data_source_response_success(self) -> None:
        """Test valid successful response."""
        stock_price = StockPrice(
            symbol="AAPL",
            timestamp=datetime(2023, 1, 1),
            open=100.0,
            high=105.0,
            low=99.0,
            close=102.0,
            volume=1000000,
            source="test"
        )
        
        response = DataSourceResponse(
            success=True,
            data=[stock_price]
        )
        
        assert response.success is True
        assert response.data is not None
        assert len(response.data) == 1
        assert response.error is None

    def test_valid_data_source_response_error(self) -> None:
        """Test valid error response."""
        response = DataSourceResponse(
            success=False,
            error="API Error"
        )
        
        assert response.success is False
        assert response.data is None
        assert response.error == "API Error"

    def test_data_source_response_minimal(self) -> None:
        """Test minimal response."""
        response = DataSourceResponse(success=True)
        
        assert response.success is True
        assert response.data is None
        assert response.error is None

    def test_data_source_response_edge_cases(self) -> None:
        """Test edge cases."""
        # Empty data list
        response = DataSourceResponse(success=True, data=[])
        assert response.success is True
        assert response.data == []
        
        # Both success and error
        response = DataSourceResponse(success=False, data=[], error="Error message")
        assert response.success is False
        assert response.data == []
        assert response.error == "Error message"