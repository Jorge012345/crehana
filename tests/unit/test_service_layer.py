"""
Simplified services tests to improve coverage without interface issues.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from src.application.services import TaskListService, TaskService, NotificationService
from src.application.dto import TaskListCreateDTO, TaskCreateDTO, EmailNotificationDTO
from src.domain.entities import TaskList, Task, TaskStatus, TaskPriority


class TestTaskListServiceSimple:
    """Simple tests for TaskListService."""

    @pytest.fixture
    def mock_repos_and_service(self):
        mock_task_list_repo = AsyncMock()
        mock_task_repo = AsyncMock()
        mock_notification_service = AsyncMock()
        
        service = TaskListService(
            task_list_repository=mock_task_list_repo,
            task_repository=mock_task_repo,
            notification_service=mock_notification_service
        )
        
        return service, mock_task_list_repo, mock_task_repo, mock_notification_service

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_repos_and_service):
        """Test service initialization."""
        service, mock_task_list_repo, mock_task_repo, mock_notification_service = mock_repos_and_service
        
        assert service.task_list_repository == mock_task_list_repo
        assert service.task_repository == mock_task_repo
        assert service.notification_service == mock_notification_service

    @pytest.mark.asyncio
    async def test_create_task_list_basic(self, mock_repos_and_service):
        """Test basic task list creation."""
        service, mock_task_list_repo, mock_task_repo, mock_notification_service = mock_repos_and_service
        
        # Mock the created task list
        mock_task_list = TaskList(
            id=1,
            name="Test List",
            description="Test Description",
            owner_id=1,
            created_at=datetime.utcnow()
        )
        mock_task_list_repo.create.return_value = mock_task_list
        
        # Create DTO
        task_list_data = TaskListCreateDTO(
            name="Test List",
            description="Test Description"
        )
        
        # Call service
        result = await service.create_task_list(task_list_data, 1)
        
        # Verify
        assert result.name == "Test List"
        assert result.owner_id == 1
        mock_task_list_repo.create.assert_called_once()


class TestTaskServiceSimple:
    """Simple tests for TaskService."""

    @pytest.fixture
    def mock_repos_and_service(self):
        mock_task_repo = AsyncMock()
        mock_task_list_repo = AsyncMock()
        mock_user_repo = AsyncMock()
        mock_notification_service = AsyncMock()
        
        service = TaskService(
            task_repository=mock_task_repo,
            task_list_repository=mock_task_list_repo,
            user_repository=mock_user_repo,
            notification_service=mock_notification_service
        )
        
        return service, mock_task_repo, mock_task_list_repo, mock_user_repo, mock_notification_service

    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_repos_and_service):
        """Test service initialization."""
        service, mock_task_repo, mock_task_list_repo, mock_user_repo, mock_notification_service = mock_repos_and_service
        
        assert service.task_repository == mock_task_repo
        assert service.task_list_repository == mock_task_list_repo
        assert service.user_repository == mock_user_repo
        assert service.notification_service == mock_notification_service

    @pytest.mark.asyncio
    async def test_create_task_basic(self, mock_repos_and_service):
        """Test basic task creation."""
        service, mock_task_repo, mock_task_list_repo, mock_user_repo, mock_notification_service = mock_repos_and_service
        
        # Mock task list
        mock_task_list = TaskList(
            id=1,
            name="Test List",
            description="Test Description",
            owner_id=1,
            created_at=datetime.utcnow()
        )
        mock_task_list_repo.get_by_id.return_value = mock_task_list
        
        # Mock created task
        mock_task = Task(
            id=1,
            title="Test Task",
            description="Test Description",
            task_list_id=1,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow()
        )
        mock_task_repo.create.return_value = mock_task
        
        # Create DTO
        task_data = TaskCreateDTO(
            title="Test Task",
            description="Test Description",
            task_list_id=1,
            priority=TaskPriority.MEDIUM
        )
        
        # Call service
        result = await service.create_task(1, task_data, 1)
        
        # Verify
        assert result.title == "Test Task"
        mock_task_repo.create.assert_called_once()


class TestNotificationServiceSimple:
    """Simple tests for NotificationService."""

    def test_notification_service_initialization(self):
        """Test NotificationService initialization."""
        service = NotificationService(email_enabled=True)
        assert service.email_enabled is True
        
        service_disabled = NotificationService(email_enabled=False)
        assert service_disabled.email_enabled is False

    @pytest.mark.asyncio
    async def test_send_email_notification_enabled(self):
        """Test email notification when enabled."""
        service = NotificationService(email_enabled=True)
        
        email_data = EmailNotificationDTO(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        result = await service.send_email_notification(email_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_send_email_notification_disabled(self):
        """Test email notification when disabled."""
        service = NotificationService(email_enabled=False)
        
        email_data = EmailNotificationDTO(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        result = await service.send_email_notification(email_data)
        assert result is False


def test_service_imports():
    """Test that all services can be imported."""
    from src.application.services import TaskListService, TaskService, NotificationService
    
    assert TaskListService is not None
    assert TaskService is not None
    assert NotificationService is not None


def test_service_classes_exist():
    """Test that service classes exist and are properly defined."""
    assert hasattr(TaskListService, '__init__')
    assert hasattr(TaskService, '__init__')
    assert hasattr(NotificationService, '__init__')
    
    # Test that services have expected methods
    assert hasattr(TaskListService, 'create_task_list')
    assert hasattr(TaskService, 'create_task')
    assert hasattr(NotificationService, 'send_email_notification') 