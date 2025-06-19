from typing import Optional, Any, Dict
import os
from pydantic import SecretStr
from pydantic_settings import BaseSettings

# Configuration constants
DEFAULT_POSTGRES_HOST = "localhost"
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_POSTGRES_DB = "portfolio_analyzer"
DEFAULT_POSTGRES_USER = "postgres"
DEFAULT_REDIS_HOST = "localhost"
DEFAULT_REDIS_PORT = 6379
DEFAULT_REDIS_DB = 0
DEFAULT_SQLITE_DB = "sqlite:///portfolio_data.db"
DEFAULT_REDIS_URL_TEMPLATE = "redis://{host}:{port}/{db}"
REDIS_URL_SCHEME = "redis://"

class Settings(BaseSettings):
    # Data Source Settings
    ALPHA_VANTAGE_API_KEY: Optional[SecretStr] = None
    ALPHA_VANTAGE_RATE_LIMIT: int = 5  # requests per minute
    ALPHA_VANTAGE_RATE_LIMIT_WINDOW_MINUTES: int = 1  # rate limit window
    ALPHA_VANTAGE_COMPACT_LIMIT_THRESHOLD: int = 100  # when to use compact vs full
    ALPHA_VANTAGE_DEFAULT_OUTPUTSIZE: str = "full"  # default output size
    ALPHA_VANTAGE_DAILY_TIMESTAMP_FORMAT: str = "%Y-%m-%d"
    ALPHA_VANTAGE_INTRADAY_TIMESTAMP_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    YAHOO_FINANCE_BACKOFF_MAX: int = 60  # seconds
    
    # Database Settings
    POSTGRES_HOST: str = DEFAULT_POSTGRES_HOST
    POSTGRES_PORT: int = DEFAULT_POSTGRES_PORT
    POSTGRES_DB: str = DEFAULT_POSTGRES_DB
    POSTGRES_USER: str = DEFAULT_POSTGRES_USER
    POSTGRES_PASSWORD: SecretStr
    DATABASE_URL: Optional[str] = None
    
    # Redis Settings
    REDIS_HOST: str = DEFAULT_REDIS_HOST
    REDIS_PORT: int = DEFAULT_REDIS_PORT
    REDIS_DB: int = DEFAULT_REDIS_DB
    REDIS_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._init_database_url()
        self._init_redis_url()
        
    def _init_database_url(self) -> None:
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
            
    def _init_redis_url(self) -> None:
        if not self.REDIS_URL:
            self.REDIS_URL = DEFAULT_REDIS_URL_TEMPLATE.format(
                host=self.REDIS_HOST, 
                port=self.REDIS_PORT, 
                db=self.REDIS_DB
            )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()


def get_api_key(source: str) -> Optional[str]:
    """Get API key for specified data source."""
    if source == 'alpha_vantage':
        env_key = 'ALPHA_VANTAGE_API_KEY'
        key = os.environ.get(env_key)
        if key and key.strip():
            return key.strip()
    return None


def get_database_url() -> str:
    """Get database URL from environment or default."""
    return os.environ.get('DATABASE_URL', DEFAULT_SQLITE_DB)


def get_redis_url() -> str:
    """Get Redis URL from environment or default."""
    default_url = DEFAULT_REDIS_URL_TEMPLATE.format(
        host=DEFAULT_REDIS_HOST,
        port=DEFAULT_REDIS_PORT,
        db=DEFAULT_REDIS_DB
    )
    return os.environ.get('REDIS_URL', default_url)


def get_data_source_config() -> Dict[str, Any]:
    """Get data source configuration."""
    return {
        'yahoo_finance': {
            'enabled': True,
            'backoff_max': 60
        },
        'alpha_vantage': {
            'enabled': get_api_key('alpha_vantage') is not None,
            'rate_limit': 5,
            'rate_limit_window_minutes': 1
        }
    }


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration dictionary."""
    required_fields = ['database_url', 'redis_url', 'data_sources']
    
    # Check required fields exist
    for field in required_fields:
        if field not in config:
            raise KeyError(f"Missing required configuration field: {field}")
    
    # Validate database URL
    db_url = config['database_url']
    if not db_url or not isinstance(db_url, str):
        raise ValueError("Invalid database URL")
    
    # Basic validation for database URL format
    valid_schemes = ['sqlite', 'postgresql', 'postgres', 'mysql']
    if not any(db_url.startswith(f'{scheme}:') for scheme in valid_schemes):
        raise ValueError("Invalid database URL scheme")
    
    # Validate Redis URL
    redis_url = config['redis_url']
    if not redis_url or not isinstance(redis_url, str):
        raise ValueError("Invalid Redis URL")
    
    if not redis_url.startswith(REDIS_URL_SCHEME):
        raise ValueError("Invalid Redis URL scheme")
    
    # Validate data sources
    data_sources = config['data_sources']
    if not isinstance(data_sources, dict):
        raise ValueError("Invalid data sources configuration")
    
    return True