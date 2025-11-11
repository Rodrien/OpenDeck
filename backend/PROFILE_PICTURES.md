# Profile Picture Support - Implementation Summary

## Overview

This document summarizes the complete backend implementation for profile picture support in OpenDeck.

## Implementation Date

November 10, 2025

## Changes Made

### 1. Database Schema

**File:** `/Users/kike/Repos/OpenDeck/backend/alembic/versions/20251110_2300_add_profile_picture.py`

- Added `profile_picture` column to `users` table (VARCHAR(255), nullable)
- Stores filename of uploaded profile picture (e.g., "uuid.jpg")
- Migration includes both upgrade and downgrade paths

**Models Updated:**
- `app/db/models.py` - Added `profile_picture` column to `UserModel`
- `app/core/models.py` - Added `profile_picture` field to `User` domain model
- `app/db/postgres_repo.py` - Updated `PostgresUserRepo` to handle profile_picture field

### 2. File Storage Service

**File:** `/Users/kike/Repos/OpenDeck/backend/app/services/file_storage.py`

A comprehensive service for handling image uploads with the following features:

**Validation:**
- Supported formats: JPEG, PNG, WebP
- Maximum file size: 5MB
- MIME type validation (not just extension)
- Image integrity verification using PIL

**Processing:**
- Automatic image resizing to 200x200px
- Aspect ratio maintained with center crop
- RGBA to RGB conversion for JPEG compatibility
- Image optimization (quality: 85%, compression)

**Security:**
- UUID-based filenames to prevent collisions and path traversal
- Filename sanitization
- Secure file storage in isolated directory

**Storage:**
- Base directory: `/backend/uploads/profile_pictures/`
- Organized file management with cleanup utilities

### 3. API Endpoints

**File:** `/Users/kike/Repos/OpenDeck/backend/app/api/users.py`

New router with the following endpoints:

#### `GET /api/v1/users/me`
- Get current authenticated user profile
- Returns user data with `profile_picture_url`

#### `POST /api/v1/users/me/profile-picture`
- Upload or update profile picture
- Accepts multipart/form-data
- Rate limited: 5 uploads per hour
- Validates file type and size
- Automatically deletes old profile picture
- Returns updated user with new `profile_picture_url`

#### `DELETE /api/v1/users/me/profile-picture`
- Remove profile picture
- Deletes file from storage
- Returns updated user without profile picture

#### `GET /api/v1/users/profile-picture/{filename}`
- Serve profile picture image
- Public endpoint (no auth required)
- Returns image with cache headers (24 hours)
- Proper content-type for JPEG/PNG/WebP

#### `GET /api/v1/users/{user_id}`
- Get public user profile
- Returns user data with `profile_picture_url`

### 4. Schema Updates

**File:** `app/schemas/user.py`
- Added `profile_picture_url: Optional[str]` to `UserResponse`
- URL is dynamically constructed from filename

**File:** `app/schemas/comment.py`
- Added `profile_picture_url: Optional[str]` to `UserInfo`
- Ensures comment authors display with their profile pictures

### 5. Authentication Integration

**File:** `app/api/auth.py`

Updated all auth endpoints to include `profile_picture_url`:
- `POST /api/v1/auth/register` - Returns user with profile_picture_url
- `POST /api/v1/auth/login` - Returns user with profile_picture_url
- `POST /api/v1/auth/refresh` - Returns user with profile_picture_url

Helper function `_user_to_response()` converts domain User to UserResponse with proper URL construction.

### 6. Comments Integration

**File:** `app/api/comments.py`

Updated all comment endpoints to include author profile pictures:
- `GET /api/v1/decks/{deck_id}/comments` - Lists comments with author profile pictures
- `GET /api/v1/decks/{deck_id}/comments/{comment_id}` - Single comment with author profile picture
- `POST /api/v1/decks/{deck_id}/comments` - Created comment includes author profile picture
- `PUT /api/v1/decks/{deck_id}/comments/{comment_id}` - Updated comment includes author profile picture

Helper function `_user_to_user_info()` converts domain User to UserInfo with proper URL construction.

### 7. Application Setup

**File:** `app/main.py`
- Added `users` router to FastAPI application
- Properly ordered after auth endpoints

### 8. Dependencies

**File:** `requirements.txt`
- Added `Pillow==10.2.0` for image processing
- `python-multipart` already present for file uploads

### 9. Upload Directory Structure

```
backend/
└── uploads/
    └── profile_pictures/
        ├── .gitkeep
        └── (user uploaded images)
```

**File:** `.gitignore`
- Configured to ignore uploaded files but preserve directory structure

## Security Features

1. **File Type Validation:** MIME type checking, not just extension
2. **Size Limits:** 5MB maximum enforced on backend
3. **Filename Sanitization:** UUID-based filenames prevent path traversal
4. **Authentication Required:** Upload/delete endpoints require valid JWT
5. **Rate Limiting:** 5 uploads per hour per user
6. **Image Verification:** PIL validation ensures uploaded files are valid images

