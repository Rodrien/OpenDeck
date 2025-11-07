# Deck Comments Feature - Implementation Plan

## Overview
This plan outlines the implementation of a comments system for deck pages, allowing users to add comments, upvote/downvote comments, and view all comments with vote counts. The implementation follows OpenDeck's clean architecture pattern and integrates seamlessly with existing authentication, API, and frontend patterns.

---

## Database Schema Changes

### 1. New Tables

#### `deck_comments` Table
Stores user comments on decks.

```sql
CREATE TABLE deck_comments (
    id VARCHAR(36) PRIMARY KEY,
    deck_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    parent_comment_id VARCHAR(36) NULL,  -- For nested replies (future)
    is_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES deck_comments(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_deck_comments_deck_id ON deck_comments(deck_id);
CREATE INDEX idx_deck_comments_user_id ON deck_comments(user_id);
CREATE INDEX idx_deck_comments_parent_id ON deck_comments(parent_comment_id);
CREATE INDEX idx_deck_comments_created_at ON deck_comments(created_at DESC);
```

#### `comment_votes` Table
Stores upvote/downvote data for comments.

```sql
CREATE TABLE comment_votes (
    id VARCHAR(36) PRIMARY KEY,
    comment_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    vote_type VARCHAR(10) NOT NULL,  -- 'upvote' or 'downvote'
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    
    FOREIGN KEY (comment_id) REFERENCES deck_comments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- One vote per user per comment
    UNIQUE(comment_id, user_id)
);

-- Indexes for performance
CREATE INDEX idx_comment_votes_comment_id ON comment_votes(comment_id);
CREATE INDEX idx_comment_votes_user_id ON comment_votes(user_id);
```

---

## Backend Implementation

### 1. Domain Models (`backend/app/core/models.py`)

Add new domain models:

```python
from enum import Enum

class VoteType(str, Enum):
    """Comment vote types."""
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


@dataclass
class DeckComment:
    """
    Deck Comment domain model.
    
    Represents a user comment on a deck with voting support.
    """
    id: str
    deck_id: str
    user_id: str
    content: str
    parent_comment_id: Optional[str] = None
    is_edited: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate comment data after initialization."""
        if not self.deck_id:
            raise ValueError("Comment must belong to a deck")
        if not self.user_id:
            raise ValueError("Comment must have an author")
        if not self.content or len(self.content.strip()) == 0:
            raise ValueError("Comment content cannot be empty")
        if len(self.content) > 5000:
            raise ValueError("Comment content cannot exceed 5000 characters")


@dataclass
class CommentVote:
    """
    Comment Vote domain model.
    
    Represents an upvote or downvote on a comment.
    """
    id: str
    comment_id: str
    user_id: str
    vote_type: VoteType
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate vote data after initialization."""
        if not self.comment_id:
            raise ValueError("Vote must reference a comment")
        if not self.user_id:
            raise ValueError("Vote must have a user")
```

### 2. Database Models (`backend/app/db/models.py`)

Add SQLAlchemy ORM models:

```python
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
    
    # Relationships
    deck = relationship("DeckModel", backref="comments")
    user = relationship("UserModel", backref="comments")
    parent = relationship("DeckCommentModel", remote_side=[id], backref="replies")
    votes = relationship("CommentVoteModel", back_populates="comment", cascade="all, delete-orphan")


class CommentVoteModel(Base):
    """Comment Vote table model."""
    
    __tablename__ = "comment_votes"
    
    id = Column(String(36), primary_key=True)
    comment_id = Column(String(36), ForeignKey("deck_comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vote_type = Column(SQLEnum(VoteType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint: one vote per user per comment
    __table_args__ = (
        sa.UniqueConstraint('comment_id', 'user_id', name='uix_comment_user_vote'),
    )
    
    # Relationships
    comment = relationship("DeckCommentModel", back_populates="votes")
    user = relationship("UserModel", backref="comment_votes")
```

### 3. Repository Interfaces (`backend/app/core/interfaces.py`)

Add repository protocols:

```python
class DeckCommentRepository(Protocol):
    """Abstract interface for deck comment data access."""
    
    def get(self, comment_id: str) -> Optional[DeckComment]:
        """Get comment by ID."""
        ...
    
    def list_by_deck(
        self,
        deck_id: str,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
    ) -> List[DeckComment]:
        """List comments for a deck with pagination."""
        ...
    
    def create(self, comment: DeckComment) -> DeckComment:
        """Create a new comment."""
        ...
    
    def update(self, comment: DeckComment) -> DeckComment:
        """Update existing comment."""
        ...
    
    def delete(self, comment_id: str, user_id: str) -> None:
        """Delete comment (with authorization check)."""
        ...


class CommentVoteRepository(Protocol):
    """Abstract interface for comment vote data access."""
    
    def get_vote(self, comment_id: str, user_id: str) -> Optional[CommentVote]:
        """Get user's vote on a specific comment."""
        ...
    
    def get_vote_counts(self, comment_id: str) -> dict:
        """Get vote counts for a comment."""
        ...
    
    def get_votes_for_comments(self, comment_ids: List[str]) -> dict:
        """Get vote counts for multiple comments (batch)."""
        ...
    
    def create_or_update_vote(self, vote: CommentVote) -> CommentVote:
        """Create or update a vote."""
        ...
    
    def delete_vote(self, comment_id: str, user_id: str) -> None:
        """Remove a vote."""
        ...
```

### 4. Repository Implementations (`backend/app/db/postgres_repo.py`)

Add PostgreSQL repository implementations:

