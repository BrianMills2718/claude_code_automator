import logging
from typing import List, Optional
from datetime import datetime

import pandas as pd
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