"""Document API Schemas"""

from datetime import datetime
from pydantic import BaseModel, Field
from app.core.models import DocumentStatus


class DocumentBase(BaseModel):
    """Base document schema."""

    filename: str = Field(..., min_length=1, max_length=255)


class DocumentCreate(DocumentBase):
    """Schema for creating a document record (after upload)."""

    file_path: str


class DocumentResponse(DocumentBase):
    """Schema for document data in responses."""

    id: str
    user_id: str
    file_path: str
    status: DocumentStatus
    deck_id: str | None = None
    processed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    """Schema for document processing status."""

    id: str
    status: DocumentStatus
    deck_id: str | None = None
    error_message: str | None = None
    processed_at: datetime | None = None
