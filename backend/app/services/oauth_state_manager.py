"""
OAuth State Manager

Manages OAuth state tokens for CSRF protection during OAuth flows.
Uses Redis for production-ready, distributed state storage with automatic expiration.
"""

import secrets
import logging
from typing import Optional
import redis
from app.config import settings

logger = logging.getLogger(__name__)


class OAuthStateManager:
    """
    Manages OAuth state tokens with Redis-backed storage.

    Uses Redis for production-ready distributed storage that:
    - Works across multiple backend instances (horizontal scaling)
    - Survives server restarts
    - Automatically expires tokens (TTL)
    - Supports single-use tokens (consume on validation)
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None, expiration_minutes: int = 10):
        """
        Initialize the OAuth state manager with Redis backend.

        Args:
            redis_client: Optional Redis client (uses settings.redis_url if not provided)
            expiration_minutes: How long state tokens remain valid (default: 10 minutes)
        """
        self._expiration_seconds = expiration_minutes * 60

        # Initialize Redis client
        if redis_client is not None:
            self._redis = redis_client
        else:
            try:
                self._redis = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self._redis.ping()
                logger.info("OAuth state manager connected to Redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis for OAuth state management: {str(e)}")
                raise RuntimeError(
                    "OAuth state manager requires Redis connection. "
                    "Ensure Redis is running and REDIS_URL is configured correctly."
                )

    def generate_state(self) -> str:
        """
        Generate a new cryptographically secure state token and store in Redis.

        Returns:
            A unique state token string

        Raises:
            RuntimeError: If Redis operation fails
        """
        try:
            state = secrets.token_urlsafe(32)
            key = self._make_key(state)

            # Store state with expiration
            self._redis.setex(
                name=key,
                time=self._expiration_seconds,
                value="1"  # Value doesn't matter, just the key existence
            )

            logger.debug(f"Generated OAuth state token (expires in {self._expiration_seconds}s)")
            return state

        except Exception as e:
            logger.error(f"Failed to generate OAuth state: {str(e)}")
            raise RuntimeError("Failed to generate authentication state. Please try again.")

    def validate_state(self, state: str) -> bool:
        """
        Validate a state token from Redis.

        Checks if the state exists in Redis. The state is consumed (deleted)
        after validation to ensure single-use only.

        Args:
            state: The state token to validate

        Returns:
            True if state is valid and not expired, False otherwise
        """
        if not state:
            logger.warning("OAuth state validation failed: empty state")
            return False

        try:
            key = self._make_key(state)

            # Check if state exists and delete it atomically (consume)
            result = self._redis.delete(key)

            if result == 0:
                logger.warning("OAuth state validation failed: state not found or expired")
                return False

            logger.debug("OAuth state validated and consumed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to validate OAuth state: {str(e)}")
            # Fail closed - reject token if we can't validate
            return False

    def _make_key(self, state: str) -> str:
        """
        Create Redis key for OAuth state token.

        Args:
            state: State token

        Returns:
            Redis key string
        """
        return f"oauth:state:{state}"


# Global instance for the application
_state_manager: Optional[OAuthStateManager] = None


def get_oauth_state_manager() -> OAuthStateManager:
    """
    Get the global OAuth state manager instance.

    Returns:
        Singleton OAuthStateManager instance backed by Redis
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = OAuthStateManager()
    return _state_manager