```python
class PostgresDeckCommentRepo:
    """PostgreSQL implementation of DeckCommentRepository."""
    
    def __init__(self, session: Session) -> None:
        self.session = session
    
    def get(self, comment_id: str) -> Optional[DeckComment]:
        """Get comment by ID."""
        model = self.session.query(DeckCommentModel).filter_by(id=comment_id).first()
        return self._to_domain(model) if model else None
    
    def list_by_deck(
        self,
        deck_id: str,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
    ) -> List[DeckComment]:
        """List comments for a deck with pagination."""
        query = self.session.query(DeckCommentModel).filter_by(
            deck_id=deck_id,
            parent_comment_id=None  # Only top-level comments
        )
        
        # Order by created_at DESC or vote count (requires join)
        if order_by == "votes":
            # TODO: Implement vote-based ordering with subquery
            query = query.order_by(DeckCommentModel.created_at.desc())
        else:
            query = query.order_by(DeckCommentModel.created_at.desc())
        
        models = query.limit(limit).offset(offset).all()
        return [self._to_domain(model) for model in models]
    
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
        comment.is_edited = True
        
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
        """Delete comment (with authorization check)."""
        model = self.session.query(DeckCommentModel).filter_by(
            id=comment_id,
            user_id=user_id
        ).first()
        if model:
            self.session.delete(model)
            self.session.commit()
    
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
    
    def get_vote(self, comment_id: str, user_id: str) -> Optional[CommentVote]:
        """Get user's vote on a specific comment."""
        model = self.session.query(CommentVoteModel).filter_by(
            comment_id=comment_id,
            user_id=user_id
        ).first()
        return self._to_domain(model) if model else None
    
    def get_vote_counts(self, comment_id: str) -> dict:
        """Get vote counts for a comment."""
        upvotes = self.session.query(func.count(CommentVoteModel.id)).filter_by(
            comment_id=comment_id,
            vote_type=VoteType.UPVOTE
        ).scalar() or 0
        
        downvotes = self.session.query(func.count(CommentVoteModel.id)).filter_by(
            comment_id=comment_id,
            vote_type=VoteType.DOWNVOTE
        ).scalar() or 0
        
        return {
            "upvotes": upvotes,
            "downvotes": downvotes,
            "score": upvotes - downvotes
        }
    
    def get_votes_for_comments(self, comment_ids: List[str]) -> dict:
        """Get vote counts for multiple comments (batch operation)."""
        # Query all votes for the given comments
        votes = self.session.query(
            CommentVoteModel.comment_id,
            CommentVoteModel.vote_type,
            func.count(CommentVoteModel.id).label('count')
        ).filter(
            CommentVoteModel.comment_id.in_(comment_ids)
        ).group_by(
            CommentVoteModel.comment_id,
            CommentVoteModel.vote_type
        ).all()
        
        # Organize results by comment_id
        result = {}
        for comment_id in comment_ids:
            result[comment_id] = {"upvotes": 0, "downvotes": 0, "score": 0}
        
        for vote in votes:
            if vote.vote_type == VoteType.UPVOTE:
                result[vote.comment_id]["upvotes"] = vote.count
            else:
                result[vote.comment_id]["downvotes"] = vote.count
        
        # Calculate scores
        for comment_id in result:
            result[comment_id]["score"] = (
                result[comment_id]["upvotes"] - result[comment_id]["downvotes"]
            )
        
        return result
    
    def create_or_update_vote(self, vote: CommentVote) -> CommentVote:
        """Create or update a vote."""
        # Check if vote already exists
        existing = self.session.query(CommentVoteModel).filter_by(
            comment_id=vote.comment_id,
            user_id=vote.user_id
        ).first()
        
        if existing:
            # Update existing vote
            existing.vote_type = vote.vote_type
            existing.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(existing)
            return self._to_domain(existing)
        else:
            # Create new vote
            if not vote.id:
                vote.id = _generate_id()
            
            model = CommentVoteModel(
                id=vote.id,
                comment_id=vote.comment_id,
                user_id=vote.user_id,
                vote_type=vote.vote_type,
                created_at=vote.created_at,
                updated_at=vote.updated_at,
            )
            self.session.add(model)
            self.session.commit()
            self.session.refresh(model)
            return self._to_domain(model)
    
    def delete_vote(self, comment_id: str, user_id: str) -> None:
        """Remove a vote."""
        model = self.session.query(CommentVoteModel).filter_by(
            comment_id=comment_id,
            user_id=user_id
        ).first()
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
            vote_type=model.vote_type,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
```

### 5. API Schemas (`backend/app/schemas/comment.py`)

Create new Pydantic schemas:

```python
"""Deck Comment API Schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.core.models import VoteType


class CommentBase(BaseModel):
    """Base comment schema with common fields."""
    content: str = Field(..., min_length=1, max_length=5000)


class CommentCreate(CommentBase):
    """Schema for creating a new comment."""
    parent_comment_id: Optional[str] = None


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: str = Field(..., min_length=1, max_length=5000)


class CommentVoteRequest(BaseModel):
    """Schema for voting on a comment."""
    vote_type: VoteType


class CommentVoteResponse(BaseModel):
    """Schema for vote data in responses."""
    upvotes: int
    downvotes: int
    score: int
    user_vote: Optional[VoteType] = None
    
    class Config:
        from_attributes = True


class CommentAuthor(BaseModel):
    """Schema for comment author information."""
    id: str
    name: str
    email: str
    
    class Config:
        from_attributes = True


class CommentResponse(CommentBase):
    """Schema for comment data in responses."""
    id: str
    deck_id: str
    user_id: str
    author: CommentAuthor
    parent_comment_id: Optional[str] = None
    is_edited: bool
    votes: CommentVoteResponse
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Schema for paginated comment list response."""
    items: list[CommentResponse]
    total: int
    limit: int
    offset: int
```

### 6. API Dependencies (`backend/app/api/dependencies.py`)

Add dependency injection functions:

```python
def get_comment_repo(db: Session = Depends(get_db)) -> PostgresDeckCommentRepo:
    """Get deck comment repository instance."""
    return PostgresDeckCommentRepo(db)


def get_comment_vote_repo(db: Session = Depends(get_db)) -> PostgresCommentVoteRepo:
    """Get comment vote repository instance."""
    return PostgresCommentVoteRepo(db)


# Type aliases
CommentRepoDepends = Annotated[PostgresDeckCommentRepo, Depends(get_comment_repo)]
CommentVoteRepoDepends = Annotated[PostgresCommentVoteRepo, Depends(get_comment_vote_repo)]
```

### 7. API Endpoints (`backend/app/api/comments.py`)

Create new API routes:

