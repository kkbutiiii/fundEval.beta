"""
Authentication Pydantic models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user model."""
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(UserBase):
    """User login model."""
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    """User response model."""
    id: int
    is_admin: bool
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload model."""
    sub: Optional[str] = None  # subject (user_id)
    exp: Optional[datetime] = None  # expiration
    type: Optional[str] = None  # token type: access or refresh


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request model."""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=128)
