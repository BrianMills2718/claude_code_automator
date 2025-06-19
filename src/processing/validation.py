from datetime import datetime
from typing import List, Optional
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
    def high_greater_than_low(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('high must be greater than low')
        return v
        
    @validator('open', 'close')
    def price_within_range(cls, v, values):
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
    def end_date_after_start(cls, v, values):
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