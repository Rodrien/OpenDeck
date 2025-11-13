"""
Card Report API Endpoints

API routes for reporting flashcards with incorrect, misleading, or unhelpful information.
"""

import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, status

from app.schemas.card_report import (
    CardReportCreate,
    CardReportResponse,
    CardReportStatusUpdate,
)
from app.api.dependencies import (
    CurrentUser,
    CardReportRepoDepends,
    CardRepoDepends,
    DeckRepoDepends,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Card Reports"])


@router.post(
    "/cards/{card_id}/report",
    response_model=CardReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a card",
    description="Create a new report for a card that has incorrect, misleading, or unhelpful information.",
)
async def report_card(
    card_id: UUID,
    report_data: CardReportCreate,
    current_user: CurrentUser,
    card_repo: CardRepoDepends,
    report_repo: CardReportRepoDepends,
) -> CardReportResponse:
    """
    Report a card for review.

    The card must exist before it can be reported. Users can report any card,
    regardless of ownership.

    Args:
        card_id: ID of the card to report
        report_data: Report details including reason
        current_user: Authenticated user creating the report
        card_repo: Card repository
        report_repo: Report repository

    Returns:
        Created report details

    Raises:
        HTTPException: If card not found or report creation fails
    """
    # Verify card exists
    card = card_repo.get(str(card_id))
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )

    try:
        report = report_repo.create(
            card_id=str(card_id),
            user_id=current_user.id,
            reason=report_data.reason,
        )
        return CardReportResponse(
            id=UUID(report.id),
            card_id=UUID(report.card_id),
            user_id=UUID(report.user_id),
            reason=report.reason,
            status=report.status,
            created_at=report.created_at,
            updated_at=report.updated_at,
            reviewed_by=UUID(report.reviewed_by) if report.reviewed_by else None,
            reviewed_at=report.reviewed_at,
        )
    except ValueError as e:
        # Log internal error but return generic message
        logger.error(f"Failed to create report for card {card_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to submit report. Please try again.",
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error creating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit report. Please try again later.",
        )


@router.get(
    "/cards/{card_id}",
    response_model=List[CardReportResponse],
    summary="Get reports for a card",
    description="Retrieve all reports submitted for a specific card.",
)
async def get_card_reports(
    card_id: UUID,
    current_user: CurrentUser,
    card_repo: CardRepoDepends,
    report_repo: CardReportRepoDepends,
) -> List[CardReportResponse]:
    """
    Get all reports for a specific card.

    Only authenticated users can view reports. This endpoint could be enhanced
    in the future to restrict access to admins or deck owners only.

    Args:
        card_id: ID of the card
        current_user: Authenticated user
        card_repo: Card repository
        report_repo: Report repository

    Returns:
        List of reports for the card

    Raises:
        HTTPException: If card not found
    """
    # Verify card exists
    card = card_repo.get(str(card_id))
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )

    reports = report_repo.get_by_card_id(str(card_id))
    return [
        CardReportResponse(
            id=UUID(r.id),
            card_id=UUID(r.card_id),
            user_id=UUID(r.user_id),
            reason=r.reason,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            reviewed_by=UUID(r.reviewed_by) if r.reviewed_by else None,
            reviewed_at=r.reviewed_at,
        )
        for r in reports
    ]


@router.get(
    "/my-reports",
    response_model=List[CardReportResponse],
    summary="Get user's reports",
    description="Retrieve all reports submitted by the authenticated user.",
)
async def get_my_reports(
    current_user: CurrentUser,
    report_repo: CardReportRepoDepends,
    skip: int = 0,
    limit: int = 100,
) -> List[CardReportResponse]:
    """
    Get all reports created by the current user.

    Args:
        current_user: Authenticated user
        report_repo: Report repository
        skip: Number of reports to skip (pagination)
        limit: Maximum number of reports to return

    Returns:
        List of user's reports
    """
    reports = report_repo.get_by_user_id(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return [
        CardReportResponse(
            id=UUID(r.id),
            card_id=UUID(r.card_id),
            user_id=UUID(r.user_id),
            reason=r.reason,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
            reviewed_by=UUID(r.reviewed_by) if r.reviewed_by else None,
            reviewed_at=r.reviewed_at,
        )
        for r in reports
    ]


@router.put(
    "/{report_id}/status",
    response_model=CardReportResponse,
    summary="Update report status",
    description="Update the status of a report. Only deck owners can update report status for cards in their decks.",
)
async def update_report_status(
    report_id: UUID,
    status_update: CardReportStatusUpdate,
    current_user: CurrentUser,
    report_repo: CardReportRepoDepends,
    card_repo: CardRepoDepends,
    deck_repo: DeckRepoDepends,
) -> CardReportResponse:
    """
    Update the status of a report.

    Only deck owners can update the status of reports for cards in their decks.
    This ensures proper authorization for report management.

    Uses an optimized JOIN query to fetch report, card, and deck information in a
    single database query, avoiding the N+1 query problem.

    Args:
        report_id: ID of the report to update
        status_update: New status for the report
        current_user: Authenticated user (must be deck owner)
        report_repo: Report repository
        card_repo: Card repository (unused, kept for dependency injection)
        deck_repo: Deck repository (unused, kept for dependency injection)

    Returns:
        Updated report details

    Raises:
        HTTPException: If report not found or user is not authorized
    """
    # Get report with card and deck information in a single query (avoids N+1 problem)
    result = report_repo.get_with_card_and_deck(str(report_id))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )

    report, deck_user_id = result

    # Verify user is the deck owner
    if deck_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update reports for this card. Only deck owners can manage reports.",
        )

    try:
        updated_report = report_repo.update_status(
            report_id=str(report_id),
            status=status_update.status,
            reviewed_by=current_user.id,
        )
        return CardReportResponse(
            id=UUID(updated_report.id),
            card_id=UUID(updated_report.card_id),
            user_id=UUID(updated_report.user_id),
            reason=updated_report.reason,
            status=updated_report.status,
            created_at=updated_report.created_at,
            updated_at=updated_report.updated_at,
            reviewed_by=UUID(updated_report.reviewed_by) if updated_report.reviewed_by else None,
            reviewed_at=updated_report.reviewed_at,
        )
    except ValueError as e:
        # Log internal error but return generic message
        logger.error(f"Failed to update report {report_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to update report status. Please try again.",
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error updating report status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update report. Please try again later.",
        )
