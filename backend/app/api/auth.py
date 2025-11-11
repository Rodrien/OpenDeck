"""Authentication API Endpoints"""

from fastapi import APIRouter, HTTPException, status, Request
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserCreate, UserResponse
from app.api.dependencies import AuthServiceDepends
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _build_profile_picture_url(request: Request, filename: str | None) -> str | None:
    """Build full URL for profile picture."""
    if not filename:
        return None
    base_url = str(request.base_url).rstrip("/")
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
    user = auth_service.user_repository.get_by_id(user_id)
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
