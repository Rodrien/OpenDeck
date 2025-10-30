"""
Firebase Cloud Messaging Service

Handles sending push notifications via Firebase Cloud Messaging.
Manages FCM tokens and automatically cleans up invalid tokens.
"""

import logging
from typing import List, Optional, Dict, Any
from firebase_admin import messaging

from app.core.interfaces import UserFCMTokenRepository, NotificationRepository
from app.core.firebase import get_firebase_messaging, is_firebase_enabled


logger = logging.getLogger(__name__)


class FCMService:
    """
    Service for sending Firebase Cloud Messages.

    Handles push notification delivery via Firebase Admin SDK with automatic
    token cleanup for invalid/expired tokens.
    """

    def __init__(
        self,
        token_repo: UserFCMTokenRepository,
        notification_repo: NotificationRepository,
    ) -> None:
        """
        Initialize FCM service.

        Args:
            token_repo: Repository for FCM token data access
            notification_repo: Repository for notification history
        """
        self.token_repo = token_repo
        self.notification_repo = notification_repo

    async def send_notification(
        self,
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
        action_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple devices.

        Args:
            fcm_tokens: List of FCM token strings
            title: Notification title
            body: Notification body text
            data: Optional data payload (all values must be strings)
            image_url: Optional image URL
            action_url: Optional URL to navigate to on click

        Returns:
            Dictionary with:
                - success_count: Number of successful sends
                - failure_count: Number of failed sends
                - invalid_tokens: List of invalid token strings
        """
        if not fcm_tokens:
            logger.debug("No FCM tokens provided, skipping send")
            return {"success_count": 0, "failure_count": 0, "invalid_tokens": []}

        # Check if Firebase is enabled
        fcm = get_firebase_messaging()
        if fcm is None:
            logger.warning(
                "Firebase not initialized. Notification not sent via FCM. "
                "Notification will only be saved to database."
            )
            return {"success_count": 0, "failure_count": len(fcm_tokens), "invalid_tokens": []}

        # Build notification payload
        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url,
        )

        # Build data payload (all values must be strings)
        payload_data = data or {}
        if action_url:
            payload_data["action_url"] = action_url

        # Build messages for each token
        messages = [
            messaging.Message(
                notification=notification,
                data=payload_data,
                token=token,
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon="/assets/images/opendeck-icon.png",
                        badge="/assets/images/badge-icon.png",
                        require_interaction=False,
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=action_url or "/dashboard"
                    ),
                ),
            )
            for token in fcm_tokens
        ]

        # Send batch (max 500 messages per batch)
        try:
            response = messaging.send_all(messages)

            # Identify invalid tokens for cleanup
            invalid_tokens = [
                fcm_tokens[i]
                for i, resp in enumerate(response.responses)
                if not resp.success and self._is_invalid_token_error(resp.exception)
            ]

            logger.info(
                f"FCM batch sent: {response.success_count} success, "
                f"{response.failure_count} failure, "
                f"{len(invalid_tokens)} invalid tokens"
            )

            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "invalid_tokens": invalid_tokens,
            }

        except Exception as e:
            logger.error(f"FCM send error: {e}", exc_info=True)
            return {
                "success_count": 0,
                "failure_count": len(fcm_tokens),
                "invalid_tokens": [],
            }

    async def send_to_user(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: str = "info",
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        image_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send notification to all user's active devices and save to history.

        Args:
            user_id: User identifier
            title: Notification title
            body: Notification body text
            notification_type: Type of notification (info, success, warning, error)
            action_url: Optional URL to navigate to on click
            metadata: Optional metadata dictionary
            image_url: Optional image URL

        Returns:
            Dictionary with send results including success/failure counts
        """
        # Get user's active FCM tokens
        tokens = self.token_repo.get_active_tokens(user_id)

        if not tokens:
            logger.info(f"No active FCM tokens for user {user_id}")
            # Still save to notification history even without tokens
            self._save_notification_history(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=body,
                action_url=action_url,
                metadata=metadata,
                image_url=image_url,
            )
            return {"success_count": 0, "failure_count": 0, "invalid_tokens": []}

        # Send via FCM
        result = await self.send_notification(
            fcm_tokens=[t.fcm_token for t in tokens],
            title=title,
            body=body,
            data={"type": notification_type, **(metadata or {})},
            image_url=image_url,
            action_url=action_url,
        )

        # Deactivate invalid tokens
        if result["invalid_tokens"]:
            self.token_repo.deactivate_tokens(result["invalid_tokens"])
            logger.info(f"Deactivated {len(result['invalid_tokens'])} invalid tokens")

        # Save to notification history
        self._save_notification_history(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=body,
            action_url=action_url,
            metadata=metadata,
            image_url=image_url,
        )

        return result

    def _save_notification_history(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str],
        metadata: Optional[Dict],
        image_url: Optional[str],
    ) -> None:
        """
        Save notification to database history.

        Args:
            user_id: User identifier
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            action_url: Optional action URL
            metadata: Optional metadata
            image_url: Optional image URL
        """
        try:
            self.notification_repo.create(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
                metadata=metadata,
                image_url=image_url,
            )
            logger.debug(f"Notification saved to history for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to save notification to history: {e}", exc_info=True)

    @staticmethod
    def _is_invalid_token_error(exception: Optional[Exception]) -> bool:
        """
        Check if exception indicates an invalid/expired token.

        Args:
            exception: Exception from FCM send attempt

        Returns:
            True if token is invalid/expired, False otherwise
        """
        if exception is None:
            return False

        error_str = str(exception).lower()
        return any(
            keyword in error_str
            for keyword in [
                "invalid",
                "not found",
                "unregistered",
                "invalid-argument",
                "registration-token-not-registered",
            ]
        )
