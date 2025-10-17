"""Authentication API Schemas"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""

    sub: str  # subject (user_id)
    exp: int  # expiration timestamp
    type: str  # "access" or "refresh"
