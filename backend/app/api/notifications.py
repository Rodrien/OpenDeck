"""
Notification Management API Endpoints

Endpoints for retrieving notification history and managing read/unread status.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Query

from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.api.dependencies import CurrentUser, NotificationServiceDepends


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=List[NotificationResponse],
    summary="Get Notifications",
)
async def get_notifications(
    current_user: CurrentUser,
    notification_service: NotificationServiceDepends,
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[NotificationResponse]:
    """
    Get notification history for current user.

    Supports pagination and filtering by read status.

    Args:
        unread_only: If True, only return unread notifications
        limit: Maximum number of notifications (1-100)
        offset: Number of notifications to skip
        current_user: Authenticated user from JWT
        notification_service: Notification service

    Returns:
        List of notifications ordered by creation date (newest first)

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            unread_only=unread_only,
            limit=limit,
            offset=offset,
        )

        return [NotificationResponse.model_validate(n) for n in notifications]

    except Exception as e:
        logger.error(
            f"Failed to retrieve notifications for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications",
        )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get Unread Count",
)
async def get_unread_count(
    current_user: CurrentUser,
    notification_service: NotificationServiceDepends,
) -> UnreadCountResponse:
    """
    Get count of unread notifications for current user.

    Useful for displaying notification badge count.

    Args:
        current_user: Authenticated user from JWT
        notification_service: Notification service

    Returns:
        Number of unread notifications

    Raises:
        HTTPException: If count retrieval fails
    """
    try:
        count = await notification_service.get_unread_count(current_user.id)
        return UnreadCountResponse(count=count)

    except Exception as e:
        logger.error(
            f"Failed to count unread notifications for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count unread notifications",
        )


@router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark Notification as Read",
)
async def mark_notification_as_read(
    notification_id: str,
    current_user: CurrentUser,
    notification_service: NotificationServiceDepends,
) -> None:
    """
    Mark a single notification as read.

    Args:
        notification_id: Notification identifier
        current_user: Authenticated user from JWT
        notification_service: Notification service

    Raises:
        HTTPException: If notification not found or doesn't belong to user
    """
    try:
        await notification_service.mark_as_read(notification_id, current_user.id)
        logger.debug(f"Marked notification {notification_id} as read")

    except ValueError as e:
        logger.warning(f"Failed to mark notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:
        logger.error(
            f"Failed to mark notification {notification_id} as read: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read",
        )


@router.patch(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark All Notifications as Read",
)
async def mark_all_notifications_as_read(
    current_user: CurrentUser,
    notification_service: NotificationServiceDepends,
) -> None:
    """
    Mark all notifications as read for current user.

    Args:
        current_user: Authenticated user from JWT
        notification_service: Notification service

    Raises:
        HTTPException: If operation fails
    """
    try:
        await notification_service.mark_all_as_read(current_user.id)
        logger.info(f"Marked all notifications as read for user {current_user.id}")

    except Exception as e:
        logger.error(
            f"Failed to mark all notifications as read for user {current_user.id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read",
        )


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Notification",
)
async def delete_notification(
    notification_id: str,
    current_user: CurrentUser,
    notification_service: NotificationServiceDepends,
) -> None:
    """
    Delete a notification.

    Args:
        notification_id: Notification identifier
        current_user: Authenticated user from JWT
        notification_service: Notification service

    Raises:
        HTTPException: If notification not found or doesn't belong to user
    """
    try:
        await notification_service.delete_notification(
            notification_id, current_user.id
        )
        logger.info(f"Deleted notification {notification_id}")

    except ValueError as e:
        logger.warning(f"Failed to delete notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:
        logger.error(
            f"Failed to delete notification {notification_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification",
        )
