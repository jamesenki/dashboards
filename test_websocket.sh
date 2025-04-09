#!/bin/bash
# WebSocket authentication testing script

# Mock token for testing
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTAwMSIsInVzZXJuYW1lIjoidGVzdF91c2VyIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ0MDYwMDAwfQ.thisIsATestToken"

# Color for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing WebSocket endpoints with token authentication${NC}"
echo -e "${BLUE}=============================================${NC}"
echo

# Install wscat if not already present
if ! command -v wscat &> /dev/null; then
    echo -e "${RED}wscat not found, attempting to install it...${NC}"
    npm install -g wscat
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install wscat. Please install it manually with: npm install -g wscat${NC}"
        exit 1
    fi
fi

# Function to test WebSocket endpoint
test_endpoint() {
    local endpoint=$1
    local url="ws://localhost:8000${endpoint}?token=${TOKEN}"

    echo -e "${BLUE}Testing: ${endpoint}${NC}"
    echo -e "URL: ${url}"
    echo

    # Try connecting to the WebSocket endpoint with a timeout
    timeout 5s wscat -c "${url}" --no-color 2>&1 | tee /tmp/wscat_output.txt

    # Check if it was successful
    if grep -q "connected" /tmp/wscat_output.txt; then
        echo -e "${GREEN}✅ Connection succeeded!${NC}"
        return 0
    else
        echo -e "${RED}❌ Connection failed!${NC}"
        return 1
    fi
}

# Test various endpoints
endpoints=(
    "/ws/debug"
    "/ws/devices/wh-d94a7707/state"
    "/ws/devices/wh-d94a7707/telemetry"
    "/ws/devices/wh-d94a7707/alerts"
    "/ws/broadcast"
)

# Track successes and failures
successes=0
failures=0

# Test each endpoint
for endpoint in "${endpoints[@]}"; do
    echo -e "\n${BLUE}=============================================${NC}"
    test_endpoint "$endpoint"
    if [ $? -eq 0 ]; then
        ((successes++))
    else
        ((failures++))
    fi
    echo -e "${BLUE}=============================================${NC}\n"
done

# Print summary
echo -e "${BLUE}Test Summary:${NC}"
echo -e "${GREEN}Successes: ${successes}${NC}"
echo -e "${RED}Failures: ${failures}${NC}"

if [ $failures -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
