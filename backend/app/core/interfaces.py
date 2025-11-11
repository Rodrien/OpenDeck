"""
Repository Interfaces

Abstract interfaces for data access following the Repository pattern.
These interfaces enable dependency injection and allow swapping between
PostgreSQL and DynamoDB implementations without changing business logic.
"""

from __future__ import annotations
from typing import Protocol, Optional, List, Tuple
from datetime import datetime
from app.core.models import User, Deck, Card, Document, Topic, UserFCMToken, Notification, CardReview, StudySession, DeckComment, CommentVote, VoteType, CardReport, ReportStatus, Feedback, FeedbackStatus


class UserRepository(Protocol):
    """Abstract interface for user data access."""

    def get(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        ...

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        ...

    def get_by_oauth_id(self, provider: str, oauth_id: str) -> Optional[User]:
        """Get user by OAuth provider and ID."""
        ...

    def get_by_ids(self, user_ids: List[str]) -> List[User]:
        """
        Get multiple users by IDs in a single query.

        Useful for batch loading user information to avoid N+1 query problems.

        Args:
            user_ids: List of user IDs to retrieve

        Returns:
            List of users that exist (may be shorter than input list)
        """
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

    def get_by_id(self, deck_id: str) -> Optional[Deck]:
        """
        Get deck by ID without authorization check.

        Use this method when you need to verify deck existence
        without enforcing ownership (e.g., for commenting on any deck).

        Args:
            deck_id: Unique deck identifier

        Returns:
            Deck if found, None otherwise
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
            deck_id: Deck identifier
            user_id: User identifier (for authorization)
            limit: Maximum number of cards to return

        Returns:
            List of cards due for review, ordered by next_review_date
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
    ) -> Card:
        """
        Update card's spaced repetition parameters.

        Args:
            card_id: Card identifier
            ease_factor: New ease factor
            interval_days: New interval
            repetitions: New repetition count
            next_review_date: Next scheduled review date
            is_learning: Whether card is in learning phase

        Returns:
            Updated card
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


class CardReviewRepository(Protocol):
    """Abstract interface for card review data access."""

    def get(self, review_id: str) -> Optional[CardReview]:
        """
        Get card review by ID.

        Args:
            review_id: Review identifier

        Returns:
            CardReview if found, None otherwise
        """
        ...

    def get_by_card(
        self,
        card_id: str,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CardReview]:
        """
        Get review history for a specific card.

        Args:
            card_id: Card identifier
            user_id: User identifier (for authorization)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of card reviews ordered by review_date DESC
        """
        ...

    def get_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CardReview]:
        """
        Get all reviews for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of card reviews ordered by review_date DESC
        """
        ...

    def create(self, review: CardReview) -> CardReview:
        """
        Create a new card review.

        Args:
            review: Review to create

        Returns:
            Created review with ID
        """
        ...

    def delete(self, review_id: str) -> None:
        """
        Delete a card review.

        Args:
            review_id: Review to delete
        """
        ...


class StudySessionRepository(Protocol):
    """Abstract interface for study session data access."""

    def get(self, session_id: str) -> Optional[StudySession]:
        """
        Get study session by ID.

        Args:
            session_id: Session identifier

        Returns:
            StudySession if found, None otherwise
        """
        ...

    def get_by_user(
        self,
        user_id: str,
        deck_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StudySession]:
        """
        Get study sessions for a user.

        Args:
            user_id: User identifier
            deck_id: Optional deck filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of study sessions ordered by started_at DESC
        """
        ...

    def get_active_session(self, user_id: str, deck_id: str) -> Optional[StudySession]:
        """
        Get active (not ended) study session for a user and deck.

        Args:
            user_id: User identifier
            deck_id: Deck identifier

        Returns:
            Active session if found, None otherwise
        """
        ...

    def create(self, session: StudySession) -> StudySession:
        """
        Create a new study session.

        Args:
            session: Session to create

        Returns:
            Created session with ID
        """
        ...

    def update(self, session: StudySession) -> StudySession:
        """
        Update existing study session.

        Args:
            session: Session with updated data

        Returns:
            Updated session
        """
        ...

    def delete(self, session_id: str) -> None:
        """
        Delete a study session.

        Args:
            session_id: Session to delete
        """
        ...


class DeckCommentRepository(Protocol):
    """Abstract interface for deck comment data access."""

    def get(self, comment_id: str) -> Optional[DeckComment]:
        """
        Get comment by ID.

        Args:
            comment_id: Comment identifier

        Returns:
            DeckComment if found, None otherwise
        """
        ...

    def get_by_deck(
        self,
        deck_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[DeckComment], int]:
        """
        Get comments for a deck with pagination.

        Args:
            deck_id: Deck identifier
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Tuple of (list of comments ordered by created_at DESC, total count)
        """
        ...

    def get_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DeckComment]:
        """
        Get comments by a user.

        Args:
            user_id: User identifier
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of comments ordered by created_at DESC
        """
        ...

    def get_replies(
        self,
        parent_comment_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DeckComment]:
        """
        Get replies to a comment.

        Args:
            parent_comment_id: Parent comment identifier
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of reply comments ordered by created_at ASC
        """
        ...

    def create(self, comment: DeckComment) -> DeckComment:
        """
        Create a new comment.

        Args:
            comment: Comment to create

        Returns:
            Created comment with ID
        """
        ...

    def update(self, comment: DeckComment) -> DeckComment:
        """
        Update existing comment.

        Args:
            comment: Comment with updated data

        Returns:
            Updated comment
        """
        ...

    def delete(self, comment_id: str, user_id: str) -> None:
        """
        Delete a comment.

        Args:
            comment_id: Comment to delete
            user_id: User ID for authorization check
        """
        ...

    def count_by_deck(self, deck_id: str) -> int:
        """
        Count total comments for a deck.

        Args:
            deck_id: Deck identifier

        Returns:
            Total number of comments
        """
        ...