```python
"""Deck Comments API Endpoints"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
    CommentVoteRequest,
    CommentVoteResponse,
    CommentAuthor,
)
from app.api.dependencies import (
    CurrentUser,
    CommentRepoDepends,
    CommentVoteRepoDepends,
    DeckRepoDepends,
    UserRepoDepends,
)
from app.core.models import DeckComment, CommentVote

router = APIRouter(tags=["Comments"])


@router.get("/decks/{deck_id}/comments", response_model=CommentListResponse)
async def list_deck_comments(
    deck_id: str,
    current_user: CurrentUser,
    comment_repo: CommentRepoDepends,
    comment_vote_repo: CommentVoteRepoDepends,
    deck_repo: DeckRepoDepends,
    user_repo: UserRepoDepends,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    order_by: str = Query("created_at", description="Sort by: created_at or votes"),
) -> CommentListResponse:
    """
    List all comments for a deck.
    
    Args:
        deck_id: Deck identifier
        current_user: Authenticated user
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency
        deck_repo: Deck repository dependency
        user_repo: User repository dependency
        limit: Maximum number of results (1-100)
        offset: Pagination offset
        order_by: Sort order (created_at or votes)
    
    Returns:
        Paginated list of comments with vote counts
    
    Raises:
        HTTPException: If deck not found
    """
    # Verify deck exists (user can view any public deck)
    deck = deck_repo.get(deck_id, current_user.id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found",
        )
    
    # Get comments
    comments = comment_repo.list_by_deck(deck_id, limit=limit, offset=offset, order_by=order_by)
    
    # Get vote counts for all comments (batch operation)
    comment_ids = [c.id for c in comments]
    votes_data = comment_vote_repo.get_votes_for_comments(comment_ids) if comment_ids else {}
    
    # Enrich comments with author and vote data
    comment_responses = []
    for comment in comments:
        # Get author info
        author = user_repo.get(comment.user_id)
        if not author:
            continue  # Skip if user deleted
        
        # Get user's vote on this comment
        user_vote = comment_vote_repo.get_vote(comment.id, current_user.id)
        
        # Build response
        vote_counts = votes_data.get(comment.id, {"upvotes": 0, "downvotes": 0, "score": 0})
        comment_dict = comment.__dict__.copy()
        comment_dict['author'] = CommentAuthor(
            id=author.id,
            name=author.name,
            email=author.email,
        )
        comment_dict['votes'] = CommentVoteResponse(
            upvotes=vote_counts["upvotes"],
            downvotes=vote_counts["downvotes"],
            score=vote_counts["score"],
            user_vote=user_vote.vote_type if user_vote else None,
        )
        comment_responses.append(CommentResponse.model_validate(comment_dict))
    
    # Get total count (in production, use a count query)
    total = len(comments) + offset
    
    return CommentListResponse(
        items=comment_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/decks/{deck_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    deck_id: str,
    comment_data: CommentCreate,
    current_user: CurrentUser,
    comment_repo: CommentRepoDepends,
    deck_repo: DeckRepoDepends,
    user_repo: UserRepoDepends,
) -> CommentResponse:
    """
    Create a new comment on a deck.
    
    Args:
        deck_id: Deck identifier
        comment_data: Comment creation data
        current_user: Authenticated user
        comment_repo: Comment repository dependency
        deck_repo: Deck repository dependency
        user_repo: User repository dependency
    
    Returns:
        Created comment
    
    Raises:
        HTTPException: If deck not found
    """
    # Verify deck exists
    deck = deck_repo.get(deck_id, current_user.id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found",
        )
    
    # Create comment
    comment = DeckComment(
        id="",  # Will be generated by repository
        deck_id=deck_id,
        user_id=current_user.id,
        content=comment_data.content,
        parent_comment_id=comment_data.parent_comment_id,
    )
    
    created_comment = comment_repo.create(comment)
    
    # Get author info
    author = user_repo.get(current_user.id)
    
    # Build response
    comment_dict = created_comment.__dict__.copy()
    comment_dict['author'] = CommentAuthor(
        id=author.id,
        name=author.name,
        email=author.email,
    )
    comment_dict['votes'] = CommentVoteResponse(
        upvotes=0,
        downvotes=0,
        score=0,
        user_vote=None,
    )
    
    return CommentResponse.model_validate(comment_dict)


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_data: CommentUpdate,
    current_user: CurrentUser,
    comment_repo: CommentRepoDepends,
    comment_vote_repo: CommentVoteRepoDepends,
    user_repo: UserRepoDepends,
) -> CommentResponse:
    """
    Update an existing comment.
    
    Args:
        comment_id: Comment identifier
        comment_data: Comment update data
        current_user: Authenticated user
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency
        user_repo: User repository dependency
    
    Returns:
        Updated comment
    
    Raises:
        HTTPException: If comment not found or access denied
    """
    comment = comment_repo.get(comment_id)
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    
    # Check authorization: only author can edit
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )
    
    # Update comment
    comment.content = comment_data.content
    updated_comment = comment_repo.update(comment)
    
    # Get author info and votes
    author = user_repo.get(current_user.id)
    vote_counts = comment_vote_repo.get_vote_counts(comment_id)
    user_vote = comment_vote_repo.get_vote(comment_id, current_user.id)
    
    # Build response
    comment_dict = updated_comment.__dict__.copy()
    comment_dict['author'] = CommentAuthor(
        id=author.id,
        name=author.name,
        email=author.email,
    )
    comment_dict['votes'] = CommentVoteResponse(
        upvotes=vote_counts["upvotes"],
        downvotes=vote_counts["downvotes"],
        score=vote_counts["score"],
        user_vote=user_vote.vote_type if user_vote else None,
    )
    
    return CommentResponse.model_validate(comment_dict)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: str,
    current_user: CurrentUser,
    comment_repo: CommentRepoDepends,
) -> None:
    """
    Delete a comment.
    
    Args:
        comment_id: Comment identifier
        current_user: Authenticated user
        comment_repo: Comment repository dependency
    
    Raises:
        HTTPException: If comment not found or access denied
    """
    comment = comment_repo.get(comment_id)
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    
    # Check authorization: only author can delete
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )
    
    comment_repo.delete(comment_id, current_user.id)


@router.post("/comments/{comment_id}/vote", response_model=CommentVoteResponse)
async def vote_comment(
    comment_id: str,
    vote_data: CommentVoteRequest,
    current_user: CurrentUser,
    comment_repo: CommentRepoDepends,
    comment_vote_repo: CommentVoteRepoDepends,
) -> CommentVoteResponse:
    """
    Upvote or downvote a comment.
    
    Args:
        comment_id: Comment identifier
        vote_data: Vote type (upvote or downvote)
        current_user: Authenticated user
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency
    
    Returns:
        Updated vote counts
    
    Raises:
        HTTPException: If comment not found
    """
    comment = comment_repo.get(comment_id)
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    
    # Create or update vote
    vote = CommentVote(
        id="",  # Will be generated if new
        comment_id=comment_id,
        user_id=current_user.id,
        vote_type=vote_data.vote_type,
    )
    
    comment_vote_repo.create_or_update_vote(vote)
    
    # Get updated vote counts
    vote_counts = comment_vote_repo.get_vote_counts(comment_id)
    
    return CommentVoteResponse(
        upvotes=vote_counts["upvotes"],
        downvotes=vote_counts["downvotes"],
        score=vote_counts["score"],
        user_vote=vote_data.vote_type,
    )


@router.delete("/comments/{comment_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vote(
    comment_id: str,
    current_user: CurrentUser,
    comment_repo: CommentRepoDepends,
    comment_vote_repo: CommentVoteRepoDepends,
) -> None:
    """
    Remove vote from a comment.
    
    Args:
        comment_id: Comment identifier
        current_user: Authenticated user
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency
    
    Raises:
        HTTPException: If comment not found
    """
    comment = comment_repo.get(comment_id)
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    
    comment_vote_repo.delete_vote(comment_id, current_user.id)
```

