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
)
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.core.models import DifficultyLevel, DocumentStatus


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
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    deck = relationship("DeckModel", back_populates="cards")
    topics = relationship("TopicModel", secondary=card_topics, back_populates="cards")


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