class CommentVoteRepository(Protocol):
    """Abstract interface for comment vote data access."""

    def get(self, vote_id: str) -> Optional[CommentVote]:
        """
        Get vote by ID.

        Args:
            vote_id: Vote identifier

        Returns:
            CommentVote if found, None otherwise
        """
        ...

    def get_user_vote(self, comment_id: str, user_id: str) -> Optional[CommentVote]:
        """
        Get user's vote on a specific comment.

        Args:
            comment_id: Comment identifier
            user_id: User identifier

        Returns:
            CommentVote if user voted, None otherwise
        """
        ...

    def get_vote_counts(self, comment_id: str) -> Tuple[int, int]:
        """
        Get upvote and downvote counts for a comment.

        Args:
            comment_id: Comment identifier

        Returns:
            Tuple of (upvotes, downvotes)
        """
        ...

    def get_vote_counts_batch(self, comment_ids: List[str]) -> dict[str, Tuple[int, int]]:
        """
        Get vote counts for multiple comments in a single query.

        Args:
            comment_ids: List of comment identifiers

        Returns:
            Dictionary mapping comment_id to (upvotes, downvotes)
        """
        ...

    def get_user_votes_batch(self, comment_ids: List[str], user_id: str) -> dict[str, VoteType]:
        """
        Get user's votes for multiple comments in a single query.

        Args:
            comment_ids: List of comment identifiers
            user_id: User identifier

        Returns:
            Dictionary mapping comment_id to VoteType
        """
        ...

    def create_or_update(self, vote: CommentVote) -> Optional[CommentVote]:
        """
        Create a new vote or update existing vote.

        If user already voted, update the vote type.
        If user is changing to the same vote type, remove the vote.

        Args:
            vote: Vote to create or update

        Returns:
            Created/updated vote, or None if vote was removed (toggle off)
        """
        ...

    def delete(self, vote_id: str, user_id: str) -> None:
        """
        Delete a vote.

        Args:
            vote_id: Vote to delete
            user_id: User ID for authorization check
        """
        ...

    def delete_by_comment_user(self, comment_id: str, user_id: str) -> None:
        """
        Delete user's vote on a comment.

        Args:
            comment_id: Comment identifier
            user_id: User identifier
        """
        ...


class CardReportRepository(Protocol):
    """Abstract interface for card report data access."""

    def get(self, report_id: str) -> Optional[CardReport]:
        """
        Get report by ID.

        Args:
            report_id: Report identifier

        Returns:
            CardReport if found, None otherwise
        """
        ...

    def get_by_card_id(self, card_id: str) -> List[CardReport]:
        """
        Get all reports for a specific card.

        Args:
            card_id: Card identifier

        Returns:
            List of reports for the card, ordered by created_at DESC
        """
        ...

    def get_by_user_id(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CardReport]:
        """
        Get all reports created by a user.

        Args:
            user_id: User identifier
            skip: Number of results to skip
            limit: Maximum number of results

        Returns:
            List of reports ordered by created_at DESC
        """
        ...

    def create(
        self,
        card_id: str,
        user_id: str,
        reason: str,
    ) -> CardReport:
        """
        Create a new card report.

        Args:
            card_id: Card identifier
            user_id: User identifier
            reason: Reason for reporting the card

        Returns:
            Created report with ID
        """
        ...

    def update_status(
        self,
        report_id: str,
        status: ReportStatus,
        reviewed_by: Optional[str] = None,
    ) -> CardReport:
        """
        Update report status and mark as reviewed.

        Args:
            report_id: Report identifier
            status: New status
            reviewed_by: User ID of reviewer (optional)

        Returns:
            Updated report

        Raises:
            ValueError: If report not found
        """
        ...


class FeedbackRepository(Protocol):
    """Abstract interface for feedback data access."""

    def get(self, feedback_id: str) -> Optional[Feedback]:
        """
        Get feedback by ID.

        Args:
            feedback_id: Feedback identifier

        Returns:
            Feedback if found, None otherwise
        """
        ...

    def list(
        self,
        status: Optional[FeedbackStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Feedback]:
        """
        List all feedback with optional status filter.

        Args:
            status: Optional status filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of feedback ordered by created_at DESC
        """
        ...

    def create(self, feedback: Feedback) -> Feedback:
        """
        Create new feedback.

        Args:
            feedback: Feedback to create

        Returns:
            Created feedback with ID
        """
        ...

    def update_status(
        self,
        feedback_id: str,
        status: FeedbackStatus,
    ) -> Feedback:
        """
        Update feedback status.

        Args:
            feedback_id: Feedback identifier
            status: New status

        Returns:
            Updated feedback

        Raises:
            ValueError: If feedback not found
        """
        ...
