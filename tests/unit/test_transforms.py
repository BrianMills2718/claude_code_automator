import pytest
import pandas as pd  # type: ignore
import numpy as np
from datetime import datetime

from src.processing.transforms import (
    clean_market_data,
    fix_ohlc_values,
    remove_price_outliers
)


class TestCleanMarketData:
    """Unit tests for clean_market_data function."""

    def test_clean_empty_dataframe(self) -> None:
        """Test cleaning empty DataFrame."""
        df = pd.DataFrame()
        result = clean_market_data(df)
        assert result.empty

    def test_clean_valid_data(self) -> None:
        """Test cleaning valid market data."""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'AAPL', 'AAPL'],
            'timestamp': [
                datetime(2023, 1, 3),
                datetime(2023, 1, 1),
                datetime(2023, 1, 2)
            ],
            'open': [100.0, 101.0, 102.0],
            'high': [105.0, 106.0, 107.0],
            'low': [99.0, 100.0, 101.0],
            'close': [102.0, 103.0, 104.0],
            'volume': [1000000, 1100000, 1200000]
        })
        
        result = clean_market_data(df)
        
        # Should be sorted by timestamp
        assert result['timestamp'].is_monotonic_increasing
        
        # Should have correct data types
        assert result['symbol'].dtype == object
        assert result['volume'].dtype == np.int64
        assert result['open'].dtype == np.float64
        assert result['high'].dtype == np.float64
        assert result['low'].dtype == np.float64
        assert result['close'].dtype == np.float64

    def test_clean_removes_duplicates(self) -> None:
        """Test that duplicate rows are removed."""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'AAPL', 'AAPL'],
            'timestamp': [
                datetime(2023, 1, 1),
                datetime(2023, 1, 1),  # Duplicate
                datetime(2023, 1, 2)
            ],
            'open': [100.0, 99.0, 102.0],  # Different values for duplicate
            'high': [105.0, 104.0, 107.0],
            'low': [99.0, 98.0, 101.0],
            'close': [102.0, 101.0, 104.0],
            'volume': [1000000, 900000, 1200000]
        })
        
        result = clean_market_data(df)
        
        # Should keep only 2 rows (duplicate removed)
        assert len(result) == 2
        
        # Should keep the last duplicate (most recent data)
        first_row = result[result['timestamp'] == datetime(2023, 1, 1)]
        assert len(first_row) == 1
        assert first_row.iloc[0]['open'] == 99.0  # Should keep the second duplicate

    def test_clean_handles_missing_values(self) -> None:
        """Test handling of missing values."""
        df = pd.DataFrame({
            'symbol': ['AAPL', 'AAPL', 'AAPL', 'AAPL'],
            'timestamp': [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4)
            ],
            'open': [100.0, np.nan, np.nan, 104.0],
            'high': [105.0, np.nan, np.nan, 109.0],
            'low': [99.0, np.nan, np.nan, 103.0],
            'close': [102.0, np.nan, np.nan, 106.0],
            'volume': [1000000, 1100000, 1200000, 1300000]
        })
        
        result = clean_market_data(df)
        
        # Forward fill should handle up to 2 missing values
        # The third row might be filled, but the fourth should be available
        assert len(result) >= 2  # At least first and last row
        assert not result.isna().any().any()  # No NaN values remaining

    def test_clean_fixes_ohlc_values(self) -> None:
        """Test that OHLC values are fixed."""
        df = pd.DataFrame({
            'symbol': ['AAPL'],
            'timestamp': [datetime(2023, 1, 1)],
            'open': [100.0],
            'high': [99.0],  # Invalid: high < open
            'low': [101.0],  # Invalid: low > open
            'close': [102.0],
            'volume': [1000000]
        })
        
        result = clean_market_data(df)
        
        # High should be the maximum value (102.0 is the close price)
        assert result.iloc[0]['high'] == 102.0
        
        # Low should be the minimum value after high is corrected (100.0 is the open price)
        assert result.iloc[0]['low'] == 100.0

    def test_clean_removes_outliers(self) -> None:
        """Test outlier removal."""
        # Create data with one extreme outlier
        prices = [100.0] * 25 + [1000.0]  # One extreme outlier
        df = pd.DataFrame({
            'symbol': ['AAPL'] * 26,
            'timestamp': [datetime(2023, 1, i + 1) for i in range(26)],
            'open': prices,
            'high': [p + 1 for p in prices],
            'low': [p - 1 for p in prices],
            'close': prices,
            'volume': [1000000] * 26
        })
        
        result = clean_market_data(df)
        
        # Outlier should be removed
        assert len(result) < 26
        assert result['close'].max() < 500.0  # Outlier removed


