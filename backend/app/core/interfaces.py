"""
Repository Interfaces

Abstract interfaces for data access following the Repository pattern.
These interfaces enable dependency injection and allow swapping between
PostgreSQL and DynamoDB implementations without changing business logic.
"""

from __future__ import annotations
from typing import Protocol, Optional, List
from datetime import datetime
from app.core.models import User, Deck, Card, Document, Topic, UserFCMToken, Notification, StudySession, CardReview


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

    def get_due_cards(
        self,
        deck_id: str,
        user_id: str,
        limit: int = 100,
    ) -> List[Card]:
        """
        Get cards due for review in a deck.

        Returns cards where next_review_date is NULL or <= current time.

        Args:
            deck_id: Deck to query
            user_id: User ID for authorization
            limit: Maximum number of cards to return

        Returns:
            List of cards due for review
        """
        ...

    def update_review_status(
        self,
        card_id: str,
        ease_factor: float,
        interval_days: int,
        repetitions: int,
        next_review_date: datetime,
        is_learning: bool,
    ) -> None:
        """
        Update card's spaced repetition parameters after review.

        Args:
            card_id: Card to update
            ease_factor: New ease factor from SM-2 algorithm
            interval_days: Days until next review
            repetitions: Consecutive successful reviews
            next_review_date: When card is due for review
            is_learning: Whether card is in learning phase
        """
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


class UserFCMTokenRepository(Protocol):
    """Abstract interface for FCM token data access."""

    def get(self, token_id: str) -> Optional[UserFCMToken]:
        """
        Get FCM token by ID.

        Args:
            token_id: Token identifier

        Returns:
            UserFCMToken if found, None otherwise
        """
        ...

    def get_by_token(self, fcm_token: str) -> Optional[UserFCMToken]:
        """
        Get FCM token by token string.

        Args:
            fcm_token: FCM token string

        Returns:
            UserFCMToken if found, None otherwise
        """
        ...

    def get_by_user(self, user_id: str) -> List[UserFCMToken]:
        """
        Get all FCM tokens for a user.

        Args:
            user_id: User identifier

        Returns:
            List of user's FCM tokens
        """
        ...

    def get_active_tokens(self, user_id: str) -> List[UserFCMToken]:
        """
        Get all active FCM tokens for a user.

        Args:
            user_id: User identifier

        Returns:
            List of active FCM tokens
        """
        ...

    def create(self, token: UserFCMToken) -> UserFCMToken:
        """
        Create a new FCM token.

        Args:
            token: Token to create

        Returns:
            Created token with ID
        """
        ...

    def update(self, token: UserFCMToken) -> UserFCMToken:
        """
        Update existing FCM token.

        Args:
            token: Token with updated data

        Returns:
            Updated token
        """
        ...

    def deactivate_token(self, token_id: str) -> None:
        """
        Deactivate a single FCM token.

        Args:
            token_id: Token to deactivate
        """
        ...

    def deactivate_tokens(self, fcm_tokens: List[str]) -> None:
        """
        Deactivate multiple FCM tokens by token string.

        Used to clean up invalid tokens after FCM send failures.

        Args:
            fcm_tokens: List of FCM token strings to deactivate
        """
        ...

    def delete(self, token_id: str) -> None:
        """
        Delete FCM token by ID.

        Args:
            token_id: Token to delete
        """
        ...


class NotificationRepository(Protocol):
    """Abstract interface for notification data access."""

    def get(self, notification_id: str) -> Optional[Notification]:
        """
        Get notification by ID.

        Args:
            notification_id: Notification identifier

        Returns:
            Notification if found, None otherwise
        """
        ...

    def get_by_user(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: User identifier
            unread_only: If True, only return unread notifications
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of notifications
        """
        ...

    def create(
        self,
        user_id: str,
        type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        metadata: Optional[dict] = None,
        image_url: Optional[str] = None,
        fcm_message_id: Optional[str] = None,
    ) -> Notification:
        """
        Create a new notification.

        Args:
            user_id: User identifier
            type: Notification type (info, success, warning, error)
            title: Notification title
            message: Notification message
            action_url: Optional URL to navigate to
            metadata: Optional metadata dictionary
            image_url: Optional image URL
            fcm_message_id: Optional FCM message ID

        Returns:
            Created notification
        """
        ...

    def mark_as_read(self, notification_id: str) -> None:
        """
        Mark a notification as read.

        Args:
            notification_id: Notification to mark as read
        """
        ...

    def mark_all_as_read(self, user_id: str) -> None:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User identifier
        """
        ...

    def count_unread(self, user_id: str) -> int:
        """
        Count unread notifications for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of unread notifications
        """
        ...

    def delete(self, notification_id: str) -> None:
        """
        Delete a notification.

        Args:
            notification_id: Notification to delete
        """
        ...


class StudySessionRepository(Protocol):
    """Abstract interface for study session data access."""

    def get(self, session_id: str) -> Optional[StudySession]:
        """
        Get session by ID.

        Args:
            session_id: Study session identifier

        Returns:
            StudySession if found, None otherwise
        """
        ...

    def create(self, session: StudySession) -> StudySession:
        """
        Create a new study session.

        Args:
            session: Study session to create

        Returns:
            Created session with ID
        """
        ...

    def update(self, session: StudySession) -> StudySession:
        """
        Update existing session.

        Args:
            session: Session with updated data

        Returns:
            Updated session
        """
        ...

    def get_active_session(self, user_id: str, deck_id: str) -> Optional[StudySession]:
        """
        Get active (not ended) session for user and deck.

        Args:
            user_id: User identifier
            deck_id: Deck identifier

        Returns:
            Active session if found, None otherwise
        """
        ...

    def get_by_user(
        self,
        user_id: str,
        deck_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[StudySession]:
        """
        List study sessions for a user.

        Args:
            user_id: User identifier
            deck_id: Optional deck filter
            limit: Maximum number of results

        Returns:
            List of user's study sessions
        """
        ...


class CardReviewRepository(Protocol):
    """Abstract interface for card review data access."""

    def create(self, review: CardReview) -> CardReview:
        """
        Create a new card review record.

        Args:
            review: Card review to create

        Returns:
            Created review with ID
        """
        ...
