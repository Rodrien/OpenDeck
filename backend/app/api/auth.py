"""Authentication API Endpoints"""

import logging
from fastapi import APIRouter, HTTPException, status, Request, Depends
from sqlalchemy.orm import Session
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserCreate, UserResponse
from app.schemas.oauth import GoogleAuthRequest, GoogleAuthResponse, GoogleAuthUrlResponse
from app.api.dependencies import AuthServiceDepends, get_user_repo
from app.config import settings
from app.services.google_oauth_service import GoogleOAuthService
from app.db.base import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_profile_picture_url(request: Request, filename: str | None) -> str | None:
    """
    Build full URL for profile picture using configured base URL.

    Uses settings.base_url instead of request.base_url to prevent
    Host header manipulation attacks.

    Args:
        request: FastAPI request object (unused, kept for compatibility)
        filename: Profile picture filename

    Returns:
        Full URL to profile picture or None if no filename
    """
    if not filename:
        return None
    # Use configured base URL instead of request.base_url for security
    base_url = settings.base_url.rstrip("/")
    return f"{base_url}/api/v1/users/profile-picture/{filename}"


def _user_to_response(user, request: Request) -> UserResponse:
    """Convert User domain model to UserResponse with profile picture URL."""
    profile_picture_url = _build_profile_picture_url(request, user.profile_picture)
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        profile_picture_url=profile_picture_url,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    auth_service: AuthServiceDepends,
) -> UserResponse:
    """
    Register a new user account.

    Args:
        request: FastAPI request
        user_data: User registration data (email, name, password)
        auth_service: Authentication service dependency

    Returns:
        Created user information (without password)

    Raises:
        HTTPException: If email already exists
    """
    try:
        user = auth_service.register_user(
            email=user_data.email,
            name=user_data.name,
            password=user_data.password,
        )
        return _user_to_response(user, request)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthServiceDepends,
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    Args:
        request: FastAPI request
        login_data: Login credentials (email, password)
        auth_service: Authentication service dependency

    Returns:
        Access and refresh JWT tokens

    Raises:
        HTTPException: If credentials are invalid
    """
    user = auth_service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user.id)
    refresh_token = auth_service.create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=_user_to_response(user, request),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    auth_service: AuthServiceDepends,
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    Args:
        request: FastAPI request
        refresh_data: Refresh token
        auth_service: Authentication service dependency

    Returns:
        New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    user_id = auth_service.verify_token(refresh_data.refresh_token, token_type="refresh")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user data to include in response
    user = auth_service.user_repo.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user_id)
    new_refresh_token = auth_service.create_refresh_token(user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=_user_to_response(user, request),
    )


@router.get("/google/url", response_model=GoogleAuthUrlResponse)
async def get_google_auth_url(
    auth_service: AuthServiceDepends,
    user_repo = Depends(get_user_repo),
) -> GoogleAuthUrlResponse:
    """
    Get Google OAuth authorization URL.
    
    Returns:
        Google OAuth authorization URL for frontend to redirect user
    """
    try:
        # Create Google OAuth service
        google_service = GoogleOAuthService(user_repo, auth_service)
        
        auth_url = google_service.get_authorization_url()
        
        return GoogleAuthUrlResponse(authorization_url=auth_url)
        
    except ValueError as e:
        # Log internal error but return generic message
        logger.error(f"OAuth configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable. Please try again later.",
        )
    except Exception as e:
        # Log internal error but return generic message
        logger.error(f"Failed to generate Google OAuth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to initialize authentication. Please try again.",
        )


@router.post("/google/callback", response_model=GoogleAuthResponse)
async def google_auth_callback(
    request: Request,
    auth_data: GoogleAuthRequest,
    auth_service: AuthServiceDepends,
    user_repo = Depends(get_user_repo),
) -> GoogleAuthResponse:
    """
    Handle Google OAuth callback.
    
    Args:
        request: FastAPI request
        auth_data: Google authorization code
        
    Returns:
        JWT tokens and user information
        
    Raises:
        HTTPException: If OAuth flow fails
    """
    try:
        # Create Google OAuth service
        google_service = GoogleOAuthService(user_repo, auth_service)

        # Handle Google login flow with state validation
        auth_response = await google_service.handle_google_login(
            code=auth_data.code,
            state=auth_data.state
        )
        
        # Update profile picture URL for response
        user = auth_response.user
        if user.profile_picture_url and user.profile_picture_url.startswith("http"):
            # Keep external Google profile picture URL
            pass
        else:
            # Build internal profile picture URL if needed
            user.profile_picture_url = _build_profile_picture_url(request, user.profile_picture_url)
        
        return auth_response
        
    except HTTPException:
        raise
    except Exception as e:
        # Log internal error but return generic message
        logger.error(f"Failed to authenticate with Google: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again.",
        )
