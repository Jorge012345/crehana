"""
Integration tests for task and task list functionality.
Tests complete CRUD operations, filtering, and business logic.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta

from src.main import app
from src.infrastructure.database import get_db_session


class TestTaskIntegration:
    """Integration tests for task management functionality."""

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
    async def authenticated_user(self, async_client):
        """Create and authenticate a test user."""
        user_data = {
            "email": "tasktest@example.com",
            "username": "taskuser",
            "full_name": "Task Test User",
            "password": "taskpassword123"
        }
        
        # Register user
        register_response = await async_client.post("/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login user
        login_response = await async_client.post("/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        user_data_response = register_response.json()
        
        return {
            "user": user_data_response,
            "token": token_data["access_token"],
            "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
        }

    @pytest_asyncio.fixture
    async def sample_task_list(self, async_client, authenticated_user):
        """Create a sample task list for testing."""
        headers = authenticated_user["headers"]
        
        task_list_data = {
            "name": "Sample Task List",
            "description": "A sample task list for testing"
        }
        
        response = await async_client.post(
            "/api/v1/task-lists/",
            json=task_list_data,
            headers=headers
        )
        assert response.status_code == 200
        
        return response.json()

    async def test_task_list_creation(self, async_client, authenticated_user):
        """Test task list creation with various scenarios."""
        headers = authenticated_user["headers"]
        
        # Test basic creation
        task_list_data = {
            "name": "Test Task List",
            "description": "Testing task list creation"
        }
        
        response = await async_client.post(
            "/api/v1/task-lists/",
            json=task_list_data,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["name"] == task_list_data["name"]
        assert response_data["description"] == task_list_data["description"]
        assert response_data["owner_id"] == authenticated_user["user"]["id"]
        assert response_data["completion_percentage"] == 0.0
        assert "id" in response_data
        assert "created_at" in response_data

    async def test_task_list_creation_validation(self, async_client, authenticated_user):
        """Test task list creation validation."""
        headers = authenticated_user["headers"]
        
        # Test empty name
        response = await async_client.post(
            "/api/v1/task-lists/",
            json={"name": "", "description": "Test"},
            headers=headers
        )
        assert response.status_code == 422
        
        # Test missing name
        response = await async_client.post(
            "/api/v1/task-lists/",
            json={"description": "Test"},
            headers=headers
        )
        assert response.status_code == 422

    async def test_task_list_retrieval(self, async_client, authenticated_user, sample_task_list):
        """Test task list retrieval."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Get specific task list
        response = await async_client.get(
            f"/api/v1/task-lists/{task_list_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["id"] == task_list_id
        assert response_data["name"] == sample_task_list["name"]
        assert response_data["description"] == sample_task_list["description"]

    async def test_task_list_listing(self, async_client, authenticated_user):
        """Test task list listing."""
        headers = authenticated_user["headers"]
        
        # Create multiple task lists
        task_lists = []
        for i in range(3):
            task_list_data = {
                "name": f"Test List {i+1}",
                "description": f"Description {i+1}"
            }
            response = await async_client.post(
                "/api/v1/task-lists/",
                json=task_list_data,
                headers=headers
            )
            task_lists.append(response.json())
        
        # List all task lists
        response = await async_client.get("/api/v1/task-lists/", headers=headers)
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert len(response_data) >= 3
        created_ids = {tl["id"] for tl in task_lists}
        response_ids = {tl["id"] for tl in response_data}
        assert created_ids.issubset(response_ids)

    async def test_task_list_update(self, async_client, authenticated_user, sample_task_list):
        """Test task list update."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        update_data = {
            "name": "Updated Task List Name",
            "description": "Updated description"
        }
        
        response = await async_client.put(
            f"/api/v1/task-lists/{task_list_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["name"] == update_data["name"]
        assert response_data["description"] == update_data["description"]
        assert response_data["id"] == task_list_id

    async def test_task_list_deletion(self, async_client, authenticated_user, sample_task_list):
        """Test task list deletion."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Delete task list
        response = await async_client.delete(
            f"/api/v1/task-lists/{task_list_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Verify deletion
        response = await async_client.get(
            f"/api/v1/task-lists/{task_list_id}",
            headers=headers
        )
        assert response.status_code == 404

    async def test_task_creation(self, async_client, authenticated_user, sample_task_list):
        """Test task creation."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        task_data = {
            "title": "Test Task",
            "description": "Testing task creation",
            "priority": "high",
            "task_list_id": task_list_id
        }
        
        response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["title"] == task_data["title"]
        assert response_data["description"] == task_data["description"]
        assert response_data["priority"] == task_data["priority"]
        assert response_data["task_list_id"] == task_list_id
        assert response_data["status"] == "pending"
        assert "id" in response_data
        assert "created_at" in response_data

    async def test_task_creation_with_assignment(self, async_client, authenticated_user, sample_task_list):
        """Test task creation with user assignment."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        user_id = authenticated_user["user"]["id"]
        
        task_data = {
            "title": "Assigned Task",
            "description": "Task assigned to user",
            "priority": "medium",
            "task_list_id": task_list_id,
            "assigned_to": user_id
        }
        
        response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["assigned_to"] == user_id

    async def test_task_creation_with_due_date(self, async_client, authenticated_user, sample_task_list):
        """Test task creation with due date."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        task_data = {
            "title": "Task with Due Date",
            "description": "Task with due date",
            "priority": "low",
            "task_list_id": task_list_id,
            "due_date": due_date
        }
        
        response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["due_date"] is not None
        assert response_data["is_overdue"] is False

    async def test_task_retrieval(self, async_client, authenticated_user, sample_task_list):
        """Test task retrieval."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Create task first
        task_data = {
            "title": "Retrieval Test Task",
            "description": "Testing task retrieval",
            "priority": "medium",
            "task_list_id": task_list_id
        }
        
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=headers
        )
        task_id = create_response.json()["id"]
        
        # Retrieve task
        response = await async_client.get(f"/api/v1/tasks/{task_id}", headers=headers)
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["id"] == task_id
        assert response_data["title"] == task_data["title"]
        assert response_data["description"] == task_data["description"]

    async def test_task_update(self, async_client, authenticated_user, sample_task_list):
        """Test task update."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Create task first
        task_data = {
            "title": "Original Task",
            "description": "Original description",
            "priority": "low",
            "task_list_id": task_list_id
        }
        
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=headers
        )
        task_id = create_response.json()["id"]
        
        # Update task
        update_data = {
            "title": "Updated Task",
            "description": "Updated description",
            "priority": "high"
        }
        
        response = await async_client.put(
            f"/api/v1/tasks/{task_id}",
            json=update_data,
            headers=headers
        )
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["title"] == update_data["title"]
        assert response_data["description"] == update_data["description"]
        assert response_data["priority"] == update_data["priority"]

    async def test_task_status_update(self, async_client, authenticated_user, sample_task_list):
        """Test task status update."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Create task first
        task_data = {
            "title": "Status Test Task",
            "description": "Testing status updates",
            "priority": "medium",
            "task_list_id": task_list_id
        }
        
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=headers
        )
        task_id = create_response.json()["id"]
        
        # Update status to in_progress
        response = await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "in_progress"},
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress"
        
        # Update status to completed
        response = await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "completed"},
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    async def test_task_deletion(self, async_client, authenticated_user, sample_task_list):
        """Test task deletion."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Create task first
        task_data = {
            "title": "Deletion Test Task",
            "description": "Testing task deletion",
            "priority": "medium",
            "task_list_id": task_list_id
        }
        
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=headers
        )
        task_id = create_response.json()["id"]
        
        # Delete task
        response = await async_client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
        
        assert response.status_code == 200
        
        # Verify deletion
        response = await async_client.get(f"/api/v1/tasks/{task_id}", headers=headers)
        assert response.status_code == 404

    async def test_task_listing_and_filtering(self, async_client, authenticated_user, sample_task_list):
        """Test task listing with filters."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Create tasks with different priorities and statuses
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
        
        # Test listing all tasks
        response = await async_client.get(
            f"/api/v1/tasks/?task_list_id={task_list_id}",
            headers=headers
        )
        assert response.status_code == 200
        all_tasks = response.json()
        assert len(all_tasks) >= 3
        
        # Test filter by priority
        response = await async_client.get(
            f"/api/v1/tasks/?task_list_id={task_list_id}&priority=high",
            headers=headers
        )
        assert response.status_code == 200
        high_priority_tasks = response.json()
        assert len(high_priority_tasks) == 1
        assert high_priority_tasks[0]["priority"] == "high"
        
        # Test filter by status
        response = await async_client.get(
            f"/api/v1/tasks/?task_list_id={task_list_id}&status=in_progress",
            headers=headers
        )
        assert response.status_code == 200
        in_progress_tasks = response.json()
        assert len(in_progress_tasks) == 1
        assert in_progress_tasks[0]["status"] == "in_progress"

    async def test_task_list_completion_percentage(self, async_client, authenticated_user):
        """Test task list completion percentage calculation."""
        headers = authenticated_user["headers"]
        
        # Create task list
        task_list_data = {
            "name": "Completion Test List",
            "description": "Testing completion percentage"
        }
        response = await async_client.post("/api/v1/task-lists/", json=task_list_data, headers=headers)
        task_list_id = response.json()["id"]
        
        # Create 4 tasks
        for i in range(4):
            task_data = {
                "title": f"Task {i+1}",
                "description": f"Task number {i+1}",
                "task_list_id": task_list_id
            }
            await async_client.post("/api/v1/tasks/", json=task_data, headers=headers)
        
        # Get initial completion (should be 0%)
        response = await async_client.get(f"/api/v1/task-lists/{task_list_id}", headers=headers)
        assert response.json()["completion_percentage"] == 0.0
        
        # Get tasks and complete 2 of them
        tasks_response = await async_client.get(f"/api/v1/tasks/?task_list_id={task_list_id}", headers=headers)
        tasks = tasks_response.json()
        
        # Complete first two tasks
        for i in range(2):
            await async_client.patch(
                f"/api/v1/tasks/{tasks[i]['id']}/status",
                json={"status": "completed"},
                headers=headers
            )
        
        # Check completion percentage (should be 50%)
        response = await async_client.get(f"/api/v1/task-lists/{task_list_id}", headers=headers)
        completion_percentage = response.json()["completion_percentage"]
        assert 48.0 <= completion_percentage <= 52.0  # Allow some tolerance

    async def test_task_assignment_workflow(self, async_client, authenticated_user, sample_task_list):
        """Test complete task assignment workflow."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        user_id = authenticated_user["user"]["id"]
        
        # Create unassigned task
        task_data = {
            "title": "Assignment Test Task",
            "description": "Testing assignment workflow",
            "priority": "medium",
            "task_list_id": task_list_id
        }
        
        create_response = await async_client.post("/api/v1/tasks/", json=task_data, headers=headers)
        task_id = create_response.json()["id"]
        
        # Assign task to user
        response = await async_client.post(
            f"/api/v1/tasks/{task_id}/assign/{user_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["assigned_to"] == user_id

    async def test_unauthorized_task_access(self, async_client, authenticated_user):
        """Test unauthorized access to tasks."""
        headers = authenticated_user["headers"]
        
        # Create another user
        other_user_data = {
            "email": "otheruser@example.com",
            "username": "otheruser",
            "full_name": "Other User",
            "password": "otherpassword123"
        }
        
        await async_client.post("/auth/register", json=other_user_data)
        other_login_response = await async_client.post("/auth/login", json={
            "email": other_user_data["email"],
            "password": other_user_data["password"]
        })
        other_headers = {"Authorization": f"Bearer {other_login_response.json()['access_token']}"}
        
        # Create task list with first user
        task_list_response = await async_client.post("/api/v1/task-lists/", json={
            "name": "Private List",
            "description": "Private task list"
        }, headers=headers)
        task_list_id = task_list_response.json()["id"]
        
        # Try to access with second user (should fail)
        response = await async_client.get(f"/api/v1/task-lists/{task_list_id}", headers=other_headers)
        assert response.status_code in [403, 404]  # Either forbidden or not found

    async def test_task_validation_errors(self, async_client, authenticated_user, sample_task_list):
        """Test task validation errors."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Test empty title
        response = await async_client.post("/api/v1/tasks/", json={
            "title": "",
            "task_list_id": task_list_id
        }, headers=headers)
        assert response.status_code == 422
        
        # Test invalid priority
        response = await async_client.post("/api/v1/tasks/", json={
            "title": "Test Task",
            "priority": "invalid_priority",
            "task_list_id": task_list_id
        }, headers=headers)
        assert response.status_code == 422
        
        # Test invalid status update
        task_response = await async_client.post("/api/v1/tasks/", json={
            "title": "Valid Task",
            "task_list_id": task_list_id
        }, headers=headers)
        task_id = task_response.json()["id"]
        
        response = await async_client.patch(f"/api/v1/tasks/{task_id}/status", json={
            "status": "invalid_status"
        }, headers=headers)
        assert response.status_code == 422

    async def test_pagination_and_limits(self, async_client, authenticated_user, sample_task_list):
        """Test pagination and limits in task listing."""
        headers = authenticated_user["headers"]
        task_list_id = sample_task_list["id"]
        
        # Create many tasks
        for i in range(15):
            task_data = {
                "title": f"Pagination Task {i+1}",
                "description": f"Task for pagination testing {i+1}",
                "task_list_id": task_list_id
            }
            await async_client.post("/api/v1/tasks/", json=task_data, headers=headers)
        
        # Test with limit
        response = await async_client.get(
            f"/api/v1/tasks/?task_list_id={task_list_id}&limit=5",
            headers=headers
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) <= 5
        
        # Test with skip and limit
        response = await async_client.get(
            f"/api/v1/tasks/?task_list_id={task_list_id}&skip=5&limit=5",
            headers=headers
        )
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) <= 5 