### 8. Register Routes (`backend/app/api/__init__.py`)

Add the comments router:

```python
from app.api import comments

# In the main router setup
api_router.include_router(comments.router, prefix="/api/v1")
```

### 9. Database Migration (`backend/alembic/versions/YYYYMMDD_HHMM_add_deck_comments.py`)

Create migration file:

```python
"""Add deck comments and votes

Revision ID: 005
Revises: 004
Create Date: 2025-11-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create VoteType enum
    vote_type_enum = ENUM('upvote', 'downvote', name='votetype', create_type=True)
    vote_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create deck_comments table
    op.create_table(
        'deck_comments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('deck_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', sa.String(length=36), nullable=True),
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['deck_id'], ['decks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['deck_comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_deck_comments_deck_id', 'deck_comments', ['deck_id'])
    op.create_index('idx_deck_comments_user_id', 'deck_comments', ['user_id'])
    op.create_index('idx_deck_comments_parent_id', 'deck_comments', ['parent_comment_id'])
    op.create_index('idx_deck_comments_created_at', 'deck_comments', ['created_at'])
    
    # Create comment_votes table
    op.create_table(
        'comment_votes',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('comment_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('vote_type', vote_type_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['comment_id'], ['deck_comments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comment_id', 'user_id', name='uix_comment_user_vote'),
    )
    op.create_index('idx_comment_votes_comment_id', 'comment_votes', ['comment_id'])
    op.create_index('idx_comment_votes_user_id', 'comment_votes', ['user_id'])


def downgrade() -> None:
    # Drop tables
    op.drop_index('idx_comment_votes_user_id', table_name='comment_votes')
    op.drop_index('idx_comment_votes_comment_id', table_name='comment_votes')
    op.drop_table('comment_votes')
    
    op.drop_index('idx_deck_comments_created_at', table_name='deck_comments')
    op.drop_index('idx_deck_comments_parent_id', table_name='deck_comments')
    op.drop_index('idx_deck_comments_user_id', table_name='deck_comments')
    op.drop_index('idx_deck_comments_deck_id', table_name='deck_comments')
    op.drop_table('deck_comments')
    
    # Drop enum
    vote_type_enum = ENUM('upvote', 'downvote', name='votetype')
    vote_type_enum.drop(op.get_bind(), checkfirst=True)
```

---

## Frontend Implementation

### 1. TypeScript Models (`opendeck-portal/src/app/models/comment.model.ts`)

Create comment models:

```typescript
import { User } from './user.model';

/**
 * Vote Type
 */
export type VoteType = 'upvote' | 'downvote';

/**
 * Comment Vote Response
 */
export interface CommentVotes {
  upvotes: number;
  downvotes: number;
  score: number;
  user_vote: VoteType | null;
}

/**
 * Comment Author
 */
export interface CommentAuthor {
  id: string;
  name: string;
  email: string;
}

/**
 * Deck Comment Model
 */
export interface DeckComment {
  id: string;
  deck_id: string;
  user_id: string;
  author: CommentAuthor;
  content: string;
  parent_comment_id: string | null;
  is_edited: boolean;
  votes: CommentVotes;
  created_at: string;
  updated_at: string;
}

/**
 * Create Comment DTO
 */
export interface CreateCommentDto {
  content: string;
  parent_comment_id?: string;
}

/**
 * Update Comment DTO
 */
export interface UpdateCommentDto {
  content: string;
}

/**
 * Vote Request DTO
 */
export interface VoteCommentDto {
  vote_type: VoteType;
}

/**
 * Comment Filter Params
 */
export interface CommentFilterParams {
  deck_id?: string;
  limit?: number;
  offset?: number;
  order_by?: 'created_at' | 'votes';
}
```

### 2. Comment Service (`opendeck-portal/src/app/services/comment.service.ts`)

Create service for API operations:

```typescript
import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  DeckComment,
  CreateCommentDto,
  UpdateCommentDto,
  VoteCommentDto,
  CommentFilterParams,
  CommentVotes,
} from '../models/comment.model';
import { PaginatedResponse } from '../models/api-response.model';

/**
 * Comment Service
 * Handles all comment-related API operations
 */
@Injectable({
  providedIn: 'root'
})
export class CommentService {
  private readonly apiUrl = `${environment.apiBaseUrl}`;

  constructor(private http: HttpClient) {}

  /**
   * Get all comments for a deck
   * @param deckId - Deck ID
   * @param filters - Optional filter parameters
   * @returns Observable of Paginated Comment response
   */
  getCommentsForDeck(
    deckId: string,
    filters?: CommentFilterParams
  ): Observable<PaginatedResponse<DeckComment>> {
    let params = new HttpParams();

    if (filters) {
      if (filters.limit !== undefined) {
        params = params.set('limit', filters.limit.toString());
      }
      if (filters.offset !== undefined) {
        params = params.set('offset', filters.offset.toString());
      }
      if (filters.order_by) {
        params = params.set('order_by', filters.order_by);
      }
    }

    const url = `${this.apiUrl}/decks/${deckId}/comments`;
    return this.http.get<PaginatedResponse<DeckComment>>(url, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Create new comment
   * @param deckId - Deck ID
   * @param comment - Create Comment DTO
   * @returns Observable of created Comment
   */
  create(deckId: string, comment: CreateCommentDto): Observable<DeckComment> {
    const url = `${this.apiUrl}/decks/${deckId}/comments`;
    return this.http.post<DeckComment>(url, comment)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update existing comment
   * @param commentId - Comment ID
   * @param comment - Update Comment DTO
   * @returns Observable of updated Comment
   */
  update(commentId: string, comment: UpdateCommentDto): Observable<DeckComment> {
    const url = `${this.apiUrl}/comments/${commentId}`;
    return this.http.put<DeckComment>(url, comment)
      .pipe(catchError(this.handleError));
  }

  /**
   * Delete comment
   * @param commentId - Comment ID
   * @returns Observable of void
   */
  delete(commentId: string): Observable<void> {
    const url = `${this.apiUrl}/comments/${commentId}`;
    return this.http.delete<void>(url)
      .pipe(catchError(this.handleError));
  }

  /**
   * Vote on a comment
   * @param commentId - Comment ID
   * @param vote - Vote type
   * @returns Observable of updated vote counts
   */
  vote(commentId: string, vote: VoteCommentDto): Observable<CommentVotes> {
    const url = `${this.apiUrl}/comments/${commentId}/vote`;
    return this.http.post<CommentVotes>(url, vote)
      .pipe(catchError(this.handleError));
  }

  /**
   * Remove vote from a comment
   * @param commentId - Comment ID
   * @returns Observable of void
   */
  removeVote(commentId: string): Observable<void> {
    const url = `${this.apiUrl}/comments/${commentId}/vote`;
    return this.http.delete<void>(url)
      .pipe(catchError(this.handleError));
  }

  /**
   * Handle HTTP errors
   * @param error - HTTP error response
   * @returns Observable error
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
      if (error.error?.detail) {
        errorMessage = error.error.detail;
      }
    }

    console.error('CommentService Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
```

