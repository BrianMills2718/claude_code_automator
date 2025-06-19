"""Web interface routes."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Get templates directory
templates_dir = Path(__file__).parent.parent / "web" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Create web routes app
web_routes = FastAPI()


@web_routes.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@web_routes.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    """Portfolio details page."""
    return templates.TemplateResponse("portfolio.html", {"request": request})


@web_routes.get("/portfolio/{portfolio_id}", response_class=HTMLResponse)
async def portfolio_details_page(request: Request, portfolio_id: str):
    """Portfolio details page with specific ID."""
    return templates.TemplateResponse("portfolio.html", {
        "request": request,
        "portfolio_id": portfolio_id
    })


@web_routes.get("/market", response_class=HTMLResponse)
async def market_page(request: Request):
    """Market data page."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "page": "market"
    })


@web_routes.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """Analysis page."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "page": "analysis"
    })