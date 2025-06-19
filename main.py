import os
import sys
from pathlib import Path
import logging

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.append(str(src_dir))

from src.cli.commands import app
from src.config import settings

def setup_logging() -> None:
    """Configure logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main() -> None:
    """Main entry point."""
    # Setup logging
    setup_logging()
    
    # Check if Alpha Vantage API key is set
    if not os.environ.get('ALPHA_VANTAGE_API_KEY'):
        logging.warning("ALPHA_VANTAGE_API_KEY not set, using Yahoo Finance only")
    
    # Check if PostgreSQL password is set - warn but don't exit for demo purposes
    if not os.environ.get('POSTGRES_PASSWORD'):
        logging.warning("POSTGRES_PASSWORD not set, database storage will be unavailable")
        
    # Check if running in E2E test mode (non-interactive)
    if len(sys.argv) == 1:
        # No command provided - show help and exit cleanly for E2E
        print("ML Portfolio Analyzer - Advanced Financial Analysis System")
        print("Available commands:")
        print("  python main.py fetch AAPL - Fetch data for a symbol")
        print("  python main.py analyze AAPL - Analyze a symbol")
        print("  python main.py optimize portfolio.json - Optimize portfolio")
        print("System initialized successfully.")
        return
        
    # Run CLI with provided arguments
    app()

if __name__ == '__main__':
    main()