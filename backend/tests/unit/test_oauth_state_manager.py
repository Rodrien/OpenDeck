"""
Unit tests for OAuth State Manager

Tests the Redis-backed OAuth state token management including:
- State token generation
- State token validation
- State token expiration
- Single-use token consumption
- Redis connection handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import fakeredis
from app.services.oauth_state_manager import OAuthStateManager


class TestOAuthStateManager:
    """Test suite for OAuthStateManager"""

    @pytest.fixture
    def mock_redis(self):
        """Create a fake Redis instance for testing."""
        return fakeredis.FakeStrictRedis(decode_responses=True)

    @pytest.fixture
    def state_manager(self, mock_redis):
        """Create OAuthStateManager with fake Redis."""
        return OAuthStateManager(redis_client=mock_redis, expiration_minutes=10)

    def test_generate_state_creates_unique_tokens(self, state_manager):
        """Test that generate_state creates unique tokens."""
        state1 = state_manager.generate_state()
        state2 = state_manager.generate_state()

        assert state1 != state2
        assert len(state1) > 0
        assert len(state2) > 0

    def test_generate_state_stores_in_redis(self, state_manager, mock_redis):
        """Test that generated states are stored in Redis."""
        state = state_manager.generate_state()
        key = f"oauth:state:{state}"

        # Check that key exists in Redis
        assert mock_redis.exists(key) == 1

    def test_generate_state_sets_expiration(self, state_manager, mock_redis):
        """Test that generated states have TTL set."""
        state = state_manager.generate_state()
        key = f"oauth:state:{state}"

        # Check that TTL is set (should be 600 seconds = 10 minutes)
        ttl = mock_redis.ttl(key)
        assert ttl > 0
        assert ttl <= 600

    def test_validate_state_accepts_valid_token(self, state_manager):
        """Test that valid state tokens are accepted."""
        state = state_manager.generate_state()
        assert state_manager.validate_state(state) is True

    def test_validate_state_rejects_invalid_token(self, state_manager):
        """Test that invalid state tokens are rejected."""
        assert state_manager.validate_state("invalid_token") is False

    def test_validate_state_rejects_empty_token(self, state_manager):
        """Test that empty state tokens are rejected."""
        assert state_manager.validate_state("") is False
        assert state_manager.validate_state(None) is False

    def test_validate_state_consumes_token(self, state_manager, mock_redis):
        """Test that validation consumes (deletes) the token."""
        state = state_manager.generate_state()
        key = f"oauth:state:{state}"

        # Validate once
        assert state_manager.validate_state(state) is True

        # Token should be deleted from Redis
        assert mock_redis.exists(key) == 0

        # Second validation should fail
        assert state_manager.validate_state(state) is False

    def test_validate_state_single_use_only(self, state_manager):
        """Test that state tokens can only be used once."""
        state = state_manager.generate_state()

        # First validation succeeds
        assert state_manager.validate_state(state) is True

        # Second validation fails (token consumed)
        assert state_manager.validate_state(state) is False

    def test_state_expiration(self, state_manager, mock_redis):
        """Test that expired states are rejected."""
        state = state_manager.generate_state()
        key = f"oauth:state:{state}"

        # Manually expire the key
        mock_redis.delete(key)

        # Validation should fail
        assert state_manager.validate_state(state) is False

    def test_redis_connection_failure_on_init(self):
        """Test that initialization fails gracefully if Redis is unavailable."""
        with patch('redis.from_url') as mock_from_url:
            mock_redis = Mock()
            mock_redis.ping.side_effect = Exception("Connection refused")
            mock_from_url.return_value = mock_redis

            with pytest.raises(RuntimeError, match="OAuth state manager requires Redis"):
                OAuthStateManager()

    def test_generate_state_handles_redis_failure(self, state_manager):
        """Test that state generation handles Redis failures."""
        with patch.object(state_manager._redis, 'setex', side_effect=Exception("Redis error")):
            with pytest.raises(RuntimeError, match="Failed to generate authentication state"):
                state_manager.generate_state()

    def test_validate_state_handles_redis_failure(self, state_manager):
        """Test that state validation fails safely on Redis errors."""
        state = "test_state"

        with patch.object(state_manager._redis, 'delete', side_effect=Exception("Redis error")):
            # Should fail closed (reject the token)
            assert state_manager.validate_state(state) is False

    def test_custom_expiration_time(self, mock_redis):
        """Test that custom expiration time is respected."""
        custom_minutes = 5
        state_manager = OAuthStateManager(
            redis_client=mock_redis,
            expiration_minutes=custom_minutes
        )

        state = state_manager.generate_state()
        key = f"oauth:state:{state}"

        ttl = mock_redis.ttl(key)
        expected_seconds = custom_minutes * 60
        assert ttl > 0
        assert ttl <= expected_seconds

    def test_make_key_format(self, state_manager):
        """Test that Redis keys follow the expected format."""
        test_state = "abc123"
        key = state_manager._make_key(test_state)
        assert key == "oauth:state:abc123"

    def test_concurrent_state_generation(self, state_manager):
        """Test that multiple states can be generated concurrently."""
        states = [state_manager.generate_state() for _ in range(10)]

        # All states should be unique
        assert len(states) == len(set(states))

        # All states should be valid
        for state in states:
            assert state_manager.validate_state(state) is True

    def test_state_token_format(self, state_manager):
        """Test that generated state tokens are URL-safe."""
        state = state_manager.generate_state()

        # URL-safe base64 should only contain these characters
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
        assert all(c in allowed_chars for c in state)
