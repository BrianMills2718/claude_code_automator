"""Portfolio management API endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import uuid4

from ..dependencies import get_data_repository, get_current_user
from ..models.requests import PortfolioCreateRequest, PortfolioUpdateRequest
from ..models.responses import PortfolioResponse, PortfolioListResponse
from ...storage.repository import DataRepository

router = APIRouter()


def _get_mock_portfolio_data(portfolio_id: str) -> Dict[str, Any]:
    """Get mock portfolio data by ID."""
    portfolios = {
        "portfolio_1": {
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
        "portfolio_2": {
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
    }
    return portfolios.get(portfolio_id)


@router.get("/", response_model=PortfolioListResponse)
async def list_portfolios(
    user: Dict[str, Any] = Depends(get_current_user),
    repository: DataRepository = Depends(get_data_repository)
) -> PortfolioListResponse:
    """List all portfolios for the current user."""
    try:
        # For demo purposes, return mock data
        portfolios = [
            _get_mock_portfolio_data("portfolio_1"),
            _get_mock_portfolio_data("portfolio_2")
        ]
        
        return PortfolioListResponse(portfolios=portfolios)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch portfolios: {str(e)}"
        )


@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    repository: DataRepository = Depends(get_data_repository)
) -> PortfolioResponse:
    """Create a new portfolio."""
    try:
        # Generate new portfolio ID
        portfolio_id = str(uuid4())
        
        # Create portfolio (mock implementation)
        portfolio = {
            "id": portfolio_id,
            "name": portfolio_data.name,
            "description": portfolio_data.description,
            "total_value": 0.0,
            "holdings": [],
            "performance": {
                "total_return": 0.0,
                "daily_change": 0.0,
                "ytd_return": 0.0
            }
        }
        
        return PortfolioResponse(**portfolio)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portfolio: {str(e)}"
        )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    repository: DataRepository = Depends(get_data_repository)
) -> PortfolioResponse:
    """Get portfolio details by ID."""
    try:
        # Mock portfolio data
        if portfolio_id == "portfolio_1":
            portfolio = {
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
            }
            return PortfolioResponse(**portfolio)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portfolio not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch portfolio: {str(e)}"
        )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: str,
    portfolio_data: PortfolioUpdateRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    repository: DataRepository = Depends(get_data_repository)
) -> PortfolioResponse:
    """Update portfolio details."""
    try:
        # Mock update (in real implementation, would update database)
        portfolio = {
            "id": portfolio_id,
            "name": portfolio_data.name,
            "description": portfolio_data.description,
            "total_value": 125000.50,
            "holdings": [
                {"symbol": "AAPL", "shares": 100, "value": 17000.00}
            ],
            "performance": {
                "total_return": 12.5,
                "daily_change": 1.2,
                "ytd_return": 15.8
            }
        }
        
        return PortfolioResponse(**portfolio)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update portfolio: {str(e)}"
        )


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
    repository: DataRepository = Depends(get_data_repository)
) -> None:
    """Delete a portfolio."""
    try:
        # Mock deletion (in real implementation, would delete from database)
        pass
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete portfolio: {str(e)}"
        )