from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Dict, List, Optional, Any

import pandas as pd
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