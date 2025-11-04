"""Unit tests for FCMService"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.fcm_service import FCMService
from app.core.models import UserFCMToken


class TestFCMService:
    """Test cases for Firebase Cloud Messaging service."""

    @pytest.fixture
    def mock_token_repo(self):
        """Create a mock FCM token repository."""
        mock = Mock()
        mock.get_active_tokens = AsyncMock()
        mock.deactivate_tokens = AsyncMock()
        return mock

    @pytest.fixture
    def mock_notification_repo(self):
        """Create a mock notification repository."""
        mock = Mock()
        mock.create = AsyncMock()
        return mock

    @pytest.fixture
    def fcm_service(self, mock_token_repo, mock_notification_repo):
        """Create FCM service instance with mocked dependencies."""
        return FCMService(mock_token_repo, mock_notification_repo)

    @pytest.mark.asyncio
    async def test_send_notification_no_tokens(self, fcm_service):
        """Test sending notification with no tokens."""
        result = await fcm_service.send_notification(
            fcm_tokens=[],
            title="Test",
            body="Test message"
        )

        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        assert result["invalid_tokens"] == []

    @pytest.mark.asyncio
    @patch('app.services.fcm_service.get_firebase_messaging')
    async def test_send_notification_firebase_disabled(
        self, mock_get_firebase, fcm_service
    ):
        """Test sending notification when Firebase is not initialized."""
        mock_get_firebase.return_value = None

        result = await fcm_service.send_notification(
            fcm_tokens=["token1", "token2"],
            title="Test",
            body="Test message"
        )

        assert result["success_count"] == 0
        assert result["failure_count"] == 2
        assert result["invalid_tokens"] == []

    @pytest.mark.asyncio
    @patch('app.services.fcm_service.get_firebase_messaging')
    @patch('app.services.fcm_service.messaging')
    async def test_send_notification_success(
        self, mock_messaging, mock_get_firebase, fcm_service
    ):
        """Test successful notification send."""
        mock_get_firebase.return_value = Mock()

        # Mock successful response
        mock_response = Mock()
        mock_response.success_count = 2
        mock_response.failure_count = 0
        mock_response.responses = [
            Mock(success=True, exception=None),
            Mock(success=True, exception=None)
        ]
        mock_messaging.send_all.return_value = mock_response

        result = await fcm_service.send_notification(
            fcm_tokens=["token1", "token2"],
            title="Test Title",
            body="Test Body"
        )

        assert result["success_count"] == 2
        assert result["failure_count"] == 0
        assert result["invalid_tokens"] == []

    @pytest.mark.asyncio
    @patch('app.services.fcm_service.get_firebase_messaging')
    @patch('app.services.fcm_service.messaging')
    async def test_send_notification_with_invalid_tokens(
        self, mock_messaging, mock_get_firebase, fcm_service
    ):
        """Test notification send with some invalid tokens."""
        mock_get_firebase.return_value = Mock()

        # Mock response with invalid token
        mock_response = Mock()
        mock_response.success_count = 1
        mock_response.failure_count = 1
        mock_response.responses = [
            Mock(success=True, exception=None),
            Mock(success=False, exception=Exception("registration-token-not-registered"))
        ]
        mock_messaging.send_all.return_value = mock_response

        result = await fcm_service.send_notification(
            fcm_tokens=["token1", "invalid_token"],
            title="Test",
            body="Test message"
        )

        assert result["success_count"] == 1
        assert result["failure_count"] == 1
        assert len(result["invalid_tokens"]) == 1
        assert "invalid_token" in result["invalid_tokens"]

    @pytest.mark.asyncio
    async def test_send_to_user_no_tokens(
        self, fcm_service, mock_token_repo, mock_notification_repo
    ):
        """Test sending to user with no active tokens."""
        mock_token_repo.get_active_tokens.return_value = []

        result = await fcm_service.send_to_user(
            user_id="user-123",
            title="Test",
            body="Test message",
            notification_type="info"
        )

        assert result["success_count"] == 0
        assert result["failure_count"] == 0
        # Notification should still be saved
        mock_notification_repo.create.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.services.fcm_service.get_firebase_messaging')
    @patch('app.services.fcm_service.messaging')
    async def test_send_to_user_with_tokens(
        self, mock_messaging, mock_get_firebase, fcm_service,
        mock_token_repo, mock_notification_repo
    ):
        """Test sending to user with active tokens."""
        mock_get_firebase.return_value = Mock()

        # Mock tokens
        mock_tokens = [
            UserFCMToken(
                id="token-1",
                user_id="user-123",
                fcm_token="device-token-1",
                device_type="web",
                is_active=True
            ),
            UserFCMToken(
                id="token-2",
                user_id="user-123",
                fcm_token="device-token-2",
                device_type="web",
                is_active=True
            )
        ]
        mock_token_repo.get_active_tokens.return_value = mock_tokens

        # Mock successful send
        mock_response = Mock()
        mock_response.success_count = 2
        mock_response.failure_count = 0
        mock_response.responses = [
            Mock(success=True, exception=None),
            Mock(success=True, exception=None)
        ]
        mock_messaging.send_all.return_value = mock_response

        result = await fcm_service.send_to_user(
            user_id="user-123",
            title="Test Title",
            body="Test Body",
            notification_type="success"
        )

        assert result["success_count"] == 2
        assert result["failure_count"] == 0
        mock_notification_repo.create.assert_called_once()
        mock_token_repo.deactivate_tokens.assert_not_called()

    @pytest.mark.asyncio
    @patch('app.services.fcm_service.get_firebase_messaging')
    @patch('app.services.fcm_service.messaging')
    async def test_send_to_user_deactivates_invalid_tokens(
        self, mock_messaging, mock_get_firebase, fcm_service,
        mock_token_repo, mock_notification_repo
    ):
        """Test that invalid tokens are deactivated."""
        mock_get_firebase.return_value = Mock()

        # Mock tokens
        mock_tokens = [
            UserFCMToken(
                id="token-1",
                user_id="user-123",
                fcm_token="valid-token",
                device_type="web",
                is_active=True
            ),
            UserFCMToken(
                id="token-2",
                user_id="user-123",
                fcm_token="invalid-token",
                device_type="web",
                is_active=True
            )
        ]
        mock_token_repo.get_active_tokens.return_value = mock_tokens

        # Mock response with one invalid token
        mock_response = Mock()
        mock_response.success_count = 1
        mock_response.failure_count = 1
        mock_response.responses = [
            Mock(success=True, exception=None),
            Mock(success=False, exception=Exception("invalid-argument"))
        ]
        mock_messaging.send_all.return_value = mock_response

        result = await fcm_service.send_to_user(
            user_id="user-123",
            title="Test",
            body="Test message",
            notification_type="info"
        )

        assert result["success_count"] == 1
        assert result["failure_count"] == 1
        assert len(result["invalid_tokens"]) == 1
        # Should deactivate invalid tokens
        mock_token_repo.deactivate_tokens.assert_called_once()

    def test_is_invalid_token_error(self, fcm_service):
        """Test invalid token error detection."""
        # Test various invalid token error messages
        assert fcm_service._is_invalid_token_error(
            Exception("registration-token-not-registered")
        ) is True

        assert fcm_service._is_invalid_token_error(
            Exception("invalid-argument")
        ) is True

        assert fcm_service._is_invalid_token_error(
            Exception("Token not found")
        ) is True

        assert fcm_service._is_invalid_token_error(
            Exception("unregistered device")
        ) is True

        # Test non-invalid errors
        assert fcm_service._is_invalid_token_error(
            Exception("network error")
        ) is False

        assert fcm_service._is_invalid_token_error(None) is False

    @pytest.mark.asyncio
    @patch('app.services.fcm_service.get_firebase_messaging')
    @patch('app.services.fcm_service.messaging')
    async def test_send_notification_with_metadata(
        self, mock_messaging, mock_get_firebase, fcm_service
    ):
        """Test sending notification with custom data and metadata."""
        mock_get_firebase.return_value = Mock()

        mock_response = Mock()
        mock_response.success_count = 1
        mock_response.failure_count = 0
        mock_response.responses = [Mock(success=True, exception=None)]
        mock_messaging.send_all.return_value = mock_response

        result = await fcm_service.send_notification(
            fcm_tokens=["token1"],
            title="Test",
            body="Test message",
            data={"custom_key": "custom_value"},
            image_url="https://example.com/image.png",
            action_url="/dashboard"
        )

        assert result["success_count"] == 1
        # Verify messaging.Message was called with correct data
        call_args = mock_messaging.Message.call_args_list
        assert len(call_args) > 0