### 3. Comments Component (`opendeck-portal/src/app/components/deck-comments/deck-comments.component.ts`)

Create standalone component:

```typescript
import { Component, Input, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

// PrimeNG Imports
import { Card } from 'primeng/card';
import { Button } from 'primeng/button';
import { InputTextarea } from 'primeng/inputtextarea';
import { Avatar } from 'primeng/avatar';
import { Message } from 'primeng/message';
import { ProgressSpinner } from 'primeng/progressspinner';
import { ConfirmDialog } from 'primeng/confirmdialog';
import { ConfirmationService, MessageService } from 'primeng/api';

// Services
import { CommentService } from '../../services/comment.service';
import { AuthService } from '../../services/auth.service';

// Models
import { DeckComment, CreateCommentDto, VoteType } from '../../models/comment.model';

@Component({
  selector: 'app-deck-comments',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TranslateModule,
    Card,
    Button,
    InputTextarea,
    Avatar,
    Message,
    ProgressSpinner,
    ConfirmDialog,
  ],
  providers: [ConfirmationService, MessageService],
  templateUrl: './deck-comments.component.html',
  styleUrls: ['./deck-comments.component.scss']
})
export class DeckCommentsComponent implements OnInit {
  @Input() deckId!: string;

  // Reactive state using signals
  comments = signal<DeckComment[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);
  newCommentText = signal<string>('');
  editingCommentId = signal<string | null>(null);
  editCommentText = signal<string>('');

  // Pagination
  limit = signal<number>(20);
  offset = signal<number>(0);
  total = signal<number>(0);

  // Computed values
  currentUser = computed(() => this.authService.currentUser());
  hasMoreComments = computed(() => this.comments().length < this.total());
  canAddComment = computed(() => this.newCommentText().trim().length > 0);

  constructor(
    private commentService: CommentService,
    private authService: AuthService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private translate: TranslateService
  ) {}

  ngOnInit(): void {
    this.loadComments();
  }

  /**
   * Load comments for the deck
   */
  loadComments(): void {
    this.loading.set(true);
    this.error.set(null);

    this.commentService.getCommentsForDeck(this.deckId, {
      limit: this.limit(),
      offset: this.offset(),
      order_by: 'created_at'
    }).subscribe({
      next: (response) => {
        this.comments.set(response.items);
        this.total.set(response.total);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(err.message);
        this.loading.set(false);
      }
    });
  }

  /**
   * Add a new comment
   */
  addComment(): void {
    if (!this.canAddComment()) {
      return;
    }

    const commentDto: CreateCommentDto = {
      content: this.newCommentText().trim()
    };

    this.commentService.create(this.deckId, commentDto).subscribe({
      next: (newComment) => {
        // Add to beginning of list
        this.comments.update(comments => [newComment, ...comments]);
        this.total.update(t => t + 1);
        this.newCommentText.set('');
        this.messageService.add({
          severity: 'success',
          summary: this.translate.instant('comments.commentAdded'),
          life: 3000
        });
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: this.translate.instant('comments.errorAddingComment'),
          detail: err.message,
          life: 5000
        });
      }
    });
  }

  /**
   * Start editing a comment
   */
  startEdit(comment: DeckComment): void {
    this.editingCommentId.set(comment.id);
    this.editCommentText.set(comment.content);
  }

  /**
   * Cancel editing
   */
  cancelEdit(): void {
    this.editingCommentId.set(null);
    this.editCommentText.set('');
  }

  /**
   * Save edited comment
   */
  saveEdit(commentId: string): void {
    const content = this.editCommentText().trim();
    if (!content) {
      return;
    }

    this.commentService.update(commentId, { content }).subscribe({
      next: (updatedComment) => {
        // Update in list
        this.comments.update(comments =>
          comments.map(c => c.id === commentId ? updatedComment : c)
        );
        this.cancelEdit();
        this.messageService.add({
          severity: 'success',
          summary: this.translate.instant('comments.commentUpdated'),
          life: 3000
        });
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: this.translate.instant('comments.errorUpdatingComment'),
          detail: err.message,
          life: 5000
        });
      }
    });
  }

  /**
   * Delete a comment
   */
  deleteComment(comment: DeckComment): void {
    this.confirmationService.confirm({
      message: this.translate.instant('comments.deleteConfirm'),
      header: this.translate.instant('comments.deleteHeader'),
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: this.translate.instant('common.yes'),
      rejectLabel: this.translate.instant('common.no'),
      accept: () => {
        this.commentService.delete(comment.id).subscribe({
          next: () => {
            // Remove from list
            this.comments.update(comments =>
              comments.filter(c => c.id !== comment.id)
            );
            this.total.update(t => t - 1);
            this.messageService.add({
              severity: 'success',
              summary: this.translate.instant('comments.commentDeleted'),
              life: 3000
            });
          },
          error: (err) => {
            this.messageService.add({
              severity: 'error',
              summary: this.translate.instant('comments.errorDeletingComment'),
              detail: err.message,
              life: 5000
            });
          }
        });
      }
    });
  }

  /**
   * Vote on a comment
   */
  vote(comment: DeckComment, voteType: VoteType): void {
    // If user already voted this way, remove vote
    if (comment.votes.user_vote === voteType) {
      this.commentService.removeVote(comment.id).subscribe({
        next: () => {
          // Update vote counts
          this.comments.update(comments =>
            comments.map(c => {
              if (c.id === comment.id) {
                const newVotes = { ...c.votes };
                if (voteType === 'upvote') {
                  newVotes.upvotes--;
                } else {
                  newVotes.downvotes--;
                }
                newVotes.score = newVotes.upvotes - newVotes.downvotes;
                newVotes.user_vote = null;
                return { ...c, votes: newVotes };
              }
              return c;
            })
          );
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: this.translate.instant('comments.errorVoting'),
            detail: err.message,
            life: 5000
          });
        }
      });
    } else {
      // Add or change vote
      this.commentService.vote(comment.id, { vote_type: voteType }).subscribe({
        next: (updatedVotes) => {
          // Update vote counts
          this.comments.update(comments =>
            comments.map(c =>
              c.id === comment.id ? { ...c, votes: updatedVotes } : c
            )
          );
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: this.translate.instant('comments.errorVoting'),
            detail: err.message,
            life: 5000
          });
        }
      });
    }
  }

  /**
   * Load more comments
   */
  loadMore(): void {
    this.offset.update(o => o + this.limit());
    this.loadComments();
  }

  /**
   * Check if user can edit/delete comment
   */
  canModifyComment(comment: DeckComment): boolean {
    const user = this.currentUser();
    return user !== null && user.id === comment.user_id;
  }

  /**
   * Get user initials for avatar
   */
  getUserInitials(name: string): string {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  }

  /**
   * Format relative time
   */
  getRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return this.translate.instant('time.justNow');
    if (diffMins < 60) return this.translate.instant('time.minutesAgo', { count: diffMins });
    if (diffHours < 24) return this.translate.instant('time.hoursAgo', { count: diffHours });
    if (diffDays < 7) return this.translate.instant('time.daysAgo', { count: diffDays });
    return date.toLocaleDateString();
  }
}
```

