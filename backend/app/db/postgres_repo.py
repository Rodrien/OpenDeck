"""
PostgreSQL Repository Implementations

Concrete implementations of repository interfaces using SQLAlchemy.
"""

from __future__ import annotations

import uuid
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.core.models import User, Deck, Card, Document, Topic, UserFCMToken, Notification, CardReview, StudySession, DeckComment, CommentVote, VoteType
from app.core.interfaces import (
    UserRepository,
    DeckRepository,
    CardRepository,
    DocumentRepository,
    TopicRepository,
    UserFCMTokenRepository,
    NotificationRepository,
    CardReviewRepository,
    StudySessionRepository,
    DeckCommentRepository,
    CommentVoteRepository,
)
from app.db.models import (
    UserModel,
    DeckModel,
    CardModel,
    DocumentModel,
    TopicModel,
    UserFCMTokenModel,
    NotificationModel,
    CardReviewModel,
    StudySessionModel,
    DeckCommentModel,
    CommentVoteModel,
    deck_topics,
    card_topics,
)


def _generate_id() -> str:
    """Generate a unique ID for entities."""
    return str(uuid.uuid4())


class PostgresUserRepo:
    """PostgreSQL implementation of UserRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        model = self.session.query(UserModel).filter_by(id=user_id).first()
        return self._to_domain(model) if model else None

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        model = self.session.query(UserModel).filter_by(email=email).first()
        return self._to_domain(model) if model else None

    def get_by_ids(self, user_ids: List[str]) -> List[User]:
        """
        Get multiple users by IDs in a single query.

        Useful for batch loading user information to avoid N+1 query problems.

        Args:
            user_ids: List of user IDs to retrieve

        Returns:
            List of users that exist (may be shorter than input list)
        """
        if not user_ids:
            return []

        models = (
            self.session.query(UserModel)
            .filter(UserModel.id.in_(user_ids))
            .all()
        )
        return [self._to_domain(model) for model in models]

    def create(self, user: User) -> User:
        """Create a new user."""
        if not user.id:
            user.id = _generate_id()

        model = UserModel(
            id=user.id,
            email=user.email,
            name=user.name,
            password_hash=user.password_hash,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, user: User) -> User:
        """Update existing user."""
        user.updated_at = datetime.utcnow()
        model = self.session.query(UserModel).filter_by(id=user.id).first()
        if not model:
            raise ValueError(f"User {user.id} not found")

        model.email = user.email
        model.name = user.name
        model.password_hash = user.password_hash
        model.updated_at = user.updated_at

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, user_id: str) -> None:
        """Delete user by ID."""
        model = self.session.query(UserModel).filter_by(id=user_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        """Convert SQLAlchemy model to domain model."""
        return User(
            id=model.id,
            email=model.email,
            name=model.name,
            password_hash=model.password_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class PostgresDeckRepo:
    """PostgreSQL implementation of DeckRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, deck_id: str, user_id: str) -> Optional[Deck]:
        """Get deck by ID with authorization check."""
        model = (
            self.session.query(DeckModel)
            .filter_by(id=deck_id, user_id=user_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def list(
        self,
        user_id: str,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        topic_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Deck]:
        """List decks for a user with optional filters."""
        query = self.session.query(DeckModel).filter_by(user_id=user_id)

        if category:
            query = query.filter_by(category=category)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        if topic_id:
            query = query.join(DeckModel.topics).filter(TopicModel.id == topic_id)

        models = query.order_by(DeckModel.created_at.desc()).limit(limit).offset(offset).all()
        return [self._to_domain(model) for model in models]

    def create(self, deck: Deck) -> Deck:
        """Create a new deck."""
        if not deck.id:
            deck.id = _generate_id()

        model = DeckModel(
            id=deck.id,
            user_id=deck.user_id,
            title=deck.title,
            description=deck.description,
            category=deck.category,
            difficulty=deck.difficulty,
            card_count=deck.card_count,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, deck: Deck) -> Deck:
        """Update existing deck."""
        deck.updated_at = datetime.utcnow()
        model = self.session.query(DeckModel).filter_by(id=deck.id, user_id=deck.user_id).first()
        if not model:
            raise ValueError(f"Deck {deck.id} not found or access denied")

        model.title = deck.title
        model.description = deck.description
        model.category = deck.category
        model.difficulty = deck.difficulty
        model.card_count = deck.card_count
        model.updated_at = deck.updated_at

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, deck_id: str, user_id: str) -> None:
        """Delete deck by ID with authorization check."""
        model = self.session.query(DeckModel).filter_by(id=deck_id, user_id=user_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()

    @staticmethod
    def _to_domain(model: DeckModel) -> Deck:
        """Convert SQLAlchemy model to domain model."""
        return Deck(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            description=model.description,
            category=model.category,
            difficulty=model.difficulty,
            card_count=model.card_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class PostgresCardRepo:
    """PostgreSQL implementation of CardRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, card_id: str) -> Optional[Card]:
        """Get card by ID."""
        model = self.session.query(CardModel).filter_by(id=card_id).first()
        return self._to_domain(model) if model else None

    def list_by_deck(
        self,
        deck_id: str,
        topic_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Card]:
        """List all cards in a deck."""
        query = self.session.query(CardModel).filter_by(deck_id=deck_id)

        if topic_id:
            query = query.join(CardModel.topics).filter(TopicModel.id == topic_id)

        models = query.order_by(CardModel.created_at).limit(limit).offset(offset).all()
        return [self._to_domain(model) for model in models]

    def list_by_topic(
        self,
        topic_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Card]:
        """List all cards associated with a topic."""
        models = (
            self.session.query(CardModel)
            .join(CardModel.topics)
            .filter(TopicModel.id == topic_id)
            .order_by(CardModel.created_at)
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def create(self, card: Card) -> Card:
        """Create a new card."""
        if not card.id:
            card.id = _generate_id()

        model = CardModel(
            id=card.id,
            deck_id=card.deck_id,
            question=card.question,
            answer=card.answer,
            source=card.source,
            source_url=card.source_url,
            ease_factor=card.ease_factor,
            interval_days=card.interval_days,
            repetitions=card.repetitions,
            next_review_date=card.next_review_date,
            is_learning=card.is_learning,
            created_at=card.created_at,
            updated_at=card.updated_at,
        )
        self.session.add(model)
        self._update_deck_count(card.deck_id, increment=1)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def create_many(self, cards: List[Card]) -> List[Card]:
        """Create multiple cards in a single operation."""
        if not cards:
            return []

        deck_id = cards[0].deck_id
        models = []

        for card in cards:
            if not card.id:
                card.id = _generate_id()

            model = CardModel(
                id=card.id,
                deck_id=card.deck_id,
                question=card.question,
                answer=card.answer,
                source=card.source,
                source_url=card.source_url,
                ease_factor=card.ease_factor,
                interval_days=card.interval_days,
                repetitions=card.repetitions,
                next_review_date=card.next_review_date,
                is_learning=card.is_learning,
                created_at=card.created_at,
                updated_at=card.updated_at,
            )
            models.append(model)

        self.session.bulk_save_objects(models, return_defaults=True)
        self._update_deck_count(deck_id, increment=len(cards))
        self.session.commit()

        return [self._to_domain(model) for model in models]

    def update(self, card: Card) -> Card:
        """Update existing card."""
        card.updated_at = datetime.utcnow()
        model = self.session.query(CardModel).filter_by(id=card.id).first()
        if not model:
            raise ValueError(f"Card {card.id} not found")

        model.question = card.question
        model.answer = card.answer
        model.source = card.source
        model.source_url = card.source_url
        model.updated_at = card.updated_at

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, card_id: str) -> None:
        """Delete card by ID."""
        model = self.session.query(CardModel).filter_by(id=card_id).first()
        if model:
            deck_id = model.deck_id
            self.session.delete(model)
            self._update_deck_count(deck_id, increment=-1)
            self.session.commit()

    def _update_deck_count(self, deck_id: str, increment: int) -> None:
        """Update the card count for a deck."""
        deck = self.session.query(DeckModel).filter_by(id=deck_id).first()
        if deck:
            deck.card_count = max(0, deck.card_count + increment)

    def get_due_cards(
        self,
        deck_id: str,
        user_id: str,
        limit: int = 100,
    ) -> List[Card]:
        """Get cards due for review in a deck."""
        # Verify user has access to the deck
        deck = self.session.query(DeckModel).filter_by(id=deck_id, user_id=user_id).first()
        if not deck:
            return []

        # Get cards where next_review_date is NULL or <= now
        now = datetime.utcnow()
        models = (
            self.session.query(CardModel)
            .filter(
                CardModel.deck_id == deck_id,
                (CardModel.next_review_date.is_(None)) | (CardModel.next_review_date <= now)
            )
            .order_by(CardModel.next_review_date.nullsfirst())
            .limit(limit)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def update_review_status(
        self,
        card_id: str,
        ease_factor: float,
        interval_days: int,
        repetitions: int,
        next_review_date: datetime,
        is_learning: bool,
    ) -> Card:
        """Update card's spaced repetition parameters."""
        model = self.session.query(CardModel).filter_by(id=card_id).first()
        if not model:
            raise ValueError(f"Card {card_id} not found")

        model.ease_factor = ease_factor
        model.interval_days = interval_days
        model.repetitions = repetitions
        model.next_review_date = next_review_date
        model.is_learning = is_learning
        model.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: CardModel) -> Card:
        """Convert SQLAlchemy model to domain model."""
        return Card(
            id=model.id,
            deck_id=model.deck_id,
            question=model.question,
            answer=model.answer,
            source=model.source,
            source_url=model.source_url,
            ease_factor=float(model.ease_factor) if model.ease_factor else 2.5,
            interval_days=model.interval_days if model.interval_days is not None else 0,
            repetitions=model.repetitions if model.repetitions is not None else 0,
            next_review_date=model.next_review_date,
            is_learning=model.is_learning if model.is_learning is not None else True,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class PostgresDocumentRepo:
    """PostgreSQL implementation of DocumentRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, doc_id: str, user_id: str) -> Optional[Document]:
        """Get document by ID with authorization check."""
        model = (
            self.session.query(DocumentModel)
            .filter_by(id=doc_id, user_id=user_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_by_ids(self, doc_ids: List[str], user_id: str) -> List[Document]:
        """
        Get multiple documents by IDs with authorization check.

        Args:
            doc_ids: List of document IDs
            user_id: User ID for authorization

        Returns:
            List of documents that exist and belong to the user
        """
        models = (
            self.session.query(DocumentModel)
            .filter(DocumentModel.id.in_(doc_ids))
            .filter_by(user_id=user_id)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def list(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Document]:
        """List documents for a user."""
        models = (
            self.session.query(DocumentModel)
            .filter_by(user_id=user_id)
            .order_by(DocumentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def create(self, document: Document) -> Document:
        """Create a new document record."""
        if not document.id:
            document.id = _generate_id()

        model = DocumentModel(
            id=document.id,
            user_id=document.user_id,
            filename=document.filename,
            file_path=document.file_path,
            status=document.status,
            deck_id=document.deck_id,
            processed_at=document.processed_at,
            error_message=document.error_message,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, document: Document) -> Document:
        """Update existing document."""
        document.updated_at = datetime.utcnow()
        model = (
            self.session.query(DocumentModel)
            .filter_by(id=document.id, user_id=document.user_id)
            .first()
        )
        if not model:
            raise ValueError(f"Document {document.id} not found or access denied")

        model.status = document.status
        model.deck_id = document.deck_id
        model.processed_at = document.processed_at
        model.error_message = document.error_message
        model.updated_at = document.updated_at

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, doc_id: str, user_id: str) -> None:
        """Delete document by ID with authorization check."""
        model = (
            self.session.query(DocumentModel)
            .filter_by(id=doc_id, user_id=user_id)
            .first()
        )
        if model:
            self.session.delete(model)
            self.session.commit()

    @staticmethod
    def _to_domain(model: DocumentModel) -> Document:
        """Convert SQLAlchemy model to domain model."""
        return Document(
            id=model.id,
            user_id=model.user_id,
            filename=model.filename,
            file_path=model.file_path,
            status=model.status,
            deck_id=model.deck_id,
            processed_at=model.processed_at,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class PostgresTopicRepo:
    """PostgreSQL implementation of TopicRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, topic_id: str) -> Optional[Topic]:
        """Get topic by ID."""
        model = self.session.query(TopicModel).filter_by(id=topic_id).first()
        return self._to_domain(model) if model else None

    def get_by_name(self, name: str) -> Optional[Topic]:
        """Get topic by name."""
        model = self.session.query(TopicModel).filter_by(name=name).first()
        return self._to_domain(model) if model else None

    def list(self, limit: int = 100, offset: int = 0) -> List[Topic]:
        """List all topics."""
        models = (
            self.session.query(TopicModel)
            .order_by(TopicModel.name)
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def create(self, topic: Topic) -> Topic:
        """Create a new topic."""
        if not topic.id:
            topic.id = _generate_id()

        model = TopicModel(
            id=topic.id,
            name=topic.name,
            description=topic.description,
            created_at=topic.created_at,
            updated_at=topic.updated_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, topic: Topic) -> Topic:
        """Update existing topic."""
        topic.updated_at = datetime.utcnow()
        model = self.session.query(TopicModel).filter_by(id=topic.id).first()
        if not model:
            raise ValueError(f"Topic {topic.id} not found")

        model.name = topic.name
        model.description = topic.description
        model.updated_at = topic.updated_at

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, topic_id: str) -> None:
        """Delete topic by ID."""
        model = self.session.query(TopicModel).filter_by(id=topic_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()

    def get_topics_for_deck(self, deck_id: str) -> List[Topic]:
        """Get all topics associated with a deck."""
        models = (
            self.session.query(TopicModel)
            .join(deck_topics)
            .filter(deck_topics.c.deck_id == deck_id)
            .order_by(TopicModel.name)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def get_topics_for_card(self, card_id: str) -> List[Topic]:
        """Get all topics associated with a card."""
        models = (
            self.session.query(TopicModel)
            .join(card_topics)
            .filter(card_topics.c.card_id == card_id)
            .order_by(TopicModel.name)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def associate_deck_topic(self, deck_id: str, topic_id: str) -> None:
        """Associate a topic with a deck."""
        # Check if association already exists
        exists = (
            self.session.query(deck_topics)
            .filter_by(deck_id=deck_id, topic_id=topic_id)
            .first()
        )
        if not exists:
            stmt = deck_topics.insert().values(
                deck_id=deck_id,
                topic_id=topic_id,
                created_at=datetime.utcnow(),
            )
            self.session.execute(stmt)
            self.session.commit()

    def dissociate_deck_topic(self, deck_id: str, topic_id: str) -> None:
        """Remove topic association from a deck."""
        stmt = deck_topics.delete().where(
            (deck_topics.c.deck_id == deck_id) & (deck_topics.c.topic_id == topic_id)
        )
        self.session.execute(stmt)
        self.session.commit()

    def associate_card_topic(self, card_id: str, topic_id: str) -> None:
        """Associate a topic with a card."""
        # Check if association already exists
        exists = (
            self.session.query(card_topics)
            .filter_by(card_id=card_id, topic_id=topic_id)
            .first()
        )
        if not exists:
            stmt = card_topics.insert().values(
                card_id=card_id,
                topic_id=topic_id,
                created_at=datetime.utcnow(),
            )
            self.session.execute(stmt)
            self.session.commit()

    def dissociate_card_topic(self, card_id: str, topic_id: str) -> None:
        """Remove topic association from a card."""
        stmt = card_topics.delete().where(
            (card_topics.c.card_id == card_id) & (card_topics.c.topic_id == topic_id)
        )
        self.session.execute(stmt)
        self.session.commit()

    @staticmethod
    def _to_domain(model: TopicModel) -> Topic:
        """Convert SQLAlchemy model to domain model."""
        return Topic(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class PostgresUserFCMTokenRepo:
    """PostgreSQL implementation of UserFCMTokenRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, token_id: str) -> Optional[UserFCMToken]:
        """Get FCM token by ID."""
        model = self.session.query(UserFCMTokenModel).filter_by(id=token_id).first()
        return self._to_domain(model) if model else None

    def get_by_token(self, fcm_token: str) -> Optional[UserFCMToken]:
        """Get FCM token by token string."""
        model = self.session.query(UserFCMTokenModel).filter_by(fcm_token=fcm_token).first()
        return self._to_domain(model) if model else None

    def get_by_user(self, user_id: str) -> List[UserFCMToken]:
        """Get all FCM tokens for a user."""
        models = (
            self.session.query(UserFCMTokenModel)
            .filter_by(user_id=user_id)
            .order_by(UserFCMTokenModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_active_tokens(self, user_id: str) -> List[UserFCMToken]:
        """Get all active FCM tokens for a user."""
        models = (
            self.session.query(UserFCMTokenModel)
            .filter_by(user_id=user_id, is_active=True)
            .order_by(UserFCMTokenModel.last_used_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, token: UserFCMToken) -> UserFCMToken:
        """Create a new FCM token."""
        if not token.id:
            token.id = _generate_id()

        # Check if token already exists
        existing = self.get_by_token(token.fcm_token)
        if existing:
            # Update existing token: reactivate and update last_used_at
            token.id = existing.id
            return self.update(token)

        model = UserFCMTokenModel(
            id=token.id,
            user_id=token.user_id,
            fcm_token=token.fcm_token,
            device_type=token.device_type,
            device_name=token.device_name,
            is_active=token.is_active,
            created_at=token.created_at,
            updated_at=token.updated_at,
            last_used_at=token.last_used_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, token: UserFCMToken) -> UserFCMToken:
        """Update existing FCM token."""
        token.updated_at = datetime.utcnow()
        model = self.session.query(UserFCMTokenModel).filter_by(id=token.id).first()
        if not model:
            raise ValueError(f"FCM token {token.id} not found")

        model.device_type = token.device_type
        model.device_name = token.device_name
        model.is_active = token.is_active
        model.updated_at = token.updated_at
        model.last_used_at = token.last_used_at

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def deactivate_token(self, token_id: str) -> None:
        """Deactivate a single FCM token."""
        model = self.session.query(UserFCMTokenModel).filter_by(id=token_id).first()
        if model:
            model.is_active = False
            model.updated_at = datetime.utcnow()
            self.session.commit()

    def deactivate_tokens(self, fcm_tokens: List[str]) -> None:
        """Deactivate multiple FCM tokens by token string."""
        if not fcm_tokens:
            return

        self.session.query(UserFCMTokenModel).filter(
            UserFCMTokenModel.fcm_token.in_(fcm_tokens)
        ).update(
            {"is_active": False, "updated_at": datetime.utcnow()},
            synchronize_session=False,
        )
        self.session.commit()

    def delete(self, token_id: str) -> None:
        """Delete FCM token by ID."""
        model = self.session.query(UserFCMTokenModel).filter_by(id=token_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()

    @staticmethod
    def _to_domain(model: UserFCMTokenModel) -> UserFCMToken:
        """Convert SQLAlchemy model to domain model."""
        return UserFCMToken(
            id=model.id,
            user_id=model.user_id,
            fcm_token=model.fcm_token,
            device_type=model.device_type,
            device_name=model.device_name,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_used_at=model.last_used_at,
        )


class PostgresNotificationRepo:
    """PostgreSQL implementation of NotificationRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID."""
        model = self.session.query(NotificationModel).filter_by(id=notification_id).first()
        return self._to_domain(model) if model else None

    def get_by_user(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Get notifications for a user."""
        query = self.session.query(NotificationModel).filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(read=False)

        models = (
            query.order_by(NotificationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(m) for m in models]

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
        """Create a new notification."""
        notification_id = _generate_id()
        now = datetime.utcnow()

        model = NotificationModel(
            id=notification_id,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            action_url=action_url,
            notification_metadata=metadata,
            image_url=image_url,
            fcm_message_id=fcm_message_id,
            read=False,
            sent_at=now,
            created_at=now,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def mark_as_read(self, notification_id: str) -> None:
        """Mark a notification as read."""
        model = self.session.query(NotificationModel).filter_by(id=notification_id).first()
        if model and not model.read:
            model.read = True
            model.read_at = datetime.utcnow()
            self.session.commit()

    def mark_all_as_read(self, user_id: str) -> None:
        """Mark all notifications as read for a user."""
        now = datetime.utcnow()
        self.session.query(NotificationModel).filter_by(user_id=user_id, read=False).update(
            {"read": True, "read_at": now}, synchronize_session=False
        )
        self.session.commit()

    def count_unread(self, user_id: str) -> int:
        """Count unread notifications for a user."""
        return (
            self.session.query(func.count(NotificationModel.id))
            .filter_by(user_id=user_id, read=False)
            .scalar()
        )

    def delete(self, notification_id: str) -> None:
        """Delete a notification."""
        model = self.session.query(NotificationModel).filter_by(id=notification_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()

    @staticmethod
    def _to_domain(model: NotificationModel) -> Notification:
        """Convert SQLAlchemy model to domain model."""
        return Notification(
            id=model.id,
            user_id=model.user_id,
            type=model.type,
            title=model.title,
            message=model.message,
            action_url=model.action_url,
            metadata=model.notification_metadata,
            image_url=model.image_url,
            read=model.read,
            sent_at=model.sent_at,
            read_at=model.read_at,
            fcm_message_id=model.fcm_message_id,
            created_at=model.created_at,
        )


class PostgresCardReviewRepo:
    """PostgreSQL implementation of CardReviewRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, review_id: str) -> Optional[CardReview]:
        """Get card review by ID."""
        model = self.session.query(CardReviewModel).filter_by(id=review_id).first()
        return self._to_domain(model) if model else None

    def get_by_card(
        self,
        card_id: str,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CardReview]:
        """Get review history for a specific card."""
        models = (
            self.session.query(CardReviewModel)
            .filter_by(card_id=card_id, user_id=user_id)
            .order_by(CardReviewModel.review_date.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def get_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CardReview]:
        """Get all reviews for a user."""
        models = (
            self.session.query(CardReviewModel)
            .filter_by(user_id=user_id)
            .order_by(CardReviewModel.review_date.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def create(self, review: CardReview) -> CardReview:
        """Create a new card review."""
        if not review.id:
            review.id = _generate_id()

        model = CardReviewModel(
            id=review.id,
            card_id=review.card_id,
            user_id=review.user_id,
            review_date=review.review_date,
            quality=review.quality,
            ease_factor=review.ease_factor,
            interval_days=review.interval_days,
            repetitions=review.repetitions,
            created_at=review.created_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, review_id: str) -> None:
        """Delete a card review."""
        model = self.session.query(CardReviewModel).filter_by(id=review_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()

    @staticmethod
    def _to_domain(model: CardReviewModel) -> CardReview:
        """Convert SQLAlchemy model to domain model."""
        return CardReview(
            id=model.id,
            card_id=model.card_id,
            user_id=model.user_id,
            review_date=model.review_date,
            quality=model.quality,
            ease_factor=float(model.ease_factor),
            interval_days=model.interval_days,
            repetitions=model.repetitions,
            created_at=model.created_at,
        )


class PostgresStudySessionRepo:
    """PostgreSQL implementation of StudySessionRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, session_id: str) -> Optional[StudySession]:
        """Get study session by ID."""
        model = self.session.query(StudySessionModel).filter_by(id=session_id).first()
        return self._to_domain(model) if model else None

    def get_by_user(
        self,
        user_id: str,
        deck_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StudySession]:
        """Get study sessions for a user."""
        query = self.session.query(StudySessionModel).filter_by(user_id=user_id)

        if deck_id:
            query = query.filter_by(deck_id=deck_id)

        models = (
            query.order_by(StudySessionModel.started_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def get_active_session(self, user_id: str, deck_id: str) -> Optional[StudySession]:
        """Get active (not ended) study session for a user and deck."""
        model = (
            self.session.query(StudySessionModel)
            .filter_by(user_id=user_id, deck_id=deck_id)
            .filter(StudySessionModel.ended_at.is_(None))
            .order_by(StudySessionModel.started_at.desc())
            .first()
        )
        return self._to_domain(model) if model else None

    def create(self, session: StudySession) -> StudySession:
        """Create a new study session."""
        if not session.id:
            session.id = _generate_id()

        model = StudySessionModel(
            id=session.id,
            user_id=session.user_id,
            deck_id=session.deck_id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            cards_reviewed=session.cards_reviewed,
            cards_correct=session.cards_correct,
            cards_incorrect=session.cards_incorrect,
            total_duration_seconds=session.total_duration_seconds,
            session_type=session.session_type,
            created_at=session.created_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, session: StudySession) -> StudySession:
        """Update existing study session."""
        model = self.session.query(StudySessionModel).filter_by(id=session.id).first()
        if not model:
            raise ValueError(f"Study session {session.id} not found")

        model.ended_at = session.ended_at
        model.cards_reviewed = session.cards_reviewed
        model.cards_correct = session.cards_correct
        model.cards_incorrect = session.cards_incorrect
        model.total_duration_seconds = session.total_duration_seconds

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, session_id: str) -> None:
        """Delete a study session."""
        model = self.session.query(StudySessionModel).filter_by(id=session_id).first()
        if model:
            self.session.delete(model)
            self.session.commit()

    @staticmethod
    def _to_domain(model: StudySessionModel) -> StudySession:
        """Convert SQLAlchemy model to domain model."""
        return StudySession(
            id=model.id,
            user_id=model.user_id,
            deck_id=model.deck_id,
            started_at=model.started_at,
            ended_at=model.ended_at,
            cards_reviewed=model.cards_reviewed,
            cards_correct=model.cards_correct,
            cards_incorrect=model.cards_incorrect,
            total_duration_seconds=model.total_duration_seconds,
            session_type=model.session_type,
            created_at=model.created_at,
        )


class PostgresDeckCommentRepo:
    """PostgreSQL implementation of DeckCommentRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, comment_id: str) -> Optional[DeckComment]:
        """Get comment by ID."""
        model = self.session.query(DeckCommentModel).filter_by(id=comment_id).first()
        return self._to_domain(model) if model else None

    def get_by_deck(
        self,
        deck_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[DeckComment], int]:
        """Get comments for a deck with pagination."""
        # Get total count
        total = (
            self.session.query(func.count(DeckCommentModel.id))
            .filter_by(deck_id=deck_id, parent_comment_id=None)
            .scalar()
        )

        # Get paginated comments (only top-level, not replies)
        models = (
            self.session.query(DeckCommentModel)
            .filter_by(deck_id=deck_id, parent_comment_id=None)
            .order_by(DeckCommentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        comments = [self._to_domain(m) for m in models]
        return comments, total

    def get_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DeckComment]:
        """Get comments by a user."""
        models = (
            self.session.query(DeckCommentModel)
            .filter_by(user_id=user_id)
            .order_by(DeckCommentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_replies(
        self,
        parent_comment_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DeckComment]:
        """Get replies to a comment."""
        models = (
            self.session.query(DeckCommentModel)
            .filter_by(parent_comment_id=parent_comment_id)
            .order_by(DeckCommentModel.created_at.asc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, comment: DeckComment) -> DeckComment:
        """Create a new comment."""
        if not comment.id:
            comment.id = _generate_id()

        model = DeckCommentModel(
            id=comment.id,
            deck_id=comment.deck_id,
            user_id=comment.user_id,
            content=comment.content,
            parent_comment_id=comment.parent_comment_id,
            is_edited=comment.is_edited,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def update(self, comment: DeckComment) -> DeckComment:
        """Update existing comment."""
        comment.updated_at = datetime.utcnow()
        model = self.session.query(DeckCommentModel).filter_by(id=comment.id).first()
        if not model:
            raise ValueError(f"Comment {comment.id} not found")

        model.content = comment.content
        model.is_edited = comment.is_edited
        model.updated_at = comment.updated_at

        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, comment_id: str, user_id: str) -> None:
        """Delete a comment with authorization check."""
        model = (
            self.session.query(DeckCommentModel)
            .filter_by(id=comment_id, user_id=user_id)
            .first()
        )
        if model:
            self.session.delete(model)
            self.session.commit()

    def count_by_deck(self, deck_id: str) -> int:
        """Count total comments for a deck."""
        return (
            self.session.query(func.count(DeckCommentModel.id))
            .filter_by(deck_id=deck_id)
            .scalar()
        )

    @staticmethod
    def _to_domain(model: DeckCommentModel) -> DeckComment:
        """Convert SQLAlchemy model to domain model."""
        return DeckComment(
            id=model.id,
            deck_id=model.deck_id,
            user_id=model.user_id,
            content=model.content,
            parent_comment_id=model.parent_comment_id,
            is_edited=model.is_edited,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class PostgresCommentVoteRepo:
    """PostgreSQL implementation of CommentVoteRepository."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, vote_id: str) -> Optional[CommentVote]:
        """Get vote by ID."""
        model = self.session.query(CommentVoteModel).filter_by(id=vote_id).first()
        return self._to_domain(model) if model else None

    def get_user_vote(self, comment_id: str, user_id: str) -> Optional[CommentVote]:
        """Get user's vote on a specific comment."""
        model = (
            self.session.query(CommentVoteModel)
            .filter_by(comment_id=comment_id, user_id=user_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_vote_counts(self, comment_id: str) -> Tuple[int, int]:
        """Get upvote and downvote counts for a comment."""
        result = (
            self.session.query(
                func.sum(case((CommentVoteModel.vote_type == 'upvote', 1), else_=0)).label('upvotes'),
                func.sum(case((CommentVoteModel.vote_type == 'downvote', 1), else_=0)).label('downvotes'),
            )
            .filter_by(comment_id=comment_id)
            .first()
        )
        return (result.upvotes or 0, result.downvotes or 0)

    def get_vote_counts_batch(self, comment_ids: List[str]) -> dict[str, Tuple[int, int]]:
        """Get vote counts for multiple comments in a single query."""
        if not comment_ids:
            return {}

        results = (
            self.session.query(
                CommentVoteModel.comment_id,
                func.sum(case((CommentVoteModel.vote_type == 'upvote', 1), else_=0)).label('upvotes'),
                func.sum(case((CommentVoteModel.vote_type == 'downvote', 1), else_=0)).label('downvotes'),
            )
            .filter(CommentVoteModel.comment_id.in_(comment_ids))
            .group_by(CommentVoteModel.comment_id)
            .all()
        )

        vote_counts = {comment_id: (0, 0) for comment_id in comment_ids}
        for row in results:
            vote_counts[row.comment_id] = (row.upvotes or 0, row.downvotes or 0)

        return vote_counts

    def get_user_votes_batch(self, comment_ids: List[str], user_id: str) -> dict[str, VoteType]:
        """Get user's votes for multiple comments in a single query."""
        if not comment_ids:
            return {}

        results = (
            self.session.query(CommentVoteModel.comment_id, CommentVoteModel.vote_type)
            .filter(
                CommentVoteModel.comment_id.in_(comment_ids),
                CommentVoteModel.user_id == user_id,
            )
            .all()
        )

        user_votes = {}
        for row in results:
            user_votes[row.comment_id] = VoteType(row.vote_type)

        return user_votes

    def create_or_update(self, vote: CommentVote) -> Optional[CommentVote]:
        """
        Create a new vote or update existing vote.

        If user already voted with the same type, the vote is removed (toggle off).
        If user voted with a different type, the vote is updated.

        Args:
            vote: Vote to create or update

        Returns:
            Created/updated vote, or None if vote was removed (toggle off)
        """
        # Check if user already voted
        existing = (
            self.session.query(CommentVoteModel)
            .filter_by(comment_id=vote.comment_id, user_id=vote.user_id)
            .first()
        )

        if existing:
            # If same vote type, remove the vote (toggle off)
            if existing.vote_type == vote.vote_type.value:
                self.session.delete(existing)
                self.session.commit()
                return None

            # Update to new vote type
            existing.vote_type = vote.vote_type.value
            existing.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(existing)
            return self._to_domain(existing)

        # Create new vote
        if not vote.id:
            vote.id = _generate_id()

        model = CommentVoteModel(
            id=vote.id,
            comment_id=vote.comment_id,
            user_id=vote.user_id,
            vote_type=vote.vote_type.value,
            created_at=vote.created_at,
            updated_at=vote.updated_at,
        )
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def delete(self, vote_id: str, user_id: str) -> None:
        """Delete a vote with authorization check."""
        model = (
            self.session.query(CommentVoteModel)
            .filter_by(id=vote_id, user_id=user_id)
            .first()
        )
        if model:
            self.session.delete(model)
            self.session.commit()

    def delete_by_comment_user(self, comment_id: str, user_id: str) -> None:
        """Delete user's vote on a comment."""
        model = (
            self.session.query(CommentVoteModel)
            .filter_by(comment_id=comment_id, user_id=user_id)
            .first()
        )
        if model:
            self.session.delete(model)
            self.session.commit()

    @staticmethod
    def _to_domain(model: CommentVoteModel) -> CommentVote:
        """Convert SQLAlchemy model to domain model."""
        return CommentVote(
            id=model.id,
            comment_id=model.comment_id,
            user_id=model.user_id,
            vote_type=VoteType(model.vote_type),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
