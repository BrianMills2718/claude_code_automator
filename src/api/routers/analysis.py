"""Technical analysis API endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from ..dependencies import get_data_repository, get_current_user
from ..models.requests import AnalysisRequest
from ..models.responses import AnalysisResponse
from ...storage.repository import DataRepository

router = APIRouter()


@router.post("/{symbol}", response_model=AnalysisResponse)
async def run_technical_analysis(
    symbol: str,
    analysis_request: AnalysisRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    repository: DataRepository = Depends(get_data_repository)
) -> AnalysisResponse:
    """Run technical analysis on a symbol."""
    try:
        # Mock technical analysis results
        analysis_results = {
            "symbol": symbol.upper(),
            "indicators": {
                "sma_20": 172.45,
                "sma_50": 168.30,
                "ema_12": 174.20,
                "ema_26": 170.15,
                "rsi": 65.8,
                "macd": {
                    "macd_line": 2.15,
                    "signal_line": 1.85,
                    "histogram": 0.30
                },
                "bollinger_bands": {
                    "upper": 178.50,
                    "middle": 172.45,
                    "lower": 166.40
                }
            },
            "signals": [
                {
                    "type": "BUY",
                    "indicator": "MACD",
                    "strength": "STRONG",
                    "description": "MACD line crossed above signal line"
                },
                {
                    "type": "NEUTRAL",
                    "indicator": "RSI", 
                    "strength": "MODERATE",
                    "description": "RSI in neutral territory (65.8)"
                },
                {
                    "type": "BUY",
                    "indicator": "SMA",
                    "strength": "MODERATE", 
                    "description": "Price above 20-day SMA"
                }
            ],
            "risk_metrics": {
                "volatility": 0.28,
                "beta": 1.15,
                "sharpe_ratio": 1.42,
                "max_drawdown": -0.12,
                "var_95": -0.035
            },
            "recommendation": {
                "action": "BUY",
                "confidence": 0.75,
                "target_price": 185.00,
                "stop_loss": 165.00,
                "reasoning": "Strong momentum indicators and favorable risk metrics support bullish outlook"
            }
        }
        
        return AnalysisResponse(**analysis_results)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run analysis: {str(e)}"
        )


@router.get("/{symbol}/backtest", response_model=Dict[str, Any])
async def get_backtest_results(
    symbol: str,
    user: Dict[str, Any] = Depends(get_current_user),
    repository: DataRepository = Depends(get_data_repository)
) -> Dict[str, Any]:
    """Get backtesting results for a symbol's strategy."""
    try:
        # Mock backtest results
        backtest_results = {
            "symbol": symbol.upper(),
            "strategy": "Technical Analysis Combined",
            "period": "2023-01-01 to 2024-01-01",
            "performance": {
                "total_return": 0.156,
                "annual_return": 0.156,
                "sharpe_ratio": 1.25,
                "max_drawdown": -0.085,
                "win_rate": 0.62,
                "profit_factor": 1.45
            },
            "trades": {
                "total_trades": 24,
                "winning_trades": 15,
                "losing_trades": 9,
                "average_win": 0.034,
                "average_loss": -0.018,
                "largest_win": 0.087,
                "largest_loss": -0.032
            },
            "monthly_returns": [
                {"month": "2023-01", "return": 0.023},
                {"month": "2023-02", "return": -0.012},
                {"month": "2023-03", "return": 0.045},
                {"month": "2023-04", "return": 0.018},
                {"month": "2023-05", "return": -0.008},
                {"month": "2023-06", "return": 0.031}
            ]
        }
        
        return backtest_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backtest results: {str(e)}"
        )