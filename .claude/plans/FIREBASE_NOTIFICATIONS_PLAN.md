# Firebase Cloud Messaging (FCM) Notifications Implementation Plan

## Overview

This plan outlines the implementation of a real-time notification system for OpenDeck using Firebase Cloud Messaging (FCM) on the free tier. The system will enable push notifications from the backend API and Celery workers to users' browsers, even when the app is not actively open.

## Architecture Decision

**Selected Approach:** Firebase Cloud Messaging (FCM) with Service Workers

### Key Benefits
- ✅ Real-time push notifications (no polling required)
- ✅ Works even when app is not open (via service worker)
- ✅ Free tier: unlimited messages
- ✅ Cross-platform ready (web now, mobile later)
- ✅ Built-in retry and delivery guarantees
- ✅ Rich notification support (images, actions, badges)
- ✅ Production-ready with Google's infrastructure

### Notification Flow
1. User logs in → Frontend requests FCM token → Sends token to backend
2. Backend stores FCM token for user in database
3. When an event occurs (Celery task completion, API action) → Backend sends push notification via Firebase Admin SDK
4. Firebase delivers notification to user's browser (even when tab is closed)
5. User clicks notification → Navigates to relevant page in app
6. Notification history stored in database for in-app viewing

---

## Phase 0: Firebase Setup

