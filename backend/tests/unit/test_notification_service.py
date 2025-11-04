"""Unit tests for NotificationService"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime
from app.services.notification_service import NotificationService
from app.core.models import Notification


class TestNotificationService:
    """Test cases for notification service."""

    @pytest.fixture
    def mock_notification_repo(self):
        """Create a mock notification repository."""
        mock = Mock()
        mock.create = AsyncMock()
        mock.get_by_id = AsyncMock()
        mock.get_user_notifications = AsyncMock()
        mock.get_unread_count = AsyncMock()
        mock.mark_as_read = AsyncMock()
        mock.mark_all_as_read = AsyncMock()
        return mock

    @pytest.fixture
    def mock_fcm_service(self):
        """Create a mock FCM service."""
        mock = Mock()
        mock.send_to_user = AsyncMock()
        return mock

    @pytest.fixture
    def notification_service(self, mock_notification_repo, mock_fcm_service):
        """Create notification service instance with mocked dependencies."""
        return NotificationService(mock_notification_repo, mock_fcm_service)

    @pytest.mark.asyncio
    async def test_send_notification_success(
        self, notification_service, mock_fcm_service
    ):
        """Test successful notification send."""
        mock_fcm_service.send_to_user.return_value = {
            "success_count": 2,
            "failure_count": 0,
            "invalid_tokens": []
        }

        result = await notification_service.send_notification(
            user_id="user-123",
            type="success",
            title="Test Success",
            message="Operation completed successfully"
        )

        assert result["success_count"] == 2
        assert result["failure_count"] == 0
        mock_fcm_service.send_to_user.assert_called_once_with(
            user_id="user-123",
            title="Test Success",
            body="Operation completed successfully",
            notification_type="success",
            action_url=None,
            metadata=None,
            image_url=None
        )

    @pytest.mark.asyncio
    async def test_send_notification_with_action_url(
        self, notification_service, mock_fcm_service
    ):
        """Test sending notification with action URL."""
        mock_fcm_service.send_to_user.return_value = {
            "success_count": 1,
            "failure_count": 0,
            "invalid_tokens": []
        }

        await notification_service.send_notification(
            user_id="user-123",
            type="info",
            title="New Deck",
            message="A new deck has been created",
            action_url="/decks/deck-123"
        )

        mock_fcm_service.send_to_user.assert_called_once()
        call_kwargs = mock_fcm_service.send_to_user.call_args.kwargs
        assert call_kwargs["action_url"] == "/decks/deck-123"

    @pytest.mark.asyncio
    async def test_send_notification_with_metadata(
        self, notification_service, mock_fcm_service
    ):
        """Test sending notification with custom metadata."""
        mock_fcm_service.send_to_user.return_value = {
            "success_count": 1,
            "failure_count": 0,
            "invalid_tokens": []
        }

        metadata = {"deck_id": "deck-123", "card_count": 25}

        await notification_service.send_notification(
            user_id="user-123",
            type="success",
            title="Deck Processed",
            message="25 cards generated",
            metadata=metadata
        )

        mock_fcm_service.send_to_user.assert_called_once()
        call_kwargs = mock_fcm_service.send_to_user.call_args.kwargs
        assert call_kwargs["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_get_user_notifications(
        self, notification_service, mock_notification_repo
    ):
        """Test fetching user notifications."""
        mock_notifications = [
            Notification(
                id="notif-1",
                user_id="user-123",
                type="success",
                title="Test 1",
                message="Message 1",
                read=False,
                sent_at=datetime.now()
            ),
            Notification(
                id="notif-2",
                user_id="user-123",
                type="info",
                title="Test 2",
                message="Message 2",
                read=True,
                sent_at=datetime.now()
            )
        ]
        mock_notification_repo.get_user_notifications.return_value = mock_notifications

        notifications = await notification_service.get_user_notifications(
            user_id="user-123",
            limit=10,
            offset=0
        )

        assert len(notifications) == 2
        assert notifications[0].id == "notif-1"
        assert notifications[1].id == "notif-2"
        mock_notification_repo.get_user_notifications.assert_called_once_with(
            user_id="user-123",
            limit=10,
            offset=0,
            unread_only=False
        )

    @pytest.mark.asyncio
    async def test_get_user_notifications_unread_only(
        self, notification_service, mock_notification_repo
    ):
        """Test fetching only unread notifications."""
        mock_notifications = [
            Notification(
                id="notif-1",
                user_id="user-123",
                type="success",
                title="Test 1",
                message="Message 1",
                read=False,
                sent_at=datetime.now()
            )
        ]
        mock_notification_repo.get_user_notifications.return_value = mock_notifications

        notifications = await notification_service.get_user_notifications(
            user_id="user-123",
            unread_only=True
        )

        assert len(notifications) == 1
        assert notifications[0].read is False
        mock_notification_repo.get_user_notifications.assert_called_once_with(
            user_id="user-123",
            limit=20,
            offset=0,
            unread_only=True
        )

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self, notification_service, mock_notification_repo
    ):
        """Test getting unread notification count."""
        mock_notification_repo.get_unread_count.return_value = 5

        count = await notification_service.get_unread_count(user_id="user-123")

        assert count == 5
        mock_notification_repo.get_unread_count.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_mark_notification_as_read(
        self, notification_service, mock_notification_repo
    ):
        """Test marking a notification as read."""
        mock_notification = Notification(
            id="notif-1",
            user_id="user-123",
            type="info",
            title="Test",
            message="Test message",
            read=True,
            sent_at=datetime.now(),
            read_at=datetime.now()
        )
        mock_notification_repo.mark_as_read.return_value = mock_notification

        result = await notification_service.mark_as_read(
            notification_id="notif-1",
            user_id="user-123"
        )

        assert result is not None
        assert result.read is True
        assert result.read_at is not None
        mock_notification_repo.mark_as_read.assert_called_once_with(
            "notif-1", "user-123"
        )

    @pytest.mark.asyncio
    async def test_mark_all_as_read(
        self, notification_service, mock_notification_repo
    ):
        """Test marking all notifications as read."""
        mock_notification_repo.mark_all_as_read.return_value = 3

        count = await notification_service.mark_all_as_read(user_id="user-123")

        assert count == 3
        mock_notification_repo.mark_all_as_read.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_get_notification_by_id(
        self, notification_service, mock_notification_repo
    ):
        """Test getting a specific notification by ID."""
        mock_notification = Notification(
            id="notif-1",
            user_id="user-123",
            type="success",
            title="Test",
            message="Test message",
            read=False,
            sent_at=datetime.now()
        )
        mock_notification_repo.get_by_id.return_value = mock_notification

        notification = await notification_service.get_notification_by_id(
            notification_id="notif-1",
            user_id="user-123"
        )

        assert notification is not None
        assert notification.id == "notif-1"
        assert notification.user_id == "user-123"
        mock_notification_repo.get_by_id.assert_called_once_with("notif-1", "user-123")

    @pytest.mark.asyncio
    async def test_send_notification_types(
        self, notification_service, mock_fcm_service
    ):
        """Test sending different notification types."""
        mock_fcm_service.send_to_user.return_value = {
            "success_count": 1,
            "failure_count": 0,
            "invalid_tokens": []
        }

        notification_types = ["info", "success", "warning", "error"]

        for notif_type in notification_types:
            await notification_service.send_notification(
                user_id="user-123",
                type=notif_type,
                title=f"Test {notif_type.title()}",
                message=f"This is a {notif_type} notification"
            )

        # Should be called once for each type
        assert mock_fcm_service.send_to_user.call_count == len(notification_types)
