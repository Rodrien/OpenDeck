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


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""

    deck_id: str = Field(..., description="ID of the deck")
    document_ids: list[str] = Field(..., description="IDs of uploaded documents")
    task_id: str = Field(..., description="Celery task ID for tracking processing status")
    status: str = Field(default="queued", description="Processing status")
    message: str = Field(default="Documents uploaded successfully. Processing started.")

    class Config:
        json_schema_extra = {
            "example": {
                "deck_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_ids": [
                    "223e4567-e89b-12d3-a456-426614174001",
                    "323e4567-e89b-12d3-a456-426614174002",
                ],
                "task_id": "424e4567-e89b-12d3-a456-426614174003",
                "status": "queued",
                "message": "Documents uploaded successfully. Processing started.",
            }
        }
