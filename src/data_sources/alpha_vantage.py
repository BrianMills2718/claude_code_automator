from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
import asyncio
from dataclasses import dataclass
from alpha_vantage.timeseries import TimeSeries

from .. import settings
from .base import DataSourceBase, MarketData
from .exceptions import APIError, RateLimitError

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
    
    def __init__(self):
        self._client = TimeSeries(key=settings.ALPHA_VANTAGE_API_KEY.get_secret_value())
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
    
    def _extract_price_fields(self, values: Dict) -> Dict[str, Any]:
        """Extract numeric price fields from Alpha Vantage response."""
        result = {}
        for field_name, av_key in self._price_field_map.items():
            result[field_name] = self._parse_field_value(values[av_key], field_name == 'volume')
        return result

    def _parse_field_value(self, value: str, is_volume: bool) -> Any:
        """Parse a single field value from Alpha Vantage response."""
        return int(value) if is_volume else float(value)
    
    def _create_market_data_from_values(self, symbol: str, timestamp: datetime, values: Dict) -> MarketData:
        """Create MarketData from Alpha Vantage values dictionary."""
        price_data = self._extract_price_fields(values)
        return MarketData(
            symbol=symbol,
            timestamp=timestamp,
            source='alpha_vantage',
            **price_data
        )

    def _cleanup_old_requests(self, current_time: datetime) -> None:
        """Remove request timestamps older than 1 minute."""
        self._request_times = [t for t in self._request_times 
                             if self._is_request_within_window(current_time, t)]

    def _is_request_within_window(self, current_time: datetime, request_time: datetime) -> bool:
        """Check if request is within the time window."""
        return current_time - request_time < timedelta(minutes=1)

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
    
    def _apply_date_filter(self, timestamp: datetime, config: TimeSeriesConfig) -> bool:
        """Check if timestamp passes date filter criteria."""
        date_obj = timestamp.date()
        return self._is_date_in_range(date_obj, config.start_date, config.end_date)

    def _is_date_in_range(self, date_obj: date, start_date: Optional[date], end_date: Optional[date]) -> bool:
        """Check if date is within the specified range."""
        if start_date and date_obj < start_date:
            return False
        if end_date and date_obj > end_date:
            return False
        return True
    
    def _process_time_series_data(self, data: Dict, config: TimeSeriesConfig) -> List[MarketData]:
        """Process time series data into MarketData objects."""
        market_data = []
        for timestamp_str, values in data.items():
            timestamp = datetime.strptime(timestamp_str, config.timestamp_format)
            
            if not self._apply_date_filter(timestamp, config):
                continue
                
            market_data.append(self._create_market_data_from_values(config.symbol, timestamp, values))
            
            if config.limit is not None and len(market_data) >= config.limit:
                break
                
        return market_data
            
    async def _fetch_time_series(
        self,
        symbol: str,
        fetch_function: Callable[[], tuple],
        timestamp_format: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[MarketData]:
        """Common time series fetching logic."""
        def _fetch_data():
            data, _ = fetch_function()
            config = TimeSeriesConfig(
                symbol=symbol,
                timestamp_format=timestamp_format,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            return self._process_time_series_data(data, config)
        
        return await self._execute_api_operation(_fetch_data)

    def _get_outputsize_for_limit(self, limit: Optional[int]) -> str:
        """Determine Alpha Vantage outputsize parameter based on limit."""
        return 'compact' if limit and limit <= 100 else 'full'

    async def get_daily_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[MarketData]:
        return await self._fetch_time_series(
            symbol=symbol,
            fetch_function=lambda: self._client.get_daily(symbol=symbol, outputsize='full'),
            timestamp_format='%Y-%m-%d',
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
            timestamp_format='%Y-%m-%d %H:%M:%S',
            limit=limit
        )

    def _format_symbol_match(self, match: Dict) -> Dict[str, str]:
        """Format a single symbol search match."""
        return {
            'symbol': match['1. symbol'],
            'name': match['2. name'],
            'type': match['3. type'],
            'region': match['4. region']
        }
            
    async def search_symbols(self, query: str) -> List[Dict[str, str]]:
        def _search_symbols():
            matches, _ = self._client.get_symbol_search(keywords=query)
            return [self._format_symbol_match(match) for match in matches]
        
        return await self._execute_api_operation(_search_symbols)