from pathlib import Path
from typing import Dict, Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Data Source Settings
    ALPHA_VANTAGE_API_KEY: Optional[SecretStr] = None
    ALPHA_VANTAGE_RATE_LIMIT: int = 5  # requests per minute
    YAHOO_FINANCE_BACKOFF_MAX: int = 60  # seconds
    
    # Database Settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "portfolio_analyzer"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr
    DATABASE_URL: Optional[str] = None
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    def __init__(self, **kwargs):
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
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()  # type: ignore