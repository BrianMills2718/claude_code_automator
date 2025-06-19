from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator, model_validator

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
    
    @model_validator(mode='after')
    def validate_price_ranges(self) -> 'StockPrice':
        """Validate that all price values are consistent."""
        # High must be greater than or equal to low
        if self.high < self.low:
            raise ValueError('high must be greater than low')
        
        # Open and close must be within high-low range
        if self.open > self.high or self.open < self.low:
            raise ValueError('price must be within high-low range')
        
        if self.close > self.high or self.close < self.low:
            raise ValueError('price must be within high-low range')
            
        return self

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