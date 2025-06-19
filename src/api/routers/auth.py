"""Authentication API endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from ..dependencies import get_auth_service, get_current_user
from ..models.requests import LoginRequest, RegisterRequest
from ..models.responses import TokenResponse, UserResponse
from ..services.auth import AuthService

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Register a new user."""
    try:
        # Mock user registration
        user = {
            "id": "user_123",
            "email": user_data.email,
            "name": user_data.name,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        return UserResponse(**user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Authenticate user and return JWT token."""
    try:
        # Mock authentication (in real implementation, would validate credentials)
        if credentials.email == "demo@example.com" and credentials.password == "demo123":
            token = auth_service.create_access_token(
                data={"sub": "user_123", "email": credentials.email}
            )
            
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                expires_in=3600
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserResponse:
    """Get current user information."""
    try:
        # Mock user data
        user = {
            "id": current_user.get("sub", "user_123"),
            "email": current_user.get("email", "demo@example.com"),
            "name": "Demo User",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        return UserResponse(**user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )