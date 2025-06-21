"""
Integration tests for the Task Manager API.
Tests the complete API functionality end-to-end.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from src.main import app
from src.infrastructure.database import get_db_session


class TestAPIIntegration:
    """Integration tests for the complete API."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest_asyncio.fixture
    async def async_client(self, db_session):
        """Create async test client with test database."""
        
        async def override_get_db():
            yield db_session
        
        app.dependency_overrides[get_db_session] = override_get_db
        
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
        
        app.dependency_overrides.clear()

    @pytest_asyncio.fixture
    async def test_user_data(self):
        """Test user data for registration."""
        return {
            "email": "integration@example.com",
            "username": "integration_user",
            "full_name": "Integration Test User",
            "password": "integration123"
        }

    @pytest_asyncio.fixture
    async def authenticated_user(self, async_client, test_user_data):
        """Create and authenticate a test user."""
        # Register user
        register_response = await async_client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        
        # Login user
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await async_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        user_data = register_response.json()
        
        return {
            "user": user_data,
            "token": token_data["access_token"],
            "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
        }

    async def test_health_check(self, async_client):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    async def test_user_registration_flow(self, async_client):
        """Test complete user registration flow."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "newpassword123"
        }
        
        # Register user
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["email"] == user_data["email"]
        assert response_data["username"] == user_data["username"]
        assert response_data["full_name"] == user_data["full_name"]
        assert response_data["is_active"] is True
        assert "id" in response_data

    async def test_user_authentication_flow(self, async_client, test_user_data):
        """Test complete authentication flow."""
        # First register user
        register_response = await async_client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        
        # Then login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await async_client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["expires_in"] > 0

    async def test_duplicate_user_registration(self, async_client, test_user_data):
        """Test duplicate user registration prevention."""
        # Register user first time
        response1 = await async_client.post("/auth/register", json=test_user_data)
        assert response1.status_code == 200
        
        # Try to register same user again
        response2 = await async_client.post("/auth/register", json=test_user_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    async def test_invalid_login(self, async_client, test_user_data):
        """Test login with invalid credentials."""
        # Register user first
        await async_client.post("/auth/register", json=test_user_data)
        
        # Try login with wrong password
        wrong_login = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = await async_client.post("/auth/login", json=wrong_login)
        assert response.status_code == 401

    async def test_task_list_crud_flow(self, async_client, authenticated_user):
        """Test complete CRUD flow for task lists."""
        headers = authenticated_user["headers"]
        
        # Create task list
        task_list_data = {
            "name": "Integration Test List",
            "description": "Testing task list CRUD"
        }
        create_response = await async_client.post(
            "/api/v1/task-lists/", 
            json=task_list_data, 
            headers=headers
        )
        assert create_response.status_code == 200
        
        created_list = create_response.json()
        assert created_list["name"] == task_list_data["name"]
        assert created_list["description"] == task_list_data["description"]
        assert "id" in created_list
        
        task_list_id = created_list["id"]
        
        # Get task list
        get_response = await async_client.get(
            f"/api/v1/task-lists/{task_list_id}", 
            headers=headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["id"] == task_list_id
        
        # List task lists
        list_response = await async_client.get("/api/v1/task-lists/", headers=headers)
        assert list_response.status_code == 200
        task_lists = list_response.json()
        assert len(task_lists) >= 1
        assert any(tl["id"] == task_list_id for tl in task_lists)
        
        # Update task list
        update_data = {
            "name": "Updated Integration Test List",
            "description": "Updated description"
        }
        update_response = await async_client.put(
            f"/api/v1/task-lists/{task_list_id}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        
        updated_list = update_response.json()
        assert updated_list["name"] == update_data["name"]
        assert updated_list["description"] == update_data["description"]
        
        # Delete task list
        delete_response = await async_client.delete(
            f"/api/v1/task-lists/{task_list_id}",
            headers=headers
        )
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted_response = await async_client.get(
            f"/api/v1/task-lists/{task_list_id}",
            headers=headers
        )
        assert get_deleted_response.status_code == 404

    async def test_task_crud_flow(self, async_client, authenticated_user):
        """Test complete CRUD flow for tasks."""
        headers = authenticated_user["headers"]
        
        # First create a task list
        task_list_data = {
            "name": "Task Test List",
            "description": "For testing tasks"
        }
        list_response = await async_client.post(
            "/api/v1/task-lists/",
            json=task_list_data,
            headers=headers
        )
        assert list_response.status_code == 200
        task_list_id = list_response.json()["id"]
        
        # Create task
        task_data = {
            "title": "Integration Test Task",
            "description": "Testing task CRUD",
            "priority": "high",
            "task_list_id": task_list_id
        }
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=headers
        )
        assert create_response.status_code == 200
        
        created_task = create_response.json()
        assert created_task["title"] == task_data["title"]
        assert created_task["description"] == task_data["description"]
        assert created_task["priority"] == task_data["priority"]
        assert created_task["status"] == "pending"
        
        task_id = created_task["id"]
        
        # Get task
        get_response = await async_client.get(f"/api/v1/tasks/{task_id}", headers=headers)
        assert get_response.status_code == 200
        assert get_response.json()["id"] == task_id
        
        # Update task
        update_data = {
            "title": "Updated Integration Test Task",
            "description": "Updated description",
            "priority": "medium"
        }
        update_response = await async_client.put(
            f"/api/v1/tasks/{task_id}",
            json=update_data,
            headers=headers
        )
        assert update_response.status_code == 200
        
        updated_task = update_response.json()
        assert updated_task["title"] == update_data["title"]
        assert updated_task["description"] == update_data["description"]
        assert updated_task["priority"] == update_data["priority"]
        
        # Update task status
        status_data = {"status": "in_progress"}
        status_response = await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json=status_data,
            headers=headers
        )
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "in_progress"
        
        # List tasks
        list_response = await async_client.get(
            f"/api/v1/tasks/?task_list_id={task_list_id}",
            headers=headers
        )
        assert list_response.status_code == 200
        tasks = list_response.json()
        assert len(tasks) >= 1
        assert any(t["id"] == task_id for t in tasks)
        
        # Delete task
        delete_response = await async_client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted_response = await async_client.get(f"/api/v1/tasks/{task_id}", headers=headers)
        assert get_deleted_response.status_code == 404

    async def test_task_filtering(self, async_client, authenticated_user):
        """Test task filtering functionality."""
        headers = authenticated_user["headers"]
        
        # Create task list
        task_list_data = {"name": "Filter Test List", "description": "For testing filters"}
        list_response = await async_client.post("/api/v1/task-lists/", json=task_list_data, headers=headers)
        task_list_id = list_response.json()["id"]
        
        # Create tasks with different statuses and priorities
        tasks_data = [
            {"title": "High Priority Task", "priority": "high", "task_list_id": task_list_id},
            {"title": "Medium Priority Task", "priority": "medium", "task_list_id": task_list_id},
            {"title": "Low Priority Task", "priority": "low", "task_list_id": task_list_id}
        ]
        
        created_tasks = []
        for task_data in tasks_data:
            response = await async_client.post("/api/v1/tasks/", json=task_data, headers=headers)
            created_tasks.append(response.json())
        
        # Update one task to in_progress
        await async_client.patch(
            f"/api/v1/tasks/{created_tasks[0]['id']}/status",
            json={"status": "in_progress"},
            headers=headers
        )
        
        # Test filter by priority
        high_priority_response = await async_client.get(
            f"/api/v1/tasks/?task_list_id={task_list_id}&priority=high",
            headers=headers
        )
        assert high_priority_response.status_code == 200
        high_priority_tasks = high_priority_response.json()
        assert len(high_priority_tasks) == 1
        assert high_priority_tasks[0]["priority"] == "high"
        
        # Test filter by status
        in_progress_response = await async_client.get(
            f"/api/v1/tasks/?task_list_id={task_list_id}&status=in_progress",
            headers=headers
        )
        assert in_progress_response.status_code == 200
        in_progress_tasks = in_progress_response.json()
        assert len(in_progress_tasks) == 1
        assert in_progress_tasks[0]["status"] == "in_progress"

    async def test_task_assignment_flow(self, async_client, authenticated_user):
        """Test task assignment functionality."""
        headers = authenticated_user["headers"]
        
        # Create another user for assignment
        assignee_data = {
            "email": "assignee@example.com",
            "username": "assignee",
            "full_name": "Assignee User",
            "password": "assignee123"
        }
        assignee_response = await async_client.post("/auth/register", json=assignee_data)
        assignee_id = assignee_response.json()["id"]
        
        # Create task list and task
        task_list_data = {"name": "Assignment Test List", "description": "For testing assignments"}
        list_response = await async_client.post("/api/v1/task-lists/", json=task_list_data, headers=headers)
        task_list_id = list_response.json()["id"]
        
        task_data = {
            "title": "Assignment Test Task",
            "description": "Task to be assigned",
            "task_list_id": task_list_id,
            "assigned_to": assignee_id
        }
        task_response = await async_client.post("/api/v1/tasks/", json=task_data, headers=headers)
        assert task_response.status_code == 200
        
        created_task = task_response.json()
        assert created_task["assigned_to"] == assignee_id
        
        # Test assignment endpoint
        task_id = created_task["id"]
        assign_response = await async_client.post(
            f"/api/v1/tasks/{task_id}/assign/{assignee_id}",
            headers=headers
        )
        assert assign_response.status_code == 200

    async def test_unauthorized_access(self, async_client):
        """Test that protected endpoints require authentication."""
        # Test without token
        response = await async_client.get("/api/v1/task-lists/")
        assert response.status_code == 401
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = await async_client.get("/api/v1/task-lists/", headers=invalid_headers)
        assert response.status_code == 401

    async def test_task_list_completion_percentage(self, async_client, authenticated_user):
        """Test task list completion percentage calculation."""
        headers = authenticated_user["headers"]
        
        # Create task list
        task_list_data = {"name": "Completion Test List", "description": "For testing completion"}
        list_response = await async_client.post("/api/v1/task-lists/", json=task_list_data, headers=headers)
        task_list_id = list_response.json()["id"]
        
        # Create multiple tasks
        for i in range(3):
            task_data = {
                "title": f"Task {i+1}",
                "description": f"Task number {i+1}",
                "task_list_id": task_list_id
            }
            await async_client.post("/api/v1/tasks/", json=task_data, headers=headers)
        
        # Get task list to check initial completion (should be 0%)
        list_response = await async_client.get(f"/api/v1/task-lists/{task_list_id}", headers=headers)
        task_list = list_response.json()
        assert task_list["completion_percentage"] == 0.0
        
        # Get tasks and complete one
        tasks_response = await async_client.get(f"/api/v1/tasks/?task_list_id={task_list_id}", headers=headers)
        tasks = tasks_response.json()
        
        # Complete first task
        await async_client.patch(
            f"/api/v1/tasks/{tasks[0]['id']}/status",
            json={"status": "completed"},
            headers=headers
        )
        
        # Check completion percentage (should be ~33%)
        list_response = await async_client.get(f"/api/v1/task-lists/{task_list_id}", headers=headers)
        task_list = list_response.json()
        assert 30.0 <= task_list["completion_percentage"] <= 35.0  # Allow some tolerance

    async def test_error_handling(self, async_client, authenticated_user):
        """Test API error handling."""
        headers = authenticated_user["headers"]
        
        # Test 404 for non-existent task list
        response = await async_client.get("/api/v1/task-lists/99999", headers=headers)
        assert response.status_code == 404
        
        # Test 404 for non-existent task
        response = await async_client.get("/api/v1/tasks/99999", headers=headers)
        assert response.status_code == 404
        
        # Test validation error for invalid task data
        invalid_task_data = {
            "title": "",  # Empty title should fail validation
            "task_list_id": 1
        }
        response = await async_client.post("/api/v1/tasks/", json=invalid_task_data, headers=headers)
        assert response.status_code == 422

    async def test_complete_workflow(self, async_client):
        """Test complete workflow from user registration to task completion."""
        # 1. Register user
        user_data = {
            "email": "workflow@example.com",
            "username": "workflow_user",
            "full_name": "Workflow Test User",
            "password": "workflow123"
        }
        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # 2. Login
        login_response = await async_client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create task list
        task_list_response = await async_client.post("/api/v1/task-lists/", json={
            "name": "Workflow Task List",
            "description": "Complete workflow test"
        }, headers=headers)
        task_list_id = task_list_response.json()["id"]
        
        # 4. Create task
        task_response = await async_client.post("/api/v1/tasks/", json={
            "title": "Workflow Task",
            "description": "Complete workflow test task",
            "priority": "high",
            "task_list_id": task_list_id
        }, headers=headers)
        task_id = task_response.json()["id"]
        
        # 5. Update task status through workflow
        await async_client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "in_progress"}, headers=headers)
        await async_client.patch(f"/api/v1/tasks/{task_id}/status", json={"status": "completed"}, headers=headers)
        
        # 6. Verify final state
        final_task_response = await async_client.get(f"/api/v1/tasks/{task_id}", headers=headers)
        final_task = final_task_response.json()
        assert final_task["status"] == "completed"
        
        # 7. Verify task list completion
        final_list_response = await async_client.get(f"/api/v1/task-lists/{task_list_id}", headers=headers)
        final_list = final_list_response.json()
        assert final_list["completion_percentage"] == 100.0 