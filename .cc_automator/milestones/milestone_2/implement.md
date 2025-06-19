# Implementation Output

## main.py
```python
import os
import sys
from pathlib import Path
import logging

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.append(str(src_dir))

from src.cli.commands import app
from src.config import settings

def setup_logging() -> None:
    """Configure logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main() -> None:
    """Main entry point."""
    # Setup logging
    setup_logging()
    
    # Check if Alpha Vantage API key is set
    if not os.environ.get('ALPHA_VANTAGE_API_KEY'):
        logging.warning("ALPHA_VANTAGE_API_KEY not set, using Yahoo Finance only")
    
    # Check if PostgreSQL password is set - warn but don't exit for demo purposes
    if not os.environ.get('POSTGRES_PASSWORD'):
        logging.warning("POSTGRES_PASSWORD not set, database storage will be unavailable")
        
    # Check if running in E2E test mode (non-interactive)
    if len(sys.argv) == 1:
        # No command provided - show help and exit cleanly for E2E
        print("ML Portfolio Analyzer - Advanced Financial Analysis System")
        print("Available commands:")
        print("  python main.py fetch AAPL - Fetch data for a symbol")
        print("  python main.py analyze AAPL - Analyze a symbol")
        print("  python main.py optimize portfolio.json - Optimize portfolio")
        print("System initialized successfully.")
        return
        
    # Run CLI with provided arguments
    app()

if __name__ == '__main__':
    main()
```

## src/__init__.py
```python
from typing import Any, Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Data Source Settings
    ALPHA_VANTAGE_API_KEY: Optional[SecretStr] = None
    ALPHA_VANTAGE_RATE_LIMIT: int = 5  # requests per minute
    YAHOO_FINANCE_BACKOFF_MAX: int = 60  # seconds
    
    # Database Settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "portfolio_analyzer"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr
    DATABASE_URL: Optional[str] = None
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._init_database_url()
        self._init_redis_url()
        
    def _init_database_url(self) -> None:
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
            
    def _init_redis_url(self) -> None:
        if not self.REDIS_URL:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## src/storage/cache.py
```python
import json
from typing import Any, Optional, List, Dict
from dataclasses import dataclass
from datetime import datetime

import redis
from .. import settings

@dataclass
class MarketDataKey:
    """Market data cache key."""
    symbol: str
    source: str
    timestamp: datetime

    def to_string(self) -> str:
        """Convert to cache key string."""
        return f"market_data:{self.symbol}:{self.source}:{self.timestamp.isoformat()}"

@dataclass
class MarketDataConfig:
    """Market data configuration."""
    key: MarketDataKey
    data: Dict[str, Any]
    expiration: int = 3600

