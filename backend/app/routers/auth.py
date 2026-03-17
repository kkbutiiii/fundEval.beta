"""
Authentication API router.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db_models.user import UserDB
from app.models.auth import (
    UserCreate, UserLogin, UserResponse, Token,
    RefreshTokenRequest, ChangePasswordRequest
)
from app.utils.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, verify_refresh_token, decode_token
)
from app.config import get_settings

settings = get_settings()
SECRET_KEY = getattr(settings, 'secret_key', 'your-secret-key-change-in-production')

router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserDB:
    """
    Get current user from JWT token.

    This dependency validates the access token and returns the current user.
    Use this for protected routes.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token, secret_key=SECRET_KEY)
    if payload is None:
        raise credentials_exception

    # Check token type
    if payload.get("type") != "access":
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Get user from database
    result = await db.execute(select(UserDB).where(UserDB.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    return user


async def get_current_active_user(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_admin_user(current_user: UserDB = Depends(get_current_user)) -> UserDB:
    """Get current admin user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    - **username**: Username (3-50 characters)
    - **password**: Password (6-128 characters)
    """
    # Check if username already exists
    result = await db.execute(select(UserDB).where(UserDB.username == data.username))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )

    # Create new user
    user = UserDB(
        username=data.username,
        password_hash=get_password_hash(data.password),
        is_admin=False,
        is_active=True
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username and password.

    Returns access token and refresh token.
    """
    # Find user by username
    result = await db.execute(select(UserDB).where(UserDB.username == form_data.username))
    user = result.scalar_one_or_none()

    # Verify password
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Update last login time
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Create tokens
    access_token = create_access_token(subject=user.id, secret_key=SECRET_KEY)
    refresh_token = create_refresh_token(subject=user.id, secret_key=SECRET_KEY)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.

    Returns new access token and refresh token.
    """
    user_id = verify_refresh_token(data.refresh_token, secret_key=SECRET_KEY)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new tokens
    access_token = create_access_token(subject=user_id, secret_key=SECRET_KEY)
    refresh_token = create_refresh_token(subject=user_id, secret_key=SECRET_KEY)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserDB = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.post("/logout", status_code=200)
async def logout(current_user: UserDB = Depends(get_current_active_user)):
    """
    Logout user.

    Note: With JWT tokens, actual logout is handled client-side by deleting tokens.
    This endpoint can be used for logging purposes.
    """
    return {"message": "Successfully logged out"}


@router.post("/change-password", status_code=200)
async def change_password(
    data: ChangePasswordRequest,
    current_user: UserDB = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.

    - **current_password**: Current password
    - **new_password**: New password (6-128 characters)
    """
    # Verify current password
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.password_hash = get_password_hash(data.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}
