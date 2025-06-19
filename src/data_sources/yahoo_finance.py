from datetime import date
from typing import Any, Callable, Dict, List, Optional
import yfinance as yf  # type: ignore[import-untyped]
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from .base import DataSourceBase, MarketData
from .exceptions import APIError

class YahooFinanceAdapter(DataSourceBase):
    """Yahoo Finance API adapter with exponential backoff."""

    def _create_market_data(self, symbol: str, index: Any, row: Dict[str, Any]) -> MarketData:
        """Create MarketData instance from DataFrame row."""
        return MarketData(
            symbol=symbol,
            timestamp=index.to_pydatetime() if hasattr(index, 'to_pydatetime') else index,
            open=row['Open'],
            high=row['High'],
            low=row['Low'],
            close=row['Close'],
            volume=int(row['Volume']),
            source='yahoo_finance'
        )
    
    def _make_retry_decorator(self) -> Any:
        """Create retry decorator with standard settings."""
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=settings.YAHOO_FINANCE_BACKOFF_MAX)
        )

    def _handle_api_error(self, e: Exception) -> None:
        """Handle Yahoo Finance API errors."""
        raise APIError(f"Yahoo Finance API error: {str(e)}")

    def _execute_with_error_handling(self, operation: Callable[[], Any]) -> Any:
        """Execute operation with standard error handling."""
        try:
            return operation()
        except Exception as e:
            self._handle_api_error(e)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def get_daily_prices(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[MarketData]:
        def _get_daily() -> List[MarketData]:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval='1d'
            )
            return [self._create_market_data(symbol, index, row) for index, row in df.iterrows()]
        
        result: List[MarketData] = self._execute_with_error_handling(_get_daily)
        return result

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60))
    async def get_intraday_prices(
        self,
        symbol: str,
        interval: int = 5,
        limit: Optional[int] = None
    ) -> List[MarketData]:
        def _get_intraday() -> List[MarketData]:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                period='1d' if limit and limit <= 100 else '7d',
                interval=f"{interval}m"
            )
            market_data = [self._create_market_data(symbol, index, row) for index, row in df.iterrows()]
            return market_data[:limit] if limit else market_data
        
        result: List[MarketData] = self._execute_with_error_handling(_get_intraday)
        return result


    async def search_symbols(self, query: str) -> List[Dict[str, str]]:
        def _search() -> List[Dict[str, str]]:
            tickers = yf.Tickers(query)
            return [
                {
                    'symbol': ticker.ticker,
                    'name': ticker.info.get('longName', ''),
                    'type': ticker.info.get('quoteType', ''),
                    'exchange': ticker.info.get('exchange', '')
                }
                for ticker in tickers.tickers
                if hasattr(ticker, 'info') and ticker.info
            ]
        
        result: List[Dict[str, str]] = self._execute_with_error_handling(_search)
        return result