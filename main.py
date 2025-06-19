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
    log_format = settings.LOG_FORMAT
    
    # Handle JSON format from environment variable
    if log_format == "json":
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=log_level,
        format=log_format
    )

def launch_web_server() -> None:
    """Launch the FastAPI web server."""
    try:
        import uvicorn
        from src.api.app import create_app
        
        app = create_app()
        print(settings.SERVER_START_MESSAGE)
        print(settings.DASHBOARD_URL_TEMPLATE.format(port=settings.SERVER_PORT))
        print(settings.API_DOCS_URL_TEMPLATE.format(port=settings.SERVER_PORT))
        if settings.DEMO_EMAIL and settings.DEMO_PASSWORD:
            print(settings.DEMO_LOGIN_TEMPLATE.format(email=settings.DEMO_EMAIL, password=settings.DEMO_PASSWORD))
        print(f"\n{settings.SERVER_STOP_MESSAGE}")
        
        uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT, log_level=settings.UVICORN_LOG_LEVEL)
        
    except ImportError:
        print(settings.DEPENDENCY_ERROR_MESSAGE)
        print(settings.DEPENDENCY_INSTALL_MESSAGE)
        sys.exit(1)
    except Exception as e:
        print(settings.SERVER_ERROR_TEMPLATE.format(error=e))
        sys.exit(1)


def display_help_message() -> None:
    """Display help message with available commands."""
    print(settings.APP_NAME)
    print(f"\n{settings.HELP_COMMANDS_HEADER}")
    for command in settings.CLI_COMMANDS:
        print(f"  {command}")
    print(f"\n{settings.SUCCESS_MESSAGE}")

def check_environment_variables() -> None:
    """Check required environment variables and log warnings."""
    api_key_env = settings.ALPHA_VANTAGE_API_KEY_ENV
    if not os.environ.get(api_key_env):
        logging.warning(settings.API_KEY_WARNING_TEMPLATE.format(env_var=api_key_env))
    
    postgres_env = settings.POSTGRES_PASSWORD_ENV
    if not os.environ.get(postgres_env):
        logging.warning(settings.DATABASE_WARNING_TEMPLATE.format(env_var=postgres_env))

def main() -> None:
    """Main entry point."""
    setup_logging()
    
    if settings.WEB_SERVER_FLAG in sys.argv:
        launch_web_server()
        return
    
    check_environment_variables()
        
    if len(sys.argv) == 1:
        display_help_message()
        return
        
    app()

if __name__ == '__main__':
    main()