class TestFixOHLCValues:
    """Unit tests for fix_ohlc_values function."""

    def test_fix_valid_ohlc(self) -> None:
        """Test with valid OHLC values."""
        df = pd.DataFrame({
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [102.0]
        })
        
        result = fix_ohlc_values(df)
        
        # Values should remain the same
        assert result.iloc[0]['open'] == 100.0
        assert result.iloc[0]['high'] == 105.0
        assert result.iloc[0]['low'] == 99.0
        assert result.iloc[0]['close'] == 102.0

    def test_fix_invalid_high(self) -> None:
        """Test fixing invalid high value."""
        df = pd.DataFrame({
            'open': [100.0],
            'high': [98.0],  # Invalid: should be highest
            'low': [99.0],
            'close': [102.0]
        })
        
        result = fix_ohlc_values(df)
        
        # High should be corrected to maximum value
        assert result.iloc[0]['high'] == 102.0
        # Low should remain at the minimum of all values after high correction
        assert result.iloc[0]['low'] == 99.0

    def test_fix_invalid_low(self) -> None:
        """Test fixing invalid low value."""
        df = pd.DataFrame({
            'open': [100.0],
            'high': [105.0],
            'low': [103.0],  # Invalid: should be lowest
            'close': [102.0]
        })
        
        result = fix_ohlc_values(df)
        
        # High should remain valid
        assert result.iloc[0]['high'] == 105.0
        # Low should be corrected to minimum value (100.0 is the open price)
        assert result.iloc[0]['low'] == 100.0

    def test_fix_multiple_rows(self) -> None:
        """Test fixing multiple rows."""
        df = pd.DataFrame({
            'open': [100.0, 110.0],
            'high': [98.0, 115.0],  # First row invalid
            'low': [99.0, 108.0],
            'close': [102.0, 112.0]
        })
        
        result = fix_ohlc_values(df)
        
        # First row should be fixed
        assert result.iloc[0]['high'] == 102.0
        assert result.iloc[0]['low'] == 99.0  # min(100.0, 102.0, 99.0, 102.0) = 99.0
        
        # Second row should remain valid
        assert result.iloc[1]['high'] == 115.0
        assert result.iloc[1]['low'] == 108.0


class TestRemovePriceOutliers:
    """Unit tests for remove_price_outliers function."""

    def test_remove_outliers_small_dataset(self) -> None:
        """Test with dataset smaller than window."""
        df = pd.DataFrame({
            'close': [100.0, 101.0, 102.0]
        })
        
        result = remove_price_outliers(df, window=20)
        
        # Should return original data for small datasets
        assert result.equals(df)

    def test_remove_outliers_no_outliers(self) -> None:
        """Test with no outliers."""
        # Create data with no outliers
        prices = [100.0 + i * 0.1 for i in range(30)]
        df = pd.DataFrame({
            'close': prices
        })
        
        result = remove_price_outliers(df, window=20, std_threshold=3.0)
        
        # Should keep most or all data
        assert len(result) >= len(df) * 0.8  # At least 80% of data

    def test_remove_outliers_with_outliers(self) -> None:
        """Test with clear outliers."""
        # Create normal data with clear outliers
        prices = [100.0] * 15 + [1000.0] + [100.0] * 15
        df = pd.DataFrame({
            'close': prices
        })
        
        result = remove_price_outliers(df, window=20, std_threshold=2.0)
        
        # Should remove the outlier
        assert len(result) < len(df)
        assert result['close'].max() < 200.0

    def test_remove_outliers_custom_parameters(self) -> None:
        """Test with custom window and threshold."""
        prices = [100.0] * 10 + [200.0] + [100.0] * 10
        df = pd.DataFrame({
            'close': prices
        })
        
        # Strict threshold should remove the outlier
        result_strict = remove_price_outliers(df, window=10, std_threshold=1.0)
        
        # Lenient threshold should keep the outlier
        result_lenient = remove_price_outliers(df, window=10, std_threshold=5.0)
        
        assert len(result_strict) <= len(result_lenient)

    def test_remove_outliers_empty_result(self) -> None:
        """Test edge case that might result in empty DataFrame."""
        # Create data with extreme outliers
        prices = [1.0, 1000.0, 1.0]
        df = pd.DataFrame({
            'close': prices
        })
        
        result = remove_price_outliers(df, window=3, std_threshold=0.1)
        
        # Should handle edge cases gracefully
        assert isinstance(result, pd.DataFrame)

    def test_remove_outliers_preserves_structure(self) -> None:
        """Test that DataFrame structure is preserved."""
        df = pd.DataFrame({
            'symbol': ['AAPL'] * 25,
            'close': [100.0] * 25,
            'volume': [1000000] * 25
        })
        
        result = remove_price_outliers(df, window=20)
        
        # Should preserve all columns
        assert list(result.columns) == list(df.columns)
        
        # Should preserve data types where possible
        if len(result) > 0:
            assert result['symbol'].dtype == df['symbol'].dtype
            assert result['close'].dtype == df['close'].dtype
            assert result['volume'].dtype == df['volume'].dtype