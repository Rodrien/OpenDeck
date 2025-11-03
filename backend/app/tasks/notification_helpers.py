"""
Celery Task Notification Helpers

Helper functions for sending notifications from Celery background tasks.
These functions provide synchronous wrappers around the async notification service.
"""

import asyncio
import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.db.postgres_repo import PostgresUserFCMTokenRepo, PostgresNotificationRepo
from app.services.fcm_service import FCMService
from app.services.notification_service import NotificationService


logger = logging.getLogger(__name__)


def _get_notification_service(db: Session) -> NotificationService:
    """
    Get notification service instance for Celery tasks.

    Args:
        db: Database session

    Returns:
        Configured notification service
    """
    token_repo = PostgresUserFCMTokenRepo(db)
    notification_repo = PostgresNotificationRepo(db)
    fcm_service = FCMService(token_repo, notification_repo)
    return NotificationService(notification_repo, fcm_service)


def notify_user_sync(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    metadata: Optional[Dict] = None,
    image_url: Optional[str] = None,
) -> None:
    """
    Synchronous wrapper for sending notifications from Celery tasks.

    This function creates its own database session and runs the async
    notification service in a new event loop.

    Usage in Celery tasks:
        notify_user_sync(
            user_id=user.id,
            notification_type='success',
            title='Task Complete',
            message='Your document has been processed',
            action_url='/decks/123'
        )

    Args:
        user_id: User identifier
        notification_type: Type of notification (info, success, warning, error)
        title: Notification title
        message: Notification message
        action_url: Optional URL to navigate to
        metadata: Optional metadata dictionary
        image_url: Optional image URL

    Raises:
        Exception: If notification sending fails
    """
    db = SessionLocal()
    try:
        # Get notification service
        notification_service = _get_notification_service(db)

        # Run async function in sync context
        asyncio.run(
            notification_service.send_notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
                metadata=metadata,
                image_url=image_url,
            )
        )

        # Commit the transaction to persist notification history
        db.commit()
        logger.info(f"Notification sent to user {user_id}: {title}")

    except Exception as e:
        logger.error(f"Failed to send notification to user {user_id}: {e}", exc_info=True)
        db.rollback()
        raise

    finally:
        db.close()


def notify_success(
    user_id: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """
    Helper for sending success notifications.

    Args:
        user_id: User identifier
        title: Notification title
        message: Notification message
        action_url: Optional URL to navigate to
        metadata: Optional metadata dictionary

    Example:
        notify_success(
            user_id='user-123',
            title='Document Processed',
            message='Successfully generated 25 flashcards',
            action_url='/decks/abc-123'
        )
    """
    notify_user_sync(
        user_id=user_id,
        notification_type="success",
        title=title,
        message=message,
        action_url=action_url,
        metadata=metadata,
    )


def notify_error(
    user_id: str,
    title: str,
    message: str,
    error_details: Optional[Dict] = None,
) -> None:
    """
    Helper for sending error notifications.

    Args:
        user_id: User identifier
        title: Notification title
        message: Notification message
        error_details: Optional error details dictionary

    Example:
        notify_error(
            user_id='user-123',
            title='Processing Failed',
            message='Failed to process document.pdf',
            error_details={'error': 'Invalid file format'}
        )
    """
    notify_user_sync(
        user_id=user_id,
        notification_type="error",
        title=title,
        message=message,
        metadata={"error": error_details} if error_details else None,
    )


def notify_info(
    user_id: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """
    Helper for sending info notifications.

    Args:
        user_id: User identifier
        title: Notification title
        message: Notification message
        action_url: Optional URL to navigate to
        metadata: Optional metadata dictionary

    Example:
        notify_info(
            user_id='user-123',
            title='Processing Started',
            message='Your document is being processed',
            action_url='/documents/abc-123'
        )
    """
    notify_user_sync(
        user_id=user_id,
        notification_type="info",
        title=title,
        message=message,
        action_url=action_url,
        metadata=metadata,
    )


def notify_warning(
    user_id: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> None:
    """
    Helper for sending warning notifications.

    Args:
        user_id: User identifier
        title: Notification title
        message: Notification message
        action_url: Optional URL to navigate to
        metadata: Optional metadata dictionary

    Example:
        notify_warning(
            user_id='user-123',
            title='Low Quality Source',
            message='Some text could not be extracted clearly',
            action_url='/decks/abc-123'
        )
    """
    notify_user_sync(
        user_id=user_id,
        notification_type="warning",
        title=title,
        message=message,
        action_url=action_url,
        metadata=metadata,
    )


# Example Celery task integration (for reference)
"""
from celery import shared_task
from app.tasks.notification_helpers import notify_success, notify_error

@shared_task(bind=True)
def process_document(self, user_id: str, document_id: str, filename: str):
    '''Process uploaded document and generate flashcards.'''

    try:
        # Processing logic...
        result = extract_and_generate_flashcards(document_id)

        # Notify success
        notify_success(
            user_id=user_id,
            title='Document Processed',
            message=f'Generated {result["card_count"]} flashcards from "{filename}"',
            action_url=f'/decks/{result["deck_id"]}'
        )

        return result

    except Exception as e:
        # Notify error
        notify_error(
            user_id=user_id,
            title='Processing Failed',
            message=f'Failed to process "{filename}": {str(e)}',
            error_details={
                'document_id': document_id,
                'filename': filename,
                'error': str(e)
            }
        )
        raise
"""
