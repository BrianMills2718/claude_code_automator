import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
import pandas as pd

from .. import settings
from ..data_sources.alpha_vantage import AlphaVantageAdapter
from ..data_sources.yahoo_finance import YahooFinanceAdapter
from ..processing.pipeline import DataPipeline
from ..storage.repository import DataRepository

app = typer.Typer()
console = Console()

def get_pipeline() -> DataPipeline:
    """Get configured data pipeline."""
    sources = [YahooFinanceAdapter()]
    if settings.ALPHA_VANTAGE_API_KEY:
        sources.append(AlphaVantageAdapter())
    return DataPipeline(sources)

def get_repository() -> DataRepository:
    """Get configured data repository."""
    return DataRepository()

def setup_date_range_and_repository(days: int) -> tuple:
    """Set up repository and date range for data operations."""
    repository = get_repository()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return repository, start_date, end_date

def create_market_data_table(title: str, data: List) -> Table:
    """Create a standardized market data table."""
    table = Table(title=title)
    table.add_column("Timestamp")
    table.add_column("Open")
    table.add_column("High")
    table.add_column("Low")
    table.add_column("Close")
    table.add_column("Volume")
    table.add_column("Source")
    
    for item in data:
        table.add_row(
            item.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            f"{item.open:.2f}",
            f"{item.high:.2f}",
            f"{item.low:.2f}",
            f"{item.close:.2f}",
            str(item.volume),
            item.source
        )
    
    return table

def create_search_results_table(title: str, results: List, limit: int) -> Table:
    """Create a standardized search results table."""
    table = Table(title=title)
    table.add_column("Symbol")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Exchange/Region")
    
    for item in results[:limit]:
        table.add_row(
            item['symbol'],
            item.get('name', ''),
            item.get('type', ''),
            item.get('exchange', item.get('region', ''))
        )
    
    return table

@app.command()
def fetch(
    symbol: str = typer.Argument(..., help="Stock symbol to fetch"),
    days: int = typer.Option(7, help="Number of days of historical data"),
    interval: Optional[int] = typer.Option(None, help="Intraday interval in minutes")
):
    """Fetch market data for a symbol."""
    pipeline = get_pipeline()
    repository, start_date, end_date = setup_date_range_and_repository(days)
    
    async def _fetch():
        response = await pipeline.fetch_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval
        )
        
        if not response.success:
            console.print(f"[red]Error: {response.error}[/red]")
            raise typer.Exit(1)
            
        repository.save_market_data(response.data)
        
        # Display results
        table = create_market_data_table(f"Market Data for {symbol}", response.data)
        console.print(table)
        
    asyncio.run(_fetch())

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query for symbols"),
    limit: int = typer.Option(10, help="Maximum number of results")
):
    """Search for stock symbols."""
    pipeline = get_pipeline()
    
    async def _search():
        results = []
        for source in pipeline.data_sources:
            try:
                symbols = await source.search_symbols(query)
                results.extend(symbols)
            except Exception as e:
                console.print(f"[yellow]Warning: {str(e)}[/yellow]")
                
        if not results:
            console.print("[red]No results found[/red]")
            raise typer.Exit(1)
            
        # Display results
        table = create_search_results_table(f"Search Results for '{query}'", results, limit)
        console.print(table)
        
    asyncio.run(_search())

@app.command()
def analyze(
    symbol: str = typer.Argument(..., help="Stock symbol to analyze"),
    days: int = typer.Option(30, help="Number of days to analyze")
):
    """Basic price analysis for a symbol."""
    repository, start_date, end_date = setup_date_range_and_repository(days)
    
    data = repository.get_market_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date
    )
    
    if not data:
        console.print("[red]No data found[/red]")
        raise typer.Exit(1)
        
    # Convert to pandas for analysis
    df = pd.DataFrame([d.model_dump() for d in data])
    
    # Calculate basic statistics
    stats = {
        'Start Date': df['timestamp'].min(),
        'End Date': df['timestamp'].max(),
        'Days': len(df['timestamp'].unique()),
        'Average Price': df['close'].mean(),
        'Highest Price': df['high'].max(),
        'Lowest Price': df['low'].min(),
        'Total Volume': df['volume'].sum(),
        'Price Change': df['close'].iloc[-1] - df['close'].iloc[0],
        'Change %': ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
    }
    
    # Display results
    table = Table(title=f"Analysis for {symbol}")
    table.add_column("Metric")
    table.add_column("Value")
    
    for metric, value in stats.items():
        if isinstance(value, (int, float)):
            formatted_value = f"{value:,.2f}"
        else:
            formatted_value = str(value)
        table.add_row(metric, formatted_value)
        
    console.print(table)