"""User API Schemas"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
