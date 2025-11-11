"""
Card Report Schemas

Pydantic schemas for card report API requests and responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum


class ReportStatus(str, Enum):
    """Card report status types."""

    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class CardReportCreate(BaseModel):
    """Schema for creating a new card report."""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Detailed reason for reporting the card",
    )


class CardReportResponse(BaseModel):
    """Schema for card report response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    card_id: UUID
    user_id: UUID
    reason: str
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None


class CardReportStatusUpdate(BaseModel):
    """Schema for updating card report status."""

    status: ReportStatus = Field(
        ...,
        description="New status for the report",
    )
