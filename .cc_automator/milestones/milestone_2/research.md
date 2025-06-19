# Research Findings for Technical Analysis Engine

## What Exists

### main.py Status
- **Working main.py**: Complete CLI application with command handling
- **Entry Point**: Uses Typer for CLI commands with rich console output
- **Commands Available**: fetch, search, analyze (basic price analysis)
- **Architecture**: Clean separation with src/ module structure
- **Logging**: Configured logging system with environment-based settings
- **Error Handling**: Graceful handling of missing API keys and database connections

### Current requirements.txt Status
- **Core Dependencies**: FastAPI, SQLAlchemy, Pydantic for web/API framework
- **Data Processing**: pandas, numpy for numerical operations
- **Data Sources**: yfinance, alpha-vantage for market data
- **Visualization**: matplotlib, plotly for charting (will be needed for technical analysis)
- **Testing**: pytest, pytest-cov, pytest-asyncio for comprehensive testing
- **Development**: black, flake8, mypy for code quality
- **CLI**: typer, rich for command-line interface

### Current Project Structure
- **Clean Architecture**: Separation of CLI, data sources, processing, storage layers
- **Data Sources**: Base abstract class with Yahoo Finance and Alpha Vantage adapters
- **Processing Pipeline**: Data pipeline with transforms and validation
- **Storage**: Repository pattern with caching and models
- **Testing**: Comprehensive test structure with unit, integration, and fixtures

## Requirements Analysis

### Milestone 2: Technical Analysis Engine Requirements
Based on CLAUDE.md, this milestone must implement:

1. **Working main.py Interface**: Extend existing CLI to include technical analysis commands
2. **Modular Technical Indicator Library**: MA, RSI, MACD, Bollinger Bands calculations
3. **Signal Generation System**: Configurable parameters for buy/sell signals
4. **Pattern Recognition**: Common chart patterns (support/resistance, trends, etc.)
5. **Backtesting Framework**: Strategy validation with historical data
6. **Performance Metrics**: Sharpe ratio, max drawdown calculations
7. **Clean Interfaces**: Between indicators and signal generators
8. **Comprehensive Testing**: Unit tests for all calculations
9. **CLI Integration**: Technical analysis accessible from main.py

### Dependencies Needed
Current requirements.txt already includes:
- **pandas/numpy**: For time series calculations ✅
- **matplotlib/plotly**: For charting and visualization ✅
- **scipy**: For statistical calculations ✅
- **pytest**: For testing framework ✅

Additional dependencies that may be needed:
- **talib** (Technical Analysis Library): For proven technical indicator implementations
- **backtrader**: For backtesting framework (or implement custom)
- **quantlib**: For advanced financial calculations (optional)

## Implementation Approach

### Basic Code Structure Needed

1. **Technical Indicators Module** (`src/analysis/indicators.py`):
   - MovingAverage class (SMA, EMA, WMA)
   - RSI (Relative Strength Index) calculator
   - MACD (Moving Average Convergence Divergence) calculator  
   - BollingerBands calculator
   - Base TechnicalIndicator abstract class for consistency

2. **Signal Generation Module** (`src/analysis/signals.py`):
   - SignalGenerator base class
   - Buy/Sell signal logic based on indicator combinations
   - Configurable parameters (thresholds, timeframes)
   - Signal strength scoring

3. **Pattern Recognition Module** (`src/analysis/patterns.py`):
   - Chart pattern detection algorithms
   - Support/resistance level identification
   - Trend analysis (uptrend, downtrend, sideways)
   - Pattern strength assessment

4. **Backtesting Framework** (`src/analysis/backtesting.py`):
   - BacktestEngine class for strategy validation
   - Portfolio simulation with buy/sell execution
   - Performance metrics calculation
   - Trade log and statistics generation

5. **Performance Metrics Module** (`src/analysis/metrics.py`):
   - Sharpe ratio calculation
   - Maximum drawdown analysis
   - Win rate, profit factor calculations
   - Risk-adjusted returns

6. **CLI Integration** (extend `src/cli/commands.py`):
   - `analyze-technical` command for running technical analysis
   - `backtest` command for strategy validation
   - `signals` command for current signal generation
   - Rich tables for displaying results

