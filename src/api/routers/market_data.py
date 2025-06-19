"""Market data API endpoints."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..dependencies import get_data_repository, get_optional_user
from ..models.responses import MarketDataResponse, HistoricalDataResponse
from ...storage.repository import DataRepository

router = APIRouter()


@router.get("/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str,
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    repository: DataRepository = Depends(get_data_repository)
) -> MarketDataResponse:
    """Get current market data for a symbol."""
    try:
        # Mock market data (in real implementation, would fetch from data sources)
        mock_data = {
            "AAPL": {
                "symbol": "AAPL",
                "price": 175.43,
                "change": 2.15,
                "change_percent": 1.24,
                "volume": 45234567,
                "market_cap": 2750000000000,
                "pe_ratio": 28.5,
                "timestamp": datetime.now().isoformat()
            },
            "GOOGL": {
                "symbol": "GOOGL", 
                "price": 2845.67,
                "change": -15.32,
                "change_percent": -0.54,
                "volume": 1234567,
                "market_cap": 1850000000000,
                "pe_ratio": 22.8,
                "timestamp": datetime.now().isoformat()
            },
            "MSFT": {
                "symbol": "MSFT",
                "price": 342.18,
                "change": 4.82,
                "change_percent": 1.43,
                "volume": 23456789,
                "market_cap": 2550000000000,
                "pe_ratio": 32.1,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        if symbol.upper() in mock_data:
            return MarketDataResponse(**mock_data[symbol.upper()])
        else:
            # Return generic data for any symbol
            return MarketDataResponse(
                symbol=symbol.upper(),
                price=100.00,
                change=0.50,
                change_percent=0.50,
                volume=1000000,
                market_cap=50000000000,
                pe_ratio=25.0,
                timestamp=datetime.now().isoformat()
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market data: {str(e)}"
        )


@router.get("/{symbol}/historical", response_model=HistoricalDataResponse)
async def get_historical_data(
    symbol: str,
    days: int = Query(30, ge=1, le=365, description="Number of days of historical data"),
    user: Optional[Dict[str, Any]] = Depends(get_optional_user),
    repository: DataRepository = Depends(get_data_repository)
) -> HistoricalDataResponse:
    """Get historical market data for a symbol."""
    try:
        # Generate mock historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create mock price data with some variation
        base_price = 100.00
        historical_data = []
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            # Simple random walk for mock data
            price_change = (i % 10 - 5) * 0.5  # Varies between -2.5 and 2.0
            price = base_price + price_change + (i * 0.1)  # Slight upward trend
            
            historical_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(price - 0.5, 2),
                "high": round(price + 1.0, 2),
                "low": round(price - 1.0, 2),
                "close": round(price, 2),
                "volume": 1000000 + (i * 50000)
            })
        
        return HistoricalDataResponse(
            symbol=symbol.upper(),
            data=historical_data,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch historical data: {str(e)}"
        )