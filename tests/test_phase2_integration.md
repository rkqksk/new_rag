# Phase 2 Integration Test Guide

## Test Environment
- API Server: http://localhost:8001
- Frontend: http://localhost:8080
- PWA: http://localhost:8080/mobile/pwa/
- Mock Users: admin@example.com / password123, worker@example.com / password123

## 1. Authentication Tests

### 1.1 Login Flow - Web
1. Navigate to http://localhost:8080/login.html
2. Enter credentials: admin@example.com / password123
3. Click "로그인"
4. **Expected**: Redirect to /chat.html with navigation bar showing user name

### 1.2 Login Flow - PWA
1. Navigate to http://localhost:8080/mobile/pwa/login.html
2. Enter credentials: worker@example.com / password123
3. Click "로그인"
4. **Expected**: Redirect to /mobile/pwa/index.html showing user avatar

### 1.3 Login Flow - React Native
1. Open React Native app (if running)
2. Navigate to Login screen
3. Enter credentials: admin@example.com / password123
4. Click "로그인"
5. **Expected**: Navigate to Main screen with user avatar in header

### 1.4 Auto-Login Check
1. After successful login, close browser
2. Reopen browser and navigate to http://localhost:8080/chat.html
3. **Expected**: Automatically logged in (no redirect to login page)

### 1.5 Protected Routes
1. Without logging in, navigate to:
   - http://localhost:8080/chat.html
   - http://localhost:8080/realtime-demo.html
   - http://localhost:8080/profile.html
2. **Expected**: All pages redirect to /login.html

## 2. Navigation Tests

### 2.1 Web Navigation Bar
1. Login to web app
2. Check navigation bar displays:
   - Logo "🚀 RAG Enterprise"
   - Navigation links: "제품 검색", "실시간 데모"
   - User avatar and name
3. Click on "제품 검색" link
4. **Expected**: Navigate to /chat.html with active link highlighted

### 2.2 User Dropdown Menu
1. Click on user avatar in navigation bar
2. **Expected**: Dropdown menu appears with:
   - "👤 내 프로필"
   - "🚪 로그아웃" (red text)
3. Click "내 프로필"
4. **Expected**: Navigate to /profile.html

### 2.3 PWA Bottom Navigation
1. Login to PWA
2. Check bottom navigation shows:
   - 홈 (active, purple)
   - 검색
   - 프로필
3. Click "프로필" tab
4. **Expected**: Navigate to profile page

## 3. Profile Management Tests

### 3.1 Profile Information Display
1. Navigate to http://localhost:8080/profile.html
2. **Expected**: Displays:
   - User avatar (first letter of name)
   - Name, email, phone, role, status
   - Created date, last login date

### 3.2 Password Change
1. On profile page, scroll to "비밀번호 변경" section
2. Fill in:
   - Current password: password123
   - New password: newpassword123
   - Confirm password: newpassword123
3. Click "비밀번호 변경"
4. **Expected**: Success message "비밀번호가 성공적으로 변경되었습니다"
5. Logout and login with new password: newpassword123
6. **Expected**: Login successful

### 3.3 Password Strength Indicator
1. On profile page, type in new password field
2. **Expected**:
   - Short password (< 8 chars): Red bar, 33% width
   - Medium password (8-12 chars, mixed): Yellow bar, 66% width
   - Strong password (12+ chars, all types): Green bar, 100% width

## 4. Token Management Tests

### 4.1 Token Storage
1. Login to web app
2. Open browser DevTools → Application → Local Storage
3. **Expected**: Three items stored:
   - access_token
   - refresh_token
   - user (JSON object)

### 4.2 Token Auto-Refresh
1. Login to web app
2. Open browser Console
3. **Expected**: Console log shows "Token refresh scheduled in XXXs"
4. Wait for refresh to occur (or manually trigger by waiting 30 minutes)
5. **Expected**: New token refreshed automatically without logout

### 4.3 Token Expiry Handling
1. Login to web app
2. Manually edit localStorage access_token to invalid value
3. Try to navigate to protected page or make API call
4. **Expected**: Automatic token refresh attempt, or redirect to login if refresh fails

## 5. Logout Tests

### 5.1 Web Logout
1. Login to web app
2. Click user avatar → "로그아웃"
3. Confirm logout dialog
4. **Expected**:
   - Redirect to /login.html
   - localStorage cleared (no access_token, refresh_token, user)

### 5.2 PWA Logout
1. Login to PWA
2. Click user avatar in header
3. Click "로그아웃"
4. Confirm logout alert
5. **Expected**: Redirect to /mobile/pwa/login.html

### 5.3 React Native Logout
1. Login to React Native app
2. Navigate to Profile screen
3. Click "로그아웃" button
4. Confirm logout alert
5. **Expected**:
   - Navigate back to Login screen
   - AsyncStorage cleared

## 6. Cross-Platform Consistency Tests

### 6.1 Login State Sync (Web ↔ PWA)
1. Login on web (desktop)
2. Open PWA in same browser
3. **Expected**: PWA shows logged in state (same user)

### 6.2 Logout State Sync
1. Login on web and PWA (same browser)
2. Logout from web
3. Refresh PWA page
4. **Expected**: PWA redirects to login page

## 7. Error Handling Tests

### 7.1 Invalid Credentials
1. Try to login with invalid credentials
2. **Expected**: Error message "로그인 실패" with red alert

### 7.2 Network Error
1. Stop API server
2. Try to login
3. **Expected**: Error message "서버 연결에 실패했습니다"

### 7.3 Token Refresh Failure
1. Login successfully
2. Stop API server
3. Wait for token refresh attempt
4. **Expected**: Redirect to login page after refresh failure

## Test Results Summary

| Test Category | Web | PWA | React Native | Status |
|---------------|-----|-----|--------------|--------|
| Login Flow | ⏳ | ⏳ | ⏳ | Not Tested |
| Auto-Login | ⏳ | ⏳ | ⏳ | Not Tested |
| Protected Routes | ⏳ | ⏳ | ⏳ | Not Tested |
| Navigation | ⏳ | ⏳ | ⏳ | Not Tested |
| Profile | ⏳ | ⏳ | ⏳ | Not Tested |
| Token Management | ⏳ | ⏳ | ⏳ | Not Tested |
| Logout | ⏳ | ⏳ | ⏳ | Not Tested |
| Error Handling | ⏳ | ⏳ | ⏳ | Not Tested |

Legend: ⏳ Not Tested | ✅ Passed | ❌ Failed

## Notes
- All tests require API server running on http://localhost:8001
- Frontend must be served on http://localhost:8080
- React Native tests require physical device or emulator
- Mock users are in src/auth/models.py
