from datetime import datetime
from typing import List, Optional, Dict, Any
import logging
from dataclasses import dataclass
from sqlalchemy import create_engine
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
    
    def __init__(self):
        try:
            self.engine = create_engine(settings.DATABASE_URL)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
        except Exception as e:
            logging.warning(f"Database connection failed: {str(e)}. Data will not be persisted.")
            self.engine = None
            self.Session = None
        try:
            self.cache = RedisCache()
        except Exception as e:
            logging.warning(f"Redis connection failed: {str(e)}. Cache will be disabled.")
            self.cache = None
        
    def _get_session(self) -> Session:
        """Get a new database session."""
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

    def _create_market_data(self, row: MarketDataModel) -> MarketData:
        """Create MarketData instance from database row."""
        return MarketData(
            symbol=row.symbol,
            timestamp=row.timestamp,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
            source=row.source
        )

    def _get_or_create_market_data(self, row: MarketDataModel) -> MarketData:
        """Get data from cache or create from DB row."""
        if self.cache:
            key = MarketDataKey(row.symbol, row.source, row.timestamp)
            cached_data = self.cache.get_market_data(row.symbol, row.source, row.timestamp)
            
            if cached_data:
                return MarketData(**cached_data)
                
        data = self._create_market_data(row)
        
        if self.cache:
            key = MarketDataKey(row.symbol, row.source, row.timestamp)
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