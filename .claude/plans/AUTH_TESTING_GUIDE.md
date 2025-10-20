# OpenDeck Authentication Testing Guide

## Quick Start

### Test Credentials
```
Email: test@example.com
Password: password123
```

### Backend Setup
Ensure the backend is running:
```bash
cd /Users/kike/Repos/OpenDeck
docker-compose up
# Backend should be available at http://localhost:8000
```

### Frontend Setup
Start the Angular development server:
```bash
cd /Users/kike/Repos/OpenDeck/opendeck-portal
npm start
# Frontend should be available at http://localhost:4200
```

---

## Testing Scenarios

### 1. Register New User

**Steps**:
1. Navigate to `http://localhost:4200/auth/register`
2. Fill out the form:
   - Email: `newuser@test.com`
   - Username: `testuser`
   - Password: `password123`
   - Confirm Password: `password123`
3. Click "Create Account"

**Expected Result**:
- Loading spinner appears
- On success: Automatically logged in and redirected to dashboard
- User info appears in topbar (avatar with "TE" initials)
- JWT token stored in localStorage

**Check localStorage**:
```javascript
localStorage.getItem('opendeck_token')    // Should have JWT token
localStorage.getItem('opendeck_user')     // Should have user JSON
```

---

### 2. Login with Existing User

**Steps**:
1. Navigate to `http://localhost:4200/auth/login`
2. Enter credentials:
   - Email: `test@example.com`
   - Password: `password123`
3. Click "Sign In"

**Expected Result**:
- Loading spinner appears
- Redirected to dashboard (`/`)
- User info in topbar shows "test@example.com"

---

### 3. Test Protected Routes (Auth Guard)

**Steps**:
1. Open incognito/private browser window
2. Navigate directly to `http://localhost:4200/pages/flashcards`

**Expected Result**:
- Redirected to login page
- URL becomes: `http://localhost:4200/auth/login?returnUrl=/pages/flashcards`
- After login, automatically redirected back to flashcards page

---

### 4. Test Guest Guard (Prevent Logged-in Access)

**Steps**:
1. Login first
2. Try to navigate to `http://localhost:4200/auth/login`

**Expected Result**:
- Immediately redirected to dashboard (`/`)
- Same behavior for `/auth/register`

---

### 5. Test Logout

**Steps**:
1. Login first
2. Click user avatar/menu in topbar
3. Click "Logout" button
4. Confirm in dialog

**Expected Result**:
- Confirmation dialog appears
- After confirm: Redirected to login page
- User info removed from topbar
- localStorage cleared
- Attempting to access protected routes redirects to login

---

### 6. Form Validation Testing

#### Login Form Validation
**Test Cases**:
- Submit empty form → Should show "Email is required"
- Enter invalid email (e.g., "notanemail") → "Please enter a valid email"
- Enter email, leave password empty → "Password is required"
- Submit button disabled until form is valid

#### Register Form Validation
**Test Cases**:
- Submit empty form → Shows all required field errors
- Invalid email → "Please enter a valid email address"
- Username < 3 chars → "Username must be at least 3 characters"
- Password < 8 chars → "Password must be at least 8 characters"
- Passwords don't match → "Passwords do not match"
- Submit button disabled until all validations pass

---

## Visual Testing

### Dark Mode
1. Login to application
2. Toggle dark mode using sun/moon icon in topbar
3. Verify login/register pages render correctly in both modes
4. Check contrast and readability

### Responsive Testing
1. Open developer tools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test on various screen sizes:
   - Mobile (375px)
   - Tablet (768px)
   - Desktop (1920px)
4. Verify:
   - Forms are readable and usable
   - Topbar user menu works on mobile
   - Login/register pages layout properly

---

## Browser DevTools Checks

### Network Tab
After login/register:
```
POST http://localhost:8000/api/v1/auth/login
Status: 200
Response: {
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "test@example.com",
    "username": "testuser"
  }
}
```

### Console Tab
Should see:
- No errors (red messages)
- Auth guard logging if attempts to access protected routes

