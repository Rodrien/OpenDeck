"""
OAuth Schemas

Pydantic schemas for Google OAuth authentication requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.auth import UserResponse


class GoogleAuthRequest(BaseModel):
    """Request model for Google OAuth authentication."""
    
    code: str = Field(..., description="Authorization code from Google")
    redirect_uri: str = Field(..., description="Redirect URI used in the OAuth flow")


class GoogleAuthResponse(BaseModel):
    """Response model for Google OAuth authentication."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    user: UserResponse = Field(..., description="Authenticated user information")


class GoogleUserInfo(BaseModel):
    """Google user information from OAuth API."""
    
    id: str = Field(..., description="Google user ID")
    email: str = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    picture: Optional[str] = Field(None, description="URL to user's profile picture")
    verified_email: bool = Field(..., description="Whether the email is verified by Google")


class GoogleAuthUrlResponse(BaseModel):
    """Response model for Google OAuth authorization URL."""
    
    authorization_url: str = Field(..., description="Google OAuth authorization URL")