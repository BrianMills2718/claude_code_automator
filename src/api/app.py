"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .routers import portfolio, market_data, analysis, auth
from .middleware import AuthenticationMiddleware, ErrorHandlingMiddleware
from .websocket import websocket_endpoint


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="ML Portfolio Analyzer API",
        description="Advanced financial analysis system with ML-powered risk assessment",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    
    # Static files and templates
    static_dir = Path(__file__).parent.parent / "web" / "static"
    templates_dir = Path(__file__).parent.parent / "web" / "templates"
    
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Include routers
    app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
    app.include_router(market_data.router, prefix="/api/market-data", tags=["market-data"])
    app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    
    # WebSocket endpoint
    @app.websocket("/ws/{portfolio_id}")
    async def websocket_route(websocket, portfolio_id: str):
        await websocket_endpoint(websocket, portfolio_id)
    
    # Web interface routes
    from .routes import web_routes
    app.mount("/", web_routes, name="web")
    
    return app