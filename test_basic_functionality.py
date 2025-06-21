#!/usr/bin/env python3
"""Basic functionality test for ML Portfolio Analyzer."""

import os
import sys
from pathlib import Path
from typing import List

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.append(str(src_dir))

# Set minimal environment for testing
os.environ['POSTGRES_PASSWORD'] = 'test123'

def test_imports() -> bool:
    """Test that all core imports work."""
    print("Testing imports...")
    
    try:
        from src.data_sources.yahoo_finance import YahooFinanceAdapter  # noqa: F401
        from src.data_sources.base import MarketData  # noqa: F401
        from src.processing.pipeline import DataPipeline  # noqa: F401
        from src.processing.validation import StockPrice  # noqa: F401
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_yahoo_finance_adapter() -> bool:
    """Test Yahoo Finance adapter without external dependencies."""
    print("Testing Yahoo Finance adapter...")
    
    try:
        from src.data_sources.yahoo_finance import YahooFinanceAdapter
        YahooFinanceAdapter()
        print("✓ Yahoo Finance adapter created successfully")
        return True
    except Exception as e:
        print(f"✗ Yahoo Finance adapter test failed: {e}")
        return False

def test_data_pipeline() -> bool:
    """Test data pipeline creation."""
    print("Testing data pipeline...")
    
    try:
        from src.processing.pipeline import DataPipeline
        from src.data_sources.yahoo_finance import YahooFinanceAdapter
        from src.data_sources.base import DataSourceBase
        
        sources: List[DataSourceBase] = [YahooFinanceAdapter()]
        DataPipeline(sources)
        print("✓ Data pipeline created successfully")
        return True
    except Exception as e:
        print(f"✗ Data pipeline test failed: {e}")
        return False

def test_storage_models() -> bool:
    """Test storage models."""
    print("Testing storage models...")
    
    try:
        from src.processing.validation import StockPrice
        from datetime import datetime
        
        # Create a test stock price
        StockPrice(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=150.0,
            high=155.0,
            low=149.0,
            close=153.0,
            volume=1000000,
            source="test"
        )
        print("✓ Storage models work correctly")
        return True
    except Exception as e:
        print(f"✗ Storage models test failed: {e}")
        return False

def test_cli_structure() -> bool:
    """Test CLI command structure."""
    print("Testing CLI structure...")
    
    try:
        from src.cli.commands import app  # noqa: F401
        print("✓ CLI commands loaded successfully")
        return True
    except Exception as e:
        print(f"✗ CLI structure test failed: {e}")
        return False

def main() -> bool:
    """Run all basic tests."""
    print("ML Portfolio Analyzer - Basic Functionality Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_yahoo_finance_adapter,
        test_data_pipeline,
        test_storage_models,
        test_cli_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All basic functionality tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)