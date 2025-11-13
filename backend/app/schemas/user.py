"""User API Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.core.models import User


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for user profile updates."""

    name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None


class UserResponse(UserBase):
    """Schema for user data in responses."""

    id: str
    profile_picture_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_user(cls, user: "User") -> "UserResponse":
        """Create UserResponse from User domain model."""
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            profile_picture_url=user.profile_picture,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
