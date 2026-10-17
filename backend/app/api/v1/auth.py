from fastapi import APIRouter, Depends, Header, status
from app.api.deps import get_current_user
from app.schemas.auth import (
    LogoutResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegisterRequest):
    """Register a new student, alumni, faculty, recruiter, founder, or admin."""
    return await auth_service.register(req)

@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(req: UserLoginRequest):
    """Authenticate with email and password."""
    return await auth_service.login(req)

@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    current_user: dict = Depends(get_current_user),
    authorization: str = Header(..., description="Bearer <token>"),
):
    """Log out the current user and invalidate the JWT token."""
    token = authorization.replace("Bearer ", "").strip()
    return await auth_service.logout(token)

@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Retrieve authenticated user's identity and basic information."""
    return await auth_service.get_me(current_user["id"])
