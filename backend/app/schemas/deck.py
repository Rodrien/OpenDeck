"""Deck API Schemas"""

from datetime import datetime
from pydantic import BaseModel, Field
from app.core.models import DifficultyLevel


class DeckBase(BaseModel):
    """Base deck schema with common fields."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    category: str = Field(..., min_length=1, max_length=100)
    difficulty: DifficultyLevel


class DeckCreate(DeckBase):
    """Schema for creating a new deck."""

    pass


class DeckUpdate(BaseModel):
    """Schema for updating a deck."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    category: str | None = Field(None, min_length=1, max_length=100)
    difficulty: DifficultyLevel | None = None


class DeckResponse(DeckBase):
    """Schema for deck data in responses."""

    id: str
    user_id: str
    card_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeckListResponse(BaseModel):
    """Schema for paginated deck list response."""

    items: list[DeckResponse]
    total: int
    limit: int
    offset: int
