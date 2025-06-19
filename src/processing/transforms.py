import pandas as pd  # type: ignore
import numpy as np

def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize market data."""
    if df.empty:
        return df
        
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Remove duplicates, keeping the most recent data
    df = df.drop_duplicates(
        subset=['symbol', 'timestamp'],
        keep='last'
    )
    
    # Forward fill missing values (max 2 periods)
    df = df.fillna(method='ffill', limit=2)
    
    # Drop any remaining rows with missing values
    df = df.dropna()
    
    # Ensure proper data types
    df['symbol'] = df['symbol'].astype(str)
    df['volume'] = df['volume'].astype(np.int64)
    df['open'] = df['open'].astype(np.float64)
    df['high'] = df['high'].astype(np.float64)
    df['low'] = df['low'].astype(np.float64)
    df['close'] = df['close'].astype(np.float64)
    
    # Ensure OHLC validity
    df = fix_ohlc_values(df)
    
    # Remove outliers
    df = remove_price_outliers(df)
    
    return df

def fix_ohlc_values(df: pd.DataFrame) -> pd.DataFrame:
    """Fix invalid OHLC values."""
    # Ensure high is the highest value
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    
    # Ensure low is the lowest value
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    return df

def remove_price_outliers(
    df: pd.DataFrame,
    window: int = 20,
    std_threshold: float = 3.0
) -> pd.DataFrame:
    """Remove price outliers using rolling statistics."""
    if len(df) < window:
        return df
    
    # Make a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Calculate rolling mean and std of close prices (not centered to avoid NaN)
    rolling_mean = df_copy['close'].rolling(window=window, min_periods=1).mean()
    rolling_std = df_copy['close'].rolling(window=window, min_periods=1).std()
    
    # For the first few points, use expanding window
    rolling_mean[:window-1] = df_copy['close'][:window-1].expanding().mean()
    rolling_std[:window-1] = df_copy['close'][:window-1].expanding().std()
    
    # Create bands
    upper_band = rolling_mean + (rolling_std * std_threshold)
    lower_band = rolling_mean - (rolling_std * std_threshold)
    
    # Remove outliers - only remove if both bands are valid
    valid_mask = (
        (df_copy['close'] >= lower_band) &
        (df_copy['close'] <= upper_band) &
        rolling_std.notna() &
        rolling_mean.notna()
    )
    
    return df_copy[valid_mask]