## Performance Optimizations

1. **Image Optimization:** Compressed images reduce bandwidth
2. **Cache Headers:** 24-hour cache for profile pictures
3. **Batch Loading:** Comment endpoints use batch queries to avoid N+1 problems
4. **CDN Ready:** URL structure compatible with future CDN integration

## API Response Examples

### UserResponse with Profile Picture
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "profile_picture_url": "http://localhost:8000/api/v1/users/profile-picture/abc123.jpg",
  "created_at": "2025-11-10T00:00:00Z",
  "updated_at": "2025-11-10T00:00:00Z"
}
```

### CommentResponse with Author Profile Picture
```json
{
  "id": "uuid",
  "deck_id": "deck-uuid",
  "user_id": "user-uuid",
  "content": "Great deck!",
  "user": {
    "id": "user-uuid",
    "name": "John Doe",
    "email": "user@example.com",
    "profile_picture_url": "http://localhost:8000/api/v1/users/profile-picture/abc123.jpg"
  },
  "upvotes": 5,
  "downvotes": 0,
  "score": 5,
  "is_edited": false,
  "created_at": "2025-11-10T00:00:00Z",
  "updated_at": "2025-11-10T00:00:00Z"
}
```

## Migration Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Database Migration
```bash
alembic upgrade head
```

### 3. Create Upload Directory
The directory is automatically created by the FileStorageService, but you can create it manually:
```bash
mkdir -p backend/uploads/profile_pictures
```

### 4. Start Server
```bash
uvicorn app.main:app --reload
```

### 5. Test Endpoints
```bash
# Upload profile picture (requires authentication)
curl -X POST http://localhost:8000/api/v1/users/me/profile-picture \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"

# Get current user profile
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Delete profile picture
curl -X DELETE http://localhost:8000/api/v1/users/me/profile-picture \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Future Enhancements

1. **Cloud Storage:** Migrate to AWS S3 or similar for scalability
2. **Multiple Sizes:** Generate thumbnail and full-size versions
3. **Image Cropping:** Frontend crop tool for user control
4. **CDN Integration:** Use CloudFront for global distribution
5. **Social Import:** Import profile pictures from OAuth providers
6. **Animated Avatars:** Support for GIF format
7. **Content Moderation:** Automated inappropriate content detection

## Testing Checklist

- [x] Database migration runs successfully
- [x] File upload validation works (type, size)
- [x] Image processing (resize, convert) functions correctly
- [x] Upload endpoint requires authentication
- [x] Old profile pictures are deleted on new upload
- [x] Delete endpoint removes both file and DB reference
- [x] Serve endpoint returns images with proper headers
- [x] Cache headers set correctly (24 hours)
- [x] Profile picture URLs included in auth responses
- [x] Profile picture URLs included in comment author info
- [x] Rate limiting applied to upload endpoint
- [x] CORS allows image requests from frontend

## Files Modified

### Core Changes
- `/Users/kike/Repos/OpenDeck/backend/requirements.txt`
- `/Users/kike/Repos/OpenDeck/backend/alembic/versions/20251110_2300_add_profile_picture.py`
- `/Users/kike/Repos/OpenDeck/backend/app/db/models.py`
- `/Users/kike/Repos/OpenDeck/backend/app/core/models.py`
- `/Users/kike/Repos/OpenDeck/backend/app/db/postgres_repo.py`

### New Files
- `/Users/kike/Repos/OpenDeck/backend/app/services/file_storage.py`
- `/Users/kike/Repos/OpenDeck/backend/app/api/users.py`

### Updated APIs
- `/Users/kike/Repos/OpenDeck/backend/app/api/auth.py`
- `/Users/kike/Repos/OpenDeck/backend/app/api/comments.py`
- `/Users/kike/Repos/OpenDeck/backend/app/main.py`

### Schemas
- `/Users/kike/Repos/OpenDeck/backend/app/schemas/user.py`
- `/Users/kike/Repos/OpenDeck/backend/app/schemas/comment.py`

### Infrastructure
- `/Users/kike/Repos/OpenDeck/backend/.gitignore`
- `/Users/kike/Repos/OpenDeck/backend/uploads/profile_pictures/.gitkeep`

## Architecture Principles Followed

1. **Clean Architecture:** Separation of concerns (core, db, api layers)
2. **Dependency Injection:** All dependencies injected via FastAPI
3. **Type Safety:** Complete type hints on all functions
4. **Error Handling:** Comprehensive validation and error messages
5. **Security First:** Authentication, validation, sanitization
6. **Performance:** Batch queries, caching, optimization
7. **Maintainability:** Clear documentation, consistent patterns

## Notes

- All profile picture URLs are dynamically constructed based on the request's base URL
- This ensures compatibility with different deployment environments
- The implementation is ready for frontend integration
- No frontend changes are included in this backend-only implementation
