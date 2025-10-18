"""Topic API Schemas"""
from __future__ import annotations

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class TopicBase(BaseModel):
    """Base topic schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class TopicCreate(TopicBase):
    """Schema for creating a new topic."""

    pass


class TopicUpdate(BaseModel):
    """Schema for updating a topic."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class TopicResponse(TopicBase):
    """Schema for topic data in responses."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    """Schema for paginated topic list response."""

    items: List[TopicResponse]
    total: int
    limit: int
    offset: int


class TopicAssociation(BaseModel):
    """Schema for associating/dissociating topics."""

    topic_id: str = Field(..., description="Topic ID to associate/dissociate")
