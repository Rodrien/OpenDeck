"""
Pydantic Schemas for Notification Management

Request and response models for notification history and management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class NotificationResponse(BaseModel):
    """Response schema for notification."""

    id: str
    type: str
    title: str
    message: str
    action_url: Optional[str]
    metadata: Optional[Dict[str, Any]]
    image_url: Optional[str]
    read: bool
    sent_at: datetime
    read_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate notification type."""
        if v not in ("info", "success", "warning", "error"):
            raise ValueError("type must be 'info', 'success', 'warning', or 'error'")
        return v


class UnreadCountResponse(BaseModel):
    """Response schema for unread notification count."""

    count: int = Field(..., ge=0, description="Number of unread notifications")
