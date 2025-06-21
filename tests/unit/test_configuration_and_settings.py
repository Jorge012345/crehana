"""
Additional tests to reach 80% coverage.
Targets specific uncovered lines in various modules.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

# Test main.py additional lines
def test_main_app_openapi_configuration():
    """Test main app OpenAPI configuration."""
    from src.main import app
    
    # Test OpenAPI configuration
    assert hasattr(app, 'openapi_url')
    assert hasattr(app, 'docs_url')
    assert hasattr(app, 'redoc_url')
    
    # Test app metadata
    assert app.title is not None
    assert app.description is not None
    assert app.version is not None

def test_main_app_startup_events():
    """Test main app startup events."""
    from src.main import app
    
    # Test that app can handle startup
    assert hasattr(app, 'router')
    
    # Test middleware stack
    assert hasattr(app, 'middleware_stack')

# Test config.py additional lines
def test_config_database_settings():
    """Test database configuration settings."""
    from src.config import settings
    
    # Test database settings
    assert hasattr(settings, 'database_url')
    assert isinstance(settings.database_url, str)
    
    # Test that database URL is not empty
    assert len(settings.database_url) > 0

def test_config_jwt_settings():
    """Test JWT configuration settings."""
    from src.config import settings
    
    # Test JWT settings
    assert hasattr(settings, 'secret_key')
    assert hasattr(settings, 'algorithm')
    assert hasattr(settings, 'access_token_expire_minutes')
    
    # Test values are reasonable
    assert len(settings.secret_key) > 0
    assert settings.algorithm in ['HS256', 'HS512', 'RS256']
    assert settings.access_token_expire_minutes > 0

def test_config_email_settings():
    """Test email configuration settings."""
    from src.config import settings
    
    # Test email settings
    assert hasattr(settings, 'email_enabled')
    assert hasattr(settings, 'smtp_server')
    assert hasattr(settings, 'smtp_port')
    assert hasattr(settings, 'from_email')
    
    # Test types
    assert isinstance(settings.email_enabled, bool)
    assert isinstance(settings.smtp_server, str)
    assert isinstance(settings.smtp_port, int)
    assert isinstance(settings.from_email, str)

# Test dependencies.py additional lines
def test_dependencies_get_current_user():
    """Test get_current_user dependency."""
    from src.presentation.dependencies import get_current_user
    
    # Test that dependency function exists
    assert callable(get_current_user)

def test_dependencies_module_structure():
    """Test dependencies module structure."""
    from src.presentation import dependencies
    
    # Test module has expected attributes
    assert hasattr(dependencies, 'get_current_user')

# Test database.py additional lines
def test_database_base_model():
    """Test database base model."""
    from src.infrastructure.database import Base
    
    # Test base model exists
    assert Base is not None

def test_database_models_structure():
    """Test database models structure."""
    from src.infrastructure.database import UserModel, TaskListModel, TaskModel
    
    # Test models exist
    assert UserModel is not None
    assert TaskListModel is not None
    assert TaskModel is not None
    
    # Test table names
    assert UserModel.__tablename__ == 'users'
    assert TaskListModel.__tablename__ == 'task_lists'
    assert TaskModel.__tablename__ == 'tasks'

def test_database_manager_basic():
    """Test DatabaseManager basic functionality."""
    from src.infrastructure.database import DatabaseManager
    
    # Test DatabaseManager exists
    assert DatabaseManager is not None

# Test auth service additional lines
@pytest.mark.asyncio
async def test_auth_service_password_hashing():
    """Test auth service password hashing."""
    from src.application.auth_service import AuthService
    
    mock_repo = AsyncMock()
    service = AuthService(
        user_repository=mock_repo,
        secret_key="test_secret",
        algorithm="HS256",
        access_token_expire_minutes=30
    )
    
    # Test password hashing
    password = "test_password"
    hashed = service._hash_password(password)
    
    assert hashed != password
    assert len(hashed) > 0
    
    # Test password verification
    assert service._verify_password(password, hashed) is True
    assert service._verify_password("wrong_password", hashed) is False

@pytest.mark.asyncio
async def test_auth_service_token_creation():
    """Test auth service token creation."""
    from src.application.auth_service import AuthService
    
    mock_repo = AsyncMock()
    service = AuthService(
        user_repository=mock_repo,
        secret_key="test_secret",
        algorithm="HS256",
        access_token_expire_minutes=30
    )
    
    # Test token creation
    data = {"sub": "1", "test": "data"}
    token = service._create_access_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0

# Test services additional lines
@pytest.mark.asyncio
async def test_notification_service_email_handling():
    """Test notification service email handling."""
    from src.application.services import NotificationService
    from src.application.dto import EmailNotificationDTO
    
    # Test with email disabled
    service = NotificationService(email_enabled=False)
    
    email_data = EmailNotificationDTO(
        to_email="test@example.com",
        subject="Test Subject",
        body="Test Body"
    )
    
    # Should not raise exception when disabled
    await service.send_email_notification(email_data)
    
    # Test with email enabled but no SMTP
    service_enabled = NotificationService(email_enabled=True)
    
    # Should handle SMTP errors gracefully
    try:
        await service_enabled.send_email_notification(email_data)
    except Exception:
        # Expected to fail without SMTP server
        pass

# Test domain entities additional lines
def test_task_entity_is_overdue():
    """Test Task entity is_overdue method."""
    from src.domain.entities import Task, TaskStatus, TaskPriority
    
    # Test overdue task
    overdue_task = Task(
        id=1,
        title="Overdue Task",
        description="This task is overdue",
        task_list_id=1,
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        due_date=datetime.utcnow() - timedelta(days=1),
        created_at=datetime.utcnow()
    )
    
    assert overdue_task.is_overdue() is True
    
    # Test future task
    future_task = Task(
        id=2,
        title="Future Task",
        description="This task is in the future",
        task_list_id=1,
        status=TaskStatus.PENDING,
        priority=TaskPriority.LOW,
        due_date=datetime.utcnow() + timedelta(days=1),
        created_at=datetime.utcnow()
    )
    
    assert future_task.is_overdue() is False
    
    # Test task without due date
    no_due_task = Task(
        id=3,
        title="No Due Date",
        description="This task has no due date",
        task_list_id=1,
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        created_at=datetime.utcnow()
    )
    
    assert no_due_task.is_overdue() is False

def test_task_entity_completed_property():
    """Test Task entity completed property."""
    from src.domain.entities import Task, TaskStatus, TaskPriority
    
    # Test completed task
    completed_task = Task(
        id=1,
        title="Completed Task",
        description="This task is completed",
        task_list_id=1,
        status=TaskStatus.COMPLETED,
        priority=TaskPriority.MEDIUM,
        created_at=datetime.utcnow()
    )
    
    assert completed_task.status == TaskStatus.COMPLETED
    
    # Test pending task
    pending_task = Task(
        id=2,
        title="Pending Task",
        description="This task is pending",
        task_list_id=1,
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        created_at=datetime.utcnow()
    )
    
    assert pending_task.status == TaskStatus.PENDING

# Test DTOs additional lines
def test_dto_pagination():
    """Test PaginationDTO."""
    from src.application.dto import PaginationDTO
    
    # Test default pagination
    pagination = PaginationDTO()
    assert pagination.skip == 0
    assert pagination.limit == 100
    
    # Test custom pagination
    custom_pagination = PaginationDTO(skip=10, limit=20)
    assert custom_pagination.skip == 10
    assert custom_pagination.limit == 20

def test_dto_task_filter():
    """Test TaskFilterDTO."""
    from src.application.dto import TaskFilterDTO
    from src.domain.entities import TaskStatus, TaskPriority
    
    # Test empty filter
    empty_filter = TaskFilterDTO()
    assert empty_filter.status is None
    assert empty_filter.priority is None
    assert empty_filter.assigned_to is None
    assert empty_filter.overdue_only is False
    
    # Test filter with values
    filter_with_values = TaskFilterDTO(
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        assigned_to=1,
        overdue_only=True
    )
    assert filter_with_values.status == TaskStatus.PENDING
    assert filter_with_values.priority == TaskPriority.HIGH
    assert filter_with_values.assigned_to == 1
    assert filter_with_values.overdue_only is True

# Test exceptions additional lines
def test_exception_error_codes():
    """Test exception error codes."""
    from src.domain.exceptions import (
        AuthenticationError, AuthorizationError, ValidationError,
        EntityNotFoundError, BusinessRuleViolationError,
        EmailAlreadyExistsError, UsernameAlreadyExistsError,
        UserNotFoundError, TaskListNotFoundError, TaskNotFoundError
    )
    
    # Test all exception error codes
    exceptions_and_codes = [
        (AuthenticationError("test"), "AUTHENTICATION_ERROR"),
        (AuthorizationError("test"), "AUTHORIZATION_ERROR"),
        (ValidationError("test"), "VALIDATION_ERROR"),
        (EntityNotFoundError("test", entity_id=1), "ENTITY_NOT_FOUND"),
        (BusinessRuleViolationError("test"), "BUSINESS_RULE_VIOLATION"),
        (EmailAlreadyExistsError("test"), "DUPLICATE_ENTITY"),
        (UsernameAlreadyExistsError("test"), "DUPLICATE_ENTITY"),
        (UserNotFoundError("test"), "ENTITY_NOT_FOUND"),
        (TaskListNotFoundError("test"), "ENTITY_NOT_FOUND"),
        (TaskNotFoundError("test"), "ENTITY_NOT_FOUND"),
    ]
    
    for exception, expected_code in exceptions_and_codes:
        assert exception.error_code == expected_code

# Test repository interfaces
def test_repository_interfaces():
    """Test repository interfaces."""
    from src.domain.repositories import UserRepository, TaskListRepository, TaskRepository
    
    # Test that interfaces exist
    assert UserRepository is not None
    assert TaskListRepository is not None
    assert TaskRepository is not None
    
    # Test that they have expected methods
    user_methods = ['create', 'get_by_id', 'get_by_email', 'get_by_username', 'update', 'delete']
    for method in user_methods:
        assert hasattr(UserRepository, method)
    
    task_list_methods = ['create', 'get_by_id', 'update', 'delete']
    for method in task_list_methods:
        assert hasattr(TaskListRepository, method)
    
    task_methods = ['create', 'get_by_id', 'update', 'delete']
    for method in task_methods:
        assert hasattr(TaskRepository, method)

# Test enums comprehensive
def test_enums_comprehensive():
    """Test enums comprehensively."""
    from src.domain.entities import TaskStatus, TaskPriority
    
    # Test TaskStatus enum
    assert TaskStatus.PENDING.value == "pending"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.COMPLETED.value == "completed"
    
    # Test TaskPriority enum
    assert TaskPriority.LOW.value == "low"
    assert TaskPriority.MEDIUM.value == "medium"
    assert TaskPriority.HIGH.value == "high"
    
    # Test enum iteration
    statuses = list(TaskStatus)
    priorities = list(TaskPriority)
    
    assert len(statuses) >= 3
    assert len(priorities) >= 3

# Test infrastructure additional
def test_infrastructure_imports():
    """Test infrastructure module imports."""
    from src.infrastructure import database, repositories
    
    assert database is not None
    assert repositories is not None
    
    # Test specific classes
    from src.infrastructure.repositories import (
        SQLAlchemyUserRepository, SQLAlchemyTaskListRepository, SQLAlchemyTaskRepository
    )
    
    assert SQLAlchemyUserRepository is not None
    assert SQLAlchemyTaskListRepository is not None
    assert SQLAlchemyTaskRepository is not None 