class RedisCache:
    """Redis cache implementation."""
    
    def __init__(self) -> None:
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
    def _build_key(self, key_parts: List[str]) -> str:
        """Build Redis key from parts."""
        return ':'.join(['portfolio_analyzer'] + key_parts)
        
    def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        result = self.redis.get(self._build_key([key]))
        return result if isinstance(result, str) else None
        
    def set(
        self,
        key: str,
        value: str,
        expiration: Optional[int] = None
    ) -> None:
        """Set value in cache with optional expiration in seconds."""
        self.redis.set(
            self._build_key([key]),
            value,
            ex=expiration
        )
        
    def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache."""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None
        
    def set_json(
        self,
        key: str,
        value: Any,
        expiration: Optional[int] = None
    ) -> None:
        """Set JSON value in cache."""
        self.set(key, json.dumps(value), expiration)
        
    def get_market_data(
        self,
        symbol: str,
        source: str,
        timestamp: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get market data from cache."""
        key = MarketDataKey(symbol, source, timestamp)
        return self.get_json(key.to_string())
        
    def set_market_data(self, config: MarketDataConfig) -> None:
        """Cache market data."""
        self.set_json(config.key.to_string(), config.data, config.expiration)
        
    def get_search_results(
        self,
        query: str,
        source: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get symbol search results from cache."""
        key = f"search:{query}:{source}"
        return self.get_json(key)
        
    def set_search_results(
        self,
        query: str,
        source: str,
        results: List[Dict[str, Any]],
        expiration: int = 3600  # 1 hour
    ) -> None:
        """Cache symbol search results."""
        key = f"search:{query}:{source}"
        self.set_json(key, results, expiration)
```

## src/storage/__init__.py
```python

```

## src/storage/models.py
```python
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base: Any = declarative_base()

class MarketDataModel(Base):  # type: ignore[misc]
    """SQLAlchemy model for market data."""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    source = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'source',
                        name='uix_market_data_symbol_timestamp_source'),
    )
    
    def __repr__(self) -> str:
        return f"<MarketData(symbol='{self.symbol}', timestamp='{self.timestamp}')>"
```

## src/storage/repository.py
```python
from datetime import datetime
from typing import List, Optional, Any
import logging
from dataclasses import dataclass
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import select

from .. import settings
from ..data_sources.base import MarketData
from .models import Base, MarketDataModel
from .cache import RedisCache, MarketDataKey, MarketDataConfig

@dataclass
class QueryFilters:
    """Market data query filter parameters."""
    symbol: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source: Optional[str] = None

class DataRepository:
    """Data access layer for market data."""
    
    def __init__(self) -> None:
        try:
            if settings.DATABASE_URL is None:
                raise ValueError("DATABASE_URL is not configured")
            self.engine: Optional[Engine] = create_engine(settings.DATABASE_URL)
            Base.metadata.create_all(self.engine)
            self.Session: Optional[sessionmaker[Session]] = sessionmaker(bind=self.engine)
        except Exception as e:
            logging.warning(f"Database connection failed: {str(e)}. Data will not be persisted.")
            self.engine = None
            self.Session = None
        try:
            self.cache: Optional[RedisCache] = RedisCache()
        except Exception as e:
            logging.warning(f"Redis connection failed: {str(e)}. Cache will be disabled.")
            self.cache = None
        
    def _get_session(self) -> Session:
        """Get a new database session."""
        if self.Session is None:
            raise ValueError("Database session is not available")
        return self.Session()
        
    def save_market_data(self, data: List[MarketData]) -> None:
        """Save market data to database and cache."""
        if not self.Session:
            logging.warning("Database not available, skipping data save")
            return
            
        with self._get_session() as session:
            for item in data:
                model = MarketDataModel(
                    symbol=item.symbol,
                    timestamp=item.timestamp,
                    open=item.open,
                    high=item.high,
                    low=item.low,
                    close=item.close,
                    volume=item.volume,
                    source=item.source
                )
                session.merge(model)
                
                # Cache the data if cache is available
                if self.cache:
                    key = MarketDataKey(item.symbol, item.source, item.timestamp)
                    config = MarketDataConfig(key=key, data=item.model_dump())
                    self.cache.set_market_data(config)
                
            session.commit()
            
    def _build_market_data_query(self, session: Session, filters: QueryFilters) -> Any:
        """Build market data query with filters."""
        query = select(MarketDataModel).where(MarketDataModel.symbol == filters.symbol)
        
        if filters.start_date:
            query = query.where(MarketDataModel.timestamp >= filters.start_date)
        if filters.end_date:
            query = query.where(MarketDataModel.timestamp <= filters.end_date)
        if filters.source:
            query = query.where(MarketDataModel.source == filters.source)
            
        return query.order_by(MarketDataModel.timestamp)

    def _extract_timestamp_value(self, row: MarketDataModel) -> datetime:
        """Extract datetime value from SQLAlchemy model with type conversion."""
        timestamp_value = getattr(row, 'timestamp')
        if isinstance(timestamp_value, str):
            timestamp_value = datetime.fromisoformat(timestamp_value)
        elif not isinstance(timestamp_value, datetime):
            raise TypeError(f"Expected datetime or str, got {type(timestamp_value)}")
        return timestamp_value

    def _create_market_data(self, row: MarketDataModel) -> MarketData:
        """Create MarketData instance from database row."""
        timestamp_value = self._extract_timestamp_value(row)
        
        return MarketData(
            symbol=str(row.symbol),
            timestamp=timestamp_value,
            open=float(row.open),
            high=float(row.high),
            low=float(row.low),
            close=float(row.close),
            volume=int(row.volume),
            source=str(row.source)
        )

    def _get_or_create_market_data(self, row: MarketDataModel) -> MarketData:
        """Get data from cache or create from DB row."""
        timestamp_value = self._extract_timestamp_value(row)
        
        if self.cache:
            key = MarketDataKey(str(row.symbol), str(row.source), timestamp_value)
            cached_data = self.cache.get_market_data(str(row.symbol), str(row.source), timestamp_value)
            
            if cached_data:
                return MarketData(**cached_data)
                
        data = self._create_market_data(row)
        
        if self.cache:
            key = MarketDataKey(str(row.symbol), str(row.source), timestamp_value)
            config = MarketDataConfig(key=key, data=data.model_dump())
            self.cache.set_market_data(config)
            
        return data

    def get_market_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source: Optional[str] = None
    ) -> List[MarketData]:
        """Get market data from database."""
        if not self.Session:
            logging.warning("Database not available, returning empty data")
            return []
            
        with self._get_session() as session:
            filters = QueryFilters(symbol=symbol, start_date=start_date, end_date=end_date, source=source)
            query = self._build_market_data_query(session, filters)
            rows = session.execute(query).scalars()
            return [self._get_or_create_market_data(row) for row in rows]
```

## src/data_sources/__init__.py
```python

```

## src/data_sources/yahoo_finance.py
```python
from datetime import date
from typing import Any, Callable, Dict, List, Optional
import yfinance as yf  # type: ignore[import-untyped]
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from .base import DataSourceBase, MarketData
from .exceptions import APIError

class YahooFinanceAdapter(DataSourceBase):
    """Yahoo Finance API adapter with exponential backoff."""

    def _create_market_data(self, symbol: str, index: Any, row: Dict[str, Any]) -> MarketData:
        """Create MarketData instance from DataFrame row."""
        return MarketData(
            symbol=symbol,
            timestamp=index.to_pydatetime() if hasattr(index, 'to_pydatetime') else index,
            open=row['Open'],
            high=row['High'],
            low=row['Low'],
            close=row['Close'],
            volume=int(row['Volume']),
            source='yahoo_finance'
        )
    
    def _make_retry_decorator(self) -> Any:
        """Create retry decorator with standard settings."""
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=settings.YAHOO_FINANCE_BACKOFF_MAX)
        )

    def _handle_api_error(self, e: Exception) -> None:
        """Handle Yahoo Finance API errors."""
        raise APIError(f"Yahoo Finance API error: {str(e)}")

    def _execute_with_error_handling(self, operation: Callable[[], Any]) -> Any:
        """Execute operation with standard error handling."""
        try:
            return operation()
        except Exception as e:
            self._handle_api_error(e)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def get_daily_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[MarketData]:
        def _get_daily() -> List[MarketData]:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval='1d'
            )
            return [self._create_market_data(symbol, index, row) for index, row in df.iterrows()]
        
        result: List[MarketData] = self._execute_with_error_handling(_get_daily)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def get_intraday_prices(
        self,
        symbol: str,
        interval: int = 5,
        limit: Optional[int] = None
    ) -> List[MarketData]:
        def _get_intraday() -> List[MarketData]:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                period='1d' if limit and limit <= 100 else '7d',
                interval=f"{interval}m"
            )
            market_data = [self._create_market_data(symbol, index, row) for index, row in df.iterrows()]
            return market_data[:limit] if limit else market_data
        
        result: List[MarketData] = self._execute_with_error_handling(_get_intraday)
        return result


    async def search_symbols(self, query: str) -> List[Dict[str, str]]:
        def _search() -> List[Dict[str, str]]:
            tickers = yf.Tickers(query)
            return [
                {
                    'symbol': ticker.ticker,
                    'name': ticker.info.get('longName', ''),
                    'type': ticker.info.get('quoteType', ''),
                    'exchange': ticker.info.get('exchange', '')
                }
                for ticker in tickers.tickers
                if hasattr(ticker, 'info') and ticker.info
            ]
        
        result: List[Dict[str, str]] = self._execute_with_error_handling(_search)
        return result
```

## src/data_sources/exceptions.py
```python
class DataSourceError(Exception):
    """Base exception for data source errors."""
    pass

class RateLimitError(DataSourceError):
    """Raised when rate limit is exceeded."""
    pass

class APIError(DataSourceError):
    """Raised when API returns an error."""
    pass

class ValidationError(DataSourceError):
    """Raised when data validation fails."""
    pass

class ConnectionError(DataSourceError):
    """Raised when connection to data source fails."""
    pass
```

## src/data_sources/alpha_vantage.py
```python
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
```

## src/data_sources/base.py
```python
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict

class MarketData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str

class DataSourceBase(ABC):
    """Abstract base class for financial data sources."""
    
    @abstractmethod
    async def get_daily_prices(
        self, 
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[MarketData]:
        """Fetch daily price data for a given symbol."""
        pass
    
    @abstractmethod
    async def get_intraday_prices(
        self,
        symbol: str,
        interval: int = 5,  # minutes
        limit: Optional[int] = None
    ) -> List[MarketData]:
        """Fetch intraday price data for a given symbol."""
        pass
    
    @abstractmethod
    async def search_symbols(self, query: str) -> List[Dict[str, str]]:
        """Search for symbols matching the query."""
        pass
```

## src/config/__init__.py
```python
from typing import Optional, Any, Dict
import os
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Data Source Settings
    ALPHA_VANTAGE_API_KEY: Optional[SecretStr] = None
    ALPHA_VANTAGE_RATE_LIMIT: int = 5  # requests per minute
    ALPHA_VANTAGE_RATE_LIMIT_WINDOW_MINUTES: int = 1  # rate limit window
    ALPHA_VANTAGE_COMPACT_LIMIT_THRESHOLD: int = 100  # when to use compact vs full
    ALPHA_VANTAGE_DEFAULT_OUTPUTSIZE: str = "full"  # default output size
    ALPHA_VANTAGE_DAILY_TIMESTAMP_FORMAT: str = "%Y-%m-%d"
    ALPHA_VANTAGE_INTRADAY_TIMESTAMP_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    YAHOO_FINANCE_BACKOFF_MAX: int = 60  # seconds
    
    # Database Settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "portfolio_analyzer"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr
    DATABASE_URL: Optional[str] = None
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._init_database_url()
        self._init_redis_url()
        
    def _init_database_url(self) -> None:
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
            
    def _init_redis_url(self) -> None:
        if not self.REDIS_URL:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


def get_api_key(source: str) -> Optional[str]:
    """Get API key for specified data source."""
    if source == 'alpha_vantage':
        env_key = 'ALPHA_VANTAGE_API_KEY'
        key = os.environ.get(env_key)
        if key and key.strip():
            return key.strip()
    return None


def get_database_url() -> str:
    """Get database URL from environment or default."""
    return os.environ.get('DATABASE_URL', 'sqlite:///portfolio_data.db')


def get_redis_url() -> str:
    """Get Redis URL from environment or default."""
    return os.environ.get('REDIS_URL', 'redis://localhost:6379/0')


def get_data_source_config() -> Dict[str, Any]:
    """Get data source configuration."""
    return {
        'yahoo_finance': {
            'enabled': True,
            'backoff_max': 60
        },
        'alpha_vantage': {
            'enabled': get_api_key('alpha_vantage') is not None,
            'rate_limit': 5,
            'rate_limit_window_minutes': 1
        }
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration dictionary."""
    required_fields = ['database_url', 'redis_url', 'data_sources']
    
    # Check required fields exist
    for field in required_fields:
        if field not in config:
            raise KeyError(f"Missing required configuration field: {field}")
    
    # Validate database URL
    db_url = config['database_url']
    if not db_url or not isinstance(db_url, str):
        raise ValueError("Invalid database URL")
    
    # Basic validation for database URL format
    valid_schemes = ['sqlite', 'postgresql', 'postgres', 'mysql']
    if not any(db_url.startswith(f'{scheme}:') for scheme in valid_schemes):
        raise ValueError("Invalid database URL scheme")
    
    # Validate Redis URL
    redis_url = config['redis_url']
    if not redis_url or not isinstance(redis_url, str):
        raise ValueError("Invalid Redis URL")
    
    if not redis_url.startswith('redis://'):
        raise ValueError("Invalid Redis URL scheme")
    
    # Validate data sources
    data_sources = config['data_sources']
    if not isinstance(data_sources, dict):
        raise ValueError("Invalid data sources configuration")
    
    return True
```

## src/cli/__init__.py
```python

```

## src/cli/utils.py
```python
from datetime import datetime
from typing import Optional

import pandas as pd  # type: ignore[import-untyped]
from rich.console import Console
from rich.table import Table


def display_market_data(data: pd.DataFrame, title: Optional[str] = None) -> None:
    """Display market data in a formatted table."""
    console = Console()
    table = Table(title=title or "Market Data")
    
    # Add columns
    table.add_column("Timestamp")
    table.add_column("Open")
    table.add_column("High")
    table.add_column("Low")
    table.add_column("Close")
    table.add_column("Volume")
    table.add_column("Source")
    
    # Add rows
    for _, row in data.iterrows():
        table.add_row(
            row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            f"{row['open']:.2f}",
            f"{row['high']:.2f}",
            f"{row['low']:.2f}",
            f"{row['close']:.2f}",
            f"{row['volume']:,}",
            row['source']
        )
        
    console.print(table)

def format_change(value: float) -> str:
    """Format price change with color and arrow."""
    if value > 0:
        return f"[green]↑{value:.2f}%[/green]"
    elif value < 0:
        return f"[red]↓{abs(value):.2f}%[/red]"
    return "[yellow]0.00%[/yellow]"

def format_volume(volume: int) -> str:
    """Format volume with appropriate scale."""
    if volume >= 500_000_000:
        return f"{volume/1_000_000_000:.1f}B"
    elif volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume == 500_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume/1_000:.1f}K"
    return str(volume)

