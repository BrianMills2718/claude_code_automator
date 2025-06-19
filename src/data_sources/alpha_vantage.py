from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
import asyncio
from dataclasses import dataclass
from alpha_vantage.timeseries import TimeSeries  # type: ignore[import-untyped]

from ..config import settings
from .base import DataSourceBase, MarketData
from .exceptions import APIError, RateLimitError

# Constants
SOURCE_NAME = 'alpha_vantage'

@dataclass
class TimeSeriesConfig:
    """Configuration for time series data processing."""
    symbol: str
    timestamp_format: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: Optional[int] = None

class AlphaVantageAdapter(DataSourceBase):
    """Alpha Vantage API adapter with rate limiting."""
    
    def __init__(self) -> None:
        api_key = settings.ALPHA_VANTAGE_API_KEY
        if api_key is None:
            raise ValueError("ALPHA_VANTAGE_API_KEY is required")
        self._client = TimeSeries(key=api_key.get_secret_value())
        self._request_times: List[datetime] = []
        self._lock = asyncio.Lock()
        self._price_field_map = {
            'open': '1. open',
            'high': '2. high', 
            'low': '3. low',
            'close': '4. close',
            'volume': '5. volume'
        }
    
    def _handle_api_error(self, e: Exception) -> None:
        """Handle Alpha Vantage API errors."""
        raise APIError(f"Alpha Vantage API error: {str(e)}")
    
    def _extract_price_fields(self, values: Dict[str, str]) -> Dict[str, Any]:
        """Extract numeric price fields from Alpha Vantage response."""
        result = {}
        for field_name, av_key in self._price_field_map.items():
            result[field_name] = self._parse_field_value(values[av_key], field_name == 'volume')
        return result

    def _parse_field_value(self, value: str, is_volume: bool) -> Any:
        """Parse a single field value from Alpha Vantage response."""
        return int(value) if is_volume else float(value)
    
    def _create_market_data_from_values(self, symbol: str, timestamp: datetime, values: Dict[str, str]) -> MarketData:
        """Create MarketData from Alpha Vantage values dictionary."""
        price_data = self._extract_price_fields(values)
        return MarketData(
            symbol=symbol,
            timestamp=timestamp,
            source=SOURCE_NAME,
            **price_data
        )

    def _cleanup_old_requests(self, current_time: datetime) -> None:
        """Remove request timestamps older than 1 minute."""
        self._request_times = [t for t in self._request_times 
                             if self._is_request_within_window(current_time, t)]

    def _is_request_within_window(self, current_time: datetime, request_time: datetime) -> bool:
        """Check if request is within the time window."""
        return current_time - request_time < timedelta(minutes=settings.ALPHA_VANTAGE_RATE_LIMIT_WINDOW_MINUTES)

    def _is_within_rate_limit(self, current_time: datetime) -> bool:
        """Check if current request would exceed rate limit."""
        self._cleanup_old_requests(current_time)
        return len(self._request_times) < settings.ALPHA_VANTAGE_RATE_LIMIT

    async def _manage_rate_limit(self) -> None:
        """Enforce rate limiting with request tracking."""
        async with self._lock:
            now = datetime.now()
            if not self._is_within_rate_limit(now):
                raise RateLimitError("Alpha Vantage rate limit exceeded")
            self._request_times.append(now)
    
    async def _execute_api_operation(self, operation: Callable[[], Any]) -> Any:
        """Execute operation with rate limiting and error handling."""
        await self._manage_rate_limit()
        try:
            return operation()
        except Exception as e:
            self._handle_api_error(e)
    
    def _is_date_in_range(self, timestamp: datetime, start_date: Optional[date], end_date: Optional[date]) -> bool:
        """Check if timestamp is within the specified date range."""
        date_obj = timestamp.date()
        if start_date and date_obj < start_date:
            return False
        if end_date and date_obj > end_date:
            return False
        return True
    
    def _process_time_series_data(self, data: Dict[str, Dict[str, str]], config: TimeSeriesConfig) -> List[MarketData]:
        """Process time series data into MarketData objects."""
        market_data = []
        for timestamp_str, values in data.items():
            timestamp = datetime.strptime(timestamp_str, config.timestamp_format)
            
            if not self._is_date_in_range(timestamp, config.start_date, config.end_date):
                continue
                
            market_data.append(self._create_market_data_from_values(config.symbol, timestamp, values))
            
            if config.limit is not None and len(market_data) >= config.limit:
                break
                
        return market_data
            
    def _create_api_operation(self, operation_func: Callable[[], Any]) -> Callable[[], Any]:
        """Create a standardized API operation function."""
        def _operation() -> Any:
            result = operation_func()
            return result[0] if isinstance(result, tuple) else result
        return _operation

    async def _fetch_time_series(
        self,
        symbol: str,
        fetch_function: Callable[[], Tuple[Dict[str, Dict[str, str]], Any]],
        timestamp_format: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[MarketData]:
        """Common time series fetching logic."""
        def _fetch_data() -> List[MarketData]:
            data, _ = fetch_function()
            config = TimeSeriesConfig(
                symbol=symbol,
                timestamp_format=timestamp_format,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            return self._process_time_series_data(data, config)
        
        result = await self._execute_api_operation(_fetch_data)
        return result  # type: ignore[no-any-return]

    def _get_outputsize_for_limit(self, limit: Optional[int]) -> str:
        """Determine Alpha Vantage outputsize parameter based on limit."""
        return 'compact' if limit and limit <= settings.ALPHA_VANTAGE_COMPACT_LIMIT_THRESHOLD else settings.ALPHA_VANTAGE_DEFAULT_OUTPUTSIZE

    async def get_daily_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[MarketData]:
        return await self._fetch_time_series(
            symbol=symbol,
            fetch_function=lambda: self._client.get_daily(symbol=symbol, outputsize=settings.ALPHA_VANTAGE_DEFAULT_OUTPUTSIZE),
            timestamp_format=settings.ALPHA_VANTAGE_DAILY_TIMESTAMP_FORMAT,
            start_date=start_date,
            end_date=end_date
        )
            
    async def get_intraday_prices(
        self,
        symbol: str,
        interval: int = 5,
        limit: Optional[int] = None
    ) -> List[MarketData]:
        interval_str = f"{interval}min"
        outputsize = self._get_outputsize_for_limit(limit)
        return await self._fetch_time_series(
            symbol=symbol,
            fetch_function=lambda: self._client.get_intraday(symbol=symbol, interval=interval_str, outputsize=outputsize),
            timestamp_format=settings.ALPHA_VANTAGE_INTRADAY_TIMESTAMP_FORMAT,
            limit=limit
        )

    def _format_symbol_match(self, match: Dict[str, str]) -> Dict[str, str]:
        """Format a single symbol search match."""
        return {
            'symbol': match['1. symbol'],
            'name': match['2. name'],
            'type': match['3. type'],
            'region': match['4. region']
        }
            
    async def search_symbols(self, query: str) -> List[Dict[str, str]]:
        operation = self._create_api_operation(
            lambda: self._client.get_symbol_search(keywords=query)
        )
        
        async def _search_operation() -> List[Dict[str, str]]:
            matches = await self._execute_api_operation(operation)
            return [self._format_symbol_match(match) for match in matches]
            
        return await _search_operation()