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


@dataclass
class Topic:
    """
    Topic domain model.

    Represents a topic or subject area that can be associated with decks and cards.
    Enables content organization and filtering by topic.
    """

    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate topic data after initialization."""
        if not self.name:
            raise ValueError("Topic name cannot be empty")
        if len(self.name) > 100:
            raise ValueError("Topic name cannot exceed 100 characters")
        if self.description and len(self.description) > 500:
            raise ValueError("Topic description cannot exceed 500 characters")


@dataclass
class UserFCMToken:
    """
    User FCM Token domain model.

    Represents a Firebase Cloud Messaging token associated with a user's device.
    Tokens are used to send push notifications to specific devices.
    """

    id: str
    user_id: str
    fcm_token: str
    device_type: str  # 'web', 'ios', 'android'
    device_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate FCM token data after initialization."""
        if not self.user_id:
            raise ValueError("Token must belong to a user")
        if not self.fcm_token:
            raise ValueError("FCM token cannot be empty")
        if self.device_type not in ('web', 'ios', 'android'):
            raise ValueError(f"Invalid device_type: {self.device_type}. Must be 'web', 'ios', or 'android'")


@dataclass
class Notification:
    """
    Notification domain model.

    Represents a notification sent to a user via Firebase Cloud Messaging.
    Notifications can be triggered by API actions or background Celery tasks.
    """

    id: str
    user_id: str
    type: str  # 'info', 'success', 'warning', 'error'
    title: str
    message: str
    action_url: Optional[str] = None
    metadata: Optional[dict] = None
    image_url: Optional[str] = None
    read: bool = False
    sent_at: datetime = field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    fcm_message_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate notification data after initialization."""
        if not self.user_id:
            raise ValueError("Notification must belong to a user")
        if not self.title:
            raise ValueError("Notification title cannot be empty")
        if not self.message:
            raise ValueError("Notification message cannot be empty")
        if self.type not in ('info', 'success', 'warning', 'error'):
            raise ValueError(f"Invalid notification type: {self.type}. Must be 'info', 'success', 'warning', or 'error'")

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.read = True
        self.read_at = datetime.utcnow()
