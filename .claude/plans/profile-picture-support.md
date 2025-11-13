# Profile Picture Support Implementation Plan

**Status**: Pending
**Created**: 2025-11-10
**Priority**: Medium

## Overview

Add profile picture support to OpenDeck, allowing users to upload a profile picture in the preferences section and display it in the topbar and comment sections throughout the application.

## Implementation Tasks

### Backend Changes

#### 1. Database Schema
- [ ] Add `profile_picture` column to the `users` table (VARCHAR, nullable)
- [ ] Create Alembic migration for the schema change
- [ ] Column will store the filename/path relative to upload directory

#### 2. File Storage Service
- [ ] Create `app/services/file_storage.py` for image handling
- [ ] Implement image upload validation:
  - Allowed formats: JPEG, PNG, WebP
  - Max file size: 5MB
  - MIME type validation
- [ ] Implement image processing:
  - Resize to standard dimensions (200x200px)
  - Maintain aspect ratio with center crop
  - Optimize file size
- [ ] Store images in `/backend/uploads/profile_pictures/` directory
- [ ] Generate unique filenames using UUID to prevent conflicts
- [ ] Add utility functions for file deletion

#### 3. API Endpoints
- [ ] `POST /api/v1/users/me/profile-picture` - Upload profile picture
  - Accept multipart/form-data
  - Validate file type and size
  - Process and save image
  - Update user record
  - Return updated user with profile_picture_url
- [ ] `GET /api/v1/users/{user_id}/profile-picture` - Serve profile picture
  - Return image file with appropriate headers
  - Add cache-control headers for performance
  - Handle missing images gracefully
- [ ] `DELETE /api/v1/users/me/profile-picture` - Remove profile picture
  - Delete image file from storage
  - Clear profile_picture field in database
  - Return updated user
- [ ] Update `/api/v1/auth/me` to include profile_picture_url
- [ ] Ensure profile_picture_url is included in comment author responses

#### 4. Schema Updates
- [ ] Update `app/schemas/user.py`:
  - Add `profile_picture_url: Optional[str]` to `UserResponse`
- [ ] Update `app/schemas/comment.py` (if exists):
  - Ensure comment author includes profile_picture_url
- [ ] Update repository methods to construct profile_picture_url from filename

#### 5. Security & Validation
- [ ] Add file upload size limits in FastAPI
- [ ] Implement MIME type validation
- [ ] Sanitize filenames to prevent path traversal
- [ ] Add authentication requirements to all endpoints
- [ ] Implement rate limiting for uploads (prevent abuse)

### Frontend Changes

#### 1. Models & Interfaces
- [ ] Update `opendeck-portal/src/app/models/user.model.ts`:
  - Add `profilePictureUrl?: string` to User interface
- [ ] Update `opendeck-portal/src/app/models/comment.model.ts`:
  - Ensure CommentAuthor includes profilePictureUrl

#### 2. Services
- [ ] Update `opendeck-portal/src/app/services/user.service.ts`:
  - Add `uploadProfilePicture(file: File): Observable<User>` method
  - Add `deleteProfilePicture(): Observable<User>` method
  - Add `getProfilePictureUrl(userId: string): string` helper method

#### 3. Preferences Page Component
- [ ] Update `opendeck-portal/src/app/pages/preferences/preferences.component.html`:
  - Add profile picture section at the top
  - Use PrimeNG FileUpload component with custom template
  - Show current profile picture or placeholder avatar
  - Add "Change Picture" button to trigger file upload
  - Add "Remove Picture" button (only shown if picture exists)
  - Display upload progress indicator
  - Show success/error messages using PrimeNG Message component
- [ ] Update `opendeck-portal/src/app/pages/preferences/preferences.component.ts`:
  - Add file upload handler
  - Implement image preview before upload
  - Add validation (file type, size)
  - Handle upload success/error
  - Update user state after successful upload
  - Implement picture removal
- [ ] Update `opendeck-portal/src/app/pages/preferences/preferences.component.scss`:
  - Style profile picture section
  - Add circular image display
  - Ensure dark mode compatibility

#### 4. Topbar Component
- [ ] Update `opendeck-portal/src/app/layout/topbar/topbar.component.html`:
  - Update `<p-avatar>` component
  - Add `[image]` binding for profile picture URL
  - Keep `[label]` binding for initials as fallback
  - Ensure proper image sizing and styling
- [ ] Update `opendeck-portal/src/app/layout/topbar/topbar.component.ts`:
  - Add logic to determine whether to show image or initials
  - Subscribe to user changes to update picture in real-time
- [ ] Update `opendeck-portal/src/app/layout/topbar/topbar.component.scss`:
  - Ensure avatar displays correctly with both images and initials
  - Maintain dark mode compatibility

#### 5. Comments Component
- [ ] Update `opendeck-portal/src/app/components/deck-comments/deck-comments.component.html`:
  - Update comment author avatar display
  - Use `<p-avatar>` with `[image]` binding
  - Fallback to initials when no picture available
  - Ensure consistent sizing with topbar avatar