### 4. Component Template (`opendeck-portal/src/app/components/deck-comments/deck-comments.component.html`)

```html
<div class="deck-comments">
  <p-card>
    <ng-template pTemplate="header">
      <div class="flex justify-between items-center p-4">
        <h3 class="text-xl font-semibold m-0">
          {{ 'comments.title' | translate }} ({{ total() }})
        </h3>
      </div>
    </ng-template>

    <!-- New Comment Input -->
    <div class="mb-4">
      <div class="flex gap-3">
        <p-avatar 
          [label]="currentUser() ? getUserInitials(currentUser()!.name) : '?'"
          shape="circle"
          size="large"
          styleClass="bg-primary">
        </p-avatar>
        
        <div class="flex-1">
          <textarea
            pInputTextarea
            [rows]="3"
            [placeholder]="'comments.addCommentPlaceholder' | translate"
            [(ngModel)]="newCommentText"
            class="w-full"
            [maxlength]="5000">
          </textarea>
          
          <div class="flex justify-between items-center mt-2">
            <small class="text-muted">
              {{ newCommentText().length }} / 5000
            </small>
            <p-button
              [label]="'comments.postComment' | translate"
              icon="pi pi-send"
              (onClick)="addComment()"
              [disabled]="!canAddComment()"
              size="small">
            </p-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div *ngIf="loading()" class="text-center py-4">
      <p-progressSpinner styleClass="w-12 h-12"></p-progressSpinner>
    </div>

    <!-- Error Message -->
    <p-message 
      *ngIf="error()"
      severity="error" 
      [text]="error()!"
      styleClass="mb-4">
    </p-message>

    <!-- Comments List -->
    <div *ngIf="!loading() && comments().length > 0" class="comments-list">
      <div 
        *ngFor="let comment of comments()" 
        class="comment-item border-bottom-1 surface-border pb-4 mb-4">
        
        <!-- Comment Header -->
        <div class="flex gap-3">
          <p-avatar 
            [label]="getUserInitials(comment.author.name)"
            shape="circle"
            styleClass="bg-primary">
          </p-avatar>
          
          <div class="flex-1">
            <div class="flex justify-between items-start">
              <div>
                <div class="font-semibold">{{ comment.author.name }}</div>
                <div class="text-sm text-muted">
                  {{ getRelativeTime(comment.created_at) }}
                  <span *ngIf="comment.is_edited" class="ml-2">
                    ({{ 'comments.edited' | translate }})
                  </span>
                </div>
              </div>
              
              <!-- Edit/Delete Buttons -->
              <div *ngIf="canModifyComment(comment)" class="flex gap-2">
                <p-button
                  icon="pi pi-pencil"
                  [text]="true"
                  [rounded]="true"
                  severity="secondary"
                  (onClick)="startEdit(comment)"
                  [pTooltip]="'comments.edit' | translate">
                </p-button>
                <p-button
                  icon="pi pi-trash"
                  [text]="true"
                  [rounded]="true"
                  severity="danger"
                  (onClick)="deleteComment(comment)"
                  [pTooltip]="'comments.delete' | translate">
                </p-button>
              </div>
            </div>
            
            <!-- Comment Content (View Mode) -->
            <div *ngIf="editingCommentId() !== comment.id" class="mt-3">
              <p class="m-0 whitespace-pre-wrap">{{ comment.content }}</p>
            </div>
            
            <!-- Comment Content (Edit Mode) -->
            <div *ngIf="editingCommentId() === comment.id" class="mt-3">
              <textarea
                pInputTextarea
                [rows]="3"
                [(ngModel)]="editCommentText"
                class="w-full"
                [maxlength]="5000">
              </textarea>
              <div class="flex gap-2 mt-2">
                <p-button
                  [label]="'common.save' | translate"
                  icon="pi pi-check"
                  (onClick)="saveEdit(comment.id)"
                  size="small">
                </p-button>
                <p-button
                  [label]="'common.cancel' | translate"
                  icon="pi pi-times"
                  (onClick)="cancelEdit()"
                  severity="secondary"
                  [outlined]="true"
                  size="small">
                </p-button>
              </div>
            </div>
            
            <!-- Vote Buttons -->
            <div class="flex items-center gap-4 mt-3">
              <div class="flex items-center gap-2">
                <p-button
                  icon="pi pi-thumbs-up"
                  [text]="true"
                  [rounded]="true"
                  [severity]="comment.votes.user_vote === 'upvote' ? 'success' : 'secondary'"
                  (onClick)="vote(comment, 'upvote')"
                  [pTooltip]="'comments.upvote' | translate">
                </p-button>
                <span class="font-semibold">{{ comment.votes.upvotes }}</span>
              </div>
              
              <div class="flex items-center gap-2">
                <p-button
                  icon="pi pi-thumbs-down"
                  [text]="true"
                  [rounded]="true"
                  [severity]="comment.votes.user_vote === 'downvote' ? 'danger' : 'secondary'"
                  (onClick)="vote(comment, 'downvote')"
                  [pTooltip]="'comments.downvote' | translate">
                </p-button>
                <span class="font-semibold">{{ comment.votes.downvotes }}</span>
              </div>
              
              <div class="ml-4">
                <span class="font-semibold" [class.text-green-500]="comment.votes.score > 0" [class.text-red-500]="comment.votes.score < 0">
                  {{ 'comments.score' | translate }}: {{ comment.votes.score }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Comments -->
    <div *ngIf="!loading() && comments().length === 0" class="text-center py-8">
      <i class="pi pi-comment text-4xl text-muted mb-3"></i>
      <p class="text-muted">{{ 'comments.noComments' | translate }}</p>
    </div>

    <!-- Load More Button -->
    <div *ngIf="hasMoreComments()" class="text-center mt-4">
      <p-button
        [label]="'comments.loadMore' | translate"
        icon="pi pi-chevron-down"
        [outlined]="true"
        (onClick)="loadMore()">
      </p-button>
    </div>
  </p-card>
  
  <!-- Confirmation Dialog -->
  <p-confirmDialog></p-confirmDialog>
</div>
```