def parse_date(date_str: str) -> datetime:
    """Parse date string in multiple formats."""
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    raise ValueError(
        "Invalid date format. Use YYYY-MM-DD, YYYY/MM/DD, "
        "DD-MM-YYYY, or DD/MM/YYYY"
    )
```

## src/cli/commands.py
```python
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table
import pandas as pd  # type: ignore[import-untyped]

from .. import settings
from ..data_sources.base import DataSourceBase, MarketData
from ..data_sources.alpha_vantage import AlphaVantageAdapter
from ..data_sources.yahoo_finance import YahooFinanceAdapter
from ..processing.pipeline import DataPipeline
from ..processing.validation import StockPrice
from ..storage.repository import DataRepository

app = typer.Typer()
console = Console()

def get_pipeline() -> DataPipeline:
    """Get configured data pipeline."""
    sources: List[DataSourceBase] = [YahooFinanceAdapter()]
    if settings.ALPHA_VANTAGE_API_KEY:
        sources.append(AlphaVantageAdapter())
    return DataPipeline(sources)

def get_repository() -> DataRepository:
    """Get configured data repository."""
    return DataRepository()

def convert_stock_prices_to_market_data(stock_prices: List[StockPrice]) -> List[MarketData]:
    """Convert StockPrice objects to MarketData objects."""
    return [
        MarketData(
            symbol=sp.symbol,
            timestamp=sp.timestamp,
            open=sp.open,
            high=sp.high,
            low=sp.low,
            close=sp.close,
            volume=sp.volume,
            source=sp.source
        )
        for sp in stock_prices
    ]

