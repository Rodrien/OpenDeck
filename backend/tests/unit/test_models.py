"""Unit tests for domain models"""

import pytest
from datetime import datetime
from app.core.models import User, Deck, Card, Document, DifficultyLevel, DocumentStatus


class TestUserModel:
    """Test cases for User domain model."""

    def test_user_creation_valid(self):
        """Test creating a valid user."""
        user = User(
            id="test-id",
            email="test@example.com",
            name="Test User",
            password_hash="hashed_password"
        )

        assert user.id == "test-id"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.password_hash == "hashed_password"
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_user_invalid_email(self):
        """Test user creation with invalid email."""
        with pytest.raises(ValueError, match="Invalid email address"):
            User(
                id="test-id",
                email="invalid-email",
                name="Test User",
                password_hash="hashed_password"
            )

    def test_user_empty_name(self):
        """Test user creation with empty name."""
        with pytest.raises(ValueError, match="Name cannot be empty"):
            User(
                id="test-id",
                email="test@example.com",
                name="",
                password_hash="hashed_password"
            )


class TestDeckModel:
    """Test cases for Deck domain model."""

    def test_deck_creation_valid(self):
        """Test creating a valid deck."""
        deck = Deck(
            id="deck-id",
            user_id="user-id",
            title="Biology 101",
            description="Biology basics",
            category="Science",
            difficulty=DifficultyLevel.BEGINNER,
            card_count=5
        )

        assert deck.id == "deck-id"
        assert deck.user_id == "user-id"
        assert deck.title == "Biology 101"
        assert deck.difficulty == DifficultyLevel.BEGINNER
        assert deck.card_count == 5

    def test_deck_empty_title(self):
        """Test deck creation with empty title."""
        with pytest.raises(ValueError, match="Deck title cannot be empty"):
            Deck(
                id="deck-id",
                user_id="user-id",
                title="",
                description="Test",
                category="Test",
                difficulty=DifficultyLevel.BEGINNER
            )

    def test_deck_empty_user_id(self):
        """Test deck creation without user_id."""
        with pytest.raises(ValueError, match="Deck must belong to a user"):
            Deck(
                id="deck-id",
                user_id="",
                title="Test Deck",
                description="Test",
                category="Test",
                difficulty=DifficultyLevel.BEGINNER
            )


class TestCardModel:
    """Test cases for Card domain model."""

    def test_card_creation_valid(self):
        """Test creating a valid card with source attribution."""
        card = Card(
            id="card-id",
            deck_id="deck-id",
            question="What is photosynthesis?",
            answer="Process of converting light to energy",
            source="Biology101.pdf - Page 42, Section 3.2"
        )

        assert card.id == "card-id"
        assert card.deck_id == "deck-id"
        assert card.question == "What is photosynthesis?"
        assert card.source == "Biology101.pdf - Page 42, Section 3.2"

    def test_card_empty_question(self):
        """Test card creation with empty question."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            Card(
                id="card-id",
                deck_id="deck-id",
                question="",
                answer="Test answer",
                source="Test.pdf - Page 1"
            )

    def test_card_empty_answer(self):
        """Test card creation with empty answer."""
        with pytest.raises(ValueError, match="Answer cannot be empty"):
            Card(
                id="card-id",
                deck_id="deck-id",
                question="Test question?",
                answer="",
                source="Test.pdf - Page 1"
            )

    def test_card_missing_source(self):
        """Test card creation without source attribution (CRITICAL requirement)."""
        with pytest.raises(ValueError, match="Source attribution is required"):
            Card(
                id="card-id",
                deck_id="deck-id",
                question="Test question?",
                answer="Test answer",
                source=""
            )


class TestDocumentModel:
    """Test cases for Document domain model."""

    def test_document_creation_valid(self):
        """Test creating a valid document."""
        doc = Document(
            id="doc-id",
            user_id="user-id",
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            status=DocumentStatus.UPLOADED
        )

        assert doc.id == "doc-id"
        assert doc.filename == "test.pdf"
        assert doc.status == DocumentStatus.UPLOADED

    def test_document_mark_processing(self):
        """Test marking document as processing."""
        doc = Document(
            id="doc-id",
            user_id="user-id",
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            status=DocumentStatus.UPLOADED
        )

        doc.mark_processing()

        assert doc.status == DocumentStatus.PROCESSING

    def test_document_mark_completed(self):
        """Test marking document as completed."""
        doc = Document(
            id="doc-id",
            user_id="user-id",
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            status=DocumentStatus.PROCESSING
        )

        doc.mark_completed(deck_id="deck-123")

        assert doc.status == DocumentStatus.COMPLETED
        assert doc.deck_id == "deck-123"
        assert doc.processed_at is not None

    def test_document_mark_failed(self):
        """Test marking document as failed."""
        doc = Document(
            id="doc-id",
            user_id="user-id",
            filename="test.pdf",
            file_path="/path/to/test.pdf",
            status=DocumentStatus.PROCESSING
        )

        doc.mark_failed("Processing error occurred")

        assert doc.status == DocumentStatus.FAILED
        assert doc.error_message == "Processing error occurred"