- [ ] Update `opendeck-portal/src/app/components/deck-comments/deck-comments.component.ts`:
  - Add helper method to get author initials
  - Handle missing profile pictures gracefully
- [ ] Update `opendeck-portal/src/app/components/deck-comments/deck-comments.component.scss`:
  - Style comment avatars consistently
  - Ensure dark mode compatibility

#### 6. Translations
- [ ] Update `opendeck-portal/src/assets/i18n/en.json`:
  - Add profile picture section translations
  - Add upload/remove button labels
  - Add error messages (file too large, invalid type, etc.)
  - Add success messages
- [ ] Update `opendeck-portal/src/assets/i18n/es.json`:
  - Add Spanish translations for all new keys

### Testing & Validation

#### Backend Tests
- [ ] Unit tests for file storage service
- [ ] Integration tests for profile picture endpoints
- [ ] Test file upload validation (size, type)
- [ ] Test image processing (resize, format conversion)
- [ ] Test file deletion
- [ ] Test authentication requirements

#### Frontend Tests
- [ ] Component tests for preferences page upload functionality
- [ ] Test avatar display in topbar and comments
- [ ] Test file validation on frontend
- [ ] Test error handling and user feedback
- [ ] Visual regression tests for dark mode

#### Manual Testing
- [ ] Upload various image formats (JPEG, PNG, WebP)
- [ ] Test large file rejection (> 5MB)
- [ ] Test invalid file type rejection
- [ ] Verify image display in topbar
- [ ] Verify image display in comments section
- [ ] Test picture removal functionality
- [ ] Test on different screen sizes (responsive)
- [ ] Test in light and dark modes
- [ ] Test with multiple users/comments
- [ ] Test cache behavior

## Technical Considerations

### Image Storage
- **MVP**: Use local filesystem storage in `/backend/uploads/profile_pictures/`
- **Future**: Migrate to AWS S3 or similar cloud storage for scalability
- **Directory Structure**:
  ```
  backend/uploads/profile_pictures/
  ├── {uuid1}.jpg
  ├── {uuid2}.png
  └── {uuid3}.webp
  ```

### Image Processing
- Use Pillow (PIL) library for Python image processing
- Standard dimensions: 200x200px (suitable for UI display)
- Output format: Keep original format or convert to WebP for better compression
- Quality: Balance between file size and visual quality (85% quality)

### Security
- **File Type Validation**: Check MIME type, not just extension
- **Size Limits**: Enforce 5MB limit on both frontend and backend
- **Filename Sanitization**: Use UUIDs to prevent path traversal attacks
- **Authentication**: Require valid JWT token for all upload/delete operations
- **Rate Limiting**: Limit upload frequency per user (e.g., 5 uploads per hour)

### Performance
- **Caching**: Add Cache-Control headers to profile picture GET endpoint
  - `Cache-Control: public, max-age=86400` (24 hours)
- **CDN Ready**: Structure URLs to be CDN-compatible for future optimization
- **Lazy Loading**: Use Angular's lazy loading for images
- **Compression**: Optimize images on upload to reduce bandwidth

### CORS & URL Structure
- Profile picture URLs: `http://localhost:8000/api/v1/users/{user_id}/profile-picture`
- Ensure CORS allows image requests from frontend origin
- Use relative URLs where possible for environment independence

### Fallback Behavior
- When no profile picture exists:
  - Backend returns `profile_picture_url: null`
  - Frontend displays avatar with user initials
  - Use consistent color scheme for initial-based avatars
- Graceful degradation if image fails to load

## Dependencies

### Backend
- [ ] Pillow (PIL Fork) - Image processing library
  ```bash
  pip install Pillow
  ```
- [ ] python-multipart - For handling multipart form data
  ```bash
  pip install python-multipart
  ```

### Frontend
- Already available: PrimeNG components (Avatar, FileUpload, Message)
- No additional dependencies required

## Migration Strategy

1. **Database Migration**: Run Alembic migration to add column
2. **Create Upload Directory**: Ensure `/backend/uploads/profile_pictures/` exists with proper permissions
3. **Deploy Backend**: Deploy new API endpoints
4. **Deploy Frontend**: Deploy updated UI components
5. **User Communication**: Announce new feature to users
6. **Monitor**: Watch for upload errors, storage issues

## Future Enhancements

- [ ] Support for animated avatars (GIF)
- [ ] Crop tool in frontend for user to select image area
- [ ] Multiple image sizes (thumbnail, medium, large)
- [ ] Migration to cloud storage (AWS S3, Cloudinary)
- [ ] Image moderation (detect inappropriate content)
- [ ] Default avatar generation with user initials and random colors
- [ ] Social login profile picture import (Google, GitHub)

## Success Criteria

- Users can upload profile pictures from preferences page
- Profile pictures display correctly in topbar
- Profile pictures display correctly in comments section
- Images are properly validated and processed
- System handles missing images gracefully
- Dark mode compatibility maintained
- Multi-language support maintained
- No performance degradation
- Secure file handling with no vulnerabilities

## Timeline Estimate

- Backend implementation: 4-6 hours
- Frontend implementation: 4-6 hours
- Testing and bug fixes: 2-3 hours
- **Total**: 10-15 hours