### Key Functions/Classes to Implement

```python
# Core indicator calculations
class TechnicalIndicator(ABC):
    def calculate(self, data: List[MarketData]) -> List[float]

class MovingAverage(TechnicalIndicator):
    def __init__(self, period: int, ma_type: str = 'SMA')

class RSI(TechnicalIndicator):
    def __init__(self, period: int = 14)

class MACD(TechnicalIndicator):
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9)

class BollingerBands(TechnicalIndicator):
    def __init__(self, period: int = 20, std_dev: float = 2.0)

# Signal generation
class SignalGenerator:
    def generate_signals(self, indicators: Dict[str, List[float]]) -> List[Signal]

class Signal(BaseModel):
    timestamp: datetime
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    strength: float   # 0.0 to 1.0
    indicators_used: List[str]
    reason: str

# Backtesting framework
class BacktestEngine:
    def run_backtest(self, strategy: Strategy, data: List[MarketData]) -> BacktestResult

class BacktestResult(BaseModel):
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    trades: List[Trade]
```

### User Interface Approach
Extend the existing CLI with new commands:

```bash
# Technical analysis commands
python main.py analyze-technical AAPL --indicators RSI,MACD,MA --period 30
python main.py signals AAPL --strategy momentum --strength-threshold 0.7
python main.py backtest AAPL --strategy rsi_oversold --start-date 2023-01-01 --end-date 2023-12-31
python main.py patterns AAPL --detect support,resistance,trends
```

Rich console output for:
- Technical indicator values in tabular format
- Signal alerts with color-coded strength
- Backtest results with performance metrics
- Pattern detection results with confidence scores

## Testing Strategy

### Unit Tests Needed
1. **Indicator Calculations** (`tests/unit/test_indicators.py`):
   - Test each indicator with known input/output data
   - Edge cases (insufficient data, invalid parameters)
   - Mathematical accuracy validation

2. **Signal Generation** (`tests/unit/test_signals.py`):
   - Signal logic validation with mock indicator data
   - Parameter sensitivity testing
   - Signal strength calculation accuracy

3. **Pattern Recognition** (`tests/unit/test_patterns.py`):
   - Pattern detection algorithm testing
   - False positive/negative rate validation
   - Pattern strength assessment accuracy

4. **Backtesting Framework** (`tests/unit/test_backtesting.py`):
   - Trade execution logic
   - Portfolio value calculation
   - Performance metrics accuracy

### Integration Tests Needed
1. **End-to-End Technical Analysis** (`tests/integration/test_technical_analysis.py`):
   - Complete workflow from data fetch to signal generation
   - Integration between indicators and signal generation
   - CLI command testing with real data

2. **Backtesting Pipeline** (`tests/integration/test_backtesting_pipeline.py`):
   - Full backtesting workflow with historical data
   - Strategy parameter optimization
   - Performance metric calculation validation

### Test Scenarios for This Milestone
1. **Basic Indicator Calculation**: Verify RSI, MACD, MA calculations match reference implementations
2. **Signal Generation Accuracy**: Test buy/sell signals with known market conditions
3. **Backtesting Accuracy**: Validate backtest results against manual calculations
4. **CLI Integration**: Ensure all new commands work correctly with existing data infrastructure
5. **Performance Testing**: Verify calculations complete within reasonable time for large datasets

### Mock Data Strategy
- Use existing test fixtures from Milestone 1 for consistent market data
- Create specific test datasets for different market conditions (trending, volatile, sideways)
- Generate synthetic data for edge case testing (gaps, splits, extreme volatility)

## Implementation Priority

1. **Phase 1**: Core indicator calculations (MA, RSI, MACD, Bollinger Bands)
2. **Phase 2**: Signal generation system with basic buy/sell logic
3. **Phase 3**: CLI integration and rich output formatting
4. **Phase 4**: Backtesting framework with performance metrics
5. **Phase 5**: Pattern recognition algorithms
6. **Phase 6**: Comprehensive testing and validation

This approach builds on the solid foundation from Milestone 1 and leverages the existing architecture patterns for clean, testable technical analysis functionality.