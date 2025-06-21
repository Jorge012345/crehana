"""
Integration tests for notification functionality.
Tests email notification simulation and task assignment notifications.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from src.main import app
from src.infrastructure.database import get_db_session


class TestNotificationIntegration:
    """Integration tests for notification system."""

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
    async def authenticated_users(self, async_client):
        """Create two authenticated users for testing."""
        users = []
        
        for i in range(2):
            user_data = {
                "email": f"notificationtest{i}@example.com",
                "username": f"notificationuser{i}",
                "full_name": f"Notification Test User {i}",
                "password": f"notificationpassword{i}123"
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
            
            users.append({
                "user": user_data_response,
                "token": token_data["access_token"],
                "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
            })
        
        return users

    @pytest_asyncio.fixture
    async def task_list_with_owner(self, async_client, authenticated_users):
        """Create a task list with the first user as owner."""
        owner = authenticated_users[0]
        headers = owner["headers"]
        
        task_list_data = {
            "name": "Notification Test List",
            "description": "Task list for notification testing"
        }
        
        response = await async_client.post(
            "/api/v1/task-lists/",
            json=task_list_data,
            headers=headers
        )
        assert response.status_code == 200
        
        return {
            "task_list": response.json(),
            "owner": owner,
            "assignee": authenticated_users[1]
        }

    @patch('src.application.services.logger')
    async def test_task_assignment_notification(self, mock_logger, async_client, task_list_with_owner):
        """Test that notifications are sent when tasks are assigned."""
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Create task with assignment
        task_data = {
            "title": "Assigned Task with Notification",
            "description": "This task should trigger a notification",
            "priority": "high",
            "task_list_id": task_list_id,
            "assigned_to": assignee["user"]["id"]
        }
        
        response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=owner["headers"]
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["assigned_to"] == assignee["user"]["id"]
        
        # Verify that notification logging was called
        # (Since we're using simulated notifications, we check the logger)
        mock_logger.info.assert_called()
        
        # Check that one of the log calls was about sending email
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        notification_logs = [log for log in log_calls if "Sending email" in log]
        assert len(notification_logs) > 0

    @patch('src.application.services.logger')
    async def test_task_reassignment_notification(self, mock_logger, async_client, task_list_with_owner):
        """Test notification when task is reassigned to different user."""
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Create task without assignment
        task_data = {
            "title": "Task to be Reassigned",
            "description": "This task will be reassigned",
            "priority": "medium",
            "task_list_id": task_list_id
        }
        
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=owner["headers"]
        )
        task_id = create_response.json()["id"]
        
        # Clear previous log calls
        mock_logger.reset_mock()
        
        # Update task to assign it
        update_data = {
            "title": "Task to be Reassigned",
            "description": "This task will be reassigned",
            "assigned_to": assignee["user"]["id"]
        }
        
        response = await async_client.put(
            f"/api/v1/tasks/{task_id}",
            json=update_data,
            headers=owner["headers"]
        )
        
        assert response.status_code == 200
        assert response.json()["assigned_to"] == assignee["user"]["id"]
        
        # Verify notification was sent
        mock_logger.info.assert_called()
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        notification_logs = [log for log in log_calls if "Sending email" in log]
        assert len(notification_logs) > 0

    async def test_task_assignment_endpoint(self, async_client, task_list_with_owner):
        """Test the specific task assignment endpoint."""
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Create unassigned task
        task_data = {
            "title": "Unassigned Task",
            "description": "Task to be assigned via endpoint",
            "priority": "low",
            "task_list_id": task_list_id
        }
        
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=owner["headers"]
        )
        task_id = create_response.json()["id"]
        
        # Assign task using assignment endpoint
        response = await async_client.post(
            f"/api/v1/tasks/{task_id}/assign/{assignee['user']['id']}",
            headers=owner["headers"]
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["assigned_to"] == assignee["user"]["id"]

    async def test_notification_with_invalid_assignee(self, async_client, task_list_with_owner):
        """Test notification handling with invalid assignee."""
        owner = task_list_with_owner["owner"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Try to create task with non-existent assignee
        task_data = {
            "title": "Task with Invalid Assignee",
            "description": "This should fail",
            "priority": "medium",
            "task_list_id": task_list_id,
            "assigned_to": 99999  # Non-existent user ID
        }
        
        response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=owner["headers"]
        )
        
        # Should fail due to invalid assignee
        assert response.status_code == 400

    @patch('src.application.services.NotificationService.send_email_notification')
    async def test_notification_service_called(self, mock_send_email, async_client, task_list_with_owner):
        """Test that notification service is actually called."""
        mock_send_email.return_value = True
        
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Create task with assignment
        task_data = {
            "title": "Service Test Task",
            "description": "Testing notification service call",
            "priority": "high",
            "task_list_id": task_list_id,
            "assigned_to": assignee["user"]["id"]
        }
        
        response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=owner["headers"]
        )
        
        assert response.status_code == 200
        
        # Verify notification service was called
        mock_send_email.assert_called_once()
        
        # Verify the notification data
        call_args = mock_send_email.call_args[0][0]
        assert call_args.to_email == assignee["user"]["email"]
        assert "Task Assigned" in call_args.subject
        assert task_data["title"] in call_args.body

    async def test_notification_disabled_scenario(self, async_client, task_list_with_owner):
        """Test scenario when notifications are disabled."""
        # This test verifies the system handles disabled notifications gracefully
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Mock notification service to be disabled
        with patch('src.presentation.dependencies.get_notification_service') as mock_get_service:
            from src.application.services import NotificationService
            mock_service = NotificationService(email_enabled=False)
            mock_get_service.return_value = mock_service
            
            # Create task with assignment
            task_data = {
                "title": "Disabled Notification Task",
                "description": "Testing with disabled notifications",
                "priority": "medium",
                "task_list_id": task_list_id,
                "assigned_to": assignee["user"]["id"]
            }
            
            response = await async_client.post(
                "/api/v1/tasks/",
                json=task_data,
                headers=owner["headers"]
            )
            
            # Task creation should still succeed
            assert response.status_code == 200
            assert response.json()["assigned_to"] == assignee["user"]["id"]

    async def test_multiple_task_assignments(self, async_client, task_list_with_owner):
        """Test multiple task assignments to same user."""
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Create multiple tasks assigned to same user
        for i in range(3):
            task_data = {
                "title": f"Multiple Assignment Task {i+1}",
                "description": f"Task {i+1} assigned to same user",
                "priority": "medium",
                "task_list_id": task_list_id,
                "assigned_to": assignee["user"]["id"]
            }
            
            response = await async_client.post(
                "/api/v1/tasks/",
                json=task_data,
                headers=owner["headers"]
            )
            
            assert response.status_code == 200
            assert response.json()["assigned_to"] == assignee["user"]["id"]

    async def test_task_unassignment(self, async_client, task_list_with_owner):
        """Test removing assignment from a task."""
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Create assigned task
        task_data = {
            "title": "Task to be Unassigned",
            "description": "This task will be unassigned",
            "priority": "medium",
            "task_list_id": task_list_id,
            "assigned_to": assignee["user"]["id"]
        }
        
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=owner["headers"]
        )
        task_id = create_response.json()["id"]
        
        # Unassign task (set assigned_to to null)
        update_data = {
            "title": "Task to be Unassigned",
            "description": "This task will be unassigned",
            "assigned_to": None
        }
        
        response = await async_client.put(
            f"/api/v1/tasks/{task_id}",
            json=update_data,
            headers=owner["headers"]
        )
        
        assert response.status_code == 200
        assert response.json()["assigned_to"] is None

    @patch('src.application.services.logger')
    async def test_notification_content_validation(self, mock_logger, async_client, task_list_with_owner):
        """Test that notification content is properly formatted."""
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        task_title = "Important Notification Test Task"
        task_description = "This task has a detailed description for notification testing"
        
        # Create task with assignment
        task_data = {
            "title": task_title,
            "description": task_description,
            "priority": "high",
            "task_list_id": task_list_id,
            "assigned_to": assignee["user"]["id"]
        }
        
        response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=owner["headers"]
        )
        
        assert response.status_code == 200
        
        # Check notification content in logs
        mock_logger.info.assert_called()
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        
        # Find the email notification log
        email_logs = [log for log in log_calls if "Sending email" in log]
        assert len(email_logs) > 0
        
        # Verify email contains assignee email and task title
        email_log = email_logs[0]
        assert assignee["user"]["email"] in email_log
        assert task_title in email_log

    async def test_notification_error_handling(self, async_client, task_list_with_owner):
        """Test notification error handling scenarios."""
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Mock notification service to raise exception
        with patch('src.application.services.NotificationService.send_email_notification') as mock_send:
            mock_send.side_effect = Exception("Email service unavailable")
            
            # Create task with assignment
            task_data = {
                "title": "Error Handling Task",
                "description": "Testing notification error handling",
                "priority": "medium",
                "task_list_id": task_list_id,
                "assigned_to": assignee["user"]["id"]
            }
            
            # Task creation should still succeed even if notification fails
            response = await async_client.post(
                "/api/v1/tasks/",
                json=task_data,
                headers=owner["headers"]
            )
            
            assert response.status_code == 200
            assert response.json()["assigned_to"] == assignee["user"]["id"]

    async def test_assignee_task_access(self, async_client, task_list_with_owner):
        """Test that assigned users can access their assigned tasks."""
        owner = task_list_with_owner["owner"]
        assignee = task_list_with_owner["assignee"]
        task_list_id = task_list_with_owner["task_list"]["id"]
        
        # Create task assigned to second user
        task_data = {
            "title": "Assignee Access Task",
            "description": "Task assigned to test user access",
            "priority": "medium",
            "task_list_id": task_list_id,
            "assigned_to": assignee["user"]["id"]
        }
        
        create_response = await async_client.post(
            "/api/v1/tasks/",
            json=task_data,
            headers=owner["headers"]
        )
        task_id = create_response.json()["id"]
        
        # Assignee should be able to view the task
        response = await async_client.get(
            f"/api/v1/tasks/{task_id}",
            headers=assignee["headers"]
        )
        
        assert response.status_code == 200
        assert response.json()["assigned_to"] == assignee["user"]["id"]
        
        # Assignee should be able to update task status
        response = await async_client.patch(
            f"/api/v1/tasks/{task_id}/status",
            json={"status": "in_progress"},
            headers=assignee["headers"]
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "in_progress" 