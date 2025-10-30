"""
Pydantic Schemas for FCM Token Management

Request and response models for FCM token registration and management.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class FCMTokenCreate(BaseModel):
    """Request schema for registering a new FCM token."""

    fcm_token: str = Field(..., min_length=1, description="Firebase Cloud Messaging token")
    device_type: str = Field(..., pattern="^(web|ios|android)$", description="Device type")
    device_name: str | None = Field(None, max_length=255, description="Optional device name")

    @field_validator("device_type")
    @classmethod
    def validate_device_type(cls, v: str) -> str:
        """Validate device type."""
        if v not in ("web", "ios", "android"):
            raise ValueError("device_type must be 'web', 'ios', or 'android'")
        return v


class FCMTokenResponse(BaseModel):
    """Response schema for FCM token."""

    id: str
    user_id: str
    device_type: str
    device_name: str | None
    is_active: bool
    created_at: datetime
    last_used_at: datetime

    model_config = {"from_attributes": True}
