"""Feedback API Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.core.models import FeedbackType, FeedbackStatus


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""

    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    message: str = Field(..., min_length=10, max_length=5000, description="Feedback message")


class FeedbackResponse(BaseModel):
    """Schema for feedback data in responses."""

    id: str
    user_id: Optional[str] = None
    feedback_type: FeedbackType
    message: str
    status: FeedbackStatus
    created_at: datetime

    class Config:
        from_attributes = True
