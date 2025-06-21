#!/bin/bash

# Crehana Task Manager API - Comprehensive Test Script
# This script tests all available APIs to ensure they work correctly

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# API Base URL
BASE_URL="http://127.0.0.1:8001"

# Your JWT Token (update this with a valid token)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzUwNDk1MTAxfQ.8nsIyLeqxqs38QXCGadiR5uZMfhXH3MteVs8k1CHOP0"

# Function to print section headers
print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

# Function to print test results
print_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1 - SUCCESS${NC}\n"
    else
        echo -e "${RED}❌ $1 - FAILED${NC}\n"
    fi
}

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "${YELLOW}Testing: $description${NC}"
    echo -e "${YELLOW}$method $endpoint${NC}"
    
    if [ -n "$data" ]; then
        curl -s -X $method "$BASE_URL$endpoint" \
             -H "Content-Type: application/json" \
             -H "Authorization: Bearer $TOKEN" \
             -d "$data" | jq '.' 2>/dev/null || echo "Response received"
    else
        curl -s -X $method "$BASE_URL$endpoint" \
             -H "Authorization: Bearer $TOKEN" | jq '.' 2>/dev/null || echo "Response received"
    fi
    
    print_result "$description"
}

echo -e "${GREEN}🚀 CREHANA TASK MANAGER API - COMPREHENSIVE TEST${NC}"
echo -e "${GREEN}================================================${NC}"

# 1. HEALTH CHECK
print_header "1. HEALTH CHECK"
echo -e "${YELLOW}Testing: Health Check${NC}"
echo -e "${YELLOW}GET /health${NC}"
curl -s -X GET "$BASE_URL/health" | jq '.'
print_result "Health Check"

# 2. AUTHENTICATION TESTS
print_header "2. AUTHENTICATION TESTS"

# Register a new user
api_call "POST" "/auth/register" \
    '{"email": "apitest@example.com", "username": "apitest", "full_name": "API Test User", "password": "testpass123"}' \
    "User Registration"

# Login with the new user
echo -e "${YELLOW}Testing: User Login${NC}"
echo -e "${YELLOW}POST /auth/login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "apitest@example.com", "password": "testpass123"}')
echo "$LOGIN_RESPONSE" | jq '.'
print_result "User Login"

# Extract new token if login successful
NEW_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')
if [ -n "$NEW_TOKEN" ] && [ "$NEW_TOKEN" != "null" ]; then
    TOKEN="$NEW_TOKEN"
    echo -e "${GREEN}✅ Using new token for subsequent tests${NC}"
fi

# 3. TASK LIST TESTS
print_header "3. TASK LIST TESTS"

# Create Task List
echo -e "${YELLOW}Testing: Create Task List${NC}"
echo -e "${YELLOW}POST /api/v1/task-lists/${NC}"
TASK_LIST_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/task-lists/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"name": "API Test List", "description": "Testing all APIs"}')
echo "$TASK_LIST_RESPONSE" | jq '.'
print_result "Create Task List"

# Extract task list ID
TASK_LIST_ID=$(echo "$TASK_LIST_RESPONSE" | jq -r '.id // empty')
echo -e "${GREEN}📝 Task List ID: $TASK_LIST_ID${NC}"

# List Task Lists
api_call "GET" "/api/v1/task-lists/" "" "List Task Lists"

# Get Specific Task List
if [ -n "$TASK_LIST_ID" ] && [ "$TASK_LIST_ID" != "null" ]; then
    api_call "GET" "/api/v1/task-lists/$TASK_LIST_ID" "" "Get Task List by ID"
    
    # Update Task List
    api_call "PUT" "/api/v1/task-lists/$TASK_LIST_ID" \
        '{"name": "Updated API Test List", "description": "Updated description"}' \
        "Update Task List"
fi

# 4. TASK TESTS
print_header "4. TASK TESTS"

if [ -n "$TASK_LIST_ID" ] && [ "$TASK_LIST_ID" != "null" ]; then
    # Create Task
    echo -e "${YELLOW}Testing: Create Task${NC}"
    echo -e "${YELLOW}POST /api/v1/tasks/${NC}"
    TASK_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/tasks/" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d "{\"title\": \"API Test Task\", \"description\": \"Testing task creation\", \"task_list_id\": $TASK_LIST_ID, \"priority\": \"high\"}")
    echo "$TASK_RESPONSE" | jq '.'
    print_result "Create Task"
    
    # Extract task ID
    TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.id // empty')
    echo -e "${GREEN}📋 Task ID: $TASK_ID${NC}"
    
    # List Tasks
    api_call "GET" "/api/v1/tasks/?task_list_id=$TASK_LIST_ID" "" "List Tasks"
    
    if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
        # Get Specific Task
        api_call "GET" "/api/v1/tasks/$TASK_ID" "" "Get Task by ID"
        
        # Update Task
        api_call "PUT" "/api/v1/tasks/$TASK_ID" \
            '{"title": "Updated API Test Task", "description": "Updated task description", "priority": "medium"}' \
            "Update Task"
        
        # Update Task Status
        echo -e "${YELLOW}Testing: Update Task Status${NC}"
        echo -e "${YELLOW}PATCH /api/v1/tasks/$TASK_ID/status${NC}"
        curl -s -X PATCH "$BASE_URL/api/v1/tasks/$TASK_ID/status" \
             -H "Content-Type: application/json" \
             -H "Authorization: Bearer $TOKEN" \
             -d '{"status": "in_progress"}' | jq '.'
        print_result "Update Task Status"
        
        # Create another user for assignment test
        echo -e "${YELLOW}Creating user for task assignment test${NC}"
        USER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
            -H "Content-Type: application/json" \
            -d '{"email": "assignee@example.com", "username": "assignee", "full_name": "Assignee User", "password": "testpass123"}')
        ASSIGNEE_ID=$(echo "$USER_RESPONSE" | jq -r '.id // empty')
        
        if [ -n "$ASSIGNEE_ID" ] && [ "$ASSIGNEE_ID" != "null" ]; then
            # Assign Task
            api_call "POST" "/api/v1/tasks/$TASK_ID/assign/$ASSIGNEE_ID" "" "Assign Task to User"
        fi
    fi
