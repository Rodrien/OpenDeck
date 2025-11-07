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

    # Spaced repetition fields
    ease_factor: float = 2.5
    interval_days: int = 0
    repetitions: int = 0
    next_review_date: Optional[datetime] = None
    is_learning: bool = True

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
        if self.ease_factor < 1.3:
            raise ValueError("Ease factor must be at least 1.3")
        if self.interval_days < 0:
            raise ValueError("Interval days cannot be negative")
        if self.repetitions < 0:
            raise ValueError("Repetitions cannot be negative")


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


@dataclass
class CardReview:
    """
    Card Review domain model.

    Represents a single review of a flashcard with SM-2 algorithm parameters.
    Used to track learning progress and calculate optimal review intervals.
    """

    id: str
    card_id: str
    user_id: str
    review_date: datetime
    quality: int  # 0-5 rating (0-2 = incorrect, 3-5 = correct)
    ease_factor: float  # SM-2 ease factor
    interval_days: int  # Days until next review
    repetitions: int  # Number of successful consecutive reviews
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate card review data after initialization."""
        if not self.card_id:
            raise ValueError("Review must be associated with a card")
        if not self.user_id:
            raise ValueError("Review must belong to a user")
        if not (0 <= self.quality <= 5):
            raise ValueError("Quality rating must be between 0 and 5")
        if self.ease_factor < 1.3:
            raise ValueError("Ease factor cannot be less than 1.3")
        if self.interval_days < 0:
            raise ValueError("Interval days cannot be negative")
        if self.repetitions < 0:
            raise ValueError("Repetitions cannot be negative")


@dataclass
class StudySession:
    """
    Study Session domain model.

    Represents a study session where a user reviews flashcards from a deck.
    Tracks performance metrics and duration for analytics.
    """

    id: str
    user_id: str
    deck_id: str
    started_at: datetime
    session_type: str = "review"  # 'review', 'learn_new', 'cram'
    ended_at: Optional[datetime] = None
    cards_reviewed: int = 0
    cards_correct: int = 0
    cards_incorrect: int = 0
    total_duration_seconds: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate study session data after initialization."""
        if not self.user_id:
            raise ValueError("Session must belong to a user")
        if not self.deck_id:
            raise ValueError("Session must be associated with a deck")
        if self.session_type not in ('review', 'learn_new', 'cram'):
            raise ValueError(f"Invalid session type: {self.session_type}. Must be 'review', 'learn_new', or 'cram'")
        if self.cards_reviewed < 0:
            raise ValueError("Cards reviewed cannot be negative")
        if self.cards_correct < 0:
            raise ValueError("Cards correct cannot be negative")
        if self.cards_incorrect < 0:
            raise ValueError("Cards incorrect cannot be negative")
        if self.total_duration_seconds is not None and self.total_duration_seconds < 0:
            raise ValueError("Duration cannot be negative")

    def end_session(self) -> None:
        """Mark session as ended and calculate duration."""
        if not self.ended_at:
            self.ended_at = datetime.utcnow()
            self.total_duration_seconds = int((self.ended_at - self.started_at).total_seconds())

    def record_review(self, correct: bool) -> None:
        """
        Record a card review in the session.

        Args:
            correct: Whether the card was answered correctly (quality >= 3)
        """
        self.cards_reviewed += 1
        if correct:
            self.cards_correct += 1
        else:
            self.cards_incorrect += 1


class VoteType(str, Enum):
    """Comment vote types."""

    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


@dataclass
class DeckComment:
    """
    Deck Comment domain model.

    Represents a user comment on a deck with support for nested replies.
    Comments can be upvoted/downvoted by users.
    """

    id: str
    deck_id: str
    user_id: str
    content: str
    parent_comment_id: Optional[str] = None
    is_edited: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate comment data after initialization."""
        if not self.deck_id:
            raise ValueError("Comment must be associated with a deck")
        if not self.user_id:
            raise ValueError("Comment must belong to a user")
        if not self.content or not self.content.strip():
            raise ValueError("Comment content cannot be empty")
        if len(self.content) > 5000:
            raise ValueError("Comment content cannot exceed 5000 characters")

    def edit_content(self, new_content: str) -> None:
        """
        Edit the comment content.

        Args:
            new_content: The new content for the comment
        """
        if not new_content or not new_content.strip():
            raise ValueError("Comment content cannot be empty")
        if len(new_content) > 5000:
            raise ValueError("Comment content cannot exceed 5000 characters")

        self.content = new_content
        self.is_edited = True
        self.updated_at = datetime.utcnow()


@dataclass
class CommentVote:
    """
    Comment Vote domain model.

    Represents a user's upvote or downvote on a comment.
    Each user can only have one vote per comment.
    """

    id: str
    comment_id: str
    user_id: str
    vote_type: VoteType
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate vote data after initialization."""
        if not self.comment_id:
            raise ValueError("Vote must be associated with a comment")
        if not self.user_id:
            raise ValueError("Vote must belong to a user")
        if not isinstance(self.vote_type, VoteType):
            raise ValueError(f"Invalid vote type: {self.vote_type}. Must be 'upvote' or 'downvote'")

    def toggle_vote(self) -> None:
        """Toggle the vote between upvote and downvote."""
        self.vote_type = VoteType.DOWNVOTE if self.vote_type == VoteType.UPVOTE else VoteType.UPVOTE
        self.updated_at = datetime.utcnow()
