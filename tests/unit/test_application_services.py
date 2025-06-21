"""
Simple and effective tests for application services.
Focuses on testing actual methods that exist in the codebase.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.application.services import TaskListService, TaskService, NotificationService
from src.application.dto import (
    TaskListCreateDTO, TaskListUpdateDTO, TaskCreateDTO, TaskUpdateDTO,
    TaskStatusUpdateDTO, TaskFilterDTO, PaginationDTO, EmailNotificationDTO
)
from src.domain.entities import User, TaskList, Task, TaskStatus, TaskPriority
from src.domain.exceptions import TaskListNotFoundError, AuthorizationError


class TestTaskListServiceSimple:
    """Simple tests for TaskListService."""

    @pytest.fixture
    def mock_task_list_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_task_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_notification_service(self):
        return AsyncMock()

    @pytest.fixture
    def task_list_service(self, mock_task_list_repo, mock_task_repo, mock_notification_service):
        return TaskListService(
            task_list_repository=mock_task_list_repo,
            task_repository=mock_task_repo,
            notification_service=mock_notification_service
        )

    @pytest.fixture
    def sample_task_list(self):
        return TaskList(
            id=1,
            name="Test List",
            description="Test description",
            owner_id=1,
            created_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_create_task_list(self, task_list_service, mock_task_list_repo, sample_task_list):
        """Test task list creation."""
        mock_task_list_repo.create.return_value = sample_task_list
        
        task_list_data = TaskListCreateDTO(
            name="Test List",
            description="Test description"
        )
        
        result = await task_list_service.create_task_list(task_list_data, owner_id=1)
        
        assert result.name == "Test List"
        assert result.owner_id == 1
        mock_task_list_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_list_success(self, task_list_service, mock_task_list_repo, mock_task_repo, sample_task_list):
        """Test successful task list retrieval."""
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        mock_task_repo.get_by_task_list.return_value = []  # No tasks
        
        result = await task_list_service.get_task_list(task_list_id=1, user_id=1)
        
        assert result.name == "Test List"
        mock_task_list_repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_task_list_not_found(self, task_list_service, mock_task_list_repo):
        """Test task list retrieval when not found."""
        mock_task_list_repo.get_by_id.return_value = None
        
        with pytest.raises(TaskListNotFoundError):
            await task_list_service.get_task_list(task_list_id=999, user_id=1)

    @pytest.mark.asyncio
    async def test_get_task_list_wrong_owner(self, task_list_service, mock_task_list_repo):
        """Test task list retrieval by wrong owner."""
        task_list = TaskList(
            id=1,
            name="Test List",
            description="Test description",
            owner_id=2,  # Different owner
            created_at=datetime.utcnow()
        )
        mock_task_list_repo.get_by_id.return_value = task_list
        
        with pytest.raises(AuthorizationError):
            await task_list_service.get_task_list(task_list_id=1, user_id=1)

    @pytest.mark.asyncio
    async def test_update_task_list(self, task_list_service, mock_task_list_repo, sample_task_list):
        """Test task list update."""
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        
        updated_task_list = TaskList(
            id=1,
            name="Updated List",
            description="Updated description",
            owner_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_task_list_repo.update.return_value = updated_task_list
        
        update_data = TaskListUpdateDTO(
            name="Updated List",
            description="Updated description"
        )
        
        result = await task_list_service.update_task_list(
            task_list_id=1,
            update_data=update_data,
            user_id=1
        )
        
        assert result.name == "Updated List"

    @pytest.mark.asyncio
    async def test_delete_task_list(self, task_list_service, mock_task_list_repo, sample_task_list):
        """Test task list deletion."""
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        mock_task_list_repo.delete.return_value = True
        
        result = await task_list_service.delete_task_list(task_list_id=1, user_id=1)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_list_user_task_lists(self, task_list_service, mock_task_list_repo, mock_task_repo, sample_task_list):
        """Test user task lists listing."""
        mock_task_list_repo.get_by_owner.return_value = [sample_task_list]
        mock_task_repo.get_by_task_list.return_value = []  # No tasks
        
        pagination = PaginationDTO(skip=0, limit=10)
        result = await task_list_service.list_user_task_lists(user_id=1, pagination=pagination)
        
        assert len(result) == 1
        assert result[0].name == "Test List"


class TestTaskServiceSimple:
    """Simple tests for TaskService."""

    @pytest.fixture
    def mock_task_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_task_list_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_user_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_notification_service(self):
        return AsyncMock()

    @pytest.fixture
    def task_service(self, mock_task_repo, mock_task_list_repo, mock_user_repo, mock_notification_service):
        return TaskService(
            task_repository=mock_task_repo,
            task_list_repository=mock_task_list_repo,
            user_repository=mock_user_repo,
            notification_service=mock_notification_service
        )

    @pytest.fixture
    def sample_task(self):
        return Task(
            id=1,
            title="Test Task",
            description="Test description",
            task_list_id=1,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_task_list(self):
        return TaskList(
            id=1,
            name="Test List",
            description="Test description",
            owner_id=1,
            created_at=datetime.utcnow()
        )

    @pytest.mark.asyncio
    async def test_create_task(self, task_service, mock_task_repo, mock_task_list_repo, 
                              sample_task, sample_task_list):
        """Test task creation."""
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        mock_task_repo.create.return_value = sample_task
        
        task_data = TaskCreateDTO(
            title="Test Task",
            description="Test description",
            task_list_id=1,
            priority=TaskPriority.MEDIUM
        )
        
        result = await task_service.create_task(
            task_list_id=1,
            task_data=task_data,
            user_id=1
        )
        
        assert result.title == "Test Task"
        mock_task_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task(self, task_service, mock_task_repo, mock_task_list_repo,
                           sample_task, sample_task_list):
        """Test task retrieval."""
        mock_task_repo.get_by_id.return_value = sample_task
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        
        result = await task_service.get_task(task_id=1, user_id=1)
        
        assert result.title == "Test Task"

    @pytest.mark.asyncio
    async def test_update_task(self, task_service, mock_task_repo, mock_task_list_repo,
                              sample_task, sample_task_list):
        """Test task update."""
        mock_task_repo.get_by_id.return_value = sample_task
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        
        updated_task = Task(
            id=1,
            title="Updated Task",
            description="Updated description",
            task_list_id=1,
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_task_repo.update.return_value = updated_task
        
        update_data = TaskUpdateDTO(
            title="Updated Task",
            description="Updated description",
            priority=TaskPriority.HIGH
        )
        
        result = await task_service.update_task(
            task_id=1,
            update_data=update_data,
            user_id=1
        )
        
        assert result.title == "Updated Task"

    @pytest.mark.asyncio
    async def test_update_task_status(self, task_service, mock_task_repo, mock_task_list_repo,
                                     sample_task, sample_task_list):
        """Test task status update."""
        mock_task_repo.get_by_id.return_value = sample_task
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        
        updated_task = Task(
            id=1,
            title="Test Task",
            description="Test description",
            task_list_id=1,
            status=TaskStatus.COMPLETED,
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_task_repo.update_status.return_value = updated_task
        
        status_data = TaskStatusUpdateDTO(status=TaskStatus.COMPLETED)
        
        result = await task_service.update_task_status(
            task_id=1,
            status_data=status_data,
            user_id=1
        )
        
        assert result.status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_delete_task(self, task_service, mock_task_repo, mock_task_list_repo,
                              sample_task, sample_task_list):
        """Test task deletion."""
        mock_task_repo.get_by_id.return_value = sample_task
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        mock_task_repo.delete.return_value = True
        
        result = await task_service.delete_task(task_id=1, user_id=1)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_list_tasks(self, task_service, mock_task_repo, mock_task_list_repo, sample_task, sample_task_list):
        """Test tasks listing."""
        mock_task_list_repo.get_by_id.return_value = sample_task_list
        mock_task_repo.get_by_task_list.return_value = [sample_task]
        
        filters = TaskFilterDTO()
        pagination = PaginationDTO(skip=0, limit=10)
        
        result = await task_service.list_tasks(
            task_list_id=1,
            filters=filters,
            pagination=pagination,
            user_id=1
        )
        
        assert len(result) == 1
        assert result[0].title == "Test Task"


class TestNotificationServiceSimple:
    """Simple tests for NotificationService."""

    @pytest.fixture
    def notification_service(self):
        return NotificationService()

    def test_notification_service_initialization(self):
        """Test NotificationService initialization."""
        service = NotificationService()
        assert service.email_enabled is True
        
        service_disabled = NotificationService(email_enabled=False)
        assert service_disabled.email_enabled is False

    @pytest.mark.asyncio
    async def test_send_email_notification(self, notification_service):
        """Test email notification sending."""
        email_data = EmailNotificationDTO(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Should not raise exception
        result = await notification_service.send_email_notification(email_data)
        assert isinstance(result, bool)

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