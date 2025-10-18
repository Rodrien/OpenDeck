"""
API Dependencies

FastAPI dependencies for dependency injection of repositories and services.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.postgres_repo import (
    PostgresUserRepo,
    PostgresDeckRepo,
    PostgresCardRepo,
    PostgresDocumentRepo,
    PostgresTopicRepo,
)
from app.services.auth_service import AuthService
from app.core.models import User

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer()


def get_user_repo(db: Session = Depends(get_db)) -> PostgresUserRepo:
    """Get user repository instance."""
    return PostgresUserRepo(db)


def get_deck_repo(db: Session = Depends(get_db)) -> PostgresDeckRepo:
    """Get deck repository instance."""
    return PostgresDeckRepo(db)


def get_card_repo(db: Session = Depends(get_db)) -> PostgresCardRepo:
    """Get card repository instance."""
    return PostgresCardRepo(db)


def get_document_repo(db: Session = Depends(get_db)) -> PostgresDocumentRepo:
    """Get document repository instance."""
    return PostgresDocumentRepo(db)


def get_topic_repo(db: Session = Depends(get_db)) -> PostgresTopicRepo:
    """Get topic repository instance."""
    return PostgresTopicRepo(db)


def get_auth_service(
    user_repo: PostgresUserRepo = Depends(get_user_repo),
) -> AuthService:
    """Get authentication service instance."""
    return AuthService(user_repo)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Get current authenticated user from JWT token.

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    user = auth_service.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
UserRepoDepends = Annotated[PostgresUserRepo, Depends(get_user_repo)]
DeckRepoDepends = Annotated[PostgresDeckRepo, Depends(get_deck_repo)]
CardRepoDepends = Annotated[PostgresCardRepo, Depends(get_card_repo)]
DocumentRepoDepends = Annotated[PostgresDocumentRepo, Depends(get_document_repo)]
TopicRepoDepends = Annotated[PostgresTopicRepo, Depends(get_topic_repo)]
AuthServiceDepends = Annotated[AuthService, Depends(get_auth_service)]
