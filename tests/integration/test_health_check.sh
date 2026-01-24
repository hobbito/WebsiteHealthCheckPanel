#!/bin/bash

# Test Health Check End-to-End
set -e

echo "🧪 Testing Health Check System"
echo "================================"
echo ""

API_URL="http://localhost:8000/api/v1"
TOKEN=""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}1. Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@admin.com&password=adminadmin")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed"
  echo $LOGIN_RESPONSE | jq
  exit 1
fi

echo -e "${GREEN}✓ Logged in${NC}"
echo ""

echo -e "${BLUE}2. Create Site${NC}"
SITE_RESPONSE=$(curl -s -X POST "$API_URL/sites/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Google Test",
    "url": "https://google.com",
    "description": "Test site for health check",
    "is_active": true
  }')

SITE_ID=$(echo $SITE_RESPONSE | jq -r '.id')

if [ "$SITE_ID" == "null" ] || [ -z "$SITE_ID" ]; then
  echo "❌ Site creation failed"
  echo $SITE_RESPONSE | jq
  exit 1
fi

echo -e "${GREEN}✓ Site created (ID: $SITE_ID)${NC}"
echo ""

echo -e "${BLUE}3. List available check types${NC}"
CHECK_TYPES=$(curl -s -X GET "$API_URL/checks/types" \
  -H "Authorization: Bearer $TOKEN")

echo $CHECK_TYPES | jq
echo ""

echo -e "${BLUE}4. Create HTTP Check${NC}"
CHECK_RESPONSE=$(curl -s -X POST "$API_URL/checks/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"site_id\": $SITE_ID,
    \"check_type\": \"http\",
    \"name\": \"Google Homepage Check\",
    \"configuration\": {
      \"expected_status_code\": 200,
      \"timeout_seconds\": 10,
      \"follow_redirects\": true
    },
    \"interval_seconds\": 60,
    \"is_enabled\": true
  }")

CHECK_ID=$(echo $CHECK_RESPONSE | jq -r '.id')

if [ "$CHECK_ID" == "null" ] || [ -z "$CHECK_ID" ]; then
  echo "❌ Check creation failed"
  echo $CHECK_RESPONSE | jq
  exit 1
fi

echo -e "${GREEN}✓ Check created (ID: $CHECK_ID)${NC}"
echo ""

echo -e "${BLUE}5. Run check manually${NC}"
RUN_RESPONSE=$(curl -s -X POST "$API_URL/checks/$CHECK_ID/run-now" \
  -H "Authorization: Bearer $TOKEN")

echo $RUN_RESPONSE | jq
echo ""

echo -e "${BLUE}6. Wait 3 seconds for check to complete...${NC}"
sleep 3
echo ""

echo -e "${BLUE}7. Get check results${NC}"
RESULTS=$(curl -s -X GET "$API_URL/checks/$CHECK_ID/results?limit=5" \
  -H "Authorization: Bearer $TOKEN")

echo $RESULTS | jq
echo ""

RESULT_COUNT=$(echo $RESULTS | jq 'length')

if [ "$RESULT_COUNT" -gt 0 ]; then
  LATEST_STATUS=$(echo $RESULTS | jq -r '.[0].status')
  LATEST_RESPONSE_TIME=$(echo $RESULTS | jq -r '.[0].response_time_ms')

  echo -e "${GREEN}✅ Health Check Working!${NC}"
  echo -e "  Status: ${YELLOW}$LATEST_STATUS${NC}"
  echo -e "  Response Time: ${YELLOW}${LATEST_RESPONSE_TIME}ms${NC}"
  echo ""
else
  echo -e "${YELLOW}⚠️  No results yet (check might still be running)${NC}"
  echo ""
fi

echo -e "${BLUE}8. Get all checks for site${NC}"
ALL_CHECKS=$(curl -s -X GET "$API_URL/checks/?site_id=$SITE_ID" \
  -H "Authorization: Bearer $TOKEN")

echo $ALL_CHECKS | jq
echo ""

echo "================================"
echo -e "${GREEN}✅ Test completed!${NC}"
echo ""
echo "Site ID: $SITE_ID"
echo "Check ID: $CHECK_ID"
echo ""
echo "View in UI: http://localhost:3000/dashboard/sites/$SITE_ID"
