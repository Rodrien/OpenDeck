"""Card Review API Schemas"""

from datetime import datetime
from pydantic import BaseModel, Field


class CardReviewBase(BaseModel):
    """Base card review schema with common fields."""

    card_id: str
    quality: int = Field(..., ge=0, le=5, description="Quality rating (0-5)")
    ease_factor: float = Field(..., ge=1.3, description="SM-2 ease factor")
    interval_days: int = Field(..., ge=0, description="Days until next review")
    repetitions: int = Field(..., ge=0, description="Consecutive successful reviews")


class CardReviewCreate(CardReviewBase):
    """Schema for creating a new card review."""

    pass


class CardReviewResponse(CardReviewBase):
    """Schema for card review data in responses."""

    id: str
    user_id: str
    review_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class CardReviewHistoryResponse(BaseModel):
    """Schema for card review history."""

    card_id: str
    total_reviews: int
    average_quality: float
    current_streak: int = Field(..., description="Current streak of correct reviews")
    reviews: list[CardReviewResponse]
