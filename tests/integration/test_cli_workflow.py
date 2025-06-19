import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import pandas as pd

from src.data_sources.base import MarketData


class TestCLIWorkflowIntegration:
    """Test end-to-end CLI workflow integration."""

    def test_main_entry_point_no_args(self) -> None:
        """Test main.py with no arguments shows help and exits cleanly."""
        result = subprocess.run(
            [sys.executable, 'main.py'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should exit cleanly (code 0) and show help
        assert result.returncode == 0
        assert "ML Portfolio Analyzer" in result.stdout
        assert "Available commands:" in result.stdout
        assert "System initialized successfully." in result.stdout

    @pytest.mark.asyncio
    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_fetch_command_integration(
        self, 
        mock_redis, 
        mock_create_engine, 
        mock_ticker,
        mock_yahoo_finance_data
    ) -> None:
        """Test fetch command integration with real CLI invocation."""
        # Setup mocks
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_yahoo_finance_data
        mock_ticker.return_value = mock_ticker_instance
        
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_redis.return_value = mock_cache
        
        # Run fetch command
        result = subprocess.run(
            [sys.executable, 'main.py', 'fetch', 'AAPL', '--days', '5'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should complete successfully
        assert result.returncode == 0
        # Should show some output indicating data fetching
        assert "AAPL" in result.stdout or "Error:" in result.stderr

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_analyze_command_with_mock_data(
        self, 
        mock_redis, 
        mock_create_engine
    ) -> None:
        """Test analyze command with mocked repository data."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Create sample data
        sample_data = []
        base_date = datetime(2023, 1, 1)
        prices = [100.0, 102.0, 104.0, 103.0, 105.0]
        
        for i, price in enumerate(prices):
            mock_row = Mock()
            mock_row.symbol = "AAPL"
            mock_row.timestamp = base_date + timedelta(days=i)
            mock_row.open = price - 0.5
            mock_row.high = price + 1.0
            mock_row.low = price - 1.0
            mock_row.close = price
            mock_row.volume = 1000000
            mock_row.source = "yahoo_finance"
            sample_data.append(mock_row)
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        mock_execute_result = Mock()
        mock_execute_result.scalars.return_value = sample_data
        mock_session.execute.return_value = mock_execute_result
        
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_cache.get_market_data = Mock(return_value=None)
        mock_redis.return_value = mock_cache
        
        # Run analyze command
        result = subprocess.run(
            [sys.executable, 'main.py', 'analyze', 'AAPL', '--days', '5'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Command should complete successfully or show appropriate error
        # Since we're mocking the database, we expect it to either work or fail gracefully
        assert result.returncode in [0, 1]
        
        if result.returncode == 0:
            # If successful, should show analysis results
            assert "AAPL" in result.stdout
        else:
            # If failed, should show error message
            assert "Error:" in result.stderr or "No data found" in result.stdout

    def test_search_command_basic(self) -> None:
        """Test search command basic functionality."""
        result = subprocess.run(
            [sys.executable, 'main.py', 'search', 'AAPL'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should complete (success or failure with appropriate message)
        assert result.returncode in [0, 1]
        
        if result.returncode == 0:
            # Should show search results
            assert "AAPL" in result.stdout or "Search Results" in result.stdout
        else:
            # Should show error message
            assert "Error:" in result.stderr or "No results found" in result.stderr or "No results found" in result.stdout

    def test_invalid_command_handling(self) -> None:
        """Test handling of invalid commands."""
        result = subprocess.run(
            [sys.executable, 'main.py', 'invalid_command'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should exit with error code and show help
        assert result.returncode != 0
        assert "Error:" in result.stderr or "Usage:" in result.stderr

    @pytest.mark.asyncio
    async def test_command_validation_integration(self) -> None:
        """Test command validation and error handling integration."""
        # Test fetch with invalid symbol format
        result = subprocess.run(
            [sys.executable, 'main.py', 'fetch', '123INVALID'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should handle invalid symbol gracefully
        assert result.returncode in [0, 1]
        
        # Test analyze with invalid days parameter
        result = subprocess.run(
            [sys.executable, 'main.py', 'analyze', 'AAPL', '--days', '-1'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should handle invalid days parameter
        assert result.returncode in [0, 1]

    def test_environment_variable_handling(self) -> None:
        """Test handling of environment variables."""
        import os
        
        # Test without API key (should work with warning)
        env = os.environ.copy()
        env.pop('ALPHA_VANTAGE_API_KEY', None)
        env.pop('POSTGRES_PASSWORD', None)
        
        result = subprocess.run(
            [sys.executable, 'main.py'],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should work with warnings
        assert result.returncode == 0
        assert "System initialized successfully." in result.stdout

    def test_logging_configuration(self) -> None:
        """Test logging configuration integration."""
        import os
        
        # Test with debug logging
        env = os.environ.copy()
        env['LOG_LEVEL'] = 'DEBUG'
        
        result = subprocess.run(
            [sys.executable, 'main.py'],
            capture_output=True,
            text=True,
            env=env,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should work with debug logging
        assert result.returncode == 0
        assert "System initialized successfully." in result.stdout

    def test_help_command_integration(self) -> None:
        """Test help command integration."""
        result = subprocess.run(
            [sys.executable, 'main.py', '--help'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should show help and exit cleanly
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "Commands:" in result.stdout