#!/bin/bash
# Script para probar el API localmente

set -e

API_URL="http://localhost:8000"
TOKEN=""

echo "🧪 Health Check Panel - Test Suite"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Health Check
echo -e "${BLUE}1. Testing Health Check...${NC}"
curl -s $API_URL/health | jq
echo ""

# 2. Register User
echo -e "${BLUE}2. Registering new user...${NC}"
REGISTER_RESPONSE=$(curl -s -X POST $API_URL/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User",
    "organization_name": "Test Organization"
  }')

echo "$REGISTER_RESPONSE" | jq
USER_ID=$(echo "$REGISTER_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ User created with ID: $USER_ID${NC}"
echo ""

# 3. Login
echo -e "${BLUE}3. Logging in...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123")

echo "$LOGIN_RESPONSE" | jq
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
echo -e "${GREEN}✓ Access token obtained${NC}"
echo ""

# 4. Get Current User
echo -e "${BLUE}4. Getting current user info...${NC}"
curl -s $API_URL/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq
echo ""

# 5. List Available Check Types
echo -e "${BLUE}5. Listing available check types...${NC}"
curl -s $API_URL/api/v1/checks/types \
  -H "Authorization: Bearer $TOKEN" | jq
echo ""

# 6. Create a Site
echo -e "${BLUE}6. Creating a site (Google)...${NC}"
SITE_RESPONSE=$(curl -s -X POST $API_URL/api/v1/sites \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Google",
    "url": "https://google.com",
    "description": "Google search engine"
  }')

echo "$SITE_RESPONSE" | jq
SITE_ID=$(echo "$SITE_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Site created with ID: $SITE_ID${NC}"
echo ""

# 7. Create HTTP Check
echo -e "${BLUE}7. Creating HTTP check for Google...${NC}"
CHECK_RESPONSE=$(curl -s -X POST $API_URL/api/v1/checks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"site_id\": $SITE_ID,
    \"check_type\": \"http\",
    \"name\": \"Homepage Status Check\",
    \"interval_seconds\": 60,
    \"configuration\": {
      \"expected_status_code\": 200,
      \"timeout_seconds\": 10,
      \"follow_redirects\": true,
      \"verify_ssl\": true,
      \"max_response_time_ms\": 3000
    }
  }")

echo "$CHECK_RESPONSE" | jq
CHECK_ID=$(echo "$CHECK_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ Check created with ID: $CHECK_ID${NC}"
echo ""

# 8. Create DNS Check
echo -e "${BLUE}8. Creating DNS check for Google...${NC}"
DNS_CHECK_RESPONSE=$(curl -s -X POST $API_URL/api/v1/checks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"site_id\": $SITE_ID,
    \"check_type\": \"dns\",
    \"name\": \"DNS A Record Check\",
    \"interval_seconds\": 300,
    \"configuration\": {
      \"record_type\": \"A\",
      \"timeout_seconds\": 5
    }
  }")

echo "$DNS_CHECK_RESPONSE" | jq
DNS_CHECK_ID=$(echo "$DNS_CHECK_RESPONSE" | jq -r '.id')
echo -e "${GREEN}✓ DNS Check created with ID: $DNS_CHECK_ID${NC}"
echo ""

# 9. List All Checks
echo -e "${BLUE}9. Listing all checks...${NC}"
curl -s "$API_URL/api/v1/checks?site_id=$SITE_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
echo ""

# 10. Manually trigger check
echo -e "${BLUE}10. Manually triggering HTTP check...${NC}"
curl -s -X POST $API_URL/api/v1/checks/$CHECK_ID/run-now \
  -H "Authorization: Bearer $TOKEN" | jq
echo -e "${YELLOW}Waiting 3 seconds for check to complete...${NC}"
sleep 3
echo ""

# 11. Get Check Results
echo -e "${BLUE}11. Getting check results...${NC}"
curl -s "$API_URL/api/v1/checks/$CHECK_ID/results?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq
echo ""

# 12. List Sites
echo -e "${BLUE}12. Listing all sites...${NC}"
curl -s $API_URL/api/v1/sites \
  -H "Authorization: Bearer $TOKEN" | jq
echo ""

echo -e "${GREEN}=================================="
echo "✅ All tests completed!"
echo "==================================${NC}"
echo ""
echo "📊 Summary:"
echo "  - User ID: $USER_ID"
echo "  - Site ID: $SITE_ID"
echo "  - HTTP Check ID: $CHECK_ID"
echo "  - DNS Check ID: $DNS_CHECK_ID"
echo "  - Access Token: $TOKEN"
echo ""
echo "🔄 To test real-time updates (SSE), run in another terminal:"
echo "  curl -N $API_URL/api/v1/stream/updates -H \"Authorization: Bearer $TOKEN\""
echo ""
echo "📖 API Documentation: http://localhost:8000/api/docs"
