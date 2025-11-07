"""Study Session API Schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StartSessionRequest(BaseModel):
    """Schema for starting a new study session."""

    deck_id: str = Field(..., description="ID of the deck to study")
    session_type: str = Field(
        default="review",
        description="Type of study session",
        pattern="^(review|learn_new|cram)$",
    )


class RecordReviewRequest(BaseModel):
    """Schema for recording a card review."""

    card_id: str = Field(..., description="ID of the card being reviewed")
    quality: int = Field(
        ...,
        ge=0,
        le=5,
        description="Quality rating (0-5): 0=total failure, 3-5=correct, 5=perfect",
    )


class RecordReviewResponse(BaseModel):
    """Schema for card review response."""

    next_interval_days: int = Field(..., description="Days until next review")
    next_review_date: datetime = Field(..., description="Next scheduled review date")
    ease_factor: float = Field(..., description="Updated ease factor")
    repetitions: int = Field(..., description="Consecutive successful reviews")
    is_learning: bool = Field(..., description="Whether card is still in learning phase")


class StudySessionResponse(BaseModel):
    """Schema for study session data in responses."""

    id: str
    user_id: str
    deck_id: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    cards_reviewed: int
    cards_correct: int
    cards_incorrect: int
    total_time_seconds: Optional[int] = Field(
        None, description="Total session duration in seconds"
    )
    session_type: str
    card_ids: list[str] = Field(
        default_factory=list, description="List of card IDs in this session"
    )
    reviews: list[dict] = Field(
        default_factory=list, description="List of card reviews in this session"
    )
    current_card_index: int = Field(
        default=0, description="Current position in the session"
    )
    is_completed: bool = Field(
        default=False, description="Whether the session is completed"
    )

    class Config:
        from_attributes = True


class StudySessionStatsResponse(BaseModel):
    """Schema for study session statistics."""

    session: StudySessionResponse
    accuracy: float = Field(..., description="Percentage of cards answered correctly")
    cards_remaining: int = Field(..., description="Number of cards still due for review")


class DueCardsCountResponse(BaseModel):
    """Schema for due cards count."""

    deck_id: str
    total_cards: int = Field(..., description="Total number of cards in deck")
    due_cards: int = Field(..., description="Number of cards due for review")
    new_cards: int = Field(..., description="Number of cards never reviewed")
    learning_cards: int = Field(..., description="Number of cards currently being learned")


class StudyStatsResponse(BaseModel):
    """Schema for deck study statistics."""

    deck_id: str = Field(..., description="Deck identifier")
    total_cards: int = Field(..., description="Total number of cards in the deck")
    new_cards: int = Field(..., description="Number of cards that have never been reviewed")
    learning_cards: int = Field(..., description="Number of cards currently in learning phase")
    review_cards: int = Field(..., description="Number of cards in review phase")
    due_cards: int = Field(..., description="Number of cards due for review now")
    next_review_date: Optional[datetime] = Field(
        None, description="Date of the next scheduled review"
    )
    average_ease_factor: float = Field(..., description="Average ease factor across all cards")
    completion_rate: float = Field(
        ..., ge=0, le=100, description="Percentage of cards that have been reviewed at least once"
    )
