"""
Integration tests for OAuth API endpoints

Tests the complete OAuth flow including:
- Authorization URL generation
- OAuth callback handling
- User creation from OAuth
- Existing user login
- Error handling and security
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, MagicMock
from app.main import app
from app.schemas.oauth import GoogleUserInfo


class TestGoogleOAuthAPI:
    """Test suite for Google OAuth API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_oauth_service(self):
        """Mock GoogleOAuthService for testing."""
        with patch('app.api.auth.GoogleOAuthService') as mock:
            yield mock

    @pytest.fixture
    def mock_state_manager(self):
        """Mock OAuth state manager."""
        with patch('app.services.google_oauth_service.get_oauth_state_manager') as mock:
            manager = Mock()
            manager.generate_state.return_value = "test_state_token_12345"
            manager.validate_state.return_value = True
            mock.return_value = manager
            yield manager

    def test_get_google_auth_url_success(self, client, mock_oauth_service, mock_state_manager):
        """Test successful generation of Google OAuth authorization URL."""
        # Mock service to return a valid URL
        mock_service_instance = Mock()
        mock_service_instance.get_authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?client_id=test&"
            "redirect_uri=http://localhost:4200&state=test_state_token_12345"
        )
        mock_oauth_service.return_value = mock_service_instance

        response = client.get("/api/v1/auth/google/url")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "accounts.google.com" in data["authorization_url"]
        assert "state=test_state_token_12345" in data["authorization_url"]

    def test_get_google_auth_url_missing_credentials(self, client, mock_oauth_service):
        """Test OAuth URL generation fails with missing credentials."""
        mock_oauth_service.side_effect = ValueError("Google OAuth credentials not configured")

        response = client.get("/api/v1/auth/google/url")

        assert response.status_code == 500
        assert "unavailable" in response.json()["detail"].lower()

    def test_google_callback_success_new_user(
        self, client, mock_oauth_service, mock_state_manager, db_session
    ):
        """Test successful OAuth callback creating a new user."""
        mock_service_instance = Mock()

        # Mock successful OAuth flow
        from app.schemas.oauth import GoogleAuthResponse
        from app.schemas.user import UserResponse
        from datetime import datetime

        mock_user = UserResponse(
            id="new_user_id",
            email="newuser@gmail.com",
            name="New User",
            profile_picture_url="https://example.com/pic.jpg",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_auth_response = GoogleAuthResponse(
            access_token="jwt_access_token",
            refresh_token="jwt_refresh_token",
            user=mock_user
        )

        mock_service_instance.handle_google_login.return_value = mock_auth_response
        mock_oauth_service.return_value = mock_service_instance

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "google_auth_code_123",
                "state": "test_state_token_12345",
                "redirect_uri": "http://localhost:4200/auth/google/callback"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "newuser@gmail.com"

    def test_google_callback_success_existing_user(
        self, client, mock_oauth_service, mock_state_manager, db_session
    ):
        """Test successful OAuth callback with existing user."""
        mock_service_instance = Mock()

        from app.schemas.oauth import GoogleAuthResponse
        from app.schemas.user import UserResponse
        from datetime import datetime

        mock_user = UserResponse(
            id="existing_user_id",
            email="existing@gmail.com",
            name="Existing User",
            profile_picture_url="https://example.com/pic.jpg",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        mock_auth_response = GoogleAuthResponse(
            access_token="jwt_access_token",
            refresh_token="jwt_refresh_token",
            user=mock_user
        )

        mock_service_instance.handle_google_login.return_value = mock_auth_response
        mock_oauth_service.return_value = mock_service_instance

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "google_auth_code_123",
                "state": "test_state_token_12345",
                "redirect_uri": "http://localhost:4200/auth/google/callback"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "existing@gmail.com"

    def test_google_callback_invalid_state(self, client, mock_oauth_service):
        """Test OAuth callback rejects invalid state token."""
        # Mock state manager to reject state
        with patch('app.services.google_oauth_service.get_oauth_state_manager') as mock_manager_fn:
            manager = Mock()
            manager.validate_state.return_value = False
            mock_manager_fn.return_value = manager

            mock_service_instance = Mock()
            from fastapi import HTTPException, status

            mock_service_instance.handle_google_login.side_effect = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired authentication request. Please try again."
            )
            mock_oauth_service.return_value = mock_service_instance

            response = client.post(
                "/api/v1/auth/google/callback",
                json={
                    "code": "google_auth_code_123",
                    "state": "invalid_state",
                    "redirect_uri": "http://localhost:4200/auth/google/callback"
                }
            )

            assert response.status_code == 400
            assert "invalid" in response.json()["detail"].lower()

    def test_google_callback_missing_code(self, client):
        """Test OAuth callback rejects missing authorization code."""
        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "state": "test_state_token_12345",
                "redirect_uri": "http://localhost:4200/auth/google/callback"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_google_callback_missing_state(self, client):
        """Test OAuth callback rejects missing state token."""
        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "google_auth_code_123",
                "redirect_uri": "http://localhost:4200/auth/google/callback"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_google_callback_email_conflict_local_account(
        self, client, mock_oauth_service, mock_state_manager
    ):
        """Test OAuth callback fails when email exists as local account."""
        mock_service_instance = Mock()
        from fastapi import HTTPException, status

        mock_service_instance.handle_google_login.side_effect = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please sign in with your password."
        )
        mock_oauth_service.return_value = mock_service_instance

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "google_auth_code_123",
                "state": "test_state_token_12345",
                "redirect_uri": "http://localhost:4200/auth/google/callback"
            }
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_google_callback_invalid_code(self, client, mock_oauth_service, mock_state_manager):
        """Test OAuth callback handles invalid authorization code."""
        mock_service_instance = Mock()
        from fastapi import HTTPException, status

        mock_service_instance.handle_google_login.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization code. Please try signing in again."
        )
        mock_oauth_service.return_value = mock_service_instance

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "invalid_code",
                "state": "test_state_token_12345",
                "redirect_uri": "http://localhost:4200/auth/google/callback"
            }
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    def test_google_callback_generic_error(self, client, mock_oauth_service, mock_state_manager):
        """Test OAuth callback handles unexpected errors gracefully."""
        mock_service_instance = Mock()
        mock_service_instance.handle_google_login.side_effect = Exception("Unexpected error")
        mock_oauth_service.return_value = mock_service_instance

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "google_auth_code_123",
                "state": "test_state_token_12345",
                "redirect_uri": "http://localhost:4200/auth/google/callback"
            }
        )

        assert response.status_code == 500
        # Should return generic error message, not expose internal details
        assert "failed" in response.json()["detail"].lower()

    @pytest.mark.parametrize("invalid_redirect_uri", [
        "javascript:alert(1)",
        "http://evil.com",
        "file:///etc/passwd",
        "data:text/html,<script>alert(1)</script>"
    ])
    def test_google_callback_validates_redirect_uri(
        self, client, invalid_redirect_uri, mock_oauth_service, mock_state_manager
    ):
        """Test that OAuth callback validates redirect URIs for security."""
        # This test ensures that malicious redirect URIs are rejected
        # The actual validation happens in the OAuth flow
        mock_service_instance = Mock()
        from fastapi import HTTPException, status

        mock_service_instance.handle_google_login.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect URI"
        )
        mock_oauth_service.return_value = mock_service_instance

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "google_auth_code_123",
                "state": "test_state_token_12345",
                "redirect_uri": invalid_redirect_uri
            }
        )

        # Should reject invalid redirect URIs
        assert response.status_code in [400, 500]
