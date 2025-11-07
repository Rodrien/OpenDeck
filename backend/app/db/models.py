"""
SQLAlchemy ORM Models

Database models for PostgreSQL implementation.
These map to database tables and handle persistence.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    Table,
    Boolean,
    Numeric,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.models import DifficultyLevel, DocumentStatus, VoteType


# Junction table for deck-topic many-to-many relationship
deck_topics = Table(
    "deck_topics",
    Base.metadata,
    Column("deck_id", String(36), ForeignKey("decks.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", String(36), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)

# Junction table for card-topic many-to-many relationship
card_topics = Table(
    "card_topics",
    Base.metadata,
    Column("card_id", String(36), ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True),
    Column("topic_id", String(36), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)


class UserModel(Base):
    """User table model."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    decks = relationship("DeckModel", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("DocumentModel", back_populates="user", cascade="all, delete-orphan")


class DeckModel(Base):
    """Deck table model."""

    __tablename__ = "decks"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category = Column(String(100), nullable=False, index=True)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False, index=True)
    card_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="decks")
    cards = relationship("CardModel", back_populates="deck", cascade="all, delete-orphan")
    topics = relationship("TopicModel", secondary=deck_topics, back_populates="decks")


class CardModel(Base):
    """Flashcard table model."""

    __tablename__ = "cards"

    id = Column(String(36), primary_key=True)
    deck_id = Column(String(36), ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    source = Column(String(500), nullable=False)  # REQUIRED: Document reference
    source_url = Column(String(500), nullable=True)

    # Spaced repetition fields
    ease_factor = Column(Numeric(precision=4, scale=2), nullable=False, default=2.5)
    interval_days = Column(Integer, nullable=False, default=0)
    repetitions = Column(Integer, nullable=False, default=0)
    next_review_date = Column(DateTime, nullable=True)
    is_learning = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    deck = relationship("DeckModel", back_populates="cards")
    topics = relationship("TopicModel", secondary=card_topics, back_populates="cards")
    reviews = relationship("CardReviewModel", back_populates="card", cascade="all, delete-orphan")


class TopicModel(Base):
    """Topic table model."""

    __tablename__ = "topics"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    decks = relationship("DeckModel", secondary=deck_topics, back_populates="topics")
    cards = relationship("CardModel", secondary=card_topics, back_populates="topics")


class DocumentModel(Base):
    """Document table model."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False, index=True)
    deck_id = Column(String(36), ForeignKey("decks.id", ondelete="SET NULL"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="documents")


class UserFCMTokenModel(Base):
    """User FCM Token table model."""

    __tablename__ = "user_fcm_tokens"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    fcm_token = Column(Text, unique=True, nullable=False)
    device_type = Column(String(20), nullable=False)
    device_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NotificationModel(Base):
    """Notification table model."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(512), nullable=True)
    notification_metadata = Column('metadata', JSON, nullable=True)  # Using 'notification_metadata' to avoid SQLAlchemy reserved name
    image_url = Column(String(512), nullable=True)
    read = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)
    fcm_message_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CardReviewModel(Base):
    """Card Review table model."""

    __tablename__ = "card_reviews"

    id = Column(String(36), primary_key=True)
    card_id = Column(String(36), ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    review_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    quality = Column(Integer, nullable=False)
    ease_factor = Column(Numeric(precision=4, scale=2), nullable=False)
    interval_days = Column(Integer, nullable=False)
    repetitions = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint('quality >= 0 AND quality <= 5', name='check_quality_range'),
    )

    # Relationships
    card = relationship("CardModel", back_populates="reviews")


class StudySessionModel(Base):
    """Study Session table model."""

    __tablename__ = "study_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    deck_id = Column(String(36), ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    cards_reviewed = Column(Integer, nullable=False, default=0)
    cards_correct = Column(Integer, nullable=False, default=0)
    cards_incorrect = Column(Integer, nullable=False, default=0)
    total_duration_seconds = Column(Integer, nullable=True)
    session_type = Column(String(50), nullable=False, default='review')
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DeckCommentModel(Base):
    """Deck Comment table model."""

    __tablename__ = "deck_comments"

    id = Column(String(36), primary_key=True)
    deck_id = Column(String(36), ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_comment_id = Column(String(36), ForeignKey("deck_comments.id", ondelete="CASCADE"), nullable=True, index=True)
    is_edited = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint('length(content) <= 5000', name='check_comment_length'),
    )

    # Relationships
    user = relationship("UserModel", foreign_keys=[user_id])
    deck = relationship("DeckModel", foreign_keys=[deck_id])
    parent_comment = relationship("DeckCommentModel", remote_side=[id], foreign_keys=[parent_comment_id])
    replies = relationship("DeckCommentModel", back_populates="parent_comment", foreign_keys=[parent_comment_id])
    votes = relationship("CommentVoteModel", back_populates="comment", cascade="all, delete-orphan")


class CommentVoteModel(Base):
    """Comment Vote table model."""

    __tablename__ = "comment_votes"

    id = Column(String(36), primary_key=True)
    comment_id = Column(String(36), ForeignKey("deck_comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vote_type = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("vote_type IN ('upvote', 'downvote')", name='check_vote_type'),
        # Unique constraint: one vote per user per comment
        CheckConstraint('1=1', name='uq_comment_user_vote'),  # Will be created as UniqueConstraint in migration
    )

    # Relationships
    comment = relationship("DeckCommentModel", back_populates="votes")
    user = relationship("UserModel", foreign_keys=[user_id])
