"""Dependency injection for FastAPI endpoints."""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..storage.repository import DataRepository
from ..config import settings
from .services.auth import AuthService


security = HTTPBearer()


def get_data_repository() -> DataRepository:
    """Get data repository instance."""
    return DataRepository()


def get_auth_service() -> AuthService:
    """Get authentication service."""
    return AuthService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Extract current user from JWT token."""
    try:
        token = credentials.credentials
        user_data = auth_service.validate_token(token)
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[Dict[str, Any]]:
    """Extract user from JWT token if present."""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        return auth_service.validate_token(token)
    except Exception:
        return None