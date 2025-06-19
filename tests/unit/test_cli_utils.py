import pytest
from datetime import datetime
import pandas as pd  # type: ignore[import-untyped]
from unittest.mock import patch

from src.cli.utils import (
    display_market_data,
    parse_date,
    format_change,
    format_volume
)


def test_display_market_data() -> None:
    """Test market data display."""
    # Create test DataFrame
    data = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1, 9, 30)],
        'open': [100.0],
        'high': [105.0],
        'low': [99.0],
        'close': [102.0],
        'volume': [1000000],
        'source': ['test']
    })
    
    # Test that it doesn't raise an exception
    with patch('src.cli.utils.Console') as mock_console:
        display_market_data(data, "Test Title")
        mock_console.assert_called_once()


def test_parse_date_valid() -> None:
    """Test date parsing with valid inputs."""
    valid_dates = [
        ("2023-01-01", datetime(2023, 1, 1)),
        ("2023-12-31", datetime(2023, 12, 31)),
        ("2024-02-29", datetime(2024, 2, 29)),  # Leap year
        ("2023/01/01", datetime(2023, 1, 1)),
        ("01-01-2023", datetime(2023, 1, 1)),
        ("01/01/2023", datetime(2023, 1, 1))
    ]
    
    for date_str, expected in valid_dates:
        result = parse_date(date_str)
        assert result == expected


def test_parse_date_invalid() -> None:
    """Test date parsing with invalid inputs."""
    invalid_dates = [
        "",
        "invalid",
        "2023-13-01",  # Invalid month
        "2023-01-32",  # Invalid day
        "not-a-date"
    ]
    
    for date_str in invalid_dates:
        with pytest.raises(ValueError):
            parse_date(date_str)


def test_format_change() -> None:
    """Test change formatting."""
    test_cases = [
        (5.0, "5.00%"),
        (-3.25, "3.25%"),
        (0.0, "0.00%")
    ]
    
    for value, expected_text in test_cases:
        result = format_change(value)
        assert expected_text in result
        
        # Check color coding
        if value > 0:
            assert "[green]" in result and "↑" in result
        elif value < 0:
            assert "[red]" in result and "↓" in result
        else:
            assert "[yellow]" in result


def test_format_volume() -> None:
    """Test volume formatting."""
    test_cases = [
        (1_000_000_000, "1.0B"),
        (500_000_000, "0.5B"),
        (1_000_000, "1.0M"),
        (500_000, "0.5M"),
        (1_000, "1.0K"),
        (500, "500")
    ]
    
    for volume, expected in test_cases:
        result = format_volume(volume)
        assert result == expected


def test_display_market_data_with_title() -> None:
    """Test market data display with custom title."""
    data = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1)],
        'open': [100.0],
        'high': [105.0],
        'low': [99.0],
        'close': [102.0],
        'volume': [1000000],
        'source': ['test']
    })
    
    with patch('src.cli.utils.Console') as mock_console:
        display_market_data(data, "Custom Title")
        mock_console.assert_called_once()


def test_display_market_data_no_title() -> None:
    """Test market data display without title."""
    data = pd.DataFrame({
        'timestamp': [datetime(2023, 1, 1)],
        'open': [100.0],
        'high': [105.0],
        'low': [99.0],
        'close': [102.0],
        'volume': [1000000],
        'source': ['test']
    })
    
    with patch('src.cli.utils.Console') as mock_console:
        display_market_data(data)
        mock_console.assert_called_once()


def test_format_change_edge_cases() -> None:
    """Test change formatting edge cases."""
    # Very small positive
    result = format_change(0.01)
    assert "[green]" in result and "↑" in result
    
    # Very small negative
    result = format_change(-0.01)
    assert "[red]" in result and "↓" in result
    
    # Large values
    result = format_change(999.99)
    assert "[green]" in result and "999.99%" in result


def test_format_volume_edge_cases() -> None:
    """Test volume formatting edge cases."""
    # Zero volume
    assert format_volume(0) == "0"
    
    # Very large volume
    assert format_volume(1_500_000_000) == "1.5B"
    
    # Boundary cases
    assert format_volume(999) == "999"
    assert format_volume(1_000) == "1.0K"
    assert format_volume(999_999) == "1000.0K"
    assert format_volume(1_000_000) == "1.0M"


def test_parse_date_edge_cases() -> None:
    """Test date parsing edge cases."""
    # Test leap year
    result = parse_date("2024-02-29")
    assert result == datetime(2024, 2, 29)
    
    # Test different formats
    formats_and_dates = [
        ("2023-01-01", datetime(2023, 1, 1)),
        ("2023/01/01", datetime(2023, 1, 1)),  
        ("01-01-2023", datetime(2023, 1, 1)),
        ("01/01/2023", datetime(2023, 1, 1))
    ]
    
    for date_str, expected in formats_and_dates:
        result = parse_date(date_str)
        assert result == expected