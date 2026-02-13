from fastapi import APIRouter, status, HTTPException, Depends
import httpx

from .config import settings
from .auth import get_current_user
from shared.schemas import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
)
from shared.utils import setup_logger


logger = setup_logger(__name__)

# Create routers
auth_router = APIRouter(prefix="/auth", tags=["auth"])

# ==================== AUTH ROUTES ====================

@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/register",
                json=user_data.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", "Registration failed")
            )
        except Exception as e:
            logger.error(f"Error calling auth service: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )
        
@auth_router.post("/login", response_model=Token)
async def login(user_data:UserLogin):
    """Login and get access token"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.AUTH_SERVICE_URL}/auth/login",
                json=user_data.model_dump(),
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", "Login failed")
            )
        except Exception as e:
            logger.error(f"Error calling auth service: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )
        
@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/auth/me",
                headers={"Authorization": f"Bearer {current_user.get('token')}"},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error calling auth service: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable"
            )
