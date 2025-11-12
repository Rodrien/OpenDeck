"""
OAuth State Manager

Manages OAuth state tokens for CSRF protection during OAuth flows.
Stores state tokens with expiration to prevent replay attacks.
"""

import secrets
import time
from typing import Optional
from datetime import datetime, timedelta


class OAuthStateManager:
    """
    Manages OAuth state tokens with expiration.

    Uses in-memory storage for development. For production, this should be
    replaced with Redis or a database-backed solution for horizontal scaling.
    """

    def __init__(self, expiration_minutes: int = 10):
        """
        Initialize the OAuth state manager.

        Args:
            expiration_minutes: How long state tokens remain valid (default: 10 minutes)
        """
        self._states: dict[str, float] = {}  # {state: expiration_timestamp}
        self._expiration_seconds = expiration_minutes * 60

    def generate_state(self) -> str:
        """
        Generate a new cryptographically secure state token.

        Returns:
            A unique state token string
        """
        state = secrets.token_urlsafe(32)
        expiration = time.time() + self._expiration_seconds
        self._states[state] = expiration

        # Clean up expired states to prevent memory leaks
        self._cleanup_expired()

        return state

    def validate_state(self, state: str) -> bool:
        """
        Validate a state token.

        Checks if the state exists and has not expired. The state is consumed
        (removed) after validation to prevent reuse.

        Args:
            state: The state token to validate

        Returns:
            True if state is valid and not expired, False otherwise
        """
        if not state or state not in self._states:
            return False

        expiration = self._states[state]
        current_time = time.time()

        # Remove state (consume it - single use only)
        del self._states[state]

        # Check if expired
        if current_time > expiration:
            return False

        return True

    def _cleanup_expired(self) -> None:
        """Remove expired state tokens from storage."""
        current_time = time.time()
        expired_states = [
            state for state, expiration in self._states.items()
            if current_time > expiration
        ]
        for state in expired_states:
            del self._states[state]


# Global instance for the application
_state_manager: Optional[OAuthStateManager] = None


def get_oauth_state_manager() -> OAuthStateManager:
    """
    Get the global OAuth state manager instance.

    Returns:
        Singleton OAuthStateManager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = OAuthStateManager()
    return _state_manager