### 5. Component Styles (`opendeck-portal/src/app/components/deck-comments/deck-comments.component.scss`)

```scss
.deck-comments {
  .comment-item {
    &:last-child {
      border-bottom: none;
      margin-bottom: 0;
      padding-bottom: 0;
    }
  }

  textarea {
    resize: vertical;
  }
}
```

### 6. Integrate into Deck View

Update the deck detail page to include the comments component:

**File**: `opendeck-portal/src/app/pages/flashcards/deck-detail/deck-detail.component.ts`

```typescript
import { DeckCommentsComponent } from '../../../components/deck-comments/deck-comments.component';

@Component({
  // ...
  imports: [
    // ... existing imports
    DeckCommentsComponent,
  ],
})
export class DeckDetailComponent {
  // ... existing code
}
```

**Template**: Add comments section below deck content:

```html
<!-- Existing deck content -->
<div class="deck-content">
  <!-- ... existing content ... -->
</div>

<!-- Comments Section -->
<div class="mt-5">
  <app-deck-comments [deckId]="deckId"></app-deck-comments>
</div>
```

### 7. Translations

Add translations to `opendeck-portal/src/assets/i18n/en.json`:

```json
{
  "comments": {
    "title": "Comments",
    "addCommentPlaceholder": "Write a comment...",
    "postComment": "Post Comment",
    "edit": "Edit",
    "delete": "Delete",
    "edited": "edited",
    "upvote": "Upvote",
    "downvote": "Downvote",
    "score": "Score",
    "noComments": "No comments yet. Be the first to comment!",
    "loadMore": "Load More Comments",
    "commentAdded": "Comment posted successfully",
    "commentUpdated": "Comment updated successfully",
    "commentDeleted": "Comment deleted successfully",
    "errorAddingComment": "Failed to post comment",
    "errorUpdatingComment": "Failed to update comment",
    "errorDeletingComment": "Failed to delete comment",
    "errorVoting": "Failed to process vote",
    "deleteConfirm": "Are you sure you want to delete this comment?",
    "deleteHeader": "Confirm Delete"
  },
  "time": {
    "justNow": "just now",
    "minutesAgo": "{{count}} minute(s) ago",
    "hoursAgo": "{{count}} hour(s) ago",
    "daysAgo": "{{count}} day(s) ago"
  }
}
```

Add translations to `opendeck-portal/src/assets/i18n/es.json`:

```json
{
  "comments": {
    "title": "Comentarios",
    "addCommentPlaceholder": "Escribe un comentario...",
    "postComment": "Publicar Comentario",
    "edit": "Editar",
    "delete": "Eliminar",
    "edited": "editado",
    "upvote": "Me gusta",
    "downvote": "No me gusta",
    "score": "Puntuación",
    "noComments": "Aún no hay comentarios. ¡Sé el primero en comentar!",
    "loadMore": "Cargar Más Comentarios",
    "commentAdded": "Comentario publicado exitosamente",
    "commentUpdated": "Comentario actualizado exitosamente",
    "commentDeleted": "Comentario eliminado exitosamente",
    "errorAddingComment": "Error al publicar el comentario",
    "errorUpdatingComment": "Error al actualizar el comentario",
    "errorDeletingComment": "Error al eliminar el comentario",
    "errorVoting": "Error al procesar el voto",
    "deleteConfirm": "¿Estás seguro de que quieres eliminar este comentario?",
    "deleteHeader": "Confirmar Eliminación"
  },
  "time": {
    "justNow": "ahora mismo",
    "minutesAgo": "hace {{count}} minuto(s)",
    "hoursAgo": "hace {{count}} hora(s)",
    "daysAgo": "hace {{count}} día(s)"
  }
}
```

---

## Testing Strategy

### Backend Tests

**File**: `backend/tests/test_comments.py`

