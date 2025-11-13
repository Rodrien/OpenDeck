"""Comment API Schemas"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.models import VoteType


class CommentBase(BaseModel):
    """Base comment schema with common fields."""

    content: str = Field(..., min_length=1, max_length=5000)


class CommentCreate(CommentBase):
    """Schema for creating a new comment."""

    parent_comment_id: Optional[str] = None


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""

    content: str = Field(..., min_length=1, max_length=5000)


class UserInfo(BaseModel):
    """Minimal user information for comment author."""

    id: str
    name: str
    email: str
    profile_picture_url: Optional[str] = None

    class Config:
        from_attributes = True


class CommentResponse(CommentBase):
    """Schema for comment data in responses."""

    id: str
    deck_id: str
    user_id: str
    user: Optional[UserInfo] = None
    parent_comment_id: Optional[str] = None
    is_edited: bool
    upvotes: int = 0
    downvotes: int = 0
    score: int = 0  # upvotes - downvotes
    user_vote: Optional[VoteType] = None  # Current user's vote on this comment
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Schema for paginated comment list response."""

    items: List[CommentResponse]
    total: int
    limit: int
    offset: int


class VoteCreate(BaseModel):
    """Schema for creating/updating a vote."""

    vote_type: VoteType


class VoteResponse(BaseModel):
    """Schema for vote data in responses."""

    id: str
    comment_id: str
    user_id: str
    vote_type: VoteType
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VoteCountsResponse(BaseModel):
    """Schema for vote counts on a comment."""

    comment_id: str
    upvotes: int
    downvotes: int
    score: int
    user_vote: Optional[VoteType] = None
