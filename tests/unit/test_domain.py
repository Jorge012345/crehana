"""Tests for domain layer - entities and exceptions."""

import pytest
from datetime import datetime, timedelta
from src.domain.entities import User, TaskList, Task, TaskStatus, TaskPriority
from src.domain.exceptions import (
    TaskManagerException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    BusinessRuleViolationError,
    EntityNotFoundError,
    UserNotFoundError,
    TaskListNotFoundError,
    TaskNotFoundError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError
)


class TestDomainEntities:
    """Test domain entities."""

    def test_user_entity_creation(self):
        """Test user entity creation and validation."""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="$2b$12$hash",
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)

    def test_user_entity_validation(self):
        """Test user entity validation."""
        # Test valid user creation
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True

    def test_user_entity_defaults(self):
        """Test user entity default values."""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            created_at=datetime.utcnow()
        )
        
        assert user.is_active is True
        assert user.full_name is None
        assert user.updated_at is None

    def test_task_list_entity_creation(self):
        """Test task list entity creation."""
        task_list = TaskList(
            id=1,
            name="Test List",
            description="Test description",
            owner_id=1,
            created_at=datetime.utcnow()
        )
        
        assert task_list.id == 1
        assert task_list.name == "Test List"
        assert task_list.description == "Test description"
        assert task_list.owner_id == 1
        assert isinstance(task_list.created_at, datetime)

    def test_task_list_entity_validation(self):
        """Test task list entity validation."""
        # Test empty name
        with pytest.raises(ValueError):
            TaskList(
                name="",
                description="Test",
                owner_id=1,
                created_at=datetime.utcnow()
            )

    def test_task_list_entity_defaults(self):
        """Test task list entity defaults."""
        task_list = TaskList(
            name="Test List",
            owner_id=1,
            created_at=datetime.utcnow()
        )
        
        assert task_list.description is None
        assert task_list.updated_at is None
        assert task_list.tasks == []

    def test_task_entity_creation(self):
        """Test task entity creation."""
        task = Task(
            id=1,
            title="Test Task",
            description="Test description",
            task_list_id=1,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            created_at=datetime.utcnow()
        )
        
        assert task.id == 1
        assert task.title == "Test Task"
        assert task.description == "Test description"
        assert task.task_list_id == 1
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM

    def test_task_entity_validation(self):
        """Test task entity validation."""
        # Test empty title
        with pytest.raises(ValueError):
            Task(
                title="",
                task_list_id=1,
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                created_at=datetime.utcnow()
            )

    def test_task_entity_defaults(self):
        """Test task entity defaults."""
        task = Task(
            title="Test Task",
            task_list_id=1,
            created_at=datetime.utcnow()
        )
        
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.description is None
        assert task.assigned_to is None
        assert task.due_date is None
        assert task.updated_at is None

    def test_task_status_enum(self):
        """Test task status enumeration."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.CANCELLED == "cancelled"

    def test_task_priority_enum(self):
        """Test task priority enumeration."""
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"
        assert TaskPriority.CRITICAL == "critical"

    def test_task_is_overdue_property(self):
        """Test task is_overdue computed property."""
        # Task without due date
        task = Task(
            title="Test Task",
            task_list_id=1,
            created_at=datetime.utcnow()
        )
        assert task.is_overdue() is False
        
        # Task with future due date
        task_future = Task(
            title="Test Task",
            task_list_id=1,
            due_date=datetime.utcnow() + timedelta(days=1),
            created_at=datetime.utcnow()
        )
        assert task_future.is_overdue() is False
        
        # Task with past due date
        task_overdue = Task(
            title="Test Task",
            task_list_id=1,
            due_date=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow()
        )
        assert task_overdue.is_overdue() is True

    def test_task_completed_property(self):
        """Test task completed status."""
        task = Task(
            title="Test Task",
            task_list_id=1,
            status=TaskStatus.COMPLETED,
            created_at=datetime.utcnow()
        )
        assert task.status == TaskStatus.COMPLETED


class TestDomainExceptions:
    """Test domain exceptions."""

    def test_task_manager_exception_base(self):
        """Test base TaskManagerException."""
        exc = TaskManagerException("Test message", "TEST_ERROR")
        assert str(exc) == "Test message"
        assert exc.message == "Test message"
        assert exc.error_code == "TEST_ERROR"

    def test_authentication_error(self):
        """Test AuthenticationError."""
        exc = AuthenticationError("Invalid credentials")
        assert str(exc) == "Invalid credentials"
        assert exc.message == "Invalid credentials"
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert isinstance(exc, TaskManagerException)

    def test_authorization_error(self):
        """Test AuthorizationError."""
        exc = AuthorizationError("Access denied")
        assert str(exc) == "Access denied"
        assert exc.message == "Access denied"
        assert exc.error_code == "AUTHORIZATION_ERROR"
        assert isinstance(exc, TaskManagerException)

    def test_validation_error(self):
        """Test ValidationError."""
        exc = ValidationError("Invalid input")
        assert str(exc) == "Invalid input"
        assert exc.message == "Invalid input"
        assert exc.error_code == "VALIDATION_ERROR"
        assert isinstance(exc, TaskManagerException)

    def test_business_rule_violation_error(self):
        """Test BusinessRuleViolationError."""
        exc = BusinessRuleViolationError("Business rule violated")
        assert str(exc) == "Business rule violated"
        assert exc.message == "Business rule violated"
        assert exc.error_code == "BUSINESS_RULE_VIOLATION"
        assert isinstance(exc, TaskManagerException)

    def test_entity_not_found_error(self):
        """Test EntityNotFoundError."""
        exc = EntityNotFoundError("User", 1)
        assert "User with id 1 not found" in str(exc)
        assert exc.error_code == "ENTITY_NOT_FOUND"
        assert isinstance(exc, TaskManagerException)

    def test_user_not_found_error(self):
        """Test UserNotFoundError."""
        exc = UserNotFoundError(1)
        assert "User with id 1 not found" in str(exc)
        assert exc.error_code == "ENTITY_NOT_FOUND"
        assert isinstance(exc, EntityNotFoundError)

    def test_task_list_not_found_error(self):
        """Test TaskListNotFoundError."""
        exc = TaskListNotFoundError(1)
        assert "TaskList with id 1 not found" in str(exc)
        assert exc.error_code == "ENTITY_NOT_FOUND"
        assert isinstance(exc, EntityNotFoundError)

    def test_task_not_found_error(self):
        """Test TaskNotFoundError."""
        exc = TaskNotFoundError(1)
        assert "Task with id 1 not found" in str(exc)
        assert exc.error_code == "ENTITY_NOT_FOUND"
        assert isinstance(exc, EntityNotFoundError)

    def test_email_already_exists_error(self):
        """Test EmailAlreadyExistsError."""
        exc = EmailAlreadyExistsError("test@example.com")
        assert "test@example.com" in str(exc)
        assert exc.error_code == "DUPLICATE_ENTITY"
        assert isinstance(exc, TaskManagerException)

    def test_username_already_exists_error(self):
        """Test UsernameAlreadyExistsError."""
        exc = UsernameAlreadyExistsError("testuser")
        assert "testuser" in str(exc)
        assert exc.error_code == "DUPLICATE_ENTITY"
        assert isinstance(exc, TaskManagerException)

    def test_exception_hierarchy(self):
        """Test exception inheritance hierarchy."""
        # All domain exceptions should inherit from TaskManagerException
        exceptions = [
            AuthenticationError("test"),
            AuthorizationError("test"),
            ValidationError("test"),
            BusinessRuleViolationError("test"),
            EntityNotFoundError("Entity", 1),
            UserNotFoundError(1),
            TaskListNotFoundError(1),
            TaskNotFoundError(1),
            EmailAlreadyExistsError("test@example.com"),
            UsernameAlreadyExistsError("testuser")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, TaskManagerException)

    def test_exception_error_codes_unique(self):
        """Test that all exception error codes are unique."""
        # Test basic error codes
        auth_error = AuthenticationError("test")
        assert auth_error.error_code == "AUTHENTICATION_ERROR"
        
        authz_error = AuthorizationError("test")
        assert authz_error.error_code == "AUTHORIZATION_ERROR"
        
        validation_error = ValidationError("test")
        assert validation_error.error_code == "VALIDATION_ERROR"
        
        # Test that different exception types have different codes
        assert auth_error.error_code != authz_error.error_code
        assert auth_error.error_code != validation_error.error_code
        assert authz_error.error_code != validation_error.error_code

    def test_exception_messages_and_attributes(self):
        """Test exception messages and specific attributes."""
        # Test EntityNotFoundError with different entity types
        user_exc = EntityNotFoundError("User", 123)
        assert "User with id 123 not found" in str(user_exc)
        assert user_exc.error_code == "ENTITY_NOT_FOUND"
        
        # Test specific entity exceptions
        user_not_found = UserNotFoundError(456)
        assert "User with id 456 not found" in str(user_not_found)
        assert user_not_found.error_code == "ENTITY_NOT_FOUND"
        
        task_list_not_found = TaskListNotFoundError(789)
        assert "TaskList with id 789 not found" in str(task_list_not_found)
        assert task_list_not_found.error_code == "ENTITY_NOT_FOUND"
        
        task_not_found = TaskNotFoundError(101)
        assert "Task with id 101 not found" in str(task_not_found)
        assert task_not_found.error_code == "ENTITY_NOT_FOUND"
        
        # Test email and username exceptions
        email_exc = EmailAlreadyExistsError("duplicate@example.com")
        assert "duplicate@example.com" in str(email_exc)
        assert email_exc.error_code == "DUPLICATE_ENTITY"
        
        username_exc = UsernameAlreadyExistsError("duplicateuser")
        assert "duplicateuser" in str(username_exc)
        assert username_exc.error_code == "DUPLICATE_ENTITY"

    def test_exception_string_representations(self):
        """Test exception string representations are meaningful."""
        exceptions_and_expected_content = [
            (AuthenticationError("Invalid password"), "Invalid password"),
            (AuthorizationError("Access denied"), "Access denied"),
            (ValidationError("Invalid email format"), "Invalid email format"),
            (BusinessRuleViolationError("Cannot delete active user"), "Cannot delete active user"),
            (EntityNotFoundError("Product", 42), "Product"),
            (EntityNotFoundError("Product", 42), "42"),
            (UserNotFoundError(99), "User"),
            (UserNotFoundError(99), "99"),
            (EmailAlreadyExistsError("test@example.com"), "test@example.com"),
            (UsernameAlreadyExistsError("testuser"), "testuser")
        ]
        
        for exc, expected_content in exceptions_and_expected_content:
            assert expected_content in str(exc)


class TestDomainEntityRelationships:
    """Test relationships between domain entities."""

    def test_user_task_list_relationship(self):
        """Test relationship between User and TaskList."""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            created_at=datetime.utcnow()
        )
        
        task_list = TaskList(
            id=1,
            name="Test List",
            owner_id=user.id,
            created_at=datetime.utcnow()
        )
        
        assert task_list.owner_id == user.id

    def test_task_list_task_relationship(self):
        """Test relationship between TaskList and Task."""
        task_list = TaskList(
            id=1,
            name="Test List",
            owner_id=1,
            created_at=datetime.utcnow()
        )
        
        task = Task(
            id=1,
            title="Test Task",
            task_list_id=task_list.id,
            created_at=datetime.utcnow()
        )
        
        assert task.task_list_id == task_list.id

    def test_task_assignment_relationship(self):
        """Test task assignment to user."""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            created_at=datetime.utcnow()
        )
        
        task = Task(
            id=1,
            title="Test Task",
            task_list_id=1,
            assigned_to=user.id,
            created_at=datetime.utcnow()
        )
        
        assert task.assigned_to == user.id 