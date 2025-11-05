"""Deck Comment Management API Endpoints"""

from fastapi import APIRouter, HTTPException, status, Query, Path
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
    VoteCreate,
    VoteCountsResponse,
    UserInfo,
)
from app.api.dependencies import (
    CurrentUser,
    CurrentUserOptional,
    CommentRepoDepends,
    CommentVoteRepoDepends,
    DeckRepoDepends,
    UserRepoDepends,
)
from app.core.models import DeckComment, CommentVote

router = APIRouter(prefix="/decks/{deck_id}/comments", tags=["Comments"])


@router.get("", response_model=CommentListResponse)
async def list_comments(
    deck_id: str = Path(..., description="Deck identifier"),
    current_user: CurrentUserOptional = None,
    comment_repo: CommentRepoDepends = None,
    comment_vote_repo: CommentVoteRepoDepends = None,
    user_repo: UserRepoDepends = None,
    deck_repo: DeckRepoDepends = None,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> CommentListResponse:
    """
    List comments for a deck with pagination.

    Includes vote counts and user's votes on each comment.

    Args:
        deck_id: Deck identifier
        current_user: Authenticated user (optional)
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency
        user_repo: User repository dependency
        deck_repo: Deck repository dependency
        limit: Maximum number of results (1-100)
        offset: Pagination offset

    Returns:
        Paginated list of comments with vote information

    Raises:
        HTTPException: If deck not found
    """
    # Verify deck exists (you can optionally check if user has access if needed)
    # For now we'll allow anyone to read comments on any deck

    comments, total = comment_repo.get_by_deck(deck_id, limit=limit, offset=offset)

    if not comments:
        return CommentListResponse(items=[], total=total, limit=limit, offset=offset)

    # Get comment IDs for batch queries
    comment_ids = [c.id for c in comments]

    # Batch load vote counts
    vote_counts = comment_vote_repo.get_vote_counts_batch(comment_ids)

    # Batch load user's votes if authenticated
    user_votes = {}
    if current_user:
        user_votes = comment_vote_repo.get_user_votes_batch(comment_ids, current_user.id)

    # Batch load user information
    user_ids = list(set(c.user_id for c in comments))
    users = {user.id: user for user in (user_repo.get(uid) for uid in user_ids) if user}

    # Build response with enriched data
    comment_responses = []
    for comment in comments:
        upvotes, downvotes = vote_counts.get(comment.id, (0, 0))
        user_vote = user_votes.get(comment.id)
        user = users.get(comment.user_id)

        comment_dict = comment.__dict__.copy()
        comment_dict['upvotes'] = upvotes
        comment_dict['downvotes'] = downvotes
        comment_dict['score'] = upvotes - downvotes
        comment_dict['user_vote'] = user_vote
        if user:
            comment_dict['user'] = UserInfo(id=user.id, name=user.name, email=user.email)

        comment_responses.append(CommentResponse.model_validate(comment_dict))

    return CommentListResponse(
        items=comment_responses,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    deck_id: str = Path(..., description="Deck identifier"),
    comment_id: str = Path(..., description="Comment identifier"),
    current_user: CurrentUserOptional = None,
    comment_repo: CommentRepoDepends = None,
    comment_vote_repo: CommentVoteRepoDepends = None,
    user_repo: UserRepoDepends = None,
) -> CommentResponse:
    """
    Get a single comment by ID.

    Args:
        deck_id: Deck identifier
        comment_id: Comment identifier
        current_user: Authenticated user (optional)
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency
        user_repo: User repository dependency

    Returns:
        Comment details with vote information

    Raises:
        HTTPException: If comment not found
    """
    comment = comment_repo.get(comment_id)
    if not comment or comment.deck_id != deck_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Get vote counts
    upvotes, downvotes = comment_vote_repo.get_vote_counts(comment_id)

    # Get user's vote if authenticated
    user_vote = None
    if current_user:
        vote = comment_vote_repo.get_user_vote(comment_id, current_user.id)
        user_vote = vote.vote_type if vote else None

    # Get comment author information
    user = user_repo.get(comment.user_id)

    comment_dict = comment.__dict__.copy()
    comment_dict['upvotes'] = upvotes
    comment_dict['downvotes'] = downvotes
    comment_dict['score'] = upvotes - downvotes
    comment_dict['user_vote'] = user_vote
    if user:
        comment_dict['user'] = UserInfo(id=user.id, name=user.name, email=user.email)

    return CommentResponse.model_validate(comment_dict)


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    deck_id: str = Path(..., description="Deck identifier"),
    comment_data: CommentCreate = None,
    current_user: CurrentUser = None,
    comment_repo: CommentRepoDepends = None,
    deck_repo: DeckRepoDepends = None,
    user_repo: UserRepoDepends = None,
) -> CommentResponse:
    """
    Create a new comment on a deck.

    Requires authentication.

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
        HTTPException: If deck not found or validation fails
    """
    # Verify deck exists
    # Note: In production, you might want to verify user has access to this deck
    # For now, we'll allow anyone authenticated to comment on any deck

    # If parent_comment_id is provided, verify it exists
    if comment_data.parent_comment_id:
        parent = comment_repo.get(comment_data.parent_comment_id)
        if not parent or parent.deck_id != deck_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found"
            )

    # Create comment
    comment = DeckComment(
        id="",  # Will be generated
        deck_id=deck_id,
        user_id=current_user.id,
        content=comment_data.content,
        parent_comment_id=comment_data.parent_comment_id,
    )

    created_comment = comment_repo.create(comment)

    # Get user information
    user = user_repo.get(created_comment.user_id)

    comment_dict = created_comment.__dict__.copy()
    comment_dict['upvotes'] = 0
    comment_dict['downvotes'] = 0
    comment_dict['score'] = 0
    comment_dict['user_vote'] = None
    if user:
        comment_dict['user'] = UserInfo(id=user.id, name=user.name, email=user.email)

    return CommentResponse.model_validate(comment_dict)


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    deck_id: str = Path(..., description="Deck identifier"),
    comment_id: str = Path(..., description="Comment identifier"),
    comment_data: CommentUpdate = None,
    current_user: CurrentUser = None,
    comment_repo: CommentRepoDepends = None,
    comment_vote_repo: CommentVoteRepoDepends = None,
    user_repo: UserRepoDepends = None,
) -> CommentResponse:
    """
    Update an existing comment.

    Requires authentication. Users can only update their own comments.

    Args:
        deck_id: Deck identifier
        comment_id: Comment identifier
        comment_data: Comment update data
        current_user: Authenticated user
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency
        user_repo: User repository dependency

    Returns:
        Updated comment

    Raises:
        HTTPException: If comment not found or user not authorized
    """
    comment = comment_repo.get(comment_id)
    if not comment or comment.deck_id != deck_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Check authorization
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments"
        )

    # Update comment
    comment.edit_content(comment_data.content)
    updated_comment = comment_repo.update(comment)

    # Get vote counts
    upvotes, downvotes = comment_vote_repo.get_vote_counts(comment_id)

    # Get user's vote
    vote = comment_vote_repo.get_user_vote(comment_id, current_user.id)
    user_vote = vote.vote_type if vote else None

    # Get comment author information
    user = user_repo.get(updated_comment.user_id)

    comment_dict = updated_comment.__dict__.copy()
    comment_dict['upvotes'] = upvotes
    comment_dict['downvotes'] = downvotes
    comment_dict['score'] = upvotes - downvotes
    comment_dict['user_vote'] = user_vote
    if user:
        comment_dict['user'] = UserInfo(id=user.id, name=user.name, email=user.email)

    return CommentResponse.model_validate(comment_dict)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    deck_id: str = Path(..., description="Deck identifier"),
    comment_id: str = Path(..., description="Comment identifier"),
    current_user: CurrentUser = None,
    comment_repo: CommentRepoDepends = None,
) -> None:
    """
    Delete a comment.

    Requires authentication. Users can only delete their own comments.

    Args:
        deck_id: Deck identifier
        comment_id: Comment identifier
        current_user: Authenticated user
        comment_repo: Comment repository dependency

    Raises:
        HTTPException: If comment not found or user not authorized
    """
    comment = comment_repo.get(comment_id)
    if not comment or comment.deck_id != deck_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Check authorization
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments"
        )

    comment_repo.delete(comment_id, current_user.id)


