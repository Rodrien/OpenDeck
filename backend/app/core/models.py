"""
Domain Models

Framework-agnostic domain models representing core business entities.
These models are independent of database implementation (PostgreSQL/DynamoDB).
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class DifficultyLevel(str, Enum):
    """Flashcard deck difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class DocumentStatus(str, Enum):
    """Document processing status."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class User:
    """
    User domain model.

    Represents an authenticated user in the system.
    """

    id: str
    email: str
    name: str
    password_hash: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate user data after initialization."""
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email address")
        if not self.name:
            raise ValueError("Name cannot be empty")


@dataclass
class Deck:
    """
    Flashcard Deck domain model.

    Represents a collection of flashcards organized by topic/class.
    """

    id: str
    user_id: str
    title: str
    description: str
    category: str
    difficulty: DifficultyLevel
    card_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate deck data after initialization."""
        if not self.title:
            raise ValueError("Deck title cannot be empty")
        if not self.user_id:
            raise ValueError("Deck must belong to a user")
        if self.card_count < 0:
            raise ValueError("Card count cannot be negative")


@dataclass
class Card:
    """
    Flashcard domain model.

    Represents a single question-answer pair with source attribution.

    CRITICAL: All cards MUST include source attribution per CLAUDE.md requirements.
    The source field should contain document name, page, and section reference.
    """

    id: str
    deck_id: str
    question: str
    answer: str
    source: str  # REQUIRED: Document name, page, section (e.g., "Biology101.pdf - Page 5, Section 2.1")
    source_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate card data after initialization."""
        if not self.question:
            raise ValueError("Question cannot be empty")
        if not self.answer:
            raise ValueError("Answer cannot be empty")
        if not self.source:
            raise ValueError(
                "Source attribution is required - must include document name, page, and section"
            )
        if not self.deck_id:
            raise ValueError("Card must belong to a deck")


@dataclass
class Document:
    """
    Document domain model.

    Represents an uploaded document that can be processed for flashcard generation.
    """

    id: str
    user_id: str
    filename: str
    file_path: str  # Local path or S3 key
    status: DocumentStatus
    deck_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate document data after initialization."""
        if not self.filename:
            raise ValueError("Filename cannot be empty")
        if not self.user_id:
            raise ValueError("Document must belong to a user")
        if not self.file_path:
            raise ValueError("File path cannot be empty")

    def mark_processing(self) -> None:
        """Mark document as currently being processed."""
        self.status = DocumentStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_completed(self, deck_id: str) -> None:
        """Mark document processing as completed."""
        self.status = DocumentStatus.COMPLETED
        self.deck_id = deck_id
        self.processed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error_message: str) -> None:
        """Mark document processing as failed."""
        self.status = DocumentStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
