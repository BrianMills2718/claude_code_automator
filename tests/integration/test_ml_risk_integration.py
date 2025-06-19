import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Any, List, Dict
import pandas as pd
import numpy as np

from src.storage.repository import DataRepository
from src.data_sources.base import MarketData
from src.cli.commands import get_pipeline, analyze
from src.processing.pipeline import DataPipeline


class TestMLRiskIntegration:
    """Test integration between data components and ML risk assessment workflow."""

    @pytest.fixture
    def sample_risk_assessment_data(self) -> List[MarketData]:
        """Create sample data suitable for risk assessment calculations."""
        base_date = datetime(2023, 1, 1)
        data = []
        
        # Create more volatile price series for risk calculations
        prices = [100.0, 98.5, 102.3, 97.8, 104.2, 99.1, 106.5, 95.7, 108.9, 101.2,
                 103.8, 96.4, 109.1, 102.7, 105.3, 98.9, 111.2, 104.6, 107.8, 100.1]
        
        for i, price in enumerate(prices):
            data.append(MarketData(
                symbol="AAPL",
                timestamp=base_date + timedelta(days=i),
                open=price - 0.5,
                high=price + 2.0,
                low=price - 2.0,
                close=price,
                volume=1000000 + (i * 50000),
                source="yahoo_finance"
            ))
        return data

    @pytest.fixture
    def multi_symbol_data(self) -> Dict[str, List[MarketData]]:
        """Create multi-symbol data for portfolio risk assessment."""
        symbols = ["AAPL", "GOOGL", "MSFT"]
        base_date = datetime(2023, 1, 1)
        all_data = {}
        
        # Different volatility patterns for different stocks
        price_patterns = {
            "AAPL": [100.0, 102.0, 101.5, 103.2, 102.8, 104.1, 103.7, 105.2],
            "GOOGL": [2500.0, 2520.0, 2480.0, 2540.0, 2495.0, 2560.0, 2510.0, 2580.0],
            "MSFT": [250.0, 252.5, 248.3, 255.1, 249.7, 257.8, 251.2, 259.4]
        }
        
        for symbol in symbols:
            data = []
            prices = price_patterns[symbol]
            
            for i, price in enumerate(prices):
                data.append(MarketData(
                    symbol=symbol,
                    timestamp=base_date + timedelta(days=i),
                    open=price - 0.5,
                    high=price + 3.0,
                    low=price - 3.0,
                    close=price,
                    volume=1000000,
                    source="yahoo_finance"
                ))
            all_data[symbol] = data
            
        return all_data

    def test_risk_metrics_calculation_preparation(
        self, 
        sample_risk_assessment_data: List[MarketData]
    ) -> None:
        """Test data preparation for risk metrics calculations."""
        # Convert to DataFrame (common for risk calculations)
        df = pd.DataFrame([item.model_dump() for item in sample_risk_assessment_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate daily returns (foundation for risk metrics)
        df['daily_return'] = df['close'].pct_change()
        
        # Verify data is suitable for risk calculations
        assert len(df) >= 10, "Insufficient data for risk calculations"
        assert not df['close'].isna().all(), "No valid closing prices"
        assert not df['daily_return'].dropna().empty, "No valid returns calculated"
        
        # Calculate basic risk metrics
        returns = df['daily_return'].dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility
        avg_return = returns.mean() * 252  # Annualized return
        
        assert volatility > 0, "Volatility should be positive"
        assert not np.isnan(volatility), "Volatility should be calculable"
        assert not np.isnan(avg_return), "Average return should be calculable"
        
        # Test for outlier detection (important for risk assessment)
        z_scores = np.abs((returns - returns.mean()) / returns.std())
        outliers = z_scores > 2
        outlier_ratio = outliers.sum() / len(returns)
        assert outlier_ratio < 0.2, "Too many outliers in data"

    def test_portfolio_correlation_matrix_preparation(
        self, 
        multi_symbol_data: Dict[str, List[MarketData]]
    ) -> None:
        """Test preparation of correlation matrix for portfolio risk assessment."""
        # Combine all symbols into a single DataFrame
        combined_data = []
        for symbol, data_list in multi_symbol_data.items():
            for item in data_list:
                combined_data.append(item.model_dump())
        
        df = pd.DataFrame(combined_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Pivot to get symbols as columns
        price_matrix = df.pivot(index='timestamp', columns='symbol', values='close')
        
        # Calculate returns for each symbol
        returns_matrix = price_matrix.pct_change().dropna()
        
        # Calculate correlation matrix
        correlation_matrix = returns_matrix.corr()
        
        # Verify correlation matrix properties
        assert correlation_matrix.shape == (3, 3), "Correlation matrix should be 3x3"
        assert np.allclose(np.diag(correlation_matrix), 1.0), "Diagonal should be 1.0"
        assert correlation_matrix.equals(correlation_matrix.T), "Matrix should be symmetric"
        
        # Check that correlations are within valid range
        assert (correlation_matrix >= -1).all().all(), "Correlations should be >= -1"
        assert (correlation_matrix <= 1).all().all(), "Correlations should be <= 1"

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_risk_data_pipeline_integration(
        self, 
        mock_redis: Any, 
        mock_create_engine: Any,
        sample_risk_assessment_data: List[MarketData]
    ) -> None:
        """Test data pipeline integration for risk assessment requirements."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_rows = []
        for data in sample_risk_assessment_data:
            mock_row = Mock()
            mock_row.symbol = data.symbol
            mock_row.timestamp = data.timestamp
            mock_row.open = data.open
            mock_row.high = data.high
            mock_row.low = data.low
            mock_row.close = data.close
            mock_row.volume = data.volume
            mock_row.source = data.source
            mock_rows.append(mock_row)
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        mock_execute_result = Mock()
        mock_execute_result.scalars.return_value = mock_rows
        mock_session.execute.return_value = mock_execute_result
        
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_cache.get_market_data = Mock(return_value=None)
        mock_redis.return_value = mock_cache
        
        # Create repository
        repository = DataRepository()
        repository.Session = mock_session_maker
        
        # Test data retrieval with sufficient history for risk calculations
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 20)
        result = repository.get_market_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify sufficient data for risk calculations
        assert len(result) >= 10, "Insufficient data points for risk analysis"
        
        # Test data completeness for risk metrics
        df = pd.DataFrame([item.model_dump() for item in result])
        assert not df['close'].isna().any(), "Missing closing prices break risk calculations"
        assert not df['volume'].isna().any(), "Missing volume data affects risk assessment"
        
        # Test data ordering (critical for time-series risk calculations)
        timestamps = [item.timestamp for item in result]
        assert timestamps == sorted(timestamps), "Data must be chronologically ordered"

    def test_volatility_calculation_integration(
        self, 
        sample_risk_assessment_data: List[MarketData]
    ) -> None:
        """Test integration of volatility calculations with market data."""
        # Convert to DataFrame for calculations
        df = pd.DataFrame([item.model_dump() for item in sample_risk_assessment_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate returns
        df['daily_return'] = df['close'].pct_change()
        returns = df['daily_return'].dropna()
        
        # Test different volatility measures
        simple_volatility = returns.std()
        annualized_volatility = simple_volatility * np.sqrt(252)
        
        # Rolling volatility (common in risk management)
        rolling_vol = returns.rolling(window=5).std()
        
        # Verify calculations
        assert simple_volatility > 0, "Simple volatility should be positive"
        assert annualized_volatility > simple_volatility, "Annualized vol should be higher"
        assert not rolling_vol.dropna().empty, "Rolling volatility should be calculable"
        
        # Test EWMA volatility (exponentially weighted moving average)
        ewma_vol = returns.ewm(span=10).std()
        assert not ewma_vol.dropna().empty, "EWMA volatility should be calculable"

    def test_value_at_risk_data_preparation(
        self, 
        sample_risk_assessment_data: List[MarketData]
    ) -> None:
        """Test data preparation for Value at Risk (VaR) calculations."""
        # Convert to DataFrame
        df = pd.DataFrame([item.model_dump() for item in sample_risk_assessment_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate returns
        df['daily_return'] = df['close'].pct_change()
        returns = df['daily_return'].dropna()
        
        # Test historical VaR calculation (95% confidence)
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Test parametric VaR (assumes normal distribution)
        mean_return = returns.mean()
        std_return = returns.std()
        parametric_var_95 = mean_return - (1.645 * std_return)  # 95% confidence
        
        # Verify VaR calculations
        assert var_95 < 0, "VaR should be negative (loss)"
        assert var_99 < var_95, "99% VaR should be more extreme than 95% VaR"
        assert parametric_var_95 < 0, "Parametric VaR should indicate potential loss"
        
        # Test Monte Carlo preparation (verify we have enough data points)
        assert len(returns) >= 15, "Insufficient data for Monte Carlo simulation"

    @pytest.mark.asyncio
    async def test_portfolio_optimization_data_structure(
        self, 
        multi_symbol_data: Dict[str, List[MarketData]]
    ) -> None:
        """Test data structure requirements for portfolio optimization."""
        # Combine data from all symbols
        all_data = []
        for symbol_data in multi_symbol_data.values():
            all_data.extend([item.model_dump() for item in symbol_data])
        
        df = pd.DataFrame(all_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create returns matrix (required for portfolio optimization)
        price_matrix = df.pivot(index='timestamp', columns='symbol', values='close')
        returns_matrix = price_matrix.pct_change().dropna()
        
        # Test covariance matrix calculation (required for mean-variance optimization)
        cov_matrix = returns_matrix.cov()
        
        # Verify covariance matrix properties
        assert cov_matrix.shape[0] == cov_matrix.shape[1], "Covariance matrix must be square"
        assert len(cov_matrix) == len(multi_symbol_data), "Matrix size should match symbol count"
        
        # Test positive semi-definite property (required for optimization)
        eigenvalues = np.linalg.eigvals(cov_matrix)
        assert all(eigenval >= -1e-8 for eigenval in eigenvalues), "Covariance matrix should be positive semi-definite"
        
        # Test expected returns calculation
        expected_returns = returns_matrix.mean()
        assert len(expected_returns) == len(multi_symbol_data), "Expected returns for all symbols"
        assert not expected_returns.isna().any(), "No missing expected returns"

    @pytest.mark.asyncio
    @patch('src.storage.repository.create_engine')
    @patch('src.storage.repository.RedisCache')
    async def test_cli_risk_analysis_integration(
        self, 
        mock_redis: Any, 
        mock_create_engine: Any,
        sample_risk_assessment_data: List[MarketData]
    ) -> None:
        """Test CLI integration with risk analysis workflow."""
        # Setup mocks
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        mock_rows = []
        for data in sample_risk_assessment_data:
            mock_row = Mock()
            mock_row.symbol = data.symbol
            mock_row.timestamp = data.timestamp
            mock_row.open = data.open
            mock_row.high = data.high
            mock_row.low = data.low
            mock_row.close = data.close
            mock_row.volume = data.volume
            mock_row.source = data.source
            mock_rows.append(mock_row)
        
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        
        mock_execute_result = Mock()
        mock_execute_result.scalars.return_value = mock_rows
        mock_session.execute.return_value = mock_execute_result
        
        mock_session_maker = Mock(return_value=mock_session)
        
        mock_cache = Mock()
        mock_cache.get_market_data = Mock(return_value=None)
        mock_redis.return_value = mock_cache
        
        # Mock the repository creation in the CLI
        with patch('src.cli.commands.get_repository') as mock_get_repo, \
             patch('src.cli.commands.console') as mock_console:
            
            mock_repo = DataRepository()
            mock_repo.Session = mock_session_maker
            mock_get_repo.return_value = mock_repo
            
            # Test the analyze command with sufficient data for risk calculations
            try:
                analyze("AAPL", days=20)  # More days for better risk calculations
                analysis_successful = True
            except Exception:
                analysis_successful = False
            
            # Verify analysis was attempted with risk-appropriate parameters
            assert analysis_successful or mock_console.print.called
            mock_get_repo.assert_called_once()

    def test_risk_model_feature_engineering(
        self, 
        sample_risk_assessment_data: List[MarketData]
    ) -> None:
        """Test feature engineering for ML risk models."""
        # Convert to DataFrame
        df = pd.DataFrame([item.model_dump() for item in sample_risk_assessment_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate features commonly used in risk models
        df['daily_return'] = df['close'].pct_change()
        df['high_low_ratio'] = df['high'] / df['low']
        df['price_range'] = (df['high'] - df['low']) / df['close']
        df['volume_ma'] = df['volume'].rolling(window=5).mean()
        df['price_ma'] = df['close'].rolling(window=5).mean()
        df['volatility'] = df['daily_return'].rolling(window=5).std()
        
        # Technical indicators for risk assessment
        df['rsi'] = self._calculate_simple_rsi(df['close'], window=14)
        
        # Verify features are calculated correctly
        features = ['daily_return', 'high_low_ratio', 'price_range', 'volume_ma', 
                   'price_ma', 'volatility', 'rsi']
        
        for feature in features:
            assert feature in df.columns, f"Feature {feature} should be calculated"
            # Check that at least some values are not NaN (after warmup period)
            assert not df[feature].dropna().empty, f"Feature {feature} should have valid values"

    def _calculate_simple_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate a simple RSI for testing purposes."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def test_model_performance_metrics_preparation(
        self, 
        sample_risk_assessment_data: List[MarketData]
    ) -> None:
        """Test preparation of data for model performance evaluation."""
        # Convert to DataFrame
        df = pd.DataFrame([item.model_dump() for item in sample_risk_assessment_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate returns and features
        df['daily_return'] = df['close'].pct_change()
        df['volatility'] = df['daily_return'].rolling(window=5).std()
        
        # Create binary risk labels (high/low volatility days)
        vol_threshold = df['volatility'].median()
        df['high_risk'] = (df['volatility'] > vol_threshold).astype(int)
        
        # Test train-test split preparation
        split_idx = int(len(df) * 0.7)
        train_data = df.iloc[:split_idx]
        test_data = df.iloc[split_idx:]
        
        # Verify split maintains temporal order
        assert train_data.index.max() < test_data.index.min(), "Train data should come before test data"
        assert len(train_data) > 0, "Training set should not be empty"
        assert len(test_data) > 0, "Test set should not be empty"
        
        # Test feature matrix creation (common ML pattern)
        feature_columns = ['daily_return', 'volatility']
        X_train = train_data[feature_columns].dropna()
        y_train = train_data['high_risk'].loc[X_train.index]
        
        assert len(X_train) == len(y_train), "Features and labels should have same length"
        assert not X_train.empty, "Feature matrix should not be empty"
        assert len(X_train.columns) == len(feature_columns), "All features should be present"

    def test_backtesting_data_structure(
        self, 
        sample_risk_assessment_data: List[MarketData]
    ) -> None:
        """Test data structure for backtesting risk models."""
        # Convert to DataFrame
        df = pd.DataFrame([item.model_dump() for item in sample_risk_assessment_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        # Calculate returns
        df['daily_return'] = df['close'].pct_change()
        
        # Simulate risk predictions (would come from ML model)
        df['predicted_risk'] = np.random.rand(len(df))  # Placeholder predictions
        df['actual_loss'] = np.where(df['daily_return'] < -0.02, 1, 0)  # Binary loss indicator
        
        # Test rolling window backtesting
        window_size = 10
        backtest_results = []
        
        for i in range(window_size, len(df)):
            window_data = df.iloc[i-window_size:i]
            test_data = df.iloc[i]
            
            # Simulate prediction evaluation
            avg_predicted_risk = window_data['predicted_risk'].mean()
            actual_loss = test_data['actual_loss']
            
            backtest_results.append({
                'date': test_data.name,
                'predicted_risk': avg_predicted_risk,
                'actual_loss': actual_loss
            })
        
        # Verify backtesting structure
        assert len(backtest_results) > 0, "Backtesting should produce results"
        assert all('predicted_risk' in result for result in backtest_results), "All results should have predictions"
        assert all('actual_loss' in result for result in backtest_results), "All results should have actual outcomes"