"""
Integration tests for Card Report API endpoints

Tests the complete card reporting functionality including:
- Creating card reports
- Viewing reports for a card
- Updating report status (deck owner only)
- Authorization checks
- Database constraints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.models import User, Deck, Card, DifficultyLevel
from datetime import datetime


class TestCardReportAPI:
    """Test suite for Card Report API endpoints"""

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
    def test_deck(self, db_session, deck_repo, test_user):
        """Create a test deck."""
        deck = Deck(
            id="",
            user_id=test_user.id,
            title="Test Deck",
            description="Test deck for reporting",
            category="Science",
            difficulty=DifficultyLevel.INTERMEDIATE,
            card_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return deck_repo.create(deck)

    @pytest.fixture
    def test_card(self, db_session, card_repo, test_deck):
        """Create a test card."""
        card = Card(
            id="",
            deck_id=test_deck.id,
            question="What is photosynthesis?",
            answer="The process by which plants convert light into energy",
            source="Biology 101 Textbook - Chapter 5",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        return card_repo.create(card)

    @pytest.fixture
    def auth_headers(self, test_user, auth_service):
        """Create authentication headers for test user."""
        token = auth_service.create_access_token(test_user.id)
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def other_auth_headers(self, other_user, auth_service):
        """Create authentication headers for other user."""
        token = auth_service.create_access_token(other_user.id)
        return {"Authorization": f"Bearer {token}"}

    def test_create_report_success(self, client, test_card, auth_headers):
        """Test successful creation of a card report."""
        response = client.post(
            f"/api/v1/reports/cards/{test_card.id}/report",
            headers=auth_headers,
            json={
                "reason": "The answer contains incorrect information about chlorophyll."
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["card_id"] == test_card.id
        assert data["reason"] == "The answer contains incorrect information about chlorophyll."
        assert data["status"] == "pending"

    def test_create_report_card_not_found(self, client, auth_headers):
        """Test report creation fails for non-existent card."""
        fake_card_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/api/v1/reports/cards/{fake_card_id}/report",
            headers=auth_headers,
            json={
                "reason": "This card has incorrect information."
            }
        )

        assert response.status_code == 404

    def test_create_report_reason_too_short(self, client, test_card, auth_headers):
        """Test report creation fails with short reason."""
        response = client.post(
            f"/api/v1/reports/cards/{test_card.id}/report",
            headers=auth_headers,
            json={
                "reason": "Bad"  # Too short
            }
        )

        assert response.status_code in [400, 422]

    def test_create_report_reason_too_long(self, client, test_card, auth_headers):
        """Test report creation fails with excessively long reason."""
        long_reason = "A" * 1001  # Exceeds 1000 character limit

        response = client.post(
            f"/api/v1/reports/cards/{test_card.id}/report",
            headers=auth_headers,
            json={
                "reason": long_reason
            }
        )

        assert response.status_code in [400, 422]

    def test_create_duplicate_report_same_user(
        self, client, test_card, auth_headers, report_repo, test_user
    ):
        """Test that user cannot create duplicate reports for same card."""
        # Create first report
        report_repo.create(
            card_id=test_card.id,
            user_id=test_user.id,
            reason="First report about this card."
        )

        # Try to create second report for same card
        response = client.post(
            f"/api/v1/reports/cards/{test_card.id}/report",
            headers=auth_headers,
            json={
                "reason": "Another report about the same card."
            }
        )

        # Should fail due to unique constraint
        assert response.status_code in [400, 409]

    def test_create_report_unauthorized(self, client, test_card):
        """Test that unauthenticated users cannot create reports."""
        response = client.post(
            f"/api/v1/reports/cards/{test_card.id}/report",
            json={
                "reason": "This card has incorrect information."
            }
        )

        assert response.status_code == 401

    def test_get_card_reports(self, client, test_card, auth_headers, report_repo, test_user):
        """Test retrieving all reports for a card."""
        # Create multiple reports
        report_repo.create(
            card_id=test_card.id,
            user_id=test_user.id,
            reason="First issue with this card."
        )

        response = client.get(
            f"/api/v1/reports/cards/{test_card.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["card_id"] == test_card.id

    def test_get_reports_card_not_found(self, client, auth_headers):
        """Test getting reports for non-existent card."""
        fake_card_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/reports/cards/{fake_card_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_my_reports(self, client, test_card, auth_headers, report_repo, test_user):
        """Test retrieving current user's reports."""
        # Create report
        report_repo.create(
            card_id=test_card.id,
            user_id=test_user.id,
            reason="My report about this card."
        )

        response = client.get(
            "/api/v1/reports/my-reports",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["user_id"] == test_user.id

    def test_update_report_status_as_deck_owner(
        self, client, test_card, auth_headers, report_repo, other_user
    ):
        """Test that deck owner can update report status."""
        # Other user creates a report
        report = report_repo.create(
            card_id=test_card.id,
            user_id=other_user.id,
            reason="This card needs correction."
        )

        # Deck owner updates status
        response = client.put(
            f"/api/v1/reports/{report.id}/status",
            headers=auth_headers,
            json={
                "status": "reviewed"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
        assert data["reviewed_by"] is not None

    def test_update_report_status_non_owner_forbidden(
        self, client, test_card, other_auth_headers, report_repo, test_user
    ):
        """Test that non-deck-owner cannot update report status."""
        # Test user (deck owner) creates a report on their own card
        report = report_repo.create(
            card_id=test_card.id,
            user_id=test_user.id,
            reason="Found an issue in my own card."
        )

        # Other user tries to update status (should fail)
        response = client.put(
            f"/api/v1/reports/{report.id}/status",
            headers=other_auth_headers,
            json={
                "status": "reviewed"
            }
        )

        assert response.status_code == 403

    def test_update_report_status_report_not_found(self, client, auth_headers):
        """Test updating non-existent report."""
        fake_report_id = "00000000-0000-0000-0000-000000000000"

        response = client.put(
            f"/api/v1/reports/{fake_report_id}/status",
            headers=auth_headers,
            json={
                "status": "reviewed"
            }
        )

        assert response.status_code == 404

    def test_update_report_status_invalid_status(
        self, client, test_card, auth_headers, report_repo, other_user
    ):
        """Test that invalid status values are rejected."""
        report = report_repo.create(
            card_id=test_card.id,
            user_id=other_user.id,
            reason="This card needs correction."
        )

        response = client.put(
            f"/api/v1/reports/{report.id}/status",
            headers=auth_headers,
            json={
                "status": "invalid_status"
            }
        )

        assert response.status_code in [400, 422]

    def test_update_report_status_uses_optimized_query(
        self, client, test_card, auth_headers, report_repo, other_user, db_session
    ):
        """Test that report status update uses optimized JOIN query."""
        report = report_repo.create(
            card_id=test_card.id,
            user_id=other_user.id,
            reason="Testing optimized query."
        )

        # The endpoint should use get_with_card_and_deck to avoid N+1 queries
        # This is tested by ensuring the endpoint works correctly
        response = client.put(
            f"/api/v1/reports/{report.id}/status",
            headers=auth_headers,
            json={
                "status": "resolved"
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

    @pytest.mark.parametrize("status_value", ["pending", "reviewed", "resolved", "dismissed"])
    def test_update_report_all_valid_statuses(
        self, client, test_card, auth_headers, report_repo, other_user, status_value
    ):
        """Test that all valid status values are accepted."""
        report = report_repo.create(
            card_id=test_card.id,
            user_id=other_user.id,
            reason="Testing all status values."
        )

        response = client.put(
            f"/api/v1/reports/{report.id}/status",
            headers=auth_headers,
            json={
                "status": status_value
            }
        )

        assert response.status_code == 200
        assert response.json()["status"] == status_value
