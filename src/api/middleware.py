"""Custom middleware for authentication and error handling."""

import logging
import traceback
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors globally."""
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # Re-raise HTTP exceptions
            raise e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error: {e}")
            logger.error(traceback.format_exc())
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(e) if logger.isEnabledFor(logging.DEBUG) else None
                }
            )


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for protected routes."""
    
    PROTECTED_PATHS = {
        "/api/portfolio": ["POST", "PUT", "DELETE"],
        "/api/analysis": ["POST"],
        "/ws/": ["GET"]
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check authentication for protected routes."""
        path = request.url.path
        method = request.method
        
        # Check if this path requires authentication
        requires_auth = any(
            path.startswith(protected_path) and method in methods
            for protected_path, methods in self.PROTECTED_PATHS.items()
        )
        
        if requires_auth:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"}
                )
        
        response = await call_next(request)
        return response