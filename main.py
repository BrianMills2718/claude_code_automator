import os
import sys
from pathlib import Path
import logging

# Add src directory to Python path
src_dir = Path(__file__).parent / 'src'
sys.path.append(str(src_dir))

from src.cli.commands import app
from src import settings

def setup_logging():
    """Configure logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main entry point."""
    # Setup logging
    setup_logging()
    
    # Check if Alpha Vantage API key is set
    if not os.environ.get('ALPHA_VANTAGE_API_KEY'):
        logging.warning("ALPHA_VANTAGE_API_KEY not set, using Yahoo Finance only")
    if not os.environ.get('POSTGRES_PASSWORD'):
        print("Error: POSTGRES_PASSWORD environment variable is not set")
        sys.exit(1)
        
    # Run CLI
    app()

if __name__ == '__main__':
    main()