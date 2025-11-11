"""User Profile API Endpoints"""

from typing import Annotated
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.schemas.user import UserResponse
from app.api.dependencies import CurrentUser, UserRepoDepends
from app.services.file_storage import FileStorageService


router = APIRouter(prefix="/users", tags=["Users"])
limiter = Limiter(key_func=get_remote_address)

# Initialize file storage service
file_storage = FileStorageService()


def _build_profile_picture_url(request: Request, filename: str | None) -> str | None:
    """
    Build full URL for profile picture.

    Args:
        request: FastAPI request object
        filename: Profile picture filename

    Returns:
        Full URL to profile picture or None if no filename
    """
    if not filename:
        return None

    # Build URL using request base URL
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/api/v1/users/profile-picture/{filename}"


def _user_to_response(user, request: Request) -> UserResponse:
    """
    Convert User domain model to UserResponse with profile picture URL.

    Args:
        user: User domain model
        request: FastAPI request object

    Returns:
        UserResponse with profile_picture_url
    """
    profile_picture_url = _build_profile_picture_url(request, user.profile_picture)
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        profile_picture_url=profile_picture_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    request: Request,
    current_user: CurrentUser,
) -> UserResponse:
    """
    Get current authenticated user's profile.

    Returns:
        User profile with profile_picture_url
    """
    return _user_to_response(current_user, request)


@router.post(
    "/me/profile-picture",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("5/hour")  # Rate limit: 5 uploads per hour
async def upload_profile_picture(
    request: Request,
    file: Annotated[UploadFile, File(description="Profile picture image (JPEG, PNG, WebP, max 5MB)")],
    current_user: CurrentUser,
    user_repo: UserRepoDepends,
) -> UserResponse:
    """
    Upload or update profile picture for authenticated user.

    Args:
        request: FastAPI request
        file: Image file (JPEG, PNG, or WebP, max 5MB)
        current_user: Current authenticated user
        user_repo: User repository

    Returns:
        Updated user profile with new profile_picture_url

    Raises:
        HTTPException: If file validation fails or upload fails
    """
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}",
        )

    # Get content type
    content_type = file.content_type or "application/octet-stream"

    # Process and save image
    filename, error = file_storage.process_profile_picture(file_content, content_type)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )

    # Delete old profile picture if exists
    if current_user.profile_picture:
        file_storage.delete_profile_picture(current_user.profile_picture)

    # Update user record with new filename
    current_user.profile_picture = filename
    updated_user = user_repo.update(current_user)

    return _user_to_response(updated_user, request)


@router.delete("/me/profile-picture", response_model=UserResponse)
async def delete_profile_picture(
    request: Request,
    current_user: CurrentUser,
    user_repo: UserRepoDepends,
) -> UserResponse:
    """
    Remove profile picture for authenticated user.

    Args:
        request: FastAPI request
        current_user: Current authenticated user
        user_repo: User repository

    Returns:
        Updated user profile without profile picture

    Raises:
        HTTPException: If user has no profile picture
    """
    if not current_user.profile_picture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no profile picture to delete",
        )

    # Delete file from storage
    old_filename = current_user.profile_picture
    success, error = file_storage.delete_profile_picture(old_filename)

    if not success:
        # Log error but don't fail the request
        # The database record will still be updated
        pass

    # Update user record
    current_user.profile_picture = None
    updated_user = user_repo.update(current_user)

    return _user_to_response(updated_user, request)


@router.get("/profile-picture/{filename}")
async def get_profile_picture(filename: str) -> FileResponse:
    """
    Serve profile picture image.

    Args:
        filename: Name of the profile picture file

    Returns:
        Image file with appropriate cache headers

    Raises:
        HTTPException: If file not found
    """
    # Sanitize filename to prevent path traversal
    safe_filename = file_storage.sanitize_filename(filename)

    # Get file path
    file_path = file_storage.get_file_path(safe_filename)

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile picture not found",
        )

    # Determine media type from extension
    media_type = "image/jpeg"
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".webp"):
        media_type = "image/webp"

    # Return file with cache headers
    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
        },
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_profile(
    request: Request,
    user_id: str,
    user_repo: UserRepoDepends,
) -> UserResponse:
    """
    Get public user profile by ID.

    Args:
        request: FastAPI request
        user_id: User ID to retrieve
        user_repo: User repository

    Returns:
        User profile with profile_picture_url

    Raises:
        HTTPException: If user not found
    """
    user = user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return _user_to_response(user, request)
