# Google OAuth Login Implementation Plan

## Overview
Add Google OAuth 2.0 authentication as an alternative login method alongside the existing email/password authentication. Users can sign up and log in using their Google accounts.

## Phase 1: Backend Implementation

### 1.1 Environment Setup
- [ ] Add Google OAuth credentials to `.env`:
  ```bash
  # Google OAuth
  GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
  GOOGLE_CLIENT_SECRET=your-client-secret
  GOOGLE_REDIRECT_URI=http://localhost:4200/auth/google/callback
  ```
- [ ] Register application in Google Cloud Console
- [ ] Enable Google+ API
- [ ] Configure authorized redirect URIs

### 1.2 Database Schema Updates
- [ ] Update `users` table to support OAuth:
  - Add `oauth_provider` column (nullable, enum: 'google', 'local')
  - Add `oauth_id` column (nullable, unique for OAuth users)
  - Make `password_hash` nullable (OAuth users won't have passwords)
  - Add unique constraint on `(oauth_provider, oauth_id)`
- [ ] Create Alembic migration for schema changes

### 1.3 Dependencies
- [ ] Add to `requirements.txt`:
  ```
  google-auth==2.27.0
  google-auth-oauthlib==1.2.0
  google-auth-httplib2==0.2.0
  ```
- [ ] Install dependencies in Docker container

### 1.4 Core Domain Updates
- [ ] Update `app/core/models.py` `User` model:
  - Add `oauth_provider: Optional[str]`
  - Add `oauth_id: Optional[str]`
  - Update validation logic (password optional for OAuth)

### 1.5 Database Layer Updates
- [ ] Update `app/db/models.py` SQLAlchemy model with new columns
- [ ] Update `app/db/postgres_repo.py`:
  - Add `get_user_by_oauth_id(provider: str, oauth_id: str)` method
  - Add `create_oauth_user()` method
  - Update `create_user()` to handle OAuth users

### 1.6 Schemas
- [ ] Create `app/schemas/oauth.py`:
  ```python
  class GoogleAuthRequest(BaseModel):
      code: str
      redirect_uri: str

  class GoogleAuthResponse(BaseModel):
      access_token: str
      refresh_token: str
      user: UserResponse

  class GoogleUserInfo(BaseModel):
      id: str
      email: str
      name: str
      picture: Optional[str]
      verified_email: bool
  ```

### 1.7 OAuth Service
- [ ] Create `app/services/google_oauth_service.py`:
  - `verify_google_token(code: str, redirect_uri: str)` - Exchange code for tokens
  - `get_google_user_info(access_token: str)` - Fetch user profile from Google
  - `handle_google_login(code: str, redirect_uri: str)` - Main orchestration:
    1. Verify token with Google
    2. Get user info
    3. Check if user exists by email or oauth_id
    4. Create new user if needed
    5. Generate JWT tokens
    6. Return tokens + user info

### 1.8 API Endpoints
- [ ] Add to `app/api/auth.py`:
  ```python
  @router.post("/auth/google", response_model=GoogleAuthResponse)
  async def google_auth(
      request: GoogleAuthRequest,
      repo: UserRepository = Depends(get_user_repository)
  ):
      """
      Exchange Google authorization code for JWT tokens.
      Creates new user if doesn't exist.
      """
      pass

  @router.get("/auth/google/url")
  async def get_google_auth_url():
      """
      Returns the Google OAuth authorization URL
      for frontend to redirect users
      """
      pass
  ```

### 1.9 Security Considerations
- [ ] Add CORS configuration for Google OAuth redirect
- [ ] Validate `redirect_uri` matches configured values
- [ ] Verify Google token signature
- [ ] Handle edge cases:
  - Email already registered with local auth
  - OAuth user tries to login with password
  - Multiple OAuth providers for same email (future)

## Phase 2: Frontend Implementation

### 2.1 Environment Configuration
- [ ] Add to `environment.ts` and `environment.development.ts`:
  ```typescript
  googleClientId: 'your-client-id.apps.googleusercontent.com',
  googleRedirectUri: 'http://localhost:4200/auth/google/callback'
  ```

### 2.2 Dependencies
- [ ] Add Google Sign-In library:
  ```bash
  npm install @abacritt/angularx-social-login
  ```
- [ ] Add types:
  ```bash
  npm install --save-dev @types/gapi.auth2
  ```

### 2.3 Service Updates
- [ ] Update `app/services/auth.service.ts`:
  - Add `loginWithGoogle(code: string)` method
  - Add `getGoogleAuthUrl()` method
  - Handle OAuth token storage (same as regular login)

### 2.4 Login Component Updates (`app/pages/login/`)
- [ ] Add Google Sign-In button to template:
  ```html
  <!-- Existing email/password form -->

  <div class="flex items-center my-4">
    <div class="flex-1 border-t border-surface-300"></div>
    <span class="px-4 text-sm text-surface-500">{{ 'auth.orContinueWith' | translate }}</span>
    <div class="flex-1 border-t border-surface-300"></div>
  </div>

  <button
    type="button"
    (click)="loginWithGoogle()"
    class="w-full flex items-center justify-center gap-3 px-4 py-3 border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
  >
    <img src="assets/images/google-icon.svg" alt="Google" class="w-5 h-5" />
    <span>{{ 'auth.continueWithGoogle' | translate }}</span>
  </button>
  ```

- [ ] Update component TypeScript:
  ```typescript
  loginWithGoogle(): void {
    // Redirect to Google OAuth consent screen
    this.authService.getGoogleAuthUrl().subscribe({
      next: (url) => {
        window.location.href = url;
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: this.translateService.instant('common.error'),
          detail: this.translateService.instant('auth.googleLoginFailed')
        });
      }
    });
  }
  ```

### 2.5 OAuth Callback Component
- [ ] Create `app/pages/auth-callback/auth-callback.component.ts`:
  ```typescript
  @Component({
    selector: 'app-auth-callback',
    standalone: true,
    template: `
      <div class="flex items-center justify-center min-h-screen">
        <p-progressSpinner />
      </div>
    `
  })
  export class AuthCallbackComponent implements OnInit {
    constructor(
      private route: ActivatedRoute,
      private router: Router,
      private authService: AuthService
    ) {}

    ngOnInit() {
      // Extract code from URL params
      const code = this.route.snapshot.queryParamMap.get('code');

      if (code) {
        this.authService.loginWithGoogle(code).subscribe({
          next: () => {
            this.router.navigate(['/dashboard']);
          },
          error: () => {
            this.router.navigate(['/login']);
          }
        });
      } else {
        this.router.navigate(['/login']);
      }
    }
  }
  ```

- [ ] Add route in `app.routes.ts`:
  ```typescript
  {
    path: 'auth/google/callback',
    component: AuthCallbackComponent
  }
  ```

### 2.6 Register Component Updates
- [ ] Add same Google Sign-Up button to register page
- [ ] Reuse same OAuth flow (backend handles user creation)

### 2.7 Styling & Assets
- [ ] Download and add Google icon to `assets/images/google-icon.svg`
- [ ] Add dark mode styles for Google button
- [ ] Match PrimeNG design system

### 2.8 Translations
- [ ] Update `assets/i18n/en.json`:
  ```json
  {
    "auth": {
      "orContinueWith": "Or continue with",
      "continueWithGoogle": "Continue with Google",
      "googleLoginFailed": "Failed to sign in with Google. Please try again.",
      "accountAlreadyExists": "An account with this email already exists. Please sign in with your password."
    }
  }
  ```

- [ ] Update `assets/i18n/es.json`:
  ```json
  {
    "auth": {
      "orContinueWith": "O continuar con",
      "continueWithGoogle": "Continuar con Google",
      "googleLoginFailed": "Error al iniciar sesión con Google. Por favor, inténtalo de nuevo.",
      "accountAlreadyExists": "Ya existe una cuenta con este correo. Por favor, inicia sesión con tu contraseña."
    }
  }
  ```

## Phase 3: Testing

### 3.1 Backend Tests
- [ ] Unit tests for `google_oauth_service.py`:
  - Mock Google API calls
  - Test user creation flow
  - Test existing user login flow
  - Test error handling
- [ ] Integration tests for `/auth/google` endpoint
- [ ] Test database constraints

### 3.2 Frontend Tests
- [ ] Unit tests for OAuth callback component
- [ ] Integration tests for login flow
- [ ] E2E tests for complete OAuth flow

### 3.3 Manual Testing
- [ ] Test new user registration via Google
- [ ] Test existing user login via Google
- [ ] Test error cases:
  - User denies OAuth consent
  - Invalid authorization code
  - Network errors
  - Email conflict scenarios

## Phase 4: Documentation & Deployment

### 4.1 Documentation
- [ ] Update backend README with Google OAuth setup instructions
- [ ] Update frontend README with environment configuration
- [ ] Add Google Cloud Console setup guide
- [ ] Update API documentation

### 4.2 Deployment Considerations
- [ ] Update production environment variables
- [ ] Configure Google OAuth for production domain
- [ ] Update CORS settings for production
- [ ] Test OAuth flow in production environment

## Security Checklist
- [ ] Google token verification implemented
- [ ] CSRF protection for OAuth flow
- [ ] State parameter validation (optional but recommended)
- [ ] Redirect URI validation
- [ ] Proper error handling (don't leak sensitive info)
- [ ] Rate limiting on OAuth endpoints
- [ ] Secure token storage (httpOnly cookies consideration)

## Edge Cases & Considerations
1. **Email Conflict**: User tries to sign in with Google but email already registered with password
   - Strategy: Show message asking them to sign in with password, or merge accounts

2. **Profile Picture**: Google provides profile picture URL
   - Future enhancement: Store and display user avatar

3. **Email Verification**: Google users have verified emails
   - Skip email verification for OAuth users

4. **Password Reset**: OAuth users shouldn't access password reset
   - Update password reset flow to check auth method

5. **Account Linking**: User wants to link Google to existing account
   - Future enhancement: Add account linking in preferences

## Timeline Estimate
- Phase 1 (Backend): 6-8 hours
- Phase 2 (Frontend): 4-6 hours
- Phase 3 (Testing): 3-4 hours
- Phase 4 (Documentation): 2-3 hours
- **Total**: 15-21 hours

## Dependencies & Prerequisites
- Google Cloud Console account
- OAuth 2.0 Client ID and Secret
- Understanding of OAuth 2.0 flow
- FastAPI OAuth integration knowledge
- Angular OAuth handling experience

## Success Criteria
- [ ] Users can sign up using Google account
- [ ] Users can sign in using Google account
- [ ] OAuth users receive JWT tokens like regular users
- [ ] All existing features work for OAuth users
- [ ] Proper error handling and user feedback
- [ ] Security best practices implemented
- [ ] Documentation complete
- [ ] Tests passing with >80% coverage
