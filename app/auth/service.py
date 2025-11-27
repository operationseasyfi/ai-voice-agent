from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.models import User
from app.models.auth_schemas import UserCreate, UserUpdate
from app.auth.utils import verify_password, get_password_hash
from typing import Optional

class AuthService:
    """Service for user authentication and management."""
    
    @staticmethod
    async def get_user_count(db: AsyncSession) -> int:
        """Get total number of users in the database."""
        result = await db.execute(select(func.count(User.id)))
        return result.scalar() or 0
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.password):
            return None
        
        return user
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
        """Create a new user."""
        # Check if username or email already exists
        existing_user = await AuthService.get_user_by_username(db, user_create.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        existing_email = await AuthService.get_user_by_email(db, user_create.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user with hashed password
        hashed_password = get_password_hash(user_create.password)
        
        # Get roles if provided, otherwise default
        roles = getattr(user_create, 'roles', None) or '["user"]'
        
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            password=hashed_password,  # The model uses 'password' field
            full_name=getattr(user_create, 'full_name', None),
            is_active=getattr(user_create, 'is_active', True),
            roles=roles,
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update user information."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Hash password if provided
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Check if username or email conflicts with existing users (excluding current user)
        if "username" in update_data:
            existing_user = await AuthService.get_user_by_username(db, update_data["username"])
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
        
        if "email" in update_data:
            existing_email = await AuthService.get_user_by_email(db, update_data["email"])
            if existing_email and existing_email.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Update user fields
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        return user