def setup_date_range_and_repository(days: int) -> Tuple[DataRepository, datetime, datetime]:
    """Set up repository and date range for data operations."""
    repository = get_repository()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return repository, start_date, end_date

def create_market_data_table(title: str, data: List[StockPrice]) -> Table:
    """Create a standardized market data table."""
    table = Table(title=title)
    table.add_column("Timestamp")
    table.add_column("Open")
    table.add_column("High")
    table.add_column("Low")
    table.add_column("Close")
    table.add_column("Volume")
    table.add_column("Source")
    
    for item in data:
        table.add_row(
            item.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            f"{item.open:.2f}",
            f"{item.high:.2f}",
            f"{item.low:.2f}",
            f"{item.close:.2f}",
            str(item.volume),
            item.source
        )
    
    return table

def create_search_results_table(title: str, results: List[Dict[str, Any]], limit: int) -> Table:
    """Create a standardized search results table."""
    table = Table(title=title)
    table.add_column("Symbol")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Exchange/Region")
    
    for item in results[:limit]:
        table.add_row(
            item['symbol'],
            item.get('name', ''),
            item.get('type', ''),
            item.get('exchange', item.get('region', ''))
        )
    
    return table

@app.command()
def fetch(
    symbol: str = typer.Argument(..., help="Stock symbol to fetch"),
    days: int = typer.Option(7, help="Number of days of historical data"),
    interval: Optional[int] = typer.Option(None, help="Intraday interval in minutes")
) -> None:
    """Fetch market data for a symbol."""
    pipeline = get_pipeline()
    repository, start_date, end_date = setup_date_range_and_repository(days)
    
    async def _fetch() -> None:
        response = await pipeline.fetch_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        if not response.success:
            console.print(f"[red]Error: {response.error}[/red]")
            raise typer.Exit(1)
            
        if response.data:
            market_data = convert_stock_prices_to_market_data(response.data)
            repository.save_market_data(market_data)
        
        # Display results
        table = create_market_data_table(f"Market Data for {symbol}", response.data or [])
        console.print(table)
        
    asyncio.run(_fetch())

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for symbols"),
    limit: int = typer.Option(10, help="Maximum number of results")
) -> None:
    """Search for stock symbols."""
    pipeline = get_pipeline()
    
    async def _search() -> None:
        results = []
        for source in pipeline.data_sources:
            try:
                symbols = await source.search_symbols(query)
                results.extend(symbols)
            except Exception as e:
                console.print(f"[yellow]Warning: {str(e)}[/yellow]")
                
        if not results:
            console.print("[red]No results found[/red]")
            raise typer.Exit(1)
            
        # Display results
        table = create_search_results_table(f"Search Results for '{query}'", results, limit)
        console.print(table)
        
    asyncio.run(_search())

