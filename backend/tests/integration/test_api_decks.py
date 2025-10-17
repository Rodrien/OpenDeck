"""Integration tests for deck API endpoints"""

import pytest
from fastapi.testclient import TestClient


def get_auth_headers(client: TestClient, test_user_data: dict) -> dict:
    """Helper function to get authentication headers."""
    # Register and login
    client.post("/api/v1/auth/register", json=test_user_data)
    login_response = client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestDeckAPI:
    """Integration tests for deck endpoints."""

    def test_create_deck_success(self, client: TestClient, test_user_data: dict, test_deck_data: dict):
        """Test successful deck creation."""
        headers = get_auth_headers(client, test_user_data)

        response = client.post("/api/v1/decks", json=test_deck_data, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_deck_data["title"]
        assert data["category"] == test_deck_data["category"]
        assert data["difficulty"] == test_deck_data["difficulty"]
        assert "id" in data
        assert data["card_count"] == 0

    def test_create_deck_unauthorized(self, client: TestClient, test_deck_data: dict):
        """Test deck creation without authentication."""
        response = client.post("/api/v1/decks", json=test_deck_data)

        assert response.status_code == 403  # No credentials

    def test_list_decks(self, client: TestClient, test_user_data: dict, test_deck_data: dict):
        """Test listing user's decks."""
        headers = get_auth_headers(client, test_user_data)

        # Create a deck
        client.post("/api/v1/decks", json=test_deck_data, headers=headers)

        # List decks
        response = client.get("/api/v1/decks", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        assert data["items"][0]["title"] == test_deck_data["title"]

    def test_get_deck_success(self, client: TestClient, test_user_data: dict, test_deck_data: dict):
        """Test getting a single deck."""
        headers = get_auth_headers(client, test_user_data)

        # Create a deck
        create_response = client.post("/api/v1/decks", json=test_deck_data, headers=headers)
        deck_id = create_response.json()["id"]

        # Get deck
        response = client.get(f"/api/v1/decks/{deck_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == deck_id
        assert data["title"] == test_deck_data["title"]

    def test_get_deck_not_found(self, client: TestClient, test_user_data: dict):
        """Test getting non-existent deck."""
        headers = get_auth_headers(client, test_user_data)

        response = client.get("/api/v1/decks/nonexistent-id", headers=headers)

        assert response.status_code == 404

    def test_update_deck_success(self, client: TestClient, test_user_data: dict, test_deck_data: dict):
        """Test updating a deck."""
        headers = get_auth_headers(client, test_user_data)

        # Create a deck
        create_response = client.post("/api/v1/decks", json=test_deck_data, headers=headers)
        deck_id = create_response.json()["id"]

        # Update deck
        update_data = {"title": "Updated Biology 101"}
        response = client.put(f"/api/v1/decks/{deck_id}", json=update_data, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Biology 101"
        assert data["category"] == test_deck_data["category"]  # Unchanged

    def test_delete_deck_success(self, client: TestClient, test_user_data: dict, test_deck_data: dict):
        """Test deleting a deck."""
        headers = get_auth_headers(client, test_user_data)

        # Create a deck
        create_response = client.post("/api/v1/decks", json=test_deck_data, headers=headers)
        deck_id = create_response.json()["id"]

        # Delete deck
        response = client.delete(f"/api/v1/decks/{deck_id}", headers=headers)

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/decks/{deck_id}", headers=headers)
        assert get_response.status_code == 404

    def test_list_decks_with_filters(self, client: TestClient, test_user_data: dict):
        """Test listing decks with category filter."""
        headers = get_auth_headers(client, test_user_data)

        # Create decks with different categories
        deck1 = {"title": "Deck 1", "category": "Science", "difficulty": "beginner", "description": ""}
        deck2 = {"title": "Deck 2", "category": "Math", "difficulty": "intermediate", "description": ""}

        client.post("/api/v1/decks", json=deck1, headers=headers)
        client.post("/api/v1/decks", json=deck2, headers=headers)

        # Filter by category
        response = client.get("/api/v1/decks?category=Science", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert all(item["category"] == "Science" for item in data["items"])