### 1. Create Firebase Project
- [ ] Go to [Firebase Console](https://console.firebase.google.com/)
- [ ] Create new project "OpenDeck"
- [ ] Enable Cloud Messaging
- [ ] Generate service account key (JSON file)
- [ ] Download and store securely
- [ ] Add web app to Firebase project
- [ ] Get Firebase config object (apiKey, projectId, etc.)
- [ ] Generate VAPID key for web push

### 2. Store Firebase Credentials

**Backend Configuration:**
```bash
# backend/firebase-service-account.json
# Download from Firebase Console → Project Settings → Service Accounts
# Add to .gitignore!

# backend/.env
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
```

**Frontend Configuration:**
```typescript
// opendeck-portal/src/environments/environment.ts
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000',
  firebase: {
    apiKey: "YOUR_API_KEY",
    authDomain: "opendeck.firebaseapp.com",
    projectId: "opendeck",
    storageBucket: "opendeck.appspot.com",
    messagingSenderId: "123456789",
    appId: "YOUR_APP_ID",
    vapidKey: "YOUR_VAPID_KEY"  // For web push
  }
};
```

**Security:**
- [ ] Add `firebase-service-account.json` to `.gitignore`
- [ ] Add Firebase config to environment files (not checked into git)
- [ ] Use environment variables in production

---

## Phase 1: Database Schema

### 3. Create Database Tables

**User FCM Tokens Table:**
```sql
CREATE TABLE user_fcm_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    fcm_token TEXT NOT NULL UNIQUE,
    device_type VARCHAR(20) NOT NULL CHECK (device_type IN ('web', 'ios', 'android')),
    device_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_user_fcm_tokens_user_id ON user_fcm_tokens(user_id);
CREATE INDEX idx_user_fcm_tokens_active ON user_fcm_tokens(user_id, is_active) WHERE is_active = true;
```

**Notification History Table:**
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('info', 'success', 'warning', 'error')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    action_url VARCHAR(512),
    metadata JSONB,
    image_url VARCHAR(512),
    read BOOLEAN DEFAULT false,
    sent_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP,
    fcm_message_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_user_read ON notifications(user_id, read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
```

### 4. Create Alembic Migration

```bash
cd backend
alembic revision --autogenerate -m "Add FCM tokens and notifications tables"
alembic upgrade head
```

**Tasks:**
- [ ] Create migration file
- [ ] Review auto-generated migration
- [ ] Apply migration to local database
- [ ] Test rollback functionality

---

## Phase 2: Backend Implementation

### 5. Install Dependencies

```bash
# backend/requirements.txt
firebase-admin==6.4.0
```

```bash
cd backend
pip install firebase-admin
```

### 6. Backend File Structure

```
backend/app/
├── core/
│   ├── models.py                     # Add Notification, UserFCMToken domain models
│   ├── interfaces.py                 # Add repository interfaces
│   └── firebase.py                   # NEW: Firebase initialization & client
├── db/
│   ├── models.py                     # Add SQLAlchemy models
│   └── postgres_repo.py              # Add repositories
├── schemas/
│   ├── notification.py               # NEW: Pydantic schemas
│   └── fcm_token.py                  # NEW: FCM token schemas
├── services/
│   ├── notification_service.py       # NEW: Notification business logic
│   └── fcm_service.py                # NEW: Firebase messaging wrapper
└── api/
    ├── notifications.py              # NEW: Notification history API
    └── fcm_tokens.py                 # NEW: Token registration API
```

### 7. Firebase Initialization

**File:** `backend/app/core/firebase.py`

```python
"""Firebase Admin SDK initialization and utilities."""
import firebase_admin
from firebase_admin import credentials, messaging
from app.core.config import settings
from typing import Optional

_firebase_app: Optional[firebase_admin.App] = None

def initialize_firebase() -> firebase_admin.App:
    """Initialize Firebase Admin SDK (singleton pattern)."""
    global _firebase_app

    if _firebase_app is None:
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        _firebase_app = firebase_admin.initialize_app(cred)

    return _firebase_app

def get_firebase_messaging():
    """Get Firebase messaging module."""
    initialize_firebase()
    return messaging
```

**Tasks:**
- [ ] Create `core/firebase.py`
- [ ] Add `FIREBASE_CREDENTIALS_PATH` to settings
- [ ] Test Firebase initialization
- [ ] Add error handling for missing credentials

### 8. Domain Models

**File:** `backend/app/core/models.py` (additions)

```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict

@dataclass
class UserFCMToken:
    """Domain model for user FCM token."""
    id: UUID
    user_id: UUID
    fcm_token: str
    device_type: str  # 'web', 'ios', 'android'
    device_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime

@dataclass
class Notification:
    """Domain model for notification."""
    id: UUID
    user_id: UUID
    type: str  # 'info', 'success', 'warning', 'error'
    title: str
    message: str
    action_url: Optional[str]
    metadata: Optional[Dict]
    image_url: Optional[str]
    read: bool
    sent_at: datetime
    read_at: Optional[datetime]
    fcm_message_id: Optional[str]
    created_at: datetime
```

### 9. Pydantic Schemas

**File:** `backend/app/schemas/fcm_token.py`

```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class FCMTokenCreate(BaseModel):
    fcm_token: str = Field(..., min_length=1)
    device_type: str = Field(..., pattern="^(web|ios|android)$")
    device_name: str | None = None

class FCMTokenResponse(BaseModel):
    id: UUID
    user_id: UUID
    device_type: str
    device_name: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

**File:** `backend/app/schemas/notification.py`

```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict

class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    message: str
    action_url: Optional[str]
    metadata: Optional[Dict]
    image_url: Optional[str]
    read: bool
    sent_at: datetime
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class UnreadCountResponse(BaseModel):
    count: int
```

### 10. Repository Implementations

**File:** `backend/app/db/models.py` (additions)

```python
from sqlalchemy import Column, String, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class UserFCMTokenModel(Base):
    __tablename__ = "user_fcm_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    fcm_token = Column(Text, unique=True, nullable=False)
    device_type = Column(String(20), nullable=False)
    device_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow)

class NotificationModel(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(512))
    metadata = Column(JSON)
    image_url = Column(String(512))
    read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)
    fcm_message_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
```

**File:** `backend/app/db/postgres_repo.py` (additions)

Add repository classes for FCM tokens and notifications with methods:
- `create()`, `get_by_id()`, `get_by_user()`, `update()`, `delete()`
- `get_active_tokens(user_id)` - Get all active FCM tokens for user
- `deactivate_tokens(tokens)` - Mark tokens as inactive
- `mark_as_read()`, `mark_all_as_read()`, `count_unread()`

### 11. FCM Service

**File:** `backend/app/services/fcm_service.py`

```python
"""Firebase Cloud Messaging service for sending push notifications."""
from firebase_admin import messaging
from typing import List, Optional, Dict
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

class FCMService:
    """Service for sending Firebase Cloud Messages."""

    def __init__(self, token_repo, notification_repo):
        self.token_repo = token_repo
        self.notification_repo = notification_repo

    async def send_notification(
        self,
        fcm_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Send push notification to multiple devices.

        Returns:
            {
                'success_count': int,
                'failure_count': int,
                'invalid_tokens': List[str]
            }
        """
        if not fcm_tokens:
            return {'success_count': 0, 'failure_count': 0, 'invalid_tokens': []}

        # Build notification payload
        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url
        )

        # Build data payload (all values must be strings)
        payload_data = data or {}
        if action_url:
            payload_data['action_url'] = action_url

        # Build messages for each token
        messages = [
            messaging.Message(
                notification=notification,
                data=payload_data,
                token=token,
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon='/assets/images/opendeck-icon.png',
                        badge='/assets/images/badge-icon.png',
                        require_interaction=False,
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link=action_url or '/dashboard'
                    )
                )
            )
            for token in fcm_tokens
        ]

        # Send batch (max 500 messages per batch)
        try:
            response = messaging.send_all(messages)

            # Identify invalid tokens for cleanup
            invalid_tokens = [
                fcm_tokens[i]
                for i, resp in enumerate(response.responses)
                if not resp.success and self._is_invalid_token_error(resp.exception)
            ]

            logger.info(
                f"FCM batch sent: {response.success_count} success, "
                f"{response.failure_count} failure, "
                f"{len(invalid_tokens)} invalid tokens"
            )

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'invalid_tokens': invalid_tokens
            }

        except Exception as e:
            logger.error(f"FCM send error: {e}")
            return {
                'success_count': 0,
                'failure_count': len(fcm_tokens),
                'invalid_tokens': []
            }

    async def send_to_user(
        self,
        user_id: UUID,
        title: str,
        body: str,
        notification_type: str = 'info',
        action_url: Optional[str] = None,
        metadata: Optional[Dict] = None,
        image_url: Optional[str] = None
    ):
        """
        Send notification to all user's active devices and save to history.
        """
        # Get user's active FCM tokens
        tokens = await self.token_repo.get_active_tokens(user_id)

        if not tokens:
            logger.warning(f"No active FCM tokens for user {user_id}")
            # Still save to notification history
            await self._save_notification_history(
                user_id, notification_type, title, body,
                action_url, metadata, image_url
            )
            return

        # Send via FCM
        result = await self.send_notification(
            fcm_tokens=[t.fcm_token for t in tokens],
            title=title,
            body=body,
            data={'type': notification_type, **(metadata or {})},
            image_url=image_url,
            action_url=action_url
        )

        # Deactivate invalid tokens
        if result['invalid_tokens']:
            await self.token_repo.deactivate_tokens(result['invalid_tokens'])
            logger.info(f"Deactivated {len(result['invalid_tokens'])} invalid tokens")

        # Save to notification history
        await self._save_notification_history(
            user_id, notification_type, title, body,
            action_url, metadata, image_url
        )

        return result

    async def _save_notification_history(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        action_url: Optional[str],
        metadata: Optional[Dict],
        image_url: Optional[str]
    ):
        """Save notification to database history."""
        await self.notification_repo.create(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            metadata=metadata,
            image_url=image_url
        )

    @staticmethod
    def _is_invalid_token_error(exception) -> bool:
        """Check if exception indicates an invalid token."""
        if exception is None:
            return False
        error_str = str(exception).lower()
        return any(keyword in error_str for keyword in [
            'invalid', 'not found', 'unregistered'
        ])
```

### 12. Notification Service

**File:** `backend/app/services/notification_service.py`

```python
"""Business logic for managing notifications."""
from uuid import UUID
from typing import List, Optional
from app.core.models import Notification

class NotificationService:
    """Service for notification business logic."""

    def __init__(self, notification_repo, fcm_service):
        self.repo = notification_repo
        self.fcm = fcm_service

    async def send_notification(
        self,
        user_id: UUID,
        type: str,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        metadata: Optional[dict] = None,
        image_url: Optional[str] = None
    ):
        """Send push notification via FCM and save to history."""
        return await self.fcm.send_to_user(
            user_id=user_id,
            title=title,
            body=message,
            notification_type=type,
            action_url=action_url,
            metadata=metadata,
            image_url=image_url
        )

    async def get_user_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notification history for user."""
        return await self.repo.get_by_user(
            user_id=user_id,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> None:
        """Mark single notification as read."""
        # Verify notification belongs to user
        notification = await self.repo.get_by_id(notification_id)
        if notification and notification.user_id == user_id:
            await self.repo.mark_as_read(notification_id)

    async def mark_all_as_read(self, user_id: UUID) -> None:
        """Mark all user notifications as read."""
        await self.repo.mark_all_as_read(user_id)

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications."""
        return await self.repo.count_unread(user_id)

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> None:
        """Delete a notification (verify ownership)."""
        notification = await self.repo.get_by_id(notification_id)
        if notification and notification.user_id == user_id:
            await self.repo.delete(notification_id)
```

### 13. API Endpoints

**File:** `backend/app/api/fcm_tokens.py`

```python
"""API endpoints for FCM token management."""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from app.schemas.fcm_token import FCMTokenCreate, FCMTokenResponse
from app.core.models import User
from app.api.dependencies import get_current_user, get_token_service

router = APIRouter(prefix="/api/v1/fcm-tokens", tags=["fcm-tokens"])

@router.post("", response_model=FCMTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_fcm_token(
    token_data: FCMTokenCreate,
    current_user: User = Depends(get_current_user),
    token_service = Depends(get_token_service)
):
    """
    Register or update FCM token for current user.

    If token already exists, updates last_used_at and reactivates if needed.
    """
    return await token_service.register_token(
        user_id=current_user.id,
        fcm_token=token_data.fcm_token,
        device_type=token_data.device_type,
        device_name=token_data.device_name
    )

@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_fcm_token(
    token_id: UUID,
    current_user: User = Depends(get_current_user),
    token_service = Depends(get_token_service)
):
    """
    Unregister FCM token (mark as inactive).

    Called when user logs out or revokes notification permission.
    """
    await token_service.deactivate_token(token_id, current_user.id)
    return None

@router.get("/my-tokens", response_model=list[FCMTokenResponse])
async def get_my_tokens(
    current_user: User = Depends(get_current_user),
    token_service = Depends(get_token_service)
):
    """Get all FCM tokens registered for current user."""
    return await token_service.get_user_tokens(current_user.id)
```

**File:** `backend/app/api/notifications.py`

```python
"""API endpoints for notification management."""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from uuid import UUID
from typing import List
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.core.models import User
from app.api.dependencies import get_current_user, get_notification_service

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    notification_service = Depends(get_notification_service)
):
    """Get notification history for current user."""
    return await notification_service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    notification_service = Depends(get_notification_service)
):
    """Get count of unread notifications for current user."""
    count = await notification_service.get_unread_count(current_user.id)
    return UnreadCountResponse(count=count)

@router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service = Depends(get_notification_service)
):
    """Mark a single notification as read."""
    await notification_service.mark_as_read(notification_id, current_user.id)
    return None

@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    notification_service = Depends(get_notification_service)
):
    """Mark all notifications as read for current user."""
    await notification_service.mark_all_as_read(current_user.id)
    return None

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    notification_service = Depends(get_notification_service)
):
    """Delete a notification."""
    await notification_service.delete_notification(notification_id, current_user.id)
    return None
```

**Register routes in main app:**
```python
# backend/app/main.py
from app.api import fcm_tokens, notifications

app.include_router(fcm_tokens.router)
app.include_router(notifications.router)
```

### 14. Celery Integration

**File:** `backend/app/tasks/notification_helpers.py`

```python
"""Helper functions for sending notifications from Celery tasks."""
import asyncio
from uuid import UUID
from typing import Optional, Dict
from app.services.notification_service import get_notification_service

def notify_user_sync(
    user_id: UUID,
    notification_type: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    metadata: Optional[Dict] = None
):
    """
    Synchronous wrapper for sending notifications from Celery tasks.

    Usage in Celery tasks:
        notify_user_sync(
            user_id=user.id,
            notification_type='success',
            title='Task Complete',
            message='Your document has been processed',
            action_url='/decks/123'
        )
    """
    notification_service = get_notification_service()

    asyncio.run(
        notification_service.send_notification(
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            metadata=metadata
        )
    )

def notify_success(user_id: UUID, title: str, message: str, action_url: Optional[str] = None):
    """Helper for success notifications."""
    notify_user_sync(user_id, 'success', title, message, action_url)

def notify_error(user_id: UUID, title: str, message: str, error_details: Optional[Dict] = None):
    """Helper for error notifications."""
    notify_user_sync(user_id, 'error', title, message, metadata={'error': error_details})

def notify_info(user_id: UUID, title: str, message: str, action_url: Optional[str] = None):
    """Helper for info notifications."""
    notify_user_sync(user_id, 'info', title, message, action_url)
```

**Update Celery tasks:**

```python
# Example: backend/app/tasks/document_processing.py
from app.tasks.notification_helpers import notify_success, notify_error
from uuid import UUID

@celery_app.task(bind=True)
def process_document(self, user_id: str, document_id: str, filename: str):
    """Process uploaded document and generate flashcards."""

    try:
        # Processing logic...
        result = extract_and_generate_flashcards(document_id)

        # Notify success
        notify_success(
            user_id=UUID(user_id),
            title='✅ Document Processed',
            message=f'Generated {result["card_count"]} flashcards from "{filename}"',
            action_url=f'/decks/{result["deck_id"]}'
        )

        return result

    except Exception as e:
        # Notify error
        notify_error(
            user_id=UUID(user_id),
            title='❌ Processing Failed',
            message=f'Failed to process "{filename}": {str(e)}',
            error_details={
                'document_id': document_id,
                'filename': filename,
                'error': str(e)
            }
        )
        raise
```

### 15. Testing

**File:** `backend/tests/test_fcm_service.py`

```python
"""Tests for FCM service."""
import pytest
from unittest.mock import Mock, patch
from app.services.fcm_service import FCMService

@pytest.mark.asyncio
async def test_send_notification():
    # Test FCM notification sending
    pass

@pytest.mark.asyncio
async def test_send_to_user():
    # Test sending to specific user
    pass

@pytest.mark.asyncio
async def test_invalid_token_cleanup():
    # Test that invalid tokens are deactivated
    pass
```

---

## Phase 3: Frontend Implementation

### 16. Install Dependencies

```bash
cd opendeck-portal
npm install firebase
```

### 17. Frontend File Structure

```
opendeck-portal/src/
├── app/
│   ├── models/
│   │   ├── notification.model.ts        # NEW
│   │   └── fcm-token.model.ts           # NEW
│   ├── services/
│   │   ├── firebase.service.ts          # NEW
│   │   ├── fcm.service.ts               # NEW
│   │   └── notification.service.ts      # NEW
│   ├── components/
│   │   ├── notification-bell/           # NEW
│   │   │   ├── notification-bell.component.ts
│   │   │   ├── notification-bell.component.html
│   │   │   └── notification-bell.component.scss
│   │   └── notification-panel/          # NEW
│   │       ├── notification-panel.component.ts
│   │       ├── notification-panel.component.html
│   │       └── notification-panel.component.scss
│   └── layout/
│       └── topbar/
│           └── topbar.component.html    # MODIFY: Add notification bell
├── assets/
│   ├── i18n/
│   │   ├── en.json                      # MODIFY: Add translations
│   │   └── es.json                      # MODIFY: Add translations
│   └── images/
│       ├── opendeck-icon.png            # Notification icon
│       └── badge-icon.png               # Badge icon
└── firebase-messaging-sw.js             # NEW: Service worker (in public/)
```

### 18. TypeScript Models

**File:** `src/app/models/notification.model.ts`

```typescript
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  actionUrl?: string;
  metadata?: Record<string, any>;
  imageUrl?: string;
  read: boolean;
  sentAt: string;
  readAt?: string;
  createdAt: string;
}

export interface UnreadCount {
  count: number;
}
```

**File:** `src/app/models/fcm-token.model.ts`

```typescript
export interface FCMTokenCreate {
  fcm_token: string;
  device_type: 'web' | 'ios' | 'android';
  device_name?: string;
}

export interface FCMTokenResponse {
  id: string;
  user_id: string;
  device_type: string;
  device_name?: string;
  is_active: boolean;
  created_at: string;
}
```

### 19. Firebase Service

**File:** `src/app/services/firebase.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { initializeApp, FirebaseApp } from 'firebase/app';
import { getMessaging, getToken, onMessage, Messaging } from 'firebase/messaging';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class FirebaseService {
  private app: FirebaseApp | null = null;
  private messaging: Messaging | null = null;

  constructor() {
    this.initialize();
  }

  private initialize(): void {
    if (!this.isSupported()) {
      console.warn('Firebase messaging not supported on this device');
      return;
    }

    try {
      this.app = initializeApp(environment.firebase);
      this.messaging = getMessaging(this.app);
    } catch (error) {
      console.error('Failed to initialize Firebase:', error);
    }
  }

  isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      'Notification' in window &&
      'serviceWorker' in navigator &&
      'PushManager' in window
    );
  }

  async requestPermission(): Promise<boolean> {
    if (!this.isSupported()) {
      console.warn('Notifications not supported');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  async getToken(): Promise<string | null> {
    if (!this.messaging) {
      console.error('Firebase messaging not initialized');
      return null;
    }

    try {
      const token = await getToken(this.messaging, {
        vapidKey: environment.firebase.vapidKey
      });

      if (token) {
        console.log('FCM token obtained:', token.substring(0, 20) + '...');
        return token;
      } else {
        console.warn('No FCM token available');
        return null;
      }
    } catch (error) {
      console.error('Error getting FCM token:', error);
      return null;
    }
  }

  onMessage(callback: (payload: any) => void): void {
    if (!this.messaging) {
      console.warn('Cannot listen for messages: Firebase messaging not initialized');
      return;
    }

    onMessage(this.messaging, (payload) => {
      console.log('Foreground message received:', payload);
      callback(payload);
    });
  }

  getPermissionStatus(): NotificationPermission {
    if (!this.isSupported()) {
      return 'denied';
    }
    return Notification.permission;
  }
}
```

### 20. FCM Service

**File:** `src/app/services/fcm.service.ts`

```typescript
import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { FirebaseService } from './firebase.service';
import { environment } from '../../environments/environment';
import { FCMTokenCreate, FCMTokenResponse } from '../models/fcm-token.model';
import { MessageService } from 'primeng/api';

@Injectable({ providedIn: 'root' })
export class FCMService {
  private currentToken = signal<string | null>(null);
  private tokenRegistered = signal<boolean>(false);
  private initialized = signal<boolean>(false);

  constructor(
    private http: HttpClient,
    private firebase: FirebaseService,
    private messageService: MessageService
  ) {}

  async initialize(): Promise<void> {
    if (this.initialized()) {
      console.log('FCM already initialized');
      return;
    }

    if (!this.firebase.isSupported()) {
      console.warn('Push notifications not supported on this device');
      return;
    }

    // Check if permission already granted
    const permissionStatus = this.firebase.getPermissionStatus();

    if (permissionStatus === 'granted') {
      await this.setupFCM();
    } else if (permissionStatus === 'default') {
      // Don't request permission immediately - wait for user action
      console.log('Notification permission not yet requested');
    }

    this.initialized.set(true);
  }

  async requestPermissionAndSetup(): Promise<boolean> {
    const granted = await this.firebase.requestPermission();

    if (!granted) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Notifications Disabled',
        detail: 'Enable notifications in your browser settings to receive updates'
      });
      return false;
    }

    await this.setupFCM();
    return true;
  }

  private async setupFCM(): Promise<void> {
    // Get FCM token
    const token = await this.firebase.getToken();

    if (!token) {
      console.error('Failed to get FCM token');
      return;
    }

    this.currentToken.set(token);

    // Register token with backend
    await this.registerToken(token);

    // Listen for foreground messages
    this.firebase.onMessage((payload) => {
      this.handleForegroundMessage(payload);
    });
  }

  private async registerToken(token: string): Promise<void> {
    const deviceName = this.getDeviceInfo();

    const tokenData: FCMTokenCreate = {
      fcm_token: token,
      device_type: 'web',
      device_name: deviceName
    };

    try {
      const response = await firstValueFrom(
        this.http.post<FCMTokenResponse>(
          `${environment.apiBaseUrl}/api/v1/fcm-tokens`,
          tokenData
        )
      );

      this.tokenRegistered.set(true);
      console.log('FCM token registered successfully');

      this.messageService.add({
        severity: 'success',
        summary: 'Notifications Enabled',
        detail: 'You will now receive real-time updates',
        life: 3000
      });

    } catch (error) {
      console.error('Failed to register FCM token:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'Registration Failed',
        detail: 'Could not enable notifications'
      });
    }
  }

  async unregisterToken(): Promise<void> {
    // Called on logout
    const token = this.currentToken();
    if (!token || !this.tokenRegistered()) return;

    try {
      // Note: Backend expects token_id, not token string
      // We might need to store the token_id when we register
      // For now, we'll just clear the local state
      this.currentToken.set(null);
      this.tokenRegistered.set(false);
      console.log('FCM token unregistered');
    } catch (error) {
      console.error('Failed to unregister FCM token:', error);
    }
  }

  private handleForegroundMessage(payload: any): void {
    const { notification, data } = payload;

    if (!notification) return;

    // Show PrimeNG toast for foreground notifications
    const severity = this.getSeverityFromType(data?.type || 'info');

    this.messageService.add({
      severity: severity,
      summary: notification.title,
      detail: notification.body,
      life: 5000,
      data: { actionUrl: data?.action_url }
    });

    // Optional: Emit event to refresh notification list
    // this.notificationReceived.emit();
  }

  private getSeverityFromType(type: string): 'success' | 'info' | 'warn' | 'error' {
    switch (type) {
      case 'success': return 'success';
      case 'warning': return 'warn';
      case 'error': return 'error';
      default: return 'info';
    }
  }

  private getDeviceInfo(): string {
    const ua = navigator.userAgent;
    if (ua.includes('Chrome')) return 'Chrome';
    if (ua.includes('Firefox')) return 'Firefox';
    if (ua.includes('Safari')) return 'Safari';
    if (ua.includes('Edge')) return 'Edge';
    return 'Web Browser';
  }

  isTokenRegistered(): boolean {
    return this.tokenRegistered();
  }
}
```

### 21. Notification Service

**File:** `src/app/services/notification.service.ts`

```typescript
import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { Notification, UnreadCount } from '../models/notification.model';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private notifications = signal<Notification[]>([]);
  private unreadCount = signal<number>(0);

  constructor(private http: HttpClient) {}

  async loadNotifications(unreadOnly: boolean = false, limit: number = 50): Promise<void> {
    try {
      const notifications = await this.getNotifications(unreadOnly, limit);
      this.notifications.set(notifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  }

  async loadUnreadCount(): Promise<void> {
    try {
      const count = await this.getUnreadCount();
      this.unreadCount.set(count);
    } catch (error) {
      console.error('Failed to load unread count:', error);
    }
  }

  getNotifications(unreadOnly: boolean = false, limit: number = 50, offset: number = 0): Promise<Notification[]> {
    let params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());

    if (unreadOnly) {
      params = params.set('unread_only', 'true');
    }

    return firstValueFrom(
      this.http.get<Notification[]>(
        `${environment.apiBaseUrl}/api/v1/notifications`,
        { params }
      )
    );
  }

  async getUnreadCount(): Promise<number> {
    const response = await firstValueFrom(
      this.http.get<UnreadCount>(`${environment.apiBaseUrl}/api/v1/notifications/unread-count`)
    );
    return response.count;
  }

  async markAsRead(notificationId: string): Promise<void> {
    await firstValueFrom(
      this.http.patch<void>(
        `${environment.apiBaseUrl}/api/v1/notifications/${notificationId}/read`,
        {}
      )
    );

    // Update local state
    await this.loadUnreadCount();
    await this.loadNotifications();
  }

  async markAllAsRead(): Promise<void> {
    await firstValueFrom(
      this.http.patch<void>(
        `${environment.apiBaseUrl}/api/v1/notifications/read-all`,
        {}
      )
    );

    // Update local state
    this.unreadCount.set(0);
    await this.loadNotifications();
  }

  async deleteNotification(notificationId: string): Promise<void> {
    await firstValueFrom(
      this.http.delete<void>(
        `${environment.apiBaseUrl}/api/v1/notifications/${notificationId}`
      )
    );

    // Update local state
    await this.loadNotifications();
    await this.loadUnreadCount();
  }

  // Signals for components
  getNotificationsSignal() {
    return this.notifications.asReadonly();
  }

  getUnreadCountSignal() {
    return this.unreadCount.asReadonly();
  }
}
```

### 22. Service Worker

**File:** `public/firebase-messaging-sw.js`

```javascript
// Firebase Cloud Messaging Service Worker
// This file must be in the public directory at the root of your app

importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Initialize Firebase app in service worker
firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  authDomain: "opendeck.firebaseapp.com",
  projectId: "opendeck",
  storageBucket: "opendeck.appspot.com",
  messagingSenderId: "123456789",
  appId: "YOUR_APP_ID"
});

const messaging = firebase.messaging();

// Handle background messages (when app is not in focus)
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message:', payload);

  const { notification, data } = payload;

  if (!notification) {
    console.warn('No notification payload');
    return;
  }

  const notificationTitle = notification.title || 'OpenDeck';
  const notificationOptions = {
    body: notification.body,
    icon: notification.icon || '/assets/images/opendeck-icon.png',
    badge: '/assets/images/badge-icon.png',
    image: notification.image,
    tag: data?.notification_id || 'opendeck-notification',
    requireInteraction: false,
    data: {
      url: data?.action_url || '/dashboard',
      notification_id: data?.notification_id
    }
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('[firebase-messaging-sw.js] Notification click:', event);

  event.notification.close();

  const urlToOpen = event.notification.data?.url || '/dashboard';
  const fullUrl = self.location.origin + urlToOpen;

  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    })
    .then((clientList) => {
      // Check if there's already a window open
      for (const client of clientList) {
        if (client.url === fullUrl && 'focus' in client) {
          return client.focus();
        }
      }

      // If no window found, open a new one
      if (clients.openWindow) {
        return clients.openWindow(fullUrl);
      }
    })
  );
});

// Handle service worker activation
self.addEventListener('activate', (event) => {
  console.log('[firebase-messaging-sw.js] Service worker activated');
});
```

### 23. Register Service Worker

**File:** `src/main.ts` (add this)

```typescript
// Register service worker for Firebase messaging
if ('serviceWorker' in navigator) {
  navigator.serviceWorker
    .register('/firebase-messaging-sw.js')
    .then((registration) => {
      console.log('Service Worker registered successfully:', registration.scope);
    })
    .catch((error) => {
      console.error('Service Worker registration failed:', error);
    });
}
```

### 24. Notification Bell Component

**File:** `src/app/components/notification-bell/notification-bell.component.ts`

```typescript
import { Component, OnInit, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BadgeModule } from 'primeng/badge';
import { OverlayPanel, OverlayPanelModule } from 'primeng/overlaypanel';
import { NotificationService } from '../../services/notification.service';
import { NotificationPanelComponent } from '../notification-panel/notification-panel.component';

@Component({
  selector: 'app-notification-bell',
  standalone: true,
  imports: [
    CommonModule,
    BadgeModule,
    OverlayPanelModule,
    NotificationPanelComponent
  ],
  template: `
    <div
      class="notification-bell relative cursor-pointer"
      (click)="togglePanel($event)"
      [class.has-notifications]="unreadCount() > 0"
    >
      <i class="pi pi-bell text-2xl"></i>
      <span
        *ngIf="unreadCount() > 0"
        class="notification-badge"
        [attr.aria-label]="unreadCount() + ' unread notifications'"
      >
        {{ unreadCount() > 99 ? '99+' : unreadCount() }}
      </span>
    </div>

    <p-overlayPanel #op [style]="{ width: '400px', maxWidth: '90vw' }">
      <app-notification-panel
        (notificationRead)="onNotificationRead()"
        (closePanel)="op.hide()">
      </app-notification-panel>
    </p-overlayPanel>
  `,
  styles: [`
    .notification-bell {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      transition: background-color 0.2s;
    }

    .notification-bell:hover {
      background-color: var(--surface-hover);
    }

    .notification-badge {
      position: absolute;
      top: 2px;
      right: 2px;
      background-color: var(--red-500);
      color: white;
      font-size: 0.75rem;
      font-weight: bold;
      padding: 2px 6px;
      border-radius: 10px;
      min-width: 20px;
      text-align: center;
      line-height: 1;
    }

    .notification-bell.has-notifications i {
      animation: bell-ring 0.5s ease-in-out;
    }

    @keyframes bell-ring {
      0%, 100% { transform: rotate(0deg); }
      10%, 30% { transform: rotate(-10deg); }
      20%, 40% { transform: rotate(10deg); }
    }
  `]
})
export class NotificationBellComponent implements OnInit {
  @ViewChild('op') overlayPanel!: OverlayPanel;

  unreadCount = signal<number>(0);

  constructor(private notificationService: NotificationService) {}

  async ngOnInit() {
    await this.loadUnreadCount();

    // Refresh count every 30 seconds as backup
    setInterval(() => this.loadUnreadCount(), 30000);
  }

  async loadUnreadCount() {
    await this.notificationService.loadUnreadCount();
    this.unreadCount.set(this.notificationService.getUnreadCountSignal()());
  }

  togglePanel(event: Event) {
    this.overlayPanel.toggle(event);
  }

  onNotificationRead() {
    this.loadUnreadCount();
  }
}
```

### 25. Notification Panel Component

**File:** `src/app/components/notification-panel/notification-panel.component.ts`

```typescript
import { Component, OnInit, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { TranslateModule } from '@ngx-translate/core';
import { NotificationService } from '../../services/notification.service';
import { Notification } from '../../models/notification.model';

@Component({
  selector: 'app-notification-panel',
  standalone: true,
  imports: [
    CommonModule,
    ButtonModule,
    ScrollPanelModule,
    TranslateModule
  ],
  template: `
    <div class="notification-panel">
      <div class="panel-header flex justify-content-between align-items-center mb-3">
        <h3 class="m-0">{{ 'notifications.title' | translate }}</h3>
        <p-button
          *ngIf="hasUnreadNotifications()"
          [label]="'notifications.markAllRead' | translate"
          icon="pi pi-check"
          [text]="true"
          size="small"
          (onClick)="markAllAsRead()"
        />
      </div>

      <p-scrollPanel [style]="{ width: '100%', height: '400px' }">
        <div class="notifications-list">
          <div
            *ngFor="let notification of notifications()"
            class="notification-item"
            [class.unread]="!notification.read"
            [class]="'type-' + notification.type"
            (click)="handleNotificationClick(notification)"
          >
            <div class="notification-icon">
              <i [class]="getNotificationIcon(notification.type)"></i>
            </div>

            <div class="notification-content flex-1">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">{{ formatTime(notification.sentAt) }}</div>
            </div>

            <div class="notification-actions">
              <button
                *ngIf="!notification.read"
                class="action-btn"
                (click)="markAsRead($event, notification.id)"
                [attr.aria-label]="'Mark as read'"
              >
                <i class="pi pi-check"></i>
              </button>
              <button
                class="action-btn"
                (click)="deleteNotification($event, notification.id)"
                [attr.aria-label]="'Delete notification'"
              >
                <i class="pi pi-trash"></i>
              </button>
            </div>
          </div>

          <div *ngIf="notifications().length === 0" class="no-notifications">
            <i class="pi pi-bell text-4xl mb-3 text-400"></i>
            <p>{{ 'notifications.noNotifications' | translate }}</p>
          </div>
        </div>
      </p-scrollPanel>
    </div>
  `,
  styles: [`
    .notification-panel {
      padding: 1rem;
    }

    .panel-header h3 {
      font-size: 1.25rem;
      font-weight: 600;
    }

    .notifications-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .notification-item {
      display: flex;
      gap: 1rem;
      padding: 1rem;
      border-radius: 8px;
      background: var(--surface-50);
      cursor: pointer;
      transition: all 0.2s;
      border-left: 4px solid transparent;
    }

    .notification-item:hover {
      background: var(--surface-100);
    }

    .notification-item.unread {
      background: var(--primary-50);
      border-left-color: var(--primary-500);
    }

    .notification-item.type-success {
      border-left-color: var(--green-500);
    }

    .notification-item.type-error {
      border-left-color: var(--red-500);
    }

    .notification-item.type-warning {
      border-left-color: var(--orange-500);
    }

    .notification-item.type-info {
      border-left-color: var(--blue-500);
    }

    .notification-icon {
      display: flex;
      align-items: flex-start;
      font-size: 1.5rem;
    }

    .notification-content {
      min-width: 0;
    }

    .notification-title {
      font-weight: 600;
      margin-bottom: 0.25rem;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .notification-message {
      font-size: 0.875rem;
      color: var(--text-color-secondary);
      margin-bottom: 0.5rem;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .notification-time {
      font-size: 0.75rem;
      color: var(--text-color-secondary);
    }

    .notification-actions {
      display: flex;
      gap: 0.5rem;
      align-items: flex-start;
    }

    .action-btn {
      background: none;
      border: none;
      padding: 0.5rem;
      cursor: pointer;
      border-radius: 4px;
      color: var(--text-color-secondary);
      transition: all 0.2s;
    }

    .action-btn:hover {
      background: var(--surface-200);
      color: var(--text-color);
    }

    .no-notifications {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem 1rem;
      text-align: center;
      color: var(--text-color-secondary);
    }
  `]
})
export class NotificationPanelComponent implements OnInit {
  @Output() notificationRead = new EventEmitter<void>();
  @Output() closePanel = new EventEmitter<void>();

  notifications = signal<Notification[]>([]);

  constructor(
    private notificationService: NotificationService,
    private router: Router
  ) {}

  async ngOnInit() {
    await this.loadNotifications();
  }

  async loadNotifications() {
    await this.notificationService.loadNotifications(false, 20);
    this.notifications.set(this.notificationService.getNotificationsSignal()());
  }

  hasUnreadNotifications(): boolean {
    return this.notifications().some(n => !n.read);
  }

  async markAsRead(event: Event, notificationId: string) {
    event.stopPropagation();
    await this.notificationService.markAsRead(notificationId);
    await this.loadNotifications();
    this.notificationRead.emit();
  }

  async markAllAsRead() {
    await this.notificationService.markAllAsRead();
    await this.loadNotifications();
    this.notificationRead.emit();
  }

  async deleteNotification(event: Event, notificationId: string) {
    event.stopPropagation();
    await this.notificationService.deleteNotification(notificationId);
    await this.loadNotifications();
    this.notificationRead.emit();
  }

  async handleNotificationClick(notification: Notification) {
    if (!notification.read) {
      await this.notificationService.markAsRead(notification.id);
      this.notificationRead.emit();
    }

    if (notification.actionUrl) {
      this.router.navigate([notification.actionUrl]);
      this.closePanel.emit();
    }
  }

  getNotificationIcon(type: string): string {
    switch (type) {
      case 'success': return 'pi pi-check-circle';
      case 'error': return 'pi pi-times-circle';
      case 'warning': return 'pi pi-exclamation-triangle';
      default: return 'pi pi-info-circle';
    }
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  }
}
```

### 26. Update Topbar

**File:** `src/app/layout/topbar/topbar.component.html`

Add notification bell before user menu:

```html
<div class="layout-topbar-actions">
  <!-- Add notification bell -->
  <app-notification-bell></app-notification-bell>

  <!-- Existing user menu -->
  <div class="layout-topbar-menu">
    <!-- ... existing code ... -->
  </div>
</div>
```

### 27. Initialize FCM on Login

**File:** `src/app/services/auth.service.ts`

```typescript
import { FCMService } from './fcm.service';

export class AuthService {
  constructor(
    private http: HttpClient,
    private fcm: FCMService,
    // ... other dependencies
  ) {}

  async login(email: string, password: string): Promise<void> {
    try {
      const response = await firstValueFrom(
        this.http.post<any>(`${environment.apiBaseUrl}/api/v1/auth/login`, {
          email,
          password
        })
      );

      // Store tokens
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);

      // Set user state
      this.currentUser.set(response.user);

      // Initialize FCM after successful login
      await this.fcm.initialize();

    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    // Unregister FCM token
    await this.fcm.unregisterToken();

    // Clear auth state
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.currentUser.set(null);
  }
}
```

### 28. Translations

**File:** `src/assets/i18n/en.json`

```json
{
  "notifications": {
    "title": "Notifications",
    "markAllRead": "Mark all as read",
    "noNotifications": "No new notifications",
    "viewAll": "View all notifications",
    "permissionDenied": "Please enable notifications in your browser settings",
    "permissionRequest": "Enable notifications to receive real-time updates",
    "enableNotifications": "Enable Notifications",
    "types": {
      "info": "Info",
      "success": "Success",
      "warning": "Warning",
      "error": "Error"
    }
  }
}
```

**File:** `src/assets/i18n/es.json`

```json
{
  "notifications": {
    "title": "Notificaciones",
    "markAllRead": "Marcar todo como leído",
    "noNotifications": "No hay notificaciones nuevas",
    "viewAll": "Ver todas las notificaciones",
    "permissionDenied": "Por favor habilita las notificaciones en la configuración de tu navegador",
    "permissionRequest": "Habilita las notificaciones para recibir actualizaciones en tiempo real",
    "enableNotifications": "Habilitar Notificaciones",
    "types": {
      "info": "Información",
      "success": "Éxito",
      "warning": "Advertencia",
      "error": "Error"
    }
  }
}
```

---

## Phase 4: Testing & Deployment

### 29. Backend Testing

**Test checklist:**
- [ ] Unit tests for FCM service
- [ ] Unit tests for notification service
- [ ] Integration tests for API endpoints
- [ ] Test Celery notification helpers
- [ ] Test token cleanup for invalid tokens
- [ ] Test notification history pagination
- [ ] Test authorization (users can only see their notifications)

### 30. Frontend Testing

**Test checklist:**
- [ ] Test Firebase initialization
- [ ] Test FCM token registration
- [ ] Test foreground notification display
- [ ] Test background notification delivery
- [ ] Test notification click navigation
- [ ] Test notification bell badge updates
- [ ] Test mark as read functionality
- [ ] Test permission denied gracefully
- [ ] Test on Chrome, Firefox, Safari
- [ ] Test on mobile browsers

### 31. Manual Testing Scenarios

1. **User Login Flow:**
   - [ ] Login → FCM token requested → Token registered with backend
   - [ ] Check browser console for logs
   - [ ] Verify token in database

2. **Background Notification:**
   - [ ] Close/minimize browser tab
   - [ ] Trigger notification from backend/Celery
   - [ ] Verify notification appears from browser
   - [ ] Click notification → App opens to correct page

3. **Foreground Notification:**
   - [ ] Keep app open
   - [ ] Trigger notification
   - [ ] Verify PrimeNG toast appears
   - [ ] Verify notification bell badge updates

4. **Notification History:**
   - [ ] Open notification panel
   - [ ] Verify notifications appear
   - [ ] Mark as read → Badge updates
   - [ ] Click notification → Navigate to action URL

5. **Permission Denied:**
   - [ ] Block notifications in browser
   - [ ] Login → Verify graceful handling
   - [ ] Verify can still see notification history

6. **Logout:**
   - [ ] Logout → FCM token deactivated
   - [ ] Verify no notifications received after logout

### 32. Production Deployment

**Backend:**
- [ ] Store Firebase service account JSON securely (e.g., AWS Secrets Manager)
- [ ] Set `FIREBASE_CREDENTIALS_PATH` environment variable
- [ ] Test Firebase connectivity from production
- [ ] Set up monitoring for FCM send failures

**Frontend:**
- [ ] Update `environment.prod.ts` with production Firebase config
- [ ] Ensure service worker is served from root path
- [ ] Configure HTTPS (required for service workers)
- [ ] Test on production domain

---

## Security & Best Practices

### Security Considerations

1. **Firebase Service Account:**
   - Never commit `firebase-service-account.json` to git
   - Use environment variables or secrets manager
   - Rotate credentials periodically

2. **FCM Tokens:**
   - Store tokens securely in database
   - Clean up invalid tokens automatically
   - Deactivate tokens on logout

3. **Notification Content:**
   - Sanitize notification content to prevent XSS
   - Don't include sensitive data in notification body
   - Use action URLs for details

4. **Authorization:**
   - Verify user owns notification before marking as read
   - Verify user owns FCM token before deactivation
   - Rate limit notification endpoints

### Performance Optimization

1. **Batch Sending:**
   - Firebase supports up to 500 messages per batch
   - Use batch API for multiple users

2. **Token Cleanup:**
   - Create Celery periodic task to clean old inactive tokens
   - Remove read notifications older than 30 days

3. **Notification History:**
   - Implement pagination for notification list
   - Index database by user_id and read status

4. **Frontend:**
   - Lazy load notification panel
   - Cache unread count with TTL
   - Debounce mark-as-read calls

---

## Future Enhancements

### Phase 2 Improvements

1. **Rich Notifications:**
   - Add action buttons to notifications
   - Include images for document previews
   - Add custom notification sounds

2. **User Preferences:**
   - Let users choose which events trigger notifications
   - Quiet hours configuration
   - Email vs push notification preferences
   - Notification frequency settings

3. **Mobile Apps:**
   - Same Firebase project for iOS/Android
   - React Native integration
   - Deep linking support

4. **Analytics:**
   - Track notification delivery rates
   - Monitor click-through rates
   - A/B test notification copy
   - User engagement metrics

5. **Advanced Features:**
   - Notification grouping/threading
   - Notification priority levels
   - Scheduled notifications
   - Multi-language notification templates

---

## Implementation Timeline

### Week 1: Backend Foundation
- **Days 1-2:** Firebase setup, database schema, migrations
- **Days 3-4:** FCM service, notification service, repositories
- **Day 5:** API endpoints and testing

### Week 2: Celery & Frontend
- **Days 1-2:** Celery integration and notification helpers
- **Days 3-4:** Frontend services and components
- **Day 5:** Service worker and testing

### Week 3: Integration & Polish
- **Days 1-2:** End-to-end testing
- **Day 3:** Bug fixes and edge cases
- **Days 4-5:** Documentation and deployment

---

## Success Criteria

- [ ] Users receive real-time notifications from Celery tasks
- [ ] Notifications work in foreground and background
- [ ] Notification bell shows accurate unread count
- [ ] Notification history accessible in-app
- [ ] Graceful handling of permission denial
- [ ] Works across Chrome, Firefox, Safari
- [ ] No performance degradation
- [ ] Full dark mode support
- [ ] Multi-language support (EN/ES)
- [ ] Production deployment successful

---

## Resources

- [Firebase Cloud Messaging Docs](https://firebase.google.com/docs/cloud-messaging)
- [Firebase Admin SDK Python](https://firebase.google.com/docs/admin/setup)
- [Web Push Notifications Guide](https://web.dev/push-notifications-overview/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [PrimeNG OverlayPanel](https://primeng.org/overlaypanel)

---

**End of Plan**