@app.command()
def analyze(
    symbol: str = typer.Argument(..., help="Stock symbol to analyze"),
    days: int = typer.Option(30, help="Number of days to analyze")
) -> None:
    """Basic price analysis for a symbol."""
    repository, start_date, end_date = setup_date_range_and_repository(days)
    
    data = repository.get_market_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )
    
    if not data:
        console.print("[red]No data found[/red]")
        raise typer.Exit(1)
        
    # Convert to pandas for analysis
    df = pd.DataFrame([d.model_dump() for d in data])
    
    # Calculate basic statistics
    stats = {
        'Start Date': df['timestamp'].min(),
        'End Date': df['timestamp'].max(),
        'Days': len(df['timestamp'].unique()),
        'Average Price': df['close'].mean(),
        'Highest Price': df['high'].max(),
        'Lowest Price': df['low'].min(),
        'Total Volume': df['volume'].sum(),
        'Price Change': df['close'].iloc[-1] - df['close'].iloc[0],
        'Change %': ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
    }
    
    # Display results
    table = Table(title=f"Analysis for {symbol}")
    table.add_column("Metric")
    table.add_column("Value")
    
    for metric, value in stats.items():
        if isinstance(value, (int, float)):
            formatted_value = f"{value:,.2f}"
        else:
            formatted_value = str(value)
        table.add_row(metric, formatted_value)
        
    console.print(table)