### Application Tab (localStorage)
After login:
```
opendeck_token: "eyJ..."
opendeck_user: '{"id":"...","email":"...","username":"..."}'
```

---

## Common Issues & Troubleshooting

### Issue: "Connection refused" or CORS errors
**Solution**:
- Ensure backend is running on port 8000
- Check backend logs for errors
- Verify CORS is enabled in backend (should allow localhost:4200)

### Issue: Login succeeds but page doesn't redirect
**Solution**:
- Check browser console for JavaScript errors
- Verify AuthService is properly updating state
- Check router navigation in DevTools

### Issue: "Invalid credentials" error
**Solution**:
- Verify backend is in development mode (auth bypass enabled)
- Check backend logs to see if request reaches server
- Verify email/password match test credentials

### Issue: Protected routes accessible without login
**Solution**:
- Check that authGuard is applied to routes
- Verify AuthService.isLoggedIn() returns correct value
- Check localStorage for token

### Issue: Form validation not working
**Solution**:
- Check ReactiveFormsModule is imported
- Verify form control names match template
- Check validation errors in component

---

## Advanced Testing

### Test Token Expiration (Manual)
1. Login and get token
2. In browser DevTools, manually modify token in localStorage
3. Try to access protected route
4. Should be redirected to login (invalid token)

### Test Return URL
1. Logout
2. Manually navigate to: `http://localhost:4200/pages/flashcards/viewer/123`
3. Should redirect to login with returnUrl
4. After login, should return to viewer page

### Test Multiple Tabs
1. Login in Tab 1
2. Open Tab 2 (same site)
3. Both tabs should show logged-in state
4. Logout in Tab 1
5. Tab 2 won't auto-update (expected behavior)
6. Refresh Tab 2 → Should show logged-out state

---

## API Endpoints Used

### Login
```
POST /api/v1/auth/login
Body: { "email": "...", "password": "..." }
Response: { "access_token": "...", "token_type": "bearer", "user": {...} }
```

### Register
```
POST /api/v1/auth/register
Body: { "email": "...", "username": "...", "password": "..." }
Response: { "access_token": "...", "token_type": "bearer", "user": {...} }
```

### Protected Endpoints (with JWT)
```
GET /api/v1/flashcards
Header: Authorization: Bearer <token>
```

---

## Automated Testing Commands

### Build Test
```bash
cd /Users/kike/Repos/OpenDeck/opendeck-portal
npm run build
```
**Expected**: No compilation errors

### Unit Tests (if configured)
```bash
npm test
```

### Linting
```bash
npm run lint
```

---

## Success Criteria

Authentication system is working correctly if:

- ✓ Users can register new accounts
- ✓ Users can login with existing credentials
- ✓ JWT tokens are stored and sent with requests
- ✓ Protected routes redirect to login when unauthenticated
- ✓ Authenticated users cannot access login/register pages
- ✓ User info displays correctly in topbar
- ✓ Logout clears authentication state
- ✓ Return URL works after login
- ✓ Form validation prevents invalid submissions
- ✓ Error messages display for failed auth attempts
- ✓ No console errors during normal operation
- ✓ Application builds without compilation errors

---

## Demo User Accounts

For testing purposes, you can create multiple users:

```
User 1:
  Email: student1@university.edu
  Username: student1
  Password: password123

User 2:
  Email: student2@university.edu
  Username: student2
  Password: password123

User 3:
  Email: teacher@university.edu
  Username: professor
  Password: password123
```

---

## Next Steps After Testing

Once authentication is verified to work:

1. **Test Flashcard Integration**: Verify flashcard decks load for authenticated users
2. **Test Auth Interceptor**: Check that all API calls include Bearer token
3. **Backend Auth Activation**: Remove development bypass in backend
4. **Token Refresh**: Implement automatic token refresh (future enhancement)
5. **Session Management**: Add session timeout warnings

---

**Guide Version**: 1.0
**Last Updated**: 2025-10-18
**Author**: Claude Code
