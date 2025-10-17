"""Flashcard API Schemas"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class CardBase(BaseModel):
    """Base card schema with common fields."""

    question: str = Field(..., min_length=1, max_length=1000)
    answer: str = Field(..., min_length=1, max_length=5000)
    source: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="REQUIRED: Document name, page, section (e.g., 'Biology101.pdf - Page 5, Section 2.1')",
    )
    source_url: str | None = Field(None, max_length=500)

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        """Ensure source attribution includes document reference."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Source attribution is required")
        # Basic validation that source contains meaningful information
        if len(v.strip()) < 5:
            raise ValueError("Source attribution must be detailed (document, page, section)")
        return v.strip()


class CardCreate(CardBase):
    """Schema for creating a new card."""

    pass


class CardUpdate(BaseModel):
    """Schema for updating a card."""

    question: str | None = Field(None, min_length=1, max_length=1000)
    answer: str | None = Field(None, min_length=1, max_length=5000)
    source: str | None = Field(None, min_length=1, max_length=500)
    source_url: str | None = Field(None, max_length=500)


class CardResponse(CardBase):
    """Schema for card data in responses."""

    id: str
    deck_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CardListResponse(BaseModel):
    """Schema for paginated card list response."""

    items: list[CardResponse]
    total: int
    limit: int
    offset: int
