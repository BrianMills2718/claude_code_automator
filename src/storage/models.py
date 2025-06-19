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