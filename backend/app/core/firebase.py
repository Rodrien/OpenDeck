"""
Firebase Admin SDK Initialization

Handles Firebase initialization with singleton pattern to avoid multiple app instances.
Provides access to Firebase Cloud Messaging for sending push notifications.

TODO: Configure Firebase credentials by setting FIREBASE_CREDENTIALS_PATH environment variable
to point to your firebase-service-account.json file.
"""

import logging
from typing import Optional
import firebase_admin
from firebase_admin import credentials, messaging

from app.config import settings


logger = logging.getLogger(__name__)

# Global Firebase app instance (singleton)
_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> Optional[firebase_admin.App]:
    """
    Initialize Firebase Admin SDK with singleton pattern.

    Returns:
        Firebase app instance if initialization successful, None otherwise

    Raises:
        Exception: If Firebase initialization fails with invalid credentials
    """
    global _firebase_app

    if _firebase_app is not None:
        logger.debug("Firebase already initialized, returning existing instance")
        return _firebase_app

    # Check if credentials path is configured
    if not settings.firebase_credentials_path:
        logger.warning(
            "Firebase credentials path not configured. "
            "Set FIREBASE_CREDENTIALS_PATH environment variable to enable push notifications. "
            "Notifications will be saved to database but not sent via FCM."
        )
        return None

    try:
        # Initialize Firebase with service account credentials
        cred = credentials.Certificate(settings.firebase_credentials_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        return _firebase_app

    except FileNotFoundError:
        logger.error(
            f"Firebase credentials file not found at: {settings.firebase_credentials_path}. "
            "Push notifications will not be sent."
        )
        return None

    except ValueError as e:
        logger.error(f"Invalid Firebase credentials: {e}. Push notifications will not be sent.")
        return None

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}. Push notifications will not be sent.")
        return None


def get_firebase_messaging() -> Optional[messaging]:
    """
    Get Firebase Cloud Messaging module.

    Returns:
        Firebase messaging module if initialized, None otherwise
    """
    app = initialize_firebase()
    if app is None:
        return None

    return messaging


def is_firebase_enabled() -> bool:
    """
    Check if Firebase is properly initialized and enabled.

    Returns:
        True if Firebase is available, False otherwise
    """
    return _firebase_app is not None or initialize_firebase() is not None


def reset_firebase() -> None:
    """
    Reset Firebase app instance (mainly for testing).

    WARNING: This should only be used in tests. In production,
    Firebase is initialized once during application startup.
    """
    global _firebase_app

    if _firebase_app is not None:
        try:
            firebase_admin.delete_app(_firebase_app)
            logger.info("Firebase app instance deleted")
        except Exception as e:
            logger.warning(f"Failed to delete Firebase app: {e}")
        finally:
            _firebase_app = None
