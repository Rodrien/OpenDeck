"""Flashcard Data Schemas"""

from pydantic import BaseModel, Field
from app.core.models import DifficultyLevel


class FlashcardData(BaseModel):
    """
    Schema for AI-generated flashcard data.

    Used as an intermediate representation between AI service output
    and database Card records.

    CRITICAL: All flashcards MUST include source attribution per CLAUDE.md requirements.
    """

    question: str = Field(..., min_length=1, max_length=1000, description="Flashcard question")
    answer: str = Field(..., min_length=1, max_length=2000, description="Flashcard answer")
    source: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Source attribution (document name, page, section)"
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.BEGINNER,
        description="Difficulty level of the flashcard"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is photosynthesis?",
                "answer": "The process by which plants convert light energy into chemical energy.",
                "source": "Biology101.pdf - Page 5, Section 2.1",
                "difficulty": "beginner"
            }
        }


class ProcessingResult(BaseModel):
    """
    Result of document processing operation.

    Contains statistics about the processing job.
    """

    total_cards: int = Field(..., ge=0, description="Total flashcards generated")
    successful_documents: int = Field(..., ge=0, description="Number of successfully processed documents")
    failed_documents: int = Field(..., ge=0, description="Number of failed documents")
    deck_id: str = Field(..., description="ID of the created/updated deck")

    class Config:
        json_schema_extra = {
            "example": {
                "total_cards": 25,
                "successful_documents": 3,
                "failed_documents": 0,
                "deck_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
