"""Configuration management for ML Portfolio Analyzer."""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class AppConfig:
    """Application configuration."""
    name: str = "ML Portfolio Analyzer"
    web_server_flag: str = "--web-server"
    success_message: str = "✅ System initialized successfully."
    help_commands_header: str = "🖥️  Available Commands:"
    
    @property
    def cli_commands(self) -> list:
        return [
            "python main.py --web-server  # Launch web dashboard",
            "python main.py analyze      # Run portfolio analysis",
            "python main.py fetch-data   # Download market data",
            "python main.py backtest     # Run backtesting"
        ]

@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    start_message: str = "🚀 Starting ML Portfolio Analyzer Web Server..."
    stop_message: str = "✨ Press Ctrl+C to stop the server"
    dashboard_url_template: str = "📊 Dashboard: http://localhost:{port}"
    api_docs_url_template: str = "📚 API Docs: http://localhost:{port}/docs"
    error_template: str = "❌ Failed to start web server: {error}"
    dependency_error: str = "❌ Web server dependencies not available."
    dependency_install: str = "📦 Install with: pip install fastapi uvicorn"

@dataclass
class DatabaseConfig:
    """Database configuration."""
    password_env: str = "POSTGRES_PASSWORD"
    warning_template: str = "{env_var} not set, database storage will be unavailable"

@dataclass
class ApiConfig:
    """API configuration."""
    alpha_vantage_key_env: str = "ALPHA_VANTAGE_API_KEY"
    key_warning_template: str = "{env_var} not set, using Yahoo Finance only"

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

@dataclass
class DemoConfig:
    """Demo configuration."""
    email: Optional[str] = None
    password: Optional[str] = None
    login_template: str = "💻 Demo Login: {email} / {password}"

class Settings:
    """Application settings container."""
    
    def __init__(self):
        """Initialize settings from environment variables."""
        self.app = AppConfig(
            name=os.environ.get('APP_NAME', 'ML Portfolio Analyzer')
        )
        self.server = ServerConfig(
            host=os.environ.get('SERVER_HOST', '127.0.0.1'),
            port=int(os.environ.get('SERVER_PORT', '8000')),
            log_level=os.environ.get('UVICORN_LOG_LEVEL', 'info')
        )
        self.database = DatabaseConfig()
        self.api = ApiConfig()
        self.logging = LoggingConfig(
            level=os.environ.get('LOG_LEVEL', 'INFO'),
            format=os.environ.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.demo = DemoConfig(
            email=os.environ.get('DEMO_EMAIL'),
            password=os.environ.get('DEMO_PASSWORD')
        )
    
    # Expose commonly used properties for backward compatibility
    @property
    def APP_NAME(self) -> str:
        return self.app.name
    
    @property
    def WEB_SERVER_FLAG(self) -> str:
        return self.app.web_server_flag
    
    @property
    def SUCCESS_MESSAGE(self) -> str:
        return self.app.success_message
    
    @property
    def HELP_COMMANDS_HEADER(self) -> str:
        return self.app.help_commands_header
    
    @property
    def CLI_COMMANDS(self) -> list:
        return self.app.cli_commands
    
    @property
    def SERVER_HOST(self) -> str:
        return self.server.host
    
    @property
    def SERVER_PORT(self) -> int:
        return self.server.port
    
    @property
    def UVICORN_LOG_LEVEL(self) -> str:
        return self.server.log_level
    
    @property
    def SERVER_START_MESSAGE(self) -> str:
        return self.server.start_message
    
    @property
    def SERVER_STOP_MESSAGE(self) -> str:
        return self.server.stop_message
    
    @property
    def DASHBOARD_URL_TEMPLATE(self) -> str:
        return self.server.dashboard_url_template
    
    @property
    def API_DOCS_URL_TEMPLATE(self) -> str:
        return self.server.api_docs_url_template
    
    @property
    def SERVER_ERROR_TEMPLATE(self) -> str:
        return self.server.error_template
    
    @property
    def DEPENDENCY_ERROR_MESSAGE(self) -> str:
        return self.server.dependency_error
    
    @property
    def DEPENDENCY_INSTALL_MESSAGE(self) -> str:
        return self.server.dependency_install
    
    @property
    def POSTGRES_PASSWORD_ENV(self) -> str:
        return self.database.password_env
    
    @property
    def DATABASE_WARNING_TEMPLATE(self) -> str:
        return self.database.warning_template
    
    @property
    def ALPHA_VANTAGE_API_KEY_ENV(self) -> str:
        return self.api.alpha_vantage_key_env
    
    @property
    def API_KEY_WARNING_TEMPLATE(self) -> str:
        return self.api.key_warning_template
    
    @property
    def LOG_LEVEL(self) -> str:
        return self.logging.level
    
    @property
    def LOG_FORMAT(self) -> str:
        return self.logging.format
    
    @property
    def DEMO_EMAIL(self) -> Optional[str]:
        return self.demo.email
    
    @property
    def DEMO_PASSWORD(self) -> Optional[str]:
        return self.demo.password
    
    @property
    def DEMO_LOGIN_TEMPLATE(self) -> str:
        return self.demo.login_template

settings = Settings()