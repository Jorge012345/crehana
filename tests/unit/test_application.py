"""
Tests for the application layer.
Includes tests for auth service, services, and DTOs.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from src.application.auth_service import AuthService
from src.application.services import TaskListService, TaskService, NotificationService
from src.application.dto import UserCreateDTO, LoginDTO, TaskListCreateDTO
from src.domain.entities import User, TaskList, Task, TaskStatus, TaskPriority
from src.domain.exceptions import EmailAlreadyExistsError, UsernameAlreadyExistsError, AuthenticationError


class TestAuthService:
    """Test AuthService functionality."""

    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()

    @pytest.fixture
    def auth_service(self, mock_user_repository):
        return AuthService(
            user_repository=mock_user_repository,
            secret_key="test-secret-key",
            algorithm="HS256",
            access_token_expire_minutes=30
        )

    def test_auth_service_initialization(self, auth_service):
        """Test AuthService initialization."""
        assert auth_service.secret_key == "test-secret-key"
        assert auth_service.algorithm == "HS256"
        assert auth_service.access_token_expire_minutes == 30

    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "test123"
        hashed = auth_service._hash_password(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 20
        assert hashed != password

    def test_verify_password(self, auth_service):
        """Test password verification."""
        password = "test123"
        hashed = auth_service._hash_password(password)
        
        assert auth_service._verify_password(password, hashed) is True
        assert auth_service._verify_password("wrong", hashed) is False

    def test_create_access_token(self, auth_service):
        """Test access token creation."""
        token_data = {"sub": "1", "user_id": 1}
        token = auth_service._create_access_token(token_data)
        
        assert isinstance(token, str)
        assert len(token) > 50
        assert "." in token  # JWT format

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_user_repository):
        """Test successful user registration."""
        # Mock no existing user
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.get_by_username.return_value = None
        
        # Mock user creation
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_user_repository.create.return_value = mock_user
        
        user_data = UserCreateDTO(
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User"
        )
        
        result = await auth_service.register_user(user_data)
        
        assert result.email == "test@example.com"
        assert result.username == "testuser"

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, auth_service, mock_user_repository):
        """Test user registration with existing email."""
        # Mock existing user
        mock_user_repository.get_by_email.return_value = Mock(id=1)
        
        user_data = UserCreateDTO(
            email="existing@example.com",
            username="newuser",
            password="password123",
            full_name="Test User"
        )
        
        with pytest.raises(EmailAlreadyExistsError):
            await auth_service.register_user(user_data)

    @pytest.mark.asyncio
    async def test_register_user_username_exists(self, auth_service, mock_user_repository):
        """Test user registration with existing username."""
        # Mock no existing email but existing username
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.get_by_username.return_value = Mock(id=1)
        
        user_data = UserCreateDTO(
            email="test@example.com",
            username="existinguser",
            password="password123",
            full_name="Test User"
        )
        
        with pytest.raises(UsernameAlreadyExistsError):
            await auth_service.register_user(user_data)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_user_repository):
        """Test successful user authentication."""
        # Mock user
        password = "password123"
        hashed_password = auth_service._hash_password(password)
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.is_active = True
        mock_user.hashed_password = hashed_password
        
        mock_user_repository.get_by_email.return_value = mock_user
        
        login_data = LoginDTO(email="test@example.com", password=password)
        result = await auth_service.authenticate_user(login_data)
        
        assert result.access_token is not None
        assert result.expires_in == 1800

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, auth_service, mock_user_repository):
        """Test authentication with invalid credentials."""
        mock_user_repository.get_by_email.return_value = None
        mock_user_repository.get_by_username.return_value = None
        
        login_data = LoginDTO(email="nonexistent@example.com", password="password")
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(login_data)

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, mock_user_repository):
        """Test authentication with wrong password."""
        # Mock user with different password
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_user.hashed_password = auth_service._hash_password("correct_password")
        
        mock_user_repository.get_by_email.return_value = mock_user
        
        login_data = LoginDTO(email="test@example.com", password="wrong_password")
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(login_data)

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive_account(self, auth_service, mock_user_repository):
        """Test authentication with inactive account."""
        # Mock inactive user
        password = "password123"
        hashed_password = auth_service._hash_password(password)
        
        mock_user = Mock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_user.is_active = False  # Inactive
        mock_user.hashed_password = hashed_password
        
        mock_user_repository.get_by_email.return_value = mock_user
        
        login_data = LoginDTO(email="test@example.com", password=password)
        with pytest.raises(AuthenticationError, match="User account is inactive"):
            await auth_service.authenticate_user(login_data)

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_service, mock_user_repository):
        """Test successful current user retrieval."""
        # Create valid token
        token_data = {"sub": "1", "user_id": 1}
        token = auth_service._create_access_token(token_data)
        
        # Mock user
        mock_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="hashed_password",
            is_active=True,
            created_at=datetime.utcnow()
        )
        mock_user_repository.get_by_id.return_value = mock_user
        
        result = await auth_service.get_current_user(token)
        
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_service, mock_user_repository):
        """Test current user retrieval with invalid token."""
        with pytest.raises(AuthenticationError, match="Invalid token"):
            await auth_service.get_current_user("invalid-token")

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, auth_service, mock_user_repository):
        """Test current user retrieval when user not found."""
        # Create valid token
        token_data = {"sub": "1", "user_id": 999}
        token = auth_service._create_access_token(token_data)
        
        # Mock no user found
        mock_user_repository.get_by_id.return_value = None
        
        with pytest.raises(AuthenticationError, match="User not found"):
            await auth_service.get_current_user(token)


class TestServices:
    """Tests for application services."""

    def test_notification_service_initialization(self):
        """Test NotificationService initialization."""
        # Test with default settings
        service_default = NotificationService()
        assert service_default.email_enabled is True
        
        # Test with email disabled
        service_disabled = NotificationService(email_enabled=False)
        assert service_disabled.email_enabled is False
        
        # Test with email enabled
        service_enabled = NotificationService(email_enabled=True)
        assert service_enabled.email_enabled is True

    @pytest.mark.asyncio
    async def test_notification_service_send_email_disabled(self):
        """Test email sending when disabled."""
        from src.application.dto import EmailNotificationDTO
        
        service = NotificationService(email_enabled=False)
        
        email_data = EmailNotificationDTO(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Should not raise an exception
        await service.send_email_notification(email_data)

    def test_task_list_service_initialization(self):
        """Test TaskListService initialization."""
        mock_task_list_repo = AsyncMock()
        mock_task_repo = AsyncMock()
        mock_notification_service = AsyncMock()
        
        service = TaskListService(
            task_list_repository=mock_task_list_repo,
            task_repository=mock_task_repo,
            notification_service=mock_notification_service
        )
        
        assert service.task_list_repository == mock_task_list_repo
        assert service.task_repository == mock_task_repo
        assert service.notification_service == mock_notification_service

    def test_task_service_initialization(self):
        """Test TaskService initialization."""
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
        
        assert service.task_repository == mock_task_repo
        assert service.task_list_repository == mock_task_list_repo
        assert service.user_repository == mock_user_repo
        assert service.notification_service == mock_notification_service


class TestDTOs:
    """Tests for Data Transfer Objects."""

    def test_user_create_dto(self):
        """Test UserCreateDTO creation and validation."""
        user_dto = UserCreateDTO(
            email="test@example.com",
            username="testuser",
            password="password123",
            full_name="Test User"
        )
        
        assert user_dto.email == "test@example.com"
        assert user_dto.username == "testuser"
        assert user_dto.password == "password123"
        assert user_dto.full_name == "Test User"

    def test_login_dto(self):
        """Test LoginDTO creation and validation."""
        login_dto = LoginDTO(
            email="test@example.com",
            password="password123"
        )
        
        assert login_dto.email == "test@example.com"
        assert login_dto.password == "password123"

    def test_task_list_create_dto(self):
        """Test TaskListCreateDTO creation and validation."""
        task_list_dto = TaskListCreateDTO(
            name="Test List",
            description="Test Description"
        )
        
        assert task_list_dto.name == "Test List"
        assert task_list_dto.description == "Test Description" 