```python
import pytest
from app.core.models import DeckComment, CommentVote, VoteType


def test_create_comment(client, auth_headers, test_deck):
    """Test creating a new comment."""
    response = client.post(
        f"/api/v1/decks/{test_deck.id}/comments",
        json={"content": "Great deck!"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Great deck!"
    assert data["deck_id"] == test_deck.id


def test_list_comments(client, auth_headers, test_deck, test_comment):
    """Test listing comments for a deck."""
    response = client.get(
        f"/api/v1/decks/{test_deck.id}/comments",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    assert data["items"][0]["id"] == test_comment.id


def test_update_comment(client, auth_headers, test_comment):
    """Test updating a comment."""
    response = client.put(
        f"/api/v1/comments/{test_comment.id}",
        json={"content": "Updated content"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content"
    assert data["is_edited"] is True


def test_delete_comment(client, auth_headers, test_comment):
    """Test deleting a comment."""
    response = client.delete(
        f"/api/v1/comments/{test_comment.id}",
        headers=auth_headers
    )
    assert response.status_code == 204


def test_vote_comment(client, auth_headers, test_comment):
    """Test upvoting a comment."""
    response = client.post(
        f"/api/v1/comments/{test_comment.id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["upvotes"] == 1
    assert data["score"] == 1


def test_change_vote(client, auth_headers, test_comment):
    """Test changing vote from upvote to downvote."""
    # First upvote
    client.post(
        f"/api/v1/comments/{test_comment.id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )
    
    # Change to downvote
    response = client.post(
        f"/api/v1/comments/{test_comment.id}/vote",
        json={"vote_type": "downvote"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["downvotes"] == 1
    assert data["upvotes"] == 0
    assert data["score"] == -1


def test_remove_vote(client, auth_headers, test_comment):
    """Test removing a vote."""
    # First vote
    client.post(
        f"/api/v1/comments/{test_comment.id}/vote",
        json={"vote_type": "upvote"},
        headers=auth_headers
    )
    
    # Remove vote
    response = client.delete(
        f"/api/v1/comments/{test_comment.id}/vote",
        headers=auth_headers
    )
    assert response.status_code == 204


def test_unauthorized_delete(client, auth_headers, another_user_comment):
    """Test that users cannot delete other users' comments."""
    response = client.delete(
        f"/api/v1/comments/{another_user_comment.id}",
        headers=auth_headers
    )
    assert response.status_code == 403
```

### Frontend Tests

**File**: `opendeck-portal/src/app/components/deck-comments/deck-comments.component.spec.ts`

```typescript
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TranslateModule } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';

import { DeckCommentsComponent } from './deck-comments.component';
import { CommentService } from '../../services/comment.service';
import { AuthService } from '../../services/auth.service';

describe('DeckCommentsComponent', () => {
  let component: DeckCommentsComponent;
  let fixture: ComponentFixture<DeckCommentsComponent>;
  let commentService: jasmine.SpyObj<CommentService>;
  let authService: jasmine.SpyObj<AuthService>;

  beforeEach(async () => {
    const commentServiceSpy = jasmine.createSpyObj('CommentService', [
      'getCommentsForDeck',
      'create',
      'update',
      'delete',
      'vote',
      'removeVote'
    ]);
    const authServiceSpy = jasmine.createSpyObj('AuthService', [], {
      currentUser: { id: '1', name: 'Test User', email: 'test@example.com' }
    });

    await TestBed.configureTestingModule({
      imports: [
        DeckCommentsComponent,
        HttpClientTestingModule,
        TranslateModule.forRoot()
      ],
      providers: [
        { provide: CommentService, useValue: commentServiceSpy },
        { provide: AuthService, useValue: authServiceSpy }
      ]
    }).compileComponents();

    commentService = TestBed.inject(CommentService) as jasmine.SpyObj<CommentService>;
    authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    
    fixture = TestBed.createComponent(DeckCommentsComponent);
    component = fixture.componentInstance;
    component.deckId = 'test-deck-id';
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load comments on init', () => {
    const mockResponse = {
      items: [],
      total: 0,
      limit: 20,
      offset: 0
    };
    commentService.getCommentsForDeck.and.returnValue(of(mockResponse));

    component.ngOnInit();

    expect(commentService.getCommentsForDeck).toHaveBeenCalledWith(
      'test-deck-id',
      { limit: 20, offset: 0, order_by: 'created_at' }
    );
  });

  it('should add a new comment', () => {
    const newComment = {
      id: '1',
      content: 'Test comment',
      // ... other fields
    };
    commentService.create.and.returnValue(of(newComment));
    component.newCommentText.set('Test comment');

    component.addComment();

    expect(commentService.create).toHaveBeenCalled();
    expect(component.comments().length).toBe(1);
    expect(component.newCommentText()).toBe('');
  });

  // Add more tests...
});
```

---

## Implementation Timeline

### Phase 1: Backend Foundation (2-3 days)
1. Create database migration
2. Add domain models and database models
3. Implement repository interfaces and PostgreSQL implementations
4. Add API schemas

### Phase 2: Backend API (2 days)
1. Create API endpoints
2. Add dependency injection
3. Register routes
4. Write backend tests

### Phase 3: Frontend Foundation (2 days)
1. Create TypeScript models
2. Implement comment service
3. Write service tests

### Phase 4: Frontend UI (3-4 days)
1. Create comments component
2. Add template and styles
3. Integrate with deck detail page
4. Add translations (English and Spanish)

### Phase 5: Testing & Polish (2 days)
1. End-to-end testing
2. UI/UX refinements
3. Performance optimization
4. Dark mode verification

**Total Estimated Time**: 11-13 days

---

## Future Enhancements

### Nested Replies (Phase 2)
- Support for replying to comments
- Threaded conversation view
- Reply notifications

### Sorting Options
- Sort by newest/oldest
- Sort by most upvoted
- Sort by controversial (high engagement)

### Moderation Features
- Report inappropriate comments
- Admin moderation panel
- Auto-hide flagged comments

### Real-time Updates
- WebSocket integration for live comments
- Live vote count updates
- New comment notifications

### Rich Text Editor
- Markdown support
- Code snippets
- @ mentions

### Analytics
- Track comment engagement
- Popular discussion topics
- User participation metrics

---

## Security Considerations

1. **Authorization**: Users can only edit/delete their own comments
2. **Input Validation**: Content length limits (5000 chars), XSS prevention
3. **Rate Limiting**: Prevent comment spam (future enhancement)
4. **SQL Injection**: Parameterized queries via SQLAlchemy
5. **Authentication**: JWT token required for all comment operations

---

## Performance Optimization

1. **Pagination**: Limit comments to 20-50 per page
2. **Batch Queries**: Load vote counts for multiple comments in single query
3. **Indexes**: Database indexes on `deck_id`, `user_id`, `created_at`
4. **Caching**: Consider caching vote counts (Redis, future)
5. **Lazy Loading**: Load comments on-demand when user scrolls

---

## Conclusion

This implementation plan provides a complete roadmap for adding a comments feature to OpenDeck. The design follows the existing clean architecture patterns, integrates seamlessly with current authentication and API structures, uses PrimeNG components for UI consistency, and includes comprehensive testing strategies.

The feature will enable users to engage with deck content, share insights, and build community around educational materials.
