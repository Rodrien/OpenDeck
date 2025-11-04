"""
Notification Service

Business logic for managing notifications including sending push notifications,
retrieving notification history, and managing read/unread status.
"""

import logging
from typing import List, Optional, Dict, Any
from app.core.models import Notification
from app.core.interfaces import NotificationRepository
from app.services.fcm_service import FCMService


logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for notification business logic.

    Coordinates between FCM sending and notification history management.
    """

    def __init__(
        self,
        notification_repo: NotificationRepository,
        fcm_service: FCMService,
    ) -> None:
        """
        Initialize notification service.

        Args:
            notification_repo: Repository for notification data access
            fcm_service: Service for sending FCM notifications
        """
        self.repo = notification_repo
        self.fcm = fcm_service

    async def send_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification via FCM and save to history.

        Args:
            user_id: User identifier
            type: Notification type (info, success, warning, error)
            title: Notification title
            message: Notification message
            action_url: Optional URL to navigate to
            metadata: Optional metadata dictionary
            image_url: Optional image URL

        Returns:
            Dictionary with send results
        """
        logger.info(f"Sending {type} notification to user {user_id}: {title}")

        try:
            result = await self.fcm.send_to_user(
                user_id=user_id,
                title=title,
                body=message,
                notification_type=type,
                action_url=action_url,
                metadata=metadata,
                image_url=image_url,
            )
            return result

        except Exception as e:
            logger.error(
                f"Failed to send notification to user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """
        Get notification history for user.

        Args:
            user_id: User identifier
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip

        Returns:
            List of notifications
        """
        try:
            notifications = self.repo.get_by_user(
                user_id=user_id,
                unread_only=unread_only,
                limit=limit,
                offset=offset,
            )
            logger.debug(
                f"Retrieved {len(notifications)} notifications for user {user_id}"
            )
            return notifications

        except Exception as e:
            logger.error(
                f"Failed to retrieve notifications for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def mark_as_read(self, notification_id: str, user_id: str) -> None:
        """
        Mark single notification as read.

        Verifies notification belongs to user before marking as read.

        Args:
            notification_id: Notification identifier
            user_id: User identifier for authorization check

        Raises:
            ValueError: If notification not found or doesn't belong to user
        """
        try:
            # Verify notification belongs to user
            notification = self.repo.get(notification_id)
            if not notification:
                raise ValueError(f"Notification {notification_id} not found")

            if notification.user_id != user_id:
                raise ValueError(
                    f"Notification {notification_id} does not belong to user {user_id}"
                )

            # Mark as read
            self.repo.mark_as_read(notification_id)
            logger.debug(f"Marked notification {notification_id} as read")

        except Exception as e:
            logger.error(
                f"Failed to mark notification {notification_id} as read: {e}",
                exc_info=True,
            )
            raise

    async def mark_all_as_read(self, user_id: str) -> None:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: User identifier
        """
        try:
            self.repo.mark_all_as_read(user_id)
            logger.info(f"Marked all notifications as read for user {user_id}")

        except Exception as e:
            logger.error(
                f"Failed to mark all notifications as read for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: User identifier

        Returns:
            Number of unread notifications
        """
        try:
            count = self.repo.count_unread(user_id)
            logger.debug(f"User {user_id} has {count} unread notifications")
            return count

        except Exception as e:
            logger.error(
                f"Failed to count unread notifications for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def delete_notification(
        self, notification_id: str, user_id: str
    ) -> None:
        """
        Delete a notification.

        Verifies notification belongs to user before deletion.

        Args:
            notification_id: Notification identifier
            user_id: User identifier for authorization check

        Raises:
            ValueError: If notification not found or doesn't belong to user
        """
        try:
            # Verify notification belongs to user
            notification = self.repo.get(notification_id)
            if not notification:
                raise ValueError(f"Notification {notification_id} not found")

            if notification.user_id != user_id:
                raise ValueError(
                    f"Notification {notification_id} does not belong to user {user_id}"
                )

            # Delete notification
            self.repo.delete(notification_id)
            logger.info(f"Deleted notification {notification_id}")

        except Exception as e:
            logger.error(
                f"Failed to delete notification {notification_id}: {e}",
                exc_info=True,
            )
            raise
