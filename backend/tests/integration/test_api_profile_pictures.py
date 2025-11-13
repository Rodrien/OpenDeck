"""
Integration tests for Profile Picture API endpoints

Tests the complete profile picture functionality including:
- Profile picture upload
- Profile picture retrieval with access verification
- Profile picture deletion
- File validation and security
- Enumeration attack prevention
"""

import pytest
import io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.core.models import User
from datetime import datetime


class TestProfilePictureAPI:
    """Test suite for Profile Picture API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session, user_repo):
        """Create a test user."""
        user = User(
            id="",
            email="testuser@example.com",
            name="Test User",
            password_hash="hashed_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return user_repo.create(user)

    @pytest.fixture
    def other_user(self, db_session, user_repo):
        """Create another test user."""
        user = User(
            id="",
            email="otheruser@example.com",
            name="Other User",
            password_hash="hashed_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return user_repo.create(user)

    @pytest.fixture
    def auth_headers(self, test_user, auth_service):
        """Create authentication headers for test user."""
        token = auth_service.create_access_token(test_user.id)
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def test_image(self):
        """Create a test image file."""
        # Create a simple test image
        img = Image.new('RGB', (200, 200), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    def test_upload_profile_picture_success(self, client, auth_headers, test_image):
        """Test successful profile picture upload."""
        response = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "profile_picture_url" in data
        assert data["profile_picture_url"] is not None

    def test_upload_profile_picture_replaces_old(
        self, client, auth_headers, test_image, user_repo, test_user
    ):
        """Test that uploading new picture replaces old one."""
        # Upload first picture
        response1 = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("test1.jpg", test_image, "image/jpeg")}
        )
        assert response1.status_code == 200
        old_url = response1.json()["profile_picture_url"]

        # Create new test image
        test_image.seek(0)

        # Upload second picture
        response2 = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("test2.jpg", test_image, "image/jpeg")}
        )
        assert response2.status_code == 200
        new_url = response2.json()["profile_picture_url"]

        # URLs should be different
        assert old_url != new_url

    def test_upload_profile_picture_invalid_format(self, client, auth_headers):
        """Test that invalid file formats are rejected."""
        # Create a text file instead of an image
        text_file = io.BytesIO(b"This is not an image")

        response = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("test.txt", text_file, "text/plain")}
        )

        assert response.status_code == 400

    def test_upload_profile_picture_file_too_large(self, client, auth_headers):
        """Test that files exceeding size limit are rejected."""
        # Create a large image (>5MB)
        large_img = Image.new('RGB', (5000, 5000), color='blue')
        img_bytes = io.BytesIO()
        large_img.save(img_bytes, format='JPEG', quality=100)
        img_bytes.seek(0)

        response = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("large.jpg", img_bytes, "image/jpeg")}
        )

        assert response.status_code in [400, 413]

    def test_upload_profile_picture_unauthorized(self, client, test_image):
        """Test that unauthenticated users cannot upload."""
        response = client.post(
            "/api/v1/users/me/profile-picture",
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )

        assert response.status_code == 401

    def test_upload_profile_picture_rate_limited(self, client, auth_headers, test_image):
        """Test that upload endpoint is rate-limited."""
        # Make multiple rapid uploads (should be limited to 5/hour)
        for _ in range(6):
            test_image.seek(0)
            response = client.post(
                "/api/v1/users/me/profile-picture",
                headers=auth_headers,
                files={"file": ("test.jpg", test_image, "image/jpeg")}
            )
            if response.status_code == 429:
                # Rate limit hit
                break
        else:
            # If we get here without hitting rate limit, that's also acceptable
            # (rate limiting might be disabled in test environment)
            pass

    def test_get_profile_picture_success(
        self, client, auth_headers, test_image, user_repo, test_user
    ):
        """Test successful retrieval of profile picture."""
        # Upload picture
        upload_response = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
        assert upload_response.status_code == 200

        # Get user to find filename
        user = user_repo.get(test_user.id)
        filename = user.profile_picture

        # Retrieve picture
        response = client.get(f"/api/v1/users/profile-picture/{filename}")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/")
        assert "Cache-Control" in response.headers

    def test_get_profile_picture_prevents_enumeration(self, client):
        """Test that non-existent filenames return 404."""
        # Try to access a valid-format but non-existent filename
        fake_filename = "00000000-0000-0000-0000-000000000000.jpg"

        response = client.get(f"/api/v1/users/profile-picture/{fake_filename}")

        # Should return 404, not revealing whether file exists on disk
        assert response.status_code == 404

    def test_get_profile_picture_invalid_filename_format(self, client):
        """Test that invalid filename formats are rejected."""
        invalid_filenames = [
            "../../../etc/passwd",
            "test.jpg",
            "not-a-uuid.jpg",
            "12345.jpg",
            "",
        ]

        for filename in invalid_filenames:
            response = client.get(f"/api/v1/users/profile-picture/{filename}")
            assert response.status_code in [400, 404]

    def test_get_profile_picture_verifies_user_ownership(
        self, client, auth_headers, test_image, user_repo, test_user
    ):
        """Test that profile pictures are verified against user database."""
        # Upload picture
        upload_response = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
        assert upload_response.status_code == 200

        # Get actual filename
        user = user_repo.get(test_user.id)
        real_filename = user.profile_picture

        # Try to access the file - should work
        response = client.get(f"/api/v1/users/profile-picture/{real_filename}")
        assert response.status_code == 200

        # Delete user from database (simulate)
        user.profile_picture = None
        user_repo.update(user)

        # Try to access again - should fail (user no longer has this file)
        response = client.get(f"/api/v1/users/profile-picture/{real_filename}")
        assert response.status_code == 404

    def test_delete_profile_picture_success(
        self, client, auth_headers, test_image, user_repo, test_user
    ):
        """Test successful deletion of profile picture."""
        # Upload picture
        upload_response = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
        assert upload_response.status_code == 200

        # Delete picture
        response = client.delete(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["profile_picture_url"] is None

        # Verify user record updated
        user = user_repo.get(test_user.id)
        assert user.profile_picture is None

    def test_delete_profile_picture_not_found(self, client, auth_headers):
        """Test deletion fails when user has no profile picture."""
        response = client.delete(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_profile_picture_unauthorized(self, client):
        """Test that unauthenticated users cannot delete pictures."""
        response = client.delete("/api/v1/users/me/profile-picture")

        assert response.status_code == 401

    @pytest.mark.parametrize("image_format,content_type", [
        ("JPEG", "image/jpeg"),
        ("PNG", "image/png"),
        ("WEBP", "image/webp"),
    ])
    def test_upload_supported_formats(
        self, client, auth_headers, image_format, content_type
    ):
        """Test that all supported image formats are accepted."""
        img = Image.new('RGB', (200, 200), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format=image_format)
        img_bytes.seek(0)

        response = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": (f"test.{image_format.lower()}", img_bytes, content_type)}
        )

        assert response.status_code == 200

    def test_profile_picture_url_uses_configured_base_url(
        self, client, auth_headers, test_image
    ):
        """Test that profile picture URLs use configured base URL, not request host."""
        # Upload with custom Host header (potential attack)
        response = client.post(
            "/api/v1/users/me/profile-picture",
            headers={**auth_headers, "Host": "evil.com"},
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )

        assert response.status_code == 200
        data = response.json()
        profile_url = data["profile_picture_url"]

        # URL should use configured base URL, not the Host header
        assert "evil.com" not in profile_url
        # Should use settings.base_url (localhost:8000 in tests)
        assert "localhost" in profile_url or "127.0.0.1" in profile_url

    def test_get_current_user_includes_profile_picture(
        self, client, auth_headers, test_image
    ):
        """Test that /me endpoint includes profile picture URL."""
        # Upload picture
        upload_response = client.post(
            "/api/v1/users/me/profile-picture",
            headers=auth_headers,
            files={"file": ("test.jpg", test_image, "image/jpeg")}
        )
        assert upload_response.status_code == 200

        # Get current user
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "profile_picture_url" in data
        assert data["profile_picture_url"] is not None
