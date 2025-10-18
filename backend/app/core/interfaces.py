"""
Repository Interfaces

Abstract interfaces for data access following the Repository pattern.
These interfaces enable dependency injection and allow swapping between
PostgreSQL and DynamoDB implementations without changing business logic.
"""

from __future__ import annotations
from typing import Protocol, Optional, List
from app.core.models import User, Deck, Card, Document, Topic


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
        topic_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Deck]:
        """
        List decks for a user with optional filters.

        Args:
            user_id: User ID to filter by
            category: Optional category filter
            difficulty: Optional difficulty filter
            topic_id: Optional topic filter
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

    def list_by_deck(
        self,
        deck_id: str,
        topic_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Card]:
        """
        List all cards in a deck.

        Args:
            deck_id: Deck ID to filter by
            topic_id: Optional topic filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of cards in the deck
        """
        ...

    def list_by_topic(
        self,
        topic_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Card]:
        """
        List all cards associated with a topic.

        Args:
            topic_id: Topic ID to filter by
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of cards for the topic
        """
        ...

    def create(self, card: Card) -> Card:
        """Create a new card."""
        ...

    def create_many(self, cards: List[Card]) -> List[Card]:
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

    def list(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Document]:
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


class TopicRepository(Protocol):
    """Abstract interface for topic data access."""

    def get(self, topic_id: str) -> Optional[Topic]:
        """
        Get topic by ID.

        Args:
            topic_id: Topic identifier

        Returns:
            Topic if found, None otherwise
        """
        ...

    def get_by_name(self, name: str) -> Optional[Topic]:
        """
        Get topic by name.

        Args:
            name: Topic name

        Returns:
            Topic if found, None otherwise
        """
        ...

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Topic]:
        """
        List all topics.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of topics
        """
        ...

    def create(self, topic: Topic) -> Topic:
        """
        Create a new topic.

        Args:
            topic: Topic to create

        Returns:
            Created topic with ID
        """
        ...

    def update(self, topic: Topic) -> Topic:
        """
        Update existing topic.

        Args:
            topic: Topic with updated data

        Returns:
            Updated topic
        """
        ...

    def delete(self, topic_id: str) -> None:
        """
        Delete topic by ID.

        Args:
            topic_id: Topic to delete
        """
        ...

    def get_topics_for_deck(self, deck_id: str) -> List[Topic]:
        """
        Get all topics associated with a deck.

        Args:
            deck_id: Deck identifier

        Returns:
            List of topics for the deck
        """
        ...

    def get_topics_for_card(self, card_id: str) -> List[Topic]:
        """
        Get all topics associated with a card.

        Args:
            card_id: Card identifier

        Returns:
            List of topics for the card
        """
        ...

    def associate_deck_topic(self, deck_id: str, topic_id: str) -> None:
        """
        Associate a topic with a deck.

        Args:
            deck_id: Deck identifier
            topic_id: Topic identifier
        """
        ...

    def dissociate_deck_topic(self, deck_id: str, topic_id: str) -> None:
        """
        Remove topic association from a deck.

        Args:
            deck_id: Deck identifier
            topic_id: Topic identifier
        """
        ...

    def associate_card_topic(self, card_id: str, topic_id: str) -> None:
        """
        Associate a topic with a card.

        Args:
            card_id: Card identifier
            topic_id: Topic identifier
        """
        ...

    def dissociate_card_topic(self, card_id: str, topic_id: str) -> None:
        """
        Remove topic association from a card.

        Args:
            card_id: Card identifier
            topic_id: Topic identifier
        """
        ...