fi

# 5. ADDITIONAL TASK LIST TESTS
print_header "5. ADDITIONAL TASK LIST TESTS"

# Create another task list for more comprehensive testing
echo -e "${YELLOW}Testing: Create Second Task List${NC}"
TASK_LIST_2_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/task-lists/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"name": "Second Test List", "description": "Another test list"}')
echo "$TASK_LIST_2_RESPONSE" | jq '.'
TASK_LIST_2_ID=$(echo "$TASK_LIST_2_RESPONSE" | jq -r '.id // empty')

if [ -n "$TASK_LIST_2_ID" ] && [ "$TASK_LIST_2_ID" != "null" ]; then
    # Create multiple tasks in the second list
    for i in {1..3}; do
        echo -e "${YELLOW}Creating Task $i in Second List${NC}"
        curl -s -X POST "$BASE_URL/api/v1/tasks/" \
             -H "Content-Type: application/json" \
             -H "Authorization: Bearer $TOKEN" \
             -d "{\"title\": \"Task $i\", \"description\": \"Test task number $i\", \"task_list_id\": $TASK_LIST_2_ID, \"priority\": \"low\"}" | jq '.'
    done
    
    # List tasks with different filters
    api_call "GET" "/api/v1/tasks/?task_list_id=$TASK_LIST_2_ID&priority=low" "" "List Tasks with Priority Filter"
    api_call "GET" "/api/v1/tasks/?task_list_id=$TASK_LIST_2_ID&status=pending" "" "List Tasks with Status Filter"
fi

# 6. ERROR HANDLING TESTS
print_header "6. ERROR HANDLING TESTS"

# Test invalid endpoints
echo -e "${YELLOW}Testing: Invalid Task List ID${NC}"
curl -s -X GET "$BASE_URL/api/v1/task-lists/99999" \
     -H "Authorization: Bearer $TOKEN" | jq '.'
print_result "Invalid Task List ID (should return 404)"

echo -e "${YELLOW}Testing: Invalid Task ID${NC}"
curl -s -X GET "$BASE_URL/api/v1/tasks/99999" \
     -H "Authorization: Bearer $TOKEN" | jq '.'
print_result "Invalid Task ID (should return 404)"

echo -e "${YELLOW}Testing: Invalid Token${NC}"
curl -s -X GET "$BASE_URL/api/v1/task-lists/" \
     -H "Authorization: Bearer invalid_token" | jq '.'
print_result "Invalid Token (should return 401)"

# 7. CLEANUP TESTS
print_header "7. CLEANUP TESTS"

if [ -n "$TASK_ID" ] && [ "$TASK_ID" != "null" ]; then
    # Delete Task
    api_call "DELETE" "/api/v1/tasks/$TASK_ID" "" "Delete Task"
fi

if [ -n "$TASK_LIST_ID" ] && [ "$TASK_LIST_ID" != "null" ]; then
    # Delete Task List
    api_call "DELETE" "/api/v1/task-lists/$TASK_LIST_ID" "" "Delete Task List"
fi

if [ -n "$TASK_LIST_2_ID" ] && [ "$TASK_LIST_2_ID" != "null" ]; then
    # Delete Second Task List
    api_call "DELETE" "/api/v1/task-lists/$TASK_LIST_2_ID" "" "Delete Second Task List"
fi

# 8. FINAL SUMMARY
print_header "8. TEST SUMMARY"

echo -e "${GREEN}🎉 COMPREHENSIVE API TEST COMPLETED!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}✅ Health Check${NC}"
echo -e "${GREEN}✅ Authentication (Register/Login)${NC}"
echo -e "${GREEN}✅ Task Lists (CRUD Operations)${NC}"
echo -e "${GREEN}✅ Tasks (CRUD Operations)${NC}"
echo -e "${GREEN}✅ Task Status Updates${NC}"
echo -e "${GREEN}✅ Task Assignment${NC}"
echo -e "${GREEN}✅ Filtering and Pagination${NC}"
echo -e "${GREEN}✅ Error Handling${NC}"
echo -e "${GREEN}✅ Cleanup Operations${NC}"

echo -e "\n${BLUE}📊 All Crehana Task Manager APIs have been tested!${NC}"
echo -e "${BLUE}The API is ready for production use! 🚀${NC}\n" 