"""Unit tests for AuthService"""

import pytest
from unittest.mock import Mock
from app.services.auth_service import AuthService
from app.core.models import User


class TestAuthService:
    """Test cases for authentication service."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert AuthService.verify_password(password, hashed)

    def test_verify_password_success(self):
        """Test successful password verification."""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = AuthService.hash_password(password)

        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_create_access_token(self):
        """Test access token creation."""
        mock_repo = Mock()
        auth_service = AuthService(mock_repo)

        user_id = "test-user-id"
        token = auth_service.create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        mock_repo = Mock()
        auth_service = AuthService(mock_repo)

        user_id = "test-user-id"
        token = auth_service.create_refresh_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self):
        """Test access token verification."""
        mock_repo = Mock()
        auth_service = AuthService(mock_repo)

        user_id = "test-user-id"
        token = auth_service.create_access_token(user_id)
        verified_user_id = auth_service.verify_token(token, token_type="access")

        assert verified_user_id == user_id

    def test_verify_refresh_token(self):
        """Test refresh token verification."""
        mock_repo = Mock()
        auth_service = AuthService(mock_repo)

        user_id = "test-user-id"
        token = auth_service.create_refresh_token(user_id)
        verified_user_id = auth_service.verify_token(token, token_type="refresh")

        assert verified_user_id == user_id

    def test_verify_token_invalid(self):
        """Test invalid token verification."""
        mock_repo = Mock()
        auth_service = AuthService(mock_repo)

        invalid_token = "invalid.token.here"
        result = auth_service.verify_token(invalid_token)

        assert result is None

    def test_verify_token_wrong_type(self):
        """Test token verification with wrong type."""
        mock_repo = Mock()
        auth_service = AuthService(mock_repo)

        user_id = "test-user-id"
        access_token = auth_service.create_access_token(user_id)

        # Try to verify access token as refresh token
        result = auth_service.verify_token(access_token, token_type="refresh")

        assert result is None

    def test_register_user_success(self):
        """Test successful user registration."""
        mock_repo = Mock()
        mock_repo.get_by_email.return_value = None
        mock_repo.create.return_value = User(
            id="test-id",
            email="test@example.com",
            name="Test User",
            password_hash="hashed_password"
        )

        auth_service = AuthService(mock_repo)
        user = auth_service.register_user(
            email="test@example.com",
            name="Test User",
            password="testpassword123"
        )

        assert user.email == "test@example.com"
        assert user.name == "Test User"
        mock_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_repo.create.assert_called_once()

    def test_register_user_duplicate_email(self):
        """Test user registration with existing email."""
        mock_repo = Mock()
        mock_repo.get_by_email.return_value = User(
            id="existing-id",
            email="test@example.com",
            name="Existing User",
            password_hash="hashed_password"
        )

        auth_service = AuthService(mock_repo)

        with pytest.raises(ValueError, match="Email already registered"):
            auth_service.register_user(
                email="test@example.com",
                name="Test User",
                password="testpassword123"
            )

    def test_authenticate_user_success(self):
        """Test successful user authentication."""
        password = "testpassword123"
        hashed_password = AuthService.hash_password(password)

        mock_repo = Mock()
        mock_repo.get_by_email.return_value = User(
            id="test-id",
            email="test@example.com",
            name="Test User",
            password_hash=hashed_password
        )

        auth_service = AuthService(mock_repo)
        user = auth_service.authenticate_user(
            email="test@example.com",
            password=password
        )

        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        password = "testpassword123"
        hashed_password = AuthService.hash_password(password)

        mock_repo = Mock()
        mock_repo.get_by_email.return_value = User(
            id="test-id",
            email="test@example.com",
            name="Test User",
            password_hash=hashed_password
        )

        auth_service = AuthService(mock_repo)
        user = auth_service.authenticate_user(
            email="test@example.com",
            password="wrongpassword"
        )

        assert user is None

    def test_authenticate_user_not_found(self):
        """Test authentication with non-existent user."""
        mock_repo = Mock()
        mock_repo.get_by_email.return_value = None

        auth_service = AuthService(mock_repo)
        user = auth_service.authenticate_user(
            email="nonexistent@example.com",
            password="testpassword123"
        )

        assert user is None
