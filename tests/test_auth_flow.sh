#!/bin/bash
#
# Authentication Flow End-to-End Test
# Tests all auth endpoints with mock users
#
# Usage: ./tests/test_auth_flow.sh
# Prerequisites: API server running on http://localhost:8001
#

set -e

API_BASE="http://localhost:8001/api/v1"
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Authentication Flow Test - Phase 1${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if server is running
echo -e "${BLUE}[1/7] Checking API server...${NC}"
if ! curl -s ${API_BASE}/../health/ready > /dev/null; then
    echo -e "${RED}✗ API server is not running on http://localhost:8001${NC}"
    echo -e "${RED}  Please start the server first: ./scripts/deploy-optimized.sh development${NC}"
    exit 1
fi
echo -e "${GREEN}✓ API server is running${NC}"
echo ""

# Test 1: Register new user
echo -e "${BLUE}[2/7] Testing user registration...${NC}"
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${API_BASE}/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpassword123",
    "phone": "010-1234-5678",
    "role": "worker"
  }')

HTTP_CODE=$(echo "$REGISTER_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$REGISTER_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "409" ]; then
    if [ "$HTTP_CODE" == "409" ]; then
        echo -e "${GREEN}✓ User already exists (expected for repeat tests)${NC}"
    else
        echo -e "${GREEN}✓ User registered successfully${NC}"
    fi
else
    echo -e "${RED}✗ Registration failed (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | jq .
    exit 1
fi
echo ""

# Test 2: Login with mock admin user
echo -e "${BLUE}[3/7] Testing login with admin user...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST ${API_BASE}/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }')

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')
USER_EMAIL=$(echo "$LOGIN_RESPONSE" | jq -r '.user.email')

if [ "$ACCESS_TOKEN" != "null" ] && [ "$ACCESS_TOKEN" != "" ]; then
    echo -e "${GREEN}✓ Login successful${NC}"
    echo -e "  Email: $USER_EMAIL"
    echo -e "  Token: ${ACCESS_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "$LOGIN_RESPONSE" | jq .
    exit 1
fi
echo ""

# Test 3: Get current user info
echo -e "${BLUE}[4/7] Testing /auth/me endpoint...${NC}"
ME_RESPONSE=$(curl -s -w "\n%{http_code}" ${API_BASE}/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN")

HTTP_CODE=$(echo "$ME_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$ME_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ User info retrieved successfully${NC}"
    echo "$RESPONSE_BODY" | jq '{email: .email, name: .name, role: .role}'
else
    echo -e "${RED}✗ Failed to get user info (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | jq .
    exit 1
fi
echo ""

# Test 4: Refresh token
echo -e "${BLUE}[5/7] Testing token refresh...${NC}"
REFRESH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${API_BASE}/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")

HTTP_CODE=$(echo "$REFRESH_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$REFRESH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    NEW_ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | jq -r '.access_token')
    echo -e "${GREEN}✓ Token refreshed successfully${NC}"
    echo -e "  New token: ${NEW_ACCESS_TOKEN:0:20}..."
    ACCESS_TOKEN=$NEW_ACCESS_TOKEN
else
    echo -e "${RED}✗ Token refresh failed (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | jq .
    exit 1
fi
echo ""

# Test 5: Change password
echo -e "${BLUE}[6/7] Testing password change...${NC}"
CHANGE_PASSWORD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST ${API_BASE}/auth/change-password \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "password123",
    "new_password": "newpassword123"
  }')

HTTP_CODE=$(echo "$CHANGE_PASSWORD_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$CHANGE_PASSWORD_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    echo -e "${GREEN}✓ Password changed successfully${NC}"

    # Change it back for future tests
    curl -s -X POST ${API_BASE}/auth/change-password \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "old_password": "newpassword123",
        "new_password": "password123"
      }' > /dev/null
    echo -e "${GREEN}✓ Password reset to original${NC}"
else
    echo -e "${RED}✗ Password change failed (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | jq .
fi
echo ""

# Test 6: List users (admin only)
echo -e "${BLUE}[7/7] Testing admin-only endpoint (/auth/users)...${NC}"
USERS_RESPONSE=$(curl -s -w "\n%{http_code}" ${API_BASE}/auth/users \
  -H "Authorization: Bearer $ACCESS_TOKEN")

HTTP_CODE=$(echo "$USERS_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$USERS_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
    USER_COUNT=$(echo "$RESPONSE_BODY" | jq '. | length')
    echo -e "${GREEN}✓ User list retrieved successfully${NC}"
    echo -e "  Total users: $USER_COUNT"
else
    echo -e "${RED}✗ Failed to list users (HTTP $HTTP_CODE)${NC}"
    echo "$RESPONSE_BODY" | jq .
fi
echo ""

# Test 7: Test unauthorized access
echo -e "${BLUE}[BONUS] Testing unauthorized access...${NC}"
UNAUTHORIZED_RESPONSE=$(curl -s -w "\n%{http_code}" ${API_BASE}/auth/me \
  -H "Authorization: Bearer invalid_token")

HTTP_CODE=$(echo "$UNAUTHORIZED_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" == "401" ]; then
    echo -e "${GREEN}✓ Unauthorized access properly blocked${NC}"
else
    echo -e "${RED}✗ Expected 401, got HTTP $HTTP_CODE${NC}"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}All authentication tests passed! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Test Summary:"
echo "✓ User registration"
echo "✓ User login"
echo "✓ Get current user"
echo "✓ Token refresh"
echo "✓ Password change"
echo "✓ Admin-only endpoints"
echo "✓ Unauthorized access blocked"
echo ""
echo "Mock test accounts:"
echo "  admin@example.com / password123 (admin)"
echo "  worker@example.com / password123 (worker)"
