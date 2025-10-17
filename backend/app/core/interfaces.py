"""
Repository Interfaces

Abstract interfaces for data access following the Repository pattern.
These interfaces enable dependency injection and allow swapping between
PostgreSQL and DynamoDB implementations without changing business logic.
"""

from typing import Protocol, Optional
from app.core.models import User, Deck, Card, Document


class UserRepository(Protocol):
    """Abstract interface for user data access."""

    def get(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        ...

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        ...

    def create(self, user: User) -> User:
        """Create a new user."""
        ...

    def update(self, user: User) -> User:
        """Update existing user."""
        ...

    def delete(self, user_id: str) -> None:
        """Delete user by ID."""
        ...


class DeckRepository(Protocol):
    """Abstract interface for deck data access."""

    def get(self, deck_id: str, user_id: str) -> Optional[Deck]:
        """
        Get deck by ID.

        Args:
            deck_id: Unique deck identifier
            user_id: User ID for authorization check

        Returns:
            Deck if found and belongs to user, None otherwise
        """
        ...

    def list(
        self,
        user_id: str,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Deck]:
        """
        List decks for a user with optional filters.

        Args:
            user_id: User ID to filter by
            category: Optional category filter
            difficulty: Optional difficulty filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of decks matching filters
        """
        ...

    def create(self, deck: Deck) -> Deck:
        """Create a new deck."""
        ...

    def update(self, deck: Deck) -> Deck:
        """Update existing deck."""
        ...

    def delete(self, deck_id: str, user_id: str) -> None:
        """
        Delete deck by ID.

        Args:
            deck_id: Deck to delete
            user_id: User ID for authorization check
        """
        ...


class CardRepository(Protocol):
    """Abstract interface for flashcard data access."""

    def get(self, card_id: str) -> Optional[Card]:
        """Get card by ID."""
        ...

    def list_by_deck(self, deck_id: str, limit: int = 100, offset: int = 0) -> list[Card]:
        """
        List all cards in a deck.

        Args:
            deck_id: Deck ID to filter by
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of cards in the deck
        """
        ...

    def create(self, card: Card) -> Card:
        """Create a new card."""
        ...

    def create_many(self, cards: list[Card]) -> list[Card]:
        """
        Create multiple cards in a single operation.

        Useful for batch importing AI-generated flashcards.

        Args:
            cards: List of cards to create

        Returns:
            List of created cards with IDs
        """
        ...

    def update(self, card: Card) -> Card:
        """Update existing card."""
        ...

    def delete(self, card_id: str) -> None:
        """Delete card by ID."""
        ...


class DocumentRepository(Protocol):
    """Abstract interface for document data access."""

    def get(self, doc_id: str, user_id: str) -> Optional[Document]:
        """
        Get document by ID.

        Args:
            doc_id: Document identifier
            user_id: User ID for authorization check

        Returns:
            Document if found and belongs to user, None otherwise
        """
        ...

    def list(self, user_id: str, limit: int = 100, offset: int = 0) -> list[Document]:
        """
        List documents for a user.

        Args:
            user_id: User ID to filter by
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of user's documents
        """
        ...

    def create(self, document: Document) -> Document:
        """Create a new document record."""
        ...

    def update(self, document: Document) -> Document:
        """Update existing document."""
        ...

    def delete(self, doc_id: str, user_id: str) -> None:
        """
        Delete document by ID.

        Args:
            doc_id: Document to delete
            user_id: User ID for authorization check
        """
        ...
