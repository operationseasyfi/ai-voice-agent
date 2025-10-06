from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings
from app.models.auth_schemas import Token, User, UserCreate, LoginRequest
from app.auth.service import AuthService
from app.auth.dependencies import get_current_active_user, get_current_superuser
from app.auth.utils import create_access_token

router = APIRouter()

@router.post("/login")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login endpoint with JSON payload."""
    user = await AuthService.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    user_dict = user.to_dict_safe()
    return {
        "token": access_token,
        "token_type": "bearer",
        "message": "Login successful",
        "user": user_dict,
        "expires_in_seconds": access_token_expires.total_seconds()
    }




@router.post("/register", response_model=User)
async def register(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)  # Only superusers can create users for now
):
    """Register a new user (superuser only)."""
    return await AuthService.create_user(db, user_create)

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

@router.get("/test-token")
async def test_token(current_user: User = Depends(get_current_active_user)):
    """Test endpoint to verify token authentication."""
    return {"message": f"Hello {current_user.username}!", "user_id": current_user.id}