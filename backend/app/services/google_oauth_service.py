"""
Google OAuth Service

Handles Google OAuth 2.0 authentication flow including token verification,
user information retrieval, and user creation/login.
"""

import os
import json
import logging
from typing import Optional, Tuple
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.models import User
from app.core.interfaces import UserRepository
from app.schemas.oauth import GoogleUserInfo, GoogleAuthResponse
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.config import settings

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""
    
    def __init__(self, user_repo: UserRepository, auth_service: AuthService):
        self.user_repo = user_repo
        self.auth_service = auth_service
        
        # Google OAuth configuration
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:4200/auth/google/callback")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Google OAuth credentials not configured")
    
    def get_authorization_url(self) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Returns:
            Authorization URL for Google OAuth consent screen
        """
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                ],
            )
            
            flow.redirect_uri = self.redirect_uri
            
            # Generate authorization URL
            authorization_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="consent",
            )
            
            logger.info(f"Generated Google OAuth authorization URL with state: {state}")
            return authorization_url
            
        except Exception as e:
            logger.error(f"Failed to generate Google OAuth authorization URL: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate OAuth authorization URL"
            )
    
    async def exchange_code_for_tokens(self, code: str) -> Tuple[str, str]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Tuple of (access_token, refresh_token)
        """
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                ],
            )
            
            flow.redirect_uri = self.redirect_uri
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            
            access_token = flow.credentials.token
            refresh_token = flow.credentials.refresh_token or ""
            
            if not access_token:
                raise ValueError("No access token received from Google")
            
            logger.info("Successfully exchanged authorization code for tokens")
            return access_token, refresh_token
            
        except Exception as e:
            logger.error(f"Failed to exchange authorization code for tokens: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )
    
    async def get_google_user_info(self, access_token: str) -> GoogleUserInfo:
        """
        Get user information from Google using access token.
        
        Args:
            access_token: Google OAuth access token
            
        Returns:
            Google user information
        """
        try:
            # Get user info from Google API
            url = "https://www.googleapis.com/oauth2/v2/userinfo"
            
            response_obj = AuthorizedSession(access_token).get(url)
            
            if response_obj.status_code != 200:
                raise ValueError(f"Google API returned status {response_obj.status_code}")
            
            user_data = response_obj.json()
            
            # Parse user info
            google_user = GoogleUserInfo(
                id=user_data.get("id"),
                email=user_data.get("email"),
                name=user_data.get("name"),
                picture=user_data.get("picture"),
                verified_email=user_data.get("verified_email", False)
            )
            
            if not google_user.email or not google_user.id:
                raise ValueError("Invalid user data received from Google")
            
            logger.info(f"Retrieved user info for Google user: {google_user.email}")
            return google_user
            
        except Exception as e:
            logger.error(f"Failed to get Google user info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to retrieve user information from Google"
            )
    
    async def handle_google_login(self, code: str) -> GoogleAuthResponse:
        """
        Handle complete Google OAuth login flow.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Authentication response with JWT tokens and user info
        """
        try:
            # Exchange code for tokens
            access_token, refresh_token = await self.exchange_code_for_tokens(code)
            
            # Get user info from Google
            google_user = await self.get_google_user_info(access_token)
            
            # Check if user exists by OAuth ID
            existing_user = self.user_repo.get_by_oauth_id("google", google_user.id)
            
            if existing_user:
                # User exists, login and return tokens
                logger.info(f"Existing Google user logging in: {google_user.email}")
                jwt_tokens = self.auth_service.create_tokens(existing_user)
                user_response = UserResponse.from_user(existing_user)
                
                return GoogleAuthResponse(
                    access_token=jwt_tokens["access_token"],
                    refresh_token=jwt_tokens["refresh_token"],
                    user=user_response
                )
            
            # Check if user exists by email (might have registered with password)
            email_user = self.user_repo.get_by_email(google_user.email)
            
            if email_user and email_user.oauth_provider != "google":
                # Email already registered with different auth method
                logger.warning(f"Email {google_user.email} already registered with non-OAuth method")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An account with this email already exists. Please sign in with your password."
                )
            
            # Create new OAuth user
            new_user = User(
                id="",  # Will be generated in repository
                email=google_user.email,
                name=google_user.name,
                password_hash=None,  # OAuth users don't have passwords
                oauth_provider="google",
                oauth_id=google_user.id,
                profile_picture=google_user.picture  # Store Google profile picture URL
            )
            
            created_user = self.user_repo.create(new_user)
            logger.info(f"Created new Google user: {google_user.email}")
            
            # Generate JWT tokens
            jwt_tokens = self.auth_service.create_tokens(created_user)
            user_response = UserResponse.from_user(created_user)
            
            return GoogleAuthResponse(
                access_token=jwt_tokens["access_token"],
                refresh_token=jwt_tokens["refresh_token"],
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to handle Google login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authenticate with Google"
            )


# Helper function to create authorized session
class AuthorizedSession:
    """Simple authorized session for Google API requests."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
    
    def get(self, url: str) -> requests.Response:
        """Make GET request with authorization header."""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        return response