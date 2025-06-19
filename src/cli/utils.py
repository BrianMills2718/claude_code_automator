from datetime import datetime
from typing import Optional

import pandas as pd
from rich.console import Console
from rich.table import Table


def display_market_data(data: pd.DataFrame, title: Optional[str] = None) -> None:
    """Display market data in a formatted table."""
    console = Console()
    table = Table(title=title or "Market Data")
    
    # Add columns
    table.add_column("Timestamp")
    table.add_column("Open")
    table.add_column("High")
    table.add_column("Low")
    table.add_column("Close")
    table.add_column("Volume")
    table.add_column("Source")
    
    # Add rows
    for _, row in data.iterrows():
        table.add_row(
            row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            f"{row['open']:.2f}",
            f"{row['high']:.2f}",
            f"{row['low']:.2f}",
            f"{row['close']:.2f}",
            f"{row['volume']:,}",
            row['source']
        )
        
    console.print(table)

def format_change(value: float) -> str:
    """Format price change with color and arrow."""
    if value > 0:
        return f"[green]↑{value:.2f}%[/green]"
    elif value < 0:
        return f"[red]↓{abs(value):.2f}%[/red]"
    return "[yellow]0.00%[/yellow]"

def format_volume(volume: int) -> str:
    """Format volume with appropriate scale."""
    if volume >= 500_000_000:
        return f"{volume/1_000_000_000:.1f}B"
    elif volume >= 1_000_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume == 500_000:
        return f"{volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume/1_000:.1f}K"
    return str(volume)

def parse_date(date_str: str) -> datetime:
    """Parse date string in multiple formats."""
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    raise ValueError(
        "Invalid date format. Use YYYY-MM-DD, YYYY/MM/DD, "
        "DD-MM-YYYY, or DD/MM/YYYY"
    )