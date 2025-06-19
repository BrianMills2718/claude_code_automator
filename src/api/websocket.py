"""WebSocket endpoint for real-time portfolio updates."""

import json
import asyncio
import logging
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)


def get_demo_holdings_data():
    """Get demo holdings data for WebSocket testing."""
    return [
        {"symbol": "AAPL", "price": 175.43, "change": 2.15},
        {"symbol": "GOOGL", "price": 2845.67, "change": -15.32},
        {"symbol": "MSFT", "price": 342.18, "change": 4.82}
    ]


def get_demo_portfolio_data():
    """Get demo portfolio data for WebSocket testing."""
    return {
        "total_value": 125000.50,
        "daily_change": 1.2,
        "holdings": get_demo_holdings_data()
    }


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, portfolio_id: str):
        """Accept WebSocket connection and add to portfolio group."""
        await websocket.accept()
        
        if portfolio_id not in self.active_connections:
            self.active_connections[portfolio_id] = []
        
        self.active_connections[portfolio_id].append(websocket)
        logger.info(f"WebSocket connected for portfolio {portfolio_id}")
    
    def disconnect(self, websocket: WebSocket, portfolio_id: str):
        """Remove WebSocket connection from portfolio group."""
        self._remove_connection_from_group(websocket, portfolio_id)
        logger.info(f"WebSocket disconnected for portfolio {portfolio_id}")
    
    def _remove_connection_from_group(self, websocket: WebSocket, portfolio_id: str):
        """Remove a connection from its portfolio group and clean up if empty."""
        if portfolio_id in self.active_connections:
            if websocket in self.active_connections[portfolio_id]:
                self.active_connections[portfolio_id].remove(websocket)
            
            # Clean up empty groups
            if not self.active_connections[portfolio_id]:
                del self.active_connections[portfolio_id]
    
    async def send_portfolio_update(self, portfolio_id: str, data: Dict):
        """Send update to all connections for a portfolio."""
        if portfolio_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[portfolio_id]:
                try:
                    await connection.send_text(json.dumps(data))
                except Exception as e:
                    logger.error(f"Error sending WebSocket message: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for connection in disconnected:
                self._remove_connection_from_group(connection, portfolio_id)


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, portfolio_id: str):
    """WebSocket endpoint for real-time portfolio updates."""
    await manager.connect(websocket, portfolio_id)
    
    try:
        # Send initial portfolio data
        initial_data = {
            "type": "portfolio_data",
            "portfolio_id": portfolio_id,
            "data": get_demo_portfolio_data(),
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_text(json.dumps(initial_data))
        
        # Start sending periodic updates
        await send_periodic_updates(websocket, portfolio_id)
        
    except WebSocketDisconnect:
        manager.disconnect(websocket, portfolio_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, portfolio_id)


async def send_periodic_updates(websocket: WebSocket, portfolio_id: str):
    """Send periodic price updates to WebSocket client."""
    try:
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds
            
            # Mock real-time price updates
            update_data = {
                "type": "price_update",
                "portfolio_id": portfolio_id,
                "data": {
                    "AAPL": {"price": 175.43 + (asyncio.get_event_loop().time() % 10 - 5), "change": 2.15},
                    "GOOGL": {"price": 2845.67 + (asyncio.get_event_loop().time() % 20 - 10), "change": -15.32},
                    "MSFT": {"price": 342.18 + (asyncio.get_event_loop().time() % 8 - 4), "change": 4.82}
                },
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_text(json.dumps(update_data))
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Error in periodic updates: {e}")