from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import UserRole

class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User's unique email address")
    password: str = Field(..., min_length=8, description="Password, minimum 8 characters")
    role: UserRole = Field(..., description="Role of the user in connectED")
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    headline: Optional[str] = Field(None, max_length=150, description="Professional headline")
    institution: Optional[str] = Field("connectED University", max_length=120)

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str = Field(..., description="Unique user identifier")
    email: str
    role: UserRole
    name: str
    is_active: bool
    telegram_linked: bool = False
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Logged out successfully."
