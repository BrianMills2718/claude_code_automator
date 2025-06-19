"""Utility functions for API endpoints."""

from typing import Dict, List, Any
from datetime import datetime, timedelta


def get_demo_holdings_data() -> List[Dict[str, Any]]:
    """Get demo holdings data for testing."""
    return [
        {"symbol": "AAPL", "price": 175.43, "change": 2.15},
        {"symbol": "GOOGL", "price": 2845.67, "change": -15.32},
        {"symbol": "MSFT", "price": 342.18, "change": 4.82}
    ]


def get_demo_portfolio_data() -> Dict[str, Any]:
    """Get demo portfolio data for testing."""
    return {
        "total_value": 125000.50,
        "daily_change": 1.2,
        "holdings": get_demo_holdings_data()
    }


def get_mock_market_data() -> Dict[str, Dict[str, Any]]:
    """Get mock market data for all symbols."""
    return {
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


def get_default_market_data(symbol: str) -> Dict[str, Any]:
    """Get default market data for unknown symbols."""
    return {
        "symbol": symbol.upper(),
        "price": 100.00,
        "change": 0.50,
        "change_percent": 0.50,
        "volume": 1000000,
        "market_cap": 50000000000,
        "pe_ratio": 25.0,
        "timestamp": datetime.now().isoformat()
    }


def generate_historical_data(symbol: str, days: int) -> List[Dict[str, Any]]:
    """Generate mock historical data for a symbol."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    base_price = 100.00
    historical_data = []
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        price_change = (i % 10 - 5) * 0.5
        price = base_price + price_change + (i * 0.1)
        
        historical_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(price - 0.5, 2),
            "high": round(price + 1.0, 2),
            "low": round(price - 1.0, 2),
            "close": round(price, 2),
            "volume": 1000000 + (i * 50000)
        })
    
    return historical_data


def get_mock_portfolios() -> List[Dict[str, Any]]:
    """Get mock portfolio data for testing."""
    return [
        {
            "id": "portfolio_1",
            "name": "Growth Portfolio",
            "description": "Technology and growth stocks",
            "total_value": 125000.50,
            "holdings": [
                {"symbol": "AAPL", "shares": 100, "value": 17000.00},
                {"symbol": "GOOGL", "shares": 50, "value": 13000.00},
                {"symbol": "MSFT", "shares": 75, "value": 25000.00}
            ],
            "performance": {
                "total_return": 12.5,
                "daily_change": 1.2,
                "ytd_return": 15.8
            }
        },
        {
            "id": "portfolio_2", 
            "name": "Value Portfolio",
            "description": "Dividend-focused value stocks",
            "total_value": 85000.25,
            "holdings": [
                {"symbol": "JNJ", "shares": 200, "value": 32000.00},
                {"symbol": "PG", "shares": 150, "value": 22000.00},
                {"symbol": "KO", "shares": 300, "value": 18000.00}
            ],
            "performance": {
                "total_return": 8.3,
                "daily_change": -0.5,
                "ytd_return": 9.2
            }
        }
    ]


def get_portfolio_by_id(portfolio_id: str) -> Dict[str, Any]:
    """Get portfolio by ID."""
    portfolios = get_mock_portfolios()
    for portfolio in portfolios:
        if portfolio["id"] == portfolio_id:
            return portfolio
    return None