"""Integration tests for authentication API endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestAuthAPI:
    """Integration tests for authentication endpoints."""

    def test_register_user_success(self, client: TestClient, test_user_data: dict):
        """Test successful user registration."""
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["name"] == test_user_data["name"]
        assert "id" in data
        assert "password" not in data

    def test_register_user_duplicate_email(self, client: TestClient, test_user_data: dict):
        """Test registration with duplicate email."""
        # First registration
        client.post("/api/v1/auth/register", json=test_user_data)

        # Second registration with same email
        response = client.post("/api/v1/auth/register", json=test_user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_login_success(self, client: TestClient, test_user_data: dict):
        """Test successful login."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)

        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_wrong_password(self, client: TestClient, test_user_data: dict):
        """Test login with wrong password."""
        # Register user first
        client.post("/api/v1/auth/register", json=test_user_data)

        # Login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent user."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "testpassword123"
        }
        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    def test_refresh_token(self, client: TestClient, test_user_data: dict):
        """Test token refresh."""
        # Register and login
        client.post("/api/v1/auth/register", json=test_user_data)
        login_response = client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client: TestClient):
        """Test token refresh with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })

        assert response.status_code == 401
