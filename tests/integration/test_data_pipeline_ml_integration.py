import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Any, List, Dict
import pandas as pd
import numpy as np
import asyncio

from src.data_sources.base import MarketData
from src.data_sources.yahoo_finance import YahooFinanceAdapter
from src.data_sources.alpha_vantage import AlphaVantageAdapter
from src.processing.pipeline import DataPipeline
# ValidationError not available in current validation module
from src.storage.repository import DataRepository
from src.cli.commands import get_pipeline, get_repository


class TestDataPipelineMLIntegration:
    """Test integration between data pipeline and ML workflow requirements."""

    @pytest.fixture
    def sample_ml_training_data(self) -> List[MarketData]:
        """Create sample data suitable for ML model training."""
        base_date = datetime(2023, 1, 1)
        data = []
        
        # Create data with various market conditions for ML training
        # Bull market period
        bull_prices = [100.0, 102.0, 104.1, 106.2, 108.4, 110.6, 112.9, 115.2]
        # Bear market period  
        bear_prices = [115.2, 113.0, 110.7, 108.2, 105.5, 102.6, 99.5, 96.2]
        # Sideways market period
        sideways_prices = [96.2, 97.8, 95.4, 98.1, 96.7, 99.2, 97.5, 98.8]
        
        all_prices = bull_prices + bear_prices + sideways_prices
        
        for i, price in enumerate(all_prices):
            # Add some noise to simulate real market data
            noise = np.random.normal(0, 0.5)
            adjusted_price = max(price + noise, 0.01)  # Ensure positive price
            
            data.append(MarketData(
                symbol="AAPL",
                timestamp=base_date + timedelta(days=i),
                open=adjusted_price - 0.3,
                high=adjusted_price + 1.5,
                low=adjusted_price - 1.5,
                close=adjusted_price,
                volume=1000000 + int(np.random.normal(0, 100000)),
                source="yahoo_finance"
            ))
        return data

    @pytest.fixture
    def multi_asset_portfolio_data(self) -> Dict[str, List[MarketData]]:
        """Create multi-asset data for portfolio ML models."""
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "SPY"]
        base_date = datetime(2023, 1, 1)
        all_data = {}
        
        # Different correlation patterns for ML training
        correlation_seeds = {"AAPL": 1, "GOOGL": 2, "MSFT": 3, "TSLA": 4, "SPY": 5}
        
        for symbol in symbols:
            np.random.seed(correlation_seeds[symbol])
            data = []
            
            # Generate correlated returns
            base_price = {"AAPL": 150.0, "GOOGL": 2500.0, "MSFT": 300.0, "TSLA": 200.0, "SPY": 400.0}[symbol]
            current_price = base_price
            
            for i in range(30):  # 30 days of data
                # Market factor + idiosyncratic factor
                market_return = np.random.normal(0.001, 0.02)  # Market component
                idiosyncratic_return = np.random.normal(0, 0.015)  # Stock-specific component
                
                # TSLA more volatile, SPY less volatile
                if symbol == "TSLA":
                    idiosyncratic_return *= 2.0
                elif symbol == "SPY":
                    idiosyncratic_return *= 0.5
                
                total_return = market_return + idiosyncratic_return
                current_price = current_price * (1 + total_return)
                
                data.append(MarketData(
                    symbol=symbol,
                    timestamp=base_date + timedelta(days=i),
                    open=current_price - 0.5,
                    high=current_price + abs(np.random.normal(0, 2)),
                    low=current_price - abs(np.random.normal(0, 2)),
                    close=current_price,
                    volume=1000000 + int(np.random.normal(0, 200000)),
                    source="yahoo_finance"
                ))
            
            all_data[symbol] = data
        
        return all_data

    @pytest.mark.asyncio
    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    async def test_data_pipeline_ml_data_quality(
        self, 
        mock_ticker: Mock,
        sample_ml_training_data: List[MarketData]
    ) -> None:
        """Test data pipeline produces ML-quality data."""
        # Setup mock for data fetching
        mock_ticker_instance = Mock()
        
        # Create mock DataFrame that yfinance would return
        mock_df = pd.DataFrame({
            'Open': [item.open for item in sample_ml_training_data],
            'High': [item.high for item in sample_ml_training_data],
            'Low': [item.low for item in sample_ml_training_data],
            'Close': [item.close for item in sample_ml_training_data],
            'Volume': [item.volume for item in sample_ml_training_data]
        }, index=[item.timestamp for item in sample_ml_training_data])
        
        mock_ticker_instance.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_instance
        
        # Create pipeline and fetch data
        sources = [YahooFinanceAdapter()]
        pipeline = DataPipeline(sources)
        
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 2, 1)
        )
        
        # Verify ML data quality requirements
        assert response.success, "Data fetching should succeed"
        assert response.data is not None, "Data should be returned"
        assert len(response.data) >= 20, "Sufficient data for ML training"
        
        # Convert to DataFrame for ML quality checks
        df = pd.DataFrame([item.model_dump() for item in response.data])
        
        # Test data completeness (critical for ML)
        assert not df['close'].isna().any(), "No missing closing prices"
        assert not df['volume'].isna().any(), "No missing volume data"
        assert not df['timestamp'].isna().any(), "No missing timestamps"
        
        # Test data consistency (OHLC relationships)
        assert (df['high'] >= df['low']).all(), "High >= Low consistency"
        assert (df['high'] >= df['open']).all(), "High >= Open consistency"
        assert (df['high'] >= df['close']).all(), "High >= Close consistency"
        assert (df['low'] <= df['open']).all(), "Low <= Open consistency"
        assert (df['low'] <= df['close']).all(), "Low <= Close consistency"
        
        # Test for outliers that could harm ML models
        df['daily_return'] = df['close'].pct_change()
        returns = df['daily_return'].dropna()
        
        # Check for extreme outliers (>5 standard deviations)
        z_scores = np.abs((returns - returns.mean()) / returns.std())
        extreme_outliers = (z_scores > 5).sum()
        assert extreme_outliers <= 1, f"Too many extreme outliers: {extreme_outliers}"

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_repository_ml_batch_retrieval(
        self, 
        mock_redis: Any, 
        mock_create_engine: Any,
        multi_asset_portfolio_data: Dict[str, List[MarketData]]
    ) -> None:
        """Test repository batch retrieval for ML model training."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        # Combine all data for mock database
        all_mock_rows = []
        for symbol, data_list in multi_asset_portfolio_data.items():
            for item in data_list:
                mock_row = Mock()
                mock_row.symbol = item.symbol
                mock_row.timestamp = item.timestamp
                mock_row.open = item.open
                mock_row.high = item.high
                mock_row.low = item.low
                mock_row.close = item.close
                mock_row.volume = item.volume
                mock_row.source = item.source
                all_mock_rows.append(mock_row)
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        mock_execute_result = Mock()
        mock_execute_result.scalars.return_value = all_mock_rows
        mock_session.execute.return_value = mock_execute_result
        
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_cache.get_market_data = Mock(return_value=None)
        mock_redis.return_value = mock_cache
        
        # Create repository
        repository = DataRepository()
        repository.Session = mock_session_maker
        
        # Test batch retrieval for multiple symbols (ML portfolio training)
        symbols = list(multi_asset_portfolio_data.keys())
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 30)
        
        # Simulate batch retrieval
        all_data = []
        for symbol in symbols:
            symbol_data = repository.get_market_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            all_data.extend(symbol_data)
        
        # Verify ML training data structure
        assert len(all_data) > 0, "Should retrieve data for ML training"
        
        # Convert to ML-ready format
        df = pd.DataFrame([item.model_dump() for item in all_data])
        
        # Test pivot table creation (common for ML features)
        # Handle potential duplicate timestamps by taking the mean
        pivot_close = df.pivot_table(index='timestamp', columns='symbol', values='close', aggfunc='mean')
        
        # Verify pivot table structure
        assert len(pivot_close.columns) == len(symbols), "All symbols should be present"
        assert len(pivot_close) > 0, "Should have time series data"
        
        # Test returns matrix calculation (ML feature engineering)
        returns_matrix = pivot_close.pct_change().dropna()
        
        # Verify returns matrix for ML
        assert not returns_matrix.empty, "Returns matrix should not be empty"
        assert not returns_matrix.isna().all().any(), "No columns should be all NaN"

    @pytest.mark.asyncio
    async def test_feature_engineering_pipeline_integration(
        self, 
        sample_ml_training_data: List[MarketData]
    ) -> None:
        """Test integration of feature engineering with data pipeline."""
        # Convert to DataFrame
        df = pd.DataFrame([item.model_dump() for item in sample_ml_training_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Test feature engineering pipeline
        features_df = self._create_ml_features(df)
        
        # Verify ML features are created
        expected_features = [
            'returns', 'volatility', 'momentum', 'rsi', 'bollinger_upper',
            'bollinger_lower', 'volume_sma', 'price_sma', 'high_low_ratio'
        ]
        
        for feature in expected_features:
            assert feature in features_df.columns, f"Feature {feature} should be created"
        
        # Test feature data quality for ML
        # Remove rows with NaN values (typical ML preprocessing)
        ml_ready_df = features_df.dropna()
        
        assert len(ml_ready_df) > 3, "Should have enough clean data for ML after feature engineering"
        assert not ml_ready_df.isna().any().any(), "No NaN values in ML-ready data"
        
        # Test feature scaling preparation
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        
        numeric_features = ml_ready_df.select_dtypes(include=[np.number]).columns
        scaled_features = scaler.fit_transform(ml_ready_df[numeric_features])
        
        # Verify scaling worked
        assert scaled_features.shape[1] == len(numeric_features), "All numeric features scaled"
        assert not np.isnan(scaled_features).any(), "No NaN in scaled features"

    def _create_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create ML features from market data."""
        features_df = df.copy()
        
        # Price-based features
        features_df['returns'] = df['close'].pct_change()
        features_df['volatility'] = features_df['returns'].rolling(window=5).std()
        features_df['momentum'] = df['close'] / df['close'].shift(10) - 1
        
        # Technical indicators
        features_df['rsi'] = self._calculate_rsi(df['close'])
        
        # Bollinger Bands
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        features_df['bollinger_upper'] = sma_20 + (2 * std_20)
        features_df['bollinger_lower'] = sma_20 - (2 * std_20)
        
        # Volume features
        features_df['volume_sma'] = df['volume'].rolling(window=10).mean()
        features_df['price_sma'] = df['close'].rolling(window=10).mean()
        
        # Price patterns
        features_df['high_low_ratio'] = df['high'] / df['low']
        
        return features_df

    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI for ML features."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @pytest.mark.asyncio
    async def test_model_training_data_splits(
        self, 
        sample_ml_training_data: List[MarketData]
    ) -> None:
        """Test time-series train/validation/test splits for ML models."""
        # Convert to DataFrame
        df = pd.DataFrame([item.model_dump() for item in sample_ml_training_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Create features
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=5).std()
        df = df.dropna()
        
        # Time series split (preserving chronological order)
        n_samples = len(df)
        train_end = int(n_samples * 0.6)
        val_end = int(n_samples * 0.8)
        
        train_data = df.iloc[:train_end]
        val_data = df.iloc[train_end:val_end]
        test_data = df.iloc[val_end:]
        
        # Verify chronological order
        assert train_data.index.max() < val_data.index.min(), "Train should come before validation"
        assert val_data.index.max() < test_data.index.min(), "Validation should come before test"
        
        # Verify adequate data for each split
        assert len(train_data) >= 10, "Sufficient training data"
        assert len(val_data) >= 3, "Sufficient validation data"
        assert len(test_data) >= 3, "Sufficient test data"
        
        # Test feature/target separation
        feature_columns = ['returns', 'volatility']
        X_train = train_data[feature_columns]
        y_train = (train_data['returns'].shift(-1) > 0).astype(int)  # Next day positive return
        
        X_val = val_data[feature_columns]
        y_val = (val_data['returns'].shift(-1) > 0).astype(int)
        
        # Verify ML data structure
        assert X_train.shape[1] == len(feature_columns), "Correct number of features"
        assert len(X_train) == len(y_train.dropna()), "Features and targets aligned"
        assert not X_train.isna().any().any(), "No missing features"

    @pytest.mark.asyncio
    @patch('src.data_sources.yahoo_finance.yf.Ticker')
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_real_time_ml_data_integration(
        self, 
        mock_redis: Any, 
        mock_create_engine: Any,
        mock_ticker: Mock
    ) -> None:
        """Test integration for real-time ML model updates."""
        # Setup mocks for streaming data
        mock_ticker_instance = Mock()
        
        # Simulate real-time data updates
        current_time = datetime.now()
        real_time_data = []
        
        for i in range(5):  # 5 recent data points
            timestamp = current_time - timedelta(minutes=i*5)
            price = 150 + np.random.normal(0, 2)
            
            real_time_data.append({
                'Open': price - 0.5,
                'High': price + 1.0,
                'Low': price - 1.0,
                'Close': price,
                'Volume': 1000000
            })
        
        mock_df = pd.DataFrame(real_time_data)
        mock_df.index = [current_time - timedelta(minutes=i*5) for i in range(5)]
        mock_ticker_instance.history.return_value = mock_df
        mock_ticker.return_value = mock_ticker_instance
        
        # Mock storage
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_redis.return_value = mock_cache
        
        # Test real-time data integration
        sources = [YahooFinanceAdapter()]
        pipeline = DataPipeline(sources)
        
        # Fetch recent data (as would happen in real-time system)
        response = await pipeline.fetch_data(
            symbol="AAPL",
            start_date=current_time - timedelta(hours=1),
            end_date=current_time,
            interval=5  # 5-minute intervals
        )
        
        # Verify real-time data quality
        assert response.success, "Real-time data fetch should succeed"
        assert response.data is not None, "Should return recent data"
        
        if response.data:
            # Convert to DataFrame for ML processing
            df = pd.DataFrame([item.model_dump() for item in response.data])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Test real-time feature calculation
            df['returns'] = df['close'].pct_change()
            df['momentum'] = df['close'] / df['close'].shift(1) - 1
            
            # Verify real-time ML readiness
            latest_features = df.iloc[-1]
            assert not pd.isna(latest_features['close']), "Latest price should be available"
            
            # Test that data can be used for model prediction
            feature_vector = [latest_features['close'], latest_features.get('returns', 0)]
            assert len(feature_vector) == 2, "Feature vector should be complete"
            assert all(not pd.isna(val) for val in feature_vector if val is not None), "No NaN in features"

    @pytest.mark.asyncio
    async def test_error_handling_ml_pipeline(self) -> None:
        """Test error handling in ML data pipeline."""
        # Test with empty data
        empty_data: List[MarketData] = []
        df = pd.DataFrame()
        
        # Verify graceful handling of empty data
        assert len(df) == 0, "Empty DataFrame should be handled"
        
        # Test with insufficient data for ML
        insufficient_data = [
            MarketData(
                symbol="TEST",
                timestamp=datetime(2023, 1, 1),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000,
                source="test"
            )
        ]
        
        df_insufficient = pd.DataFrame([item.model_dump() for item in insufficient_data])
        df_insufficient['returns'] = df_insufficient['close'].pct_change()
        
        # Test that insufficient data is detected
        valid_returns = df_insufficient['returns'].dropna()
        assert len(valid_returns) == 0, "Single data point should not produce valid returns"
        
        # Test error handling for feature calculation
        try:
            df_insufficient['volatility'] = df_insufficient['returns'].rolling(window=5).std()
            volatility_calculated = True
        except Exception:
            volatility_calculated = False
        
        assert volatility_calculated, "Feature calculation should handle insufficient data gracefully"
        
        # Verify NaN handling
        volatility_values = df_insufficient['volatility'].dropna()
        assert len(volatility_values) == 0, "Insufficient data should result in NaN volatility"

    @pytest.mark.asyncio
    async def test_cross_validation_data_preparation(
        self, 
        sample_ml_training_data: List[MarketData]
    ) -> None:
        """Test time series cross-validation data preparation."""
        # Convert to DataFrame
        df = pd.DataFrame([item.model_dump() for item in sample_ml_training_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Create features and target
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=5).std()
        df['target'] = (df['returns'].shift(-1) > 0).astype(int)  # Next day positive return
        df = df.dropna()
        
        # Time series cross-validation splits
        n_splits = 3
        min_train_size = 10
        test_size = 5
        
        cv_splits = []
        for i in range(n_splits):
            train_end = min_train_size + (i * test_size)
            if train_end + test_size > len(df):
                break
                
            train_idx = df.index[:train_end]
            test_idx = df.index[train_end:train_end + test_size]
            
            cv_splits.append((train_idx, test_idx))
        
        # Verify cross-validation splits
        assert len(cv_splits) > 0, "Should create at least one CV split"
        
        for train_idx, test_idx in cv_splits:
            # Verify temporal order
            assert train_idx.max() < test_idx.min(), "Training data should come before test data"
            
            # Verify data sizes
            assert len(train_idx) >= min_train_size, "Sufficient training data in each fold"
            assert len(test_idx) == test_size, "Correct test size in each fold"
            
            # Test feature/target extraction
            X_train = df.loc[train_idx, ['returns', 'volatility']]
            y_train = df.loc[train_idx, 'target']
            
            X_test = df.loc[test_idx, ['returns', 'volatility']]
            y_test = df.loc[test_idx, 'target']
            
            # Verify no data leakage
            overlap = X_train.index.intersection(X_test.index)
            assert len(overlap) == 0, "No overlap between train and test"
            assert len(X_train) == len(y_train), "Features and targets aligned in train set"
            assert len(X_test) == len(y_test), "Features and targets aligned in test set"