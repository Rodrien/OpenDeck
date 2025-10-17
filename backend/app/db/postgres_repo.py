"""
PostgreSQL Repository Implementations

Concrete implementations of repository interfaces using SQLAlchemy.
"""

import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.models import User, Deck, Card, Document
from app.core.interfaces import UserRepository, DeckRepository, CardRepository, DocumentRepository
from app.db.models import UserModel, DeckModel, CardModel, DocumentModel


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
        limit: int = 100,
        offset: int = 0,
    ) -> list[Deck]:
        """List decks for a user with optional filters."""
        query = self.session.query(DeckModel).filter_by(user_id=user_id)

        if category:
            query = query.filter_by(category=category)
        if difficulty:
            query = query.filter_by(difficulty=difficulty)

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

    def list_by_deck(self, deck_id: str, limit: int = 100, offset: int = 0) -> list[Card]:
        """List all cards in a deck."""
        models = (
            self.session.query(CardModel)
            .filter_by(deck_id=deck_id)
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
            created_at=card.created_at,
            updated_at=card.updated_at,
        )
        self.session.add(model)
        self._update_deck_count(card.deck_id, increment=1)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def create_many(self, cards: list[Card]) -> list[Card]:
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

    def list(self, user_id: str, limit: int = 100, offset: int = 0) -> list[Document]:
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