@router.post("/{comment_id}/vote", response_model=VoteCountsResponse)
async def vote_on_comment(
    deck_id: str = Path(..., description="Deck identifier"),
    comment_id: str = Path(..., description="Comment identifier"),
    vote_data: VoteCreate = None,
    current_user: CurrentUser = None,
    comment_repo: CommentRepoDepends = None,
    comment_vote_repo: CommentVoteRepoDepends = None,
) -> VoteCountsResponse:
    """
    Vote on a comment (upvote or downvote).

    Requires authentication. If user already voted with the same type,
    the vote is removed (toggle off). If user voted with different type,
    the vote is updated.

    Args:
        deck_id: Deck identifier
        comment_id: Comment identifier
        vote_data: Vote creation data
        current_user: Authenticated user
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency

    Returns:
        Updated vote counts for the comment

    Raises:
        HTTPException: If comment not found
    """
    # Verify comment exists
    comment = comment_repo.get(comment_id)
    if not comment or comment.deck_id != deck_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Create or update vote
    vote = CommentVote(
        id="",  # Will be generated if needed
        comment_id=comment_id,
        user_id=current_user.id,
        vote_type=vote_data.vote_type,
    )

    comment_vote_repo.create_or_update(vote)

    # Get updated vote counts
    upvotes, downvotes = comment_vote_repo.get_vote_counts(comment_id)

    # Get user's current vote
    user_vote_obj = comment_vote_repo.get_user_vote(comment_id, current_user.id)
    user_vote = user_vote_obj.vote_type if user_vote_obj else None

    return VoteCountsResponse(
        comment_id=comment_id,
        upvotes=upvotes,
        downvotes=downvotes,
        score=upvotes - downvotes,
        user_vote=user_vote,
    )


@router.delete("/{comment_id}/vote", status_code=status.HTTP_204_NO_CONTENT)
async def remove_vote(
    deck_id: str = Path(..., description="Deck identifier"),
    comment_id: str = Path(..., description="Comment identifier"),
    current_user: CurrentUser = None,
    comment_repo: CommentRepoDepends = None,
    comment_vote_repo: CommentVoteRepoDepends = None,
) -> None:
    """
    Remove user's vote on a comment.

    Requires authentication.

    Args:
        deck_id: Deck identifier
        comment_id: Comment identifier
        current_user: Authenticated user
        comment_repo: Comment repository dependency
        comment_vote_repo: Comment vote repository dependency

    Raises:
        HTTPException: If comment not found
    """
    # Verify comment exists
    comment = comment_repo.get(comment_id)
    if not comment or comment.deck_id != deck_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Delete vote
    comment_vote_repo.delete_by_comment_user(comment_id, current_user.id)