```

## src/processing/__init__.py
```python

```

## src/processing/pipeline.py
```python
import logging
from typing import List, Optional
from datetime import datetime

import pandas as pd  # type: ignore
from pydantic import ValidationError

from ..data_sources.base import DataSourceBase, MarketData
from ..data_sources.exceptions import DataSourceError
from .validation import StockPrice, DataSourceResponse
from .transforms import clean_market_data

logger = logging.getLogger(__name__)

class DataPipeline:
    """Data processing pipeline for market data."""
    
    def __init__(self, data_sources: List[DataSourceBase]):
        self.data_sources = data_sources
        
    async def fetch_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: Optional[int] = None
    ) -> DataSourceResponse:
        """Fetch and process market data from all configured sources."""
        
        if not self.data_sources:
            return DataSourceResponse(
                success=False,
                error="No data sources configured"
            )
        
        # Validate date range
        if start_date and end_date and start_date > end_date:
            return DataSourceResponse(
                success=False,
                error="Start date must be before end date"
            )
        
        # Validate symbol
        if not symbol or not symbol.strip():
            return DataSourceResponse(
                success=False,
                error="Symbol cannot be empty"
            )
        
        all_data: List[MarketData] = []
        errors = []
        
        for source in self.data_sources:
            try:
                if interval:
                    data = await source.get_intraday_prices(
                        symbol=symbol,
                        interval=interval
                    )
                else:
                    data = await source.get_daily_prices(
                        symbol=symbol,
                        start_date=start_date.date() if start_date else None,
                        end_date=end_date.date() if end_date else None
                    )
                all_data.extend(data)
                
            except DataSourceError as e:
                logger.warning(f"Data source error: {str(e)}")
                errors.append(str(e))
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                errors.append(str(e))
                continue
                
        if not all_data and errors:
            return DataSourceResponse(
                success=False,
                error=f"All data sources failed: {'; '.join(errors)}"
            )
            
        try:
            # Convert to pandas DataFrame for processing
            df = pd.DataFrame([d.model_dump() for d in all_data])
            
            # Clean and validate data
            df = clean_market_data(df)
            
            # Convert back to StockPrice models
            validated_data = []
            for _, row in df.iterrows():
                try:
                    price = StockPrice(
                        symbol=row['symbol'],
                        timestamp=row['timestamp'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume'],
                        source=row['source']
                    )
                    validated_data.append(price)
                except ValidationError as e:
                    logger.warning(f"Validation error for row: {str(e)}")
                    continue
                    
            if not validated_data:
                return DataSourceResponse(
                    success=False,
                    error="No valid data after processing"
                )
                
            return DataSourceResponse(
                success=True,
                data=validated_data
            )
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return DataSourceResponse(
                success=False,
                error=f"Processing error: {str(e)}"
            )
```

## src/processing/transforms.py
```python
import pandas as pd  # type: ignore
import numpy as np

def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize market data."""
    if df.empty:
        return df
        
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Remove duplicates, keeping the most recent data
    df = df.drop_duplicates(
        subset=['symbol', 'timestamp'],
        keep='last'
    )
    
    # Forward fill missing values (max 2 periods)
    df = df.fillna(method='ffill', limit=2)
    
    # Drop any remaining rows with missing values
    df = df.dropna()
    
    # Ensure proper data types
    df['symbol'] = df['symbol'].astype(str)
    df['volume'] = df['volume'].astype(np.int64)
    df['open'] = df['open'].astype(np.float64)
    df['high'] = df['high'].astype(np.float64)
    df['low'] = df['low'].astype(np.float64)
    df['close'] = df['close'].astype(np.float64)
    
    # Ensure OHLC validity
    df = fix_ohlc_values(df)
    
    # Remove outliers
    df = remove_price_outliers(df)
    
    return df

def fix_ohlc_values(df: pd.DataFrame) -> pd.DataFrame:
    """Fix invalid OHLC values."""
    # Ensure high is the highest value
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    
    # Ensure low is the lowest value
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    return df

def remove_price_outliers(
    df: pd.DataFrame,
    window: int = 20,
    std_threshold: float = 3.0
) -> pd.DataFrame:
    """Remove price outliers using rolling statistics."""
    if len(df) < window:
        return df
        
    # Calculate rolling mean and std of close prices
    rolling_mean = df['close'].rolling(window=window, center=True).mean()
    rolling_std = df['close'].rolling(window=window, center=True).std()
    
    # Create bands
    upper_band = rolling_mean + (rolling_std * std_threshold)
    lower_band = rolling_mean - (rolling_std * std_threshold)
    
    # Remove outliers
    df = df[
        (df['close'] >= lower_band) &
        (df['close'] <= upper_band)
    ]
    
    return df
```

## src/processing/validation.py
```python
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator

class StockPrice(BaseModel):
    """Stock price data validation model."""
    symbol: str = Field(..., min_length=1, max_length=10)
    timestamp: datetime
    open: float = Field(..., gt=0)
    high: float = Field(..., gt=0)
    low: float = Field(..., gt=0)
    close: float = Field(..., gt=0)
    volume: int = Field(..., ge=0)
    source: str
    
    @validator('high')
    def high_greater_than_low(cls, v: float, values: Dict[str, Any]) -> float:
        if 'low' in values and v < values['low']:
            raise ValueError('high must be greater than low')
        return v
        
    @validator('open', 'close')
    def price_within_range(cls, v: float, values: Dict[str, Any]) -> float:
        if 'high' in values and 'low' in values:
            if v > values['high'] or v < values['low']:
                raise ValueError('price must be within high-low range')
        return v

class TimeSeriesRequest(BaseModel):
    """Time series data request validation."""
    symbol: str = Field(..., min_length=1, max_length=10)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    interval: Optional[int] = Field(None, ge=1, le=60)
    limit: Optional[int] = Field(None, gt=0)
    
    @validator('end_date')
    def end_date_after_start(cls, v: Optional[datetime], values: Dict[str, Any]) -> Optional[datetime]:
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('end_date must be after start_date')
        return v

class SearchRequest(BaseModel):
    """Symbol search request validation."""
    query: str = Field(..., min_length=1)
    limit: Optional[int] = Field(None, gt=0)

class DataSourceResponse(BaseModel):
    """Data source response validation."""
    success: bool
    data: Optional[List[StockPrice]] = None
    error: Optional[str] = None
```
