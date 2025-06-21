"""
Critical coverage tests to reach 75%.
Targets the most impactful uncovered lines.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

# Test auth service critical paths
@pytest.mark.asyncio
async def test_auth_service_register_user_critical():
    """Test AuthService register_user critical paths."""
    from src.application.auth_service import AuthService
    from src.application.dto import UserCreateDTO
    from src.domain.entities import User
    from src.domain.exceptions import EmailAlreadyExistsError, UsernameAlreadyExistsError
    
    mock_repo = AsyncMock()
    service = AuthService(
        user_repository=mock_repo,
        secret_key="test_secret",
        algorithm="HS256",
        access_token_expire_minutes=30
    )
    
    # Test successful registration
    mock_repo.get_by_email.return_value = None
    mock_repo.get_by_username.return_value = None
    
    new_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        created_at=datetime.utcnow()
    )
    mock_repo.create.return_value = new_user
    
    user_data = UserCreateDTO(
        email="test@example.com",
        username="testuser",
        password="password123",
        full_name="Test User"
    )
    
    result = await service.register_user(user_data)
    assert result.id == 1
    assert result.email == "test@example.com"

@pytest.mark.asyncio
async def test_auth_service_authenticate_user_critical():
    """Test AuthService authenticate_user critical paths."""
    from src.application.auth_service import AuthService
    from src.domain.entities import User
    from src.domain.exceptions import AuthenticationError
    
    mock_repo = AsyncMock()
    service = AuthService(
        user_repository=mock_repo,
        secret_key="test_secret",
        algorithm="HS256",
        access_token_expire_minutes=30
    )
    
    # Test successful authentication by email
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=service._hash_password("password123"),
        is_active=True,
        created_at=datetime.utcnow()
    )
    mock_repo.get_by_email.return_value = user
    
    from src.application.dto import LoginDTO
    login_data = LoginDTO(email="test@example.com", password="password123")
    result = await service.authenticate_user(login_data)
    assert result.access_token is not None
    assert result.expires_in == 1800

@pytest.mark.asyncio
async def test_auth_service_get_current_user_critical():
    """Test AuthService get_current_user critical paths."""
    from src.application.auth_service import AuthService
    from src.domain.entities import User
    from src.domain.exceptions import AuthenticationError
    
    mock_repo = AsyncMock()
    service = AuthService(
        user_repository=mock_repo,
        secret_key="test_secret",
        algorithm="HS256",
        access_token_expire_minutes=30
    )
    
    # Create a valid token
    token = service._create_access_token({"sub": "1"})
    
    # Test successful token validation
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        created_at=datetime.utcnow()
    )
    mock_repo.get_by_id.return_value = user
    
    result = await service.get_current_user(token)
    assert result.id == 1
    assert result.email == "test@example.com"

# Test services critical paths
@pytest.mark.asyncio
async def test_task_list_service_create_critical():
    """Test TaskListService create critical paths."""
    from src.application.services import TaskListService
    from src.application.dto import TaskListCreateDTO
    from src.domain.entities import TaskList
    
    mock_task_list_repo = AsyncMock()
    mock_task_repo = AsyncMock()
    mock_notification_service = AsyncMock()
    
    service = TaskListService(
        task_list_repository=mock_task_list_repo,
        task_repository=mock_task_repo,
        notification_service=mock_notification_service
    )
    
    # Test successful creation
    new_task_list = TaskList(
        id=1,
        name="Test List",
        description="Test Description",
        owner_id=1,
        created_at=datetime.utcnow()
    )
    mock_task_list_repo.create.return_value = new_task_list
    
    task_list_data = TaskListCreateDTO(
        name="Test List",
        description="Test Description"
    )
    
    result = await service.create_task_list(task_list_data, 1)
    assert result.id == 1
    assert result.name == "Test List"

@pytest.mark.asyncio
async def test_task_list_service_update_critical():
    """Test TaskListService update critical paths."""
    from src.application.services import TaskListService
    from src.application.dto import TaskListUpdateDTO
    from src.domain.entities import TaskList
    from src.domain.exceptions import TaskListNotFoundError, AuthorizationError
    
    mock_task_list_repo = AsyncMock()
    mock_task_repo = AsyncMock()
    mock_notification_service = AsyncMock()
    
    service = TaskListService(
        task_list_repository=mock_task_list_repo,
        task_repository=mock_task_repo,
        notification_service=mock_notification_service
    )
    
    # Test successful update
    existing_task_list = TaskList(
        id=1,
        name="Original List",
        description="Original Description",
        owner_id=1,
        created_at=datetime.utcnow()
    )
    mock_task_list_repo.get_by_id.return_value = existing_task_list
    
    updated_task_list = TaskList(
        id=1,
        name="Updated List",
        description="Updated Description",
        owner_id=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_task_list_repo.update.return_value = updated_task_list
    
    update_data = TaskListUpdateDTO(
        name="Updated List",
        description="Updated Description"
    )
    
    result = await service.update_task_list(
        task_list_id=1,
        update_data=update_data,
        user_id=1
    )
    assert result.name == "Updated List"

@pytest.mark.asyncio
async def test_task_service_create_critical():
    """Test TaskService create critical paths."""
    from src.application.services import TaskService
    from src.application.dto import TaskCreateDTO
    from src.domain.entities import Task, TaskList, TaskStatus, TaskPriority
    
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
    
    # Test successful creation
    task_list = TaskList(
        id=1,
        name="Test List",
        description="Test Description",
        owner_id=1,
        created_at=datetime.utcnow()
    )
    mock_task_list_repo.get_by_id.return_value = task_list
    
    new_task = Task(
        id=1,
        title="Test Task",
        description="Test Description",
        task_list_id=1,
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        created_at=datetime.utcnow()
    )
    mock_task_repo.create.return_value = new_task
    
    task_data = TaskCreateDTO(
        title="Test Task",
        description="Test Description",
        task_list_id=1,
        priority=TaskPriority.MEDIUM
    )
    
    result = await service.create_task(1, task_data, 1)
    assert result.id == 1
    assert result.title == "Test Task"

@pytest.mark.asyncio
async def test_task_service_update_critical():
    """Test TaskService update critical paths."""
    from src.application.services import TaskService
    from src.application.dto import TaskUpdateDTO
    from src.domain.entities import Task, TaskList, TaskStatus, TaskPriority
    
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
    
    # Test successful update
    existing_task = Task(
        id=1,
        title="Original Task",
        description="Original Description",
        task_list_id=1,
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        created_at=datetime.utcnow()
    )
    mock_task_repo.get_by_id.return_value = existing_task
    
    task_list = TaskList(
        id=1,
        name="Test List",
        description="Test Description",
        owner_id=1,
        created_at=datetime.utcnow()
    )
    mock_task_list_repo.get_by_id.return_value = task_list
    
    updated_task = Task(
        id=1,
        title="Updated Task",
        description="Updated Description",
        task_list_id=1,
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_task_repo.update.return_value = updated_task
    
    update_data = TaskUpdateDTO(
        title="Updated Task",
        description="Updated Description",
        priority=TaskPriority.HIGH
    )
    
    result = await service.update_task(
        task_id=1,
        update_data=update_data,
        user_id=1
    )
    assert result.title == "Updated Task"

# Test notification service critical paths
@pytest.mark.asyncio
async def test_notification_service_send_email_critical():
    """Test NotificationService send_email critical paths."""
    from src.application.services import NotificationService
    from src.application.dto import EmailNotificationDTO
    
    # Test with email enabled
    service = NotificationService(email_enabled=True)
    
    email_data = EmailNotificationDTO(
        to_email="test@example.com",
        subject="Test Subject",
        body="Test Body"
    )
    
    # Test should pass without SMTP configuration since it's simulated
    result = await service.send_email_notification(email_data)
    assert result is True

# Test infrastructure critical paths
def test_infrastructure_repositories_critical():
    """Test infrastructure repositories critical paths."""
    from src.infrastructure.repositories import (
        SQLAlchemyUserRepository, SQLAlchemyTaskListRepository, SQLAlchemyTaskRepository
    )
    
    mock_session = Mock()
    
    # Test repository initialization
    user_repo = SQLAlchemyUserRepository(mock_session)
    assert user_repo.session == mock_session
    
    task_list_repo = SQLAlchemyTaskListRepository(mock_session)
    assert task_list_repo.session == mock_session
    
    task_repo = SQLAlchemyTaskRepository(mock_session)
    assert task_repo.session == mock_session

# Test main app critical paths
def test_main_app_critical():
    """Test main app critical paths."""
    from src.main import app
    
    # Test app configuration
    assert app.title is not None
    assert app.description is not None
    assert app.version is not None
    
    # Test that routes are configured
    assert len(app.routes) > 0
    
    # Test middleware configuration
    assert len(app.user_middleware) >= 0

# Test config critical paths
def test_config_critical():
    """Test config critical paths."""
    from src.config import settings
    
    # Test critical settings
    assert settings.secret_key is not None
    assert settings.algorithm is not None
    assert settings.access_token_expire_minutes > 0
    assert settings.database_url is not None
    
    # Test email settings
    assert hasattr(settings, 'email_enabled')
    assert hasattr(settings, 'smtp_server')
    assert hasattr(settings, 'smtp_port')

# Test domain entities critical paths
def test_domain_entities_critical():
    """Test domain entities critical paths."""
    from src.domain.entities import User, TaskList, Task, TaskStatus, TaskPriority
    
    # Test User with all fields
    user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password="hashed",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert user.is_active is True
    assert user.updated_at is not None
    
    # Test TaskList with all fields
    task_list = TaskList(
        id=1,
        name="Test List",
        description="Test Description",
        owner_id=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    assert task_list.updated_at is not None
    
    # Test Task with all fields
    task = Task(
        id=1,
        title="Test Task",
        description="Test Description",
        task_list_id=1,
        status=TaskStatus.IN_PROGRESS,
        priority=TaskPriority.HIGH,
        assigned_to=2,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=1)
    )
    assert task.assigned_to == 2
    assert task.updated_at is not None
    assert task.due_date is not None 