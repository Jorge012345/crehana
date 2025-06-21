"""
Tests for dependencies.py to improve coverage from 58%.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.presentation.dependencies import (
    get_auth_service,
    get_notification_service,
    get_task_list_service,
    get_task_service,
    get_current_user,
    security,
)
from src.application.auth_service import AuthService
from src.application.services import TaskListService, TaskService, NotificationService
from src.domain.entities import User


class TestDependenciesCoverage:
    """Tests to improve dependencies coverage."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_user(self):
        """Mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        return user

    @pytest.fixture
    def mock_token(self):
        """Mock token."""
        token = Mock()
        token.credentials = "test_token"
        return token

    def test_security_configuration(self):
        """Test security configuration."""
        from fastapi.security import HTTPBearer
        
        # Test that security is HTTPBearer instance
        assert isinstance(security, HTTPBearer)

    def test_fastapi_imports(self):
        """Test FastAPI imports."""
        from fastapi import Depends
        from fastapi.security import HTTPBearer
        
        # Test that imports are available
        assert Depends is not None
        assert HTTPBearer is not None

    def test_sqlalchemy_imports(self):
        """Test SQLAlchemy imports."""
        from sqlalchemy.ext.asyncio import AsyncSession
        
        # Test that AsyncSession is available
        assert AsyncSession is not None

    def test_service_imports(self):
        """Test service imports."""
        from src.application.auth_service import AuthService
        from src.application.services import TaskListService, TaskService, NotificationService
        
        # Test that services are available
        assert AuthService is not None
        assert TaskListService is not None
        assert TaskService is not None
        assert NotificationService is not None

    def test_config_imports(self):
        """Test config imports."""
        from src.config import settings
        
        # Test that settings is available
        assert settings is not None
        assert hasattr(settings, 'secret_key')
        assert hasattr(settings, 'algorithm')
        assert hasattr(settings, 'access_token_expire_minutes')

    def test_domain_imports(self):
        """Test domain imports."""
        from src.domain.entities import User
        
        # Test that User is available
        assert User is not None

    def test_database_imports(self):
        """Test database imports."""
        from src.infrastructure.database import get_db_session
        
        # Test that get_db_session is callable
        assert callable(get_db_session)

    def test_repository_imports(self):
        """Test repository imports."""
        from src.infrastructure.repositories import (
            SQLAlchemyUserRepository,
            SQLAlchemyTaskListRepository,
            SQLAlchemyTaskRepository,
        )
        
        # Test that repositories are available
        assert SQLAlchemyUserRepository is not None
        assert SQLAlchemyTaskListRepository is not None
        assert SQLAlchemyTaskRepository is not None

    @pytest.mark.asyncio
    async def test_get_auth_service(self, mock_db_session):
        """Test get_auth_service dependency."""
        # Call the dependency function
        auth_service = await get_auth_service(mock_db_session)
        
        # Test that it returns AuthService instance
        assert isinstance(auth_service, AuthService)

    @pytest.mark.asyncio
    async def test_get_notification_service(self):
        """Test get_notification_service dependency."""
        # Call the dependency function
        notification_service = await get_notification_service()
        
        # Test that it returns NotificationService instance
        assert isinstance(notification_service, NotificationService)
        # Test that email is enabled
        assert notification_service.email_enabled is True

    @pytest.mark.asyncio
    async def test_get_task_list_service(self, mock_db_session):
        """Test get_task_list_service dependency."""
        # Mock notification service
        mock_notification_service = Mock(spec=NotificationService)
        
        # Call the dependency function
        task_list_service = await get_task_list_service(
            db=mock_db_session,
            notification_service=mock_notification_service
        )
        
        # Test that it returns TaskListService instance
        assert isinstance(task_list_service, TaskListService)

    @pytest.mark.asyncio
    async def test_get_task_service(self, mock_db_session):
        """Test get_task_service dependency."""
        # Mock notification service
        mock_notification_service = Mock(spec=NotificationService)
        
        # Call the dependency function
        task_service = await get_task_service(
            db=mock_db_session,
            notification_service=mock_notification_service
        )
        
        # Test that it returns TaskService instance
        assert isinstance(task_service, TaskService)

    @pytest.mark.asyncio
    async def test_get_current_user(self, mock_token, mock_user):
        """Test get_current_user dependency."""
        # Mock auth service
        mock_auth_service = AsyncMock(spec=AuthService)
        mock_auth_service.get_current_user.return_value = mock_user
        
        # Call the dependency function
        user = await get_current_user(
            token=mock_token,
            auth_service=mock_auth_service
        )
        
        # Test that it returns User instance
        assert user == mock_user
        # Test that auth service was called with correct token
        mock_auth_service.get_current_user.assert_called_once_with("test_token")

    def test_dependency_function_signatures(self):
        """Test dependency function signatures."""
        import inspect
        
        # Test that all dependency functions are async
        assert inspect.iscoroutinefunction(get_auth_service)
        assert inspect.iscoroutinefunction(get_notification_service)
        assert inspect.iscoroutinefunction(get_task_list_service)
        assert inspect.iscoroutinefunction(get_task_service)
        assert inspect.iscoroutinefunction(get_current_user)

    def test_dependency_function_parameters(self):
        """Test dependency function parameters."""
        import inspect
        
        # Test get_auth_service parameters
        sig = inspect.signature(get_auth_service)
        assert 'db' in sig.parameters
        
        # Test get_task_list_service parameters
        sig = inspect.signature(get_task_list_service)
        assert 'db' in sig.parameters
        assert 'notification_service' in sig.parameters
        
        # Test get_task_service parameters
        sig = inspect.signature(get_task_service)
        assert 'db' in sig.parameters
        assert 'notification_service' in sig.parameters
        
        # Test get_current_user parameters
        sig = inspect.signature(get_current_user)
        assert 'token' in sig.parameters
        assert 'auth_service' in sig.parameters

    def test_dependency_return_annotations(self):
        """Test dependency return annotations."""
        import inspect
        
        # Test return annotations
        sig = inspect.signature(get_auth_service)
        assert sig.return_annotation == AuthService
        
        sig = inspect.signature(get_notification_service)
        assert sig.return_annotation == NotificationService
        
        sig = inspect.signature(get_task_list_service)
        assert sig.return_annotation == TaskListService
        
        sig = inspect.signature(get_task_service)
        assert sig.return_annotation == TaskService
        
        sig = inspect.signature(get_current_user)
        assert sig.return_annotation == User

    @pytest.mark.asyncio
    async def test_auth_service_configuration(self, mock_db_session):
        """Test auth service configuration."""
        from src.config import settings
        
        # Call the dependency function
        auth_service = await get_auth_service(mock_db_session)
        
        # Test that auth service has correct configuration
        assert auth_service.secret_key == settings.secret_key
        assert auth_service.algorithm == settings.algorithm
        assert auth_service.access_token_expire_minutes == settings.access_token_expire_minutes

    @pytest.mark.asyncio
    async def test_notification_service_configuration(self):
        """Test notification service configuration."""
        # Call the dependency function
        notification_service = await get_notification_service()
        
        # Test that notification service is configured correctly
        assert hasattr(notification_service, 'email_enabled')
        assert notification_service.email_enabled is True

    def test_dependency_docstrings(self):
        """Test dependency function docstrings."""
        # Test that all functions have docstrings
        assert get_auth_service.__doc__ is not None
        assert "Get authentication service" in get_auth_service.__doc__
        
        assert get_notification_service.__doc__ is not None
        assert "Get notification service" in get_notification_service.__doc__
        
        assert get_task_list_service.__doc__ is not None
        assert "Get task list service" in get_task_list_service.__doc__
        
        assert get_task_service.__doc__ is not None
        assert "Get task service" in get_task_service.__doc__
        
        assert get_current_user.__doc__ is not None
        assert "Get current authenticated user" in get_current_user.__doc__

    def test_module_docstring(self):
        """Test module docstring."""
        import src.presentation.dependencies as deps_module
        
        # Test that module has docstring
        assert deps_module.__doc__ is not None
        assert "Common dependencies for FastAPI endpoints" in deps_module.__doc__

    def test_security_instance_properties(self):
        """Test security instance properties."""
        from fastapi.security import HTTPBearer
        
        # Test that security has correct properties
        assert isinstance(security, HTTPBearer)
        # Test that it has scheme_name
        assert hasattr(security, 'scheme_name')

    @pytest.mark.asyncio
    async def test_repository_instantiation_in_auth_service(self, mock_db_session):
        """Test repository instantiation in auth service."""
        # Call the dependency function
        auth_service = await get_auth_service(mock_db_session)
        
        # Test that auth service has user repository
        assert hasattr(auth_service, 'user_repository')
        assert auth_service.user_repository is not None

    @pytest.mark.asyncio
    async def test_repository_instantiation_in_task_list_service(self, mock_db_session):
        """Test repository instantiation in task list service."""
        mock_notification_service = Mock(spec=NotificationService)
        
        # Call the dependency function
        task_list_service = await get_task_list_service(
            db=mock_db_session,
            notification_service=mock_notification_service
        )
        
        # Test that task list service has repositories
        assert hasattr(task_list_service, 'task_list_repository')
        assert hasattr(task_list_service, 'task_repository')
        assert task_list_service.task_list_repository is not None
        assert task_list_service.task_repository is not None

    @pytest.mark.asyncio
    async def test_repository_instantiation_in_task_service(self, mock_db_session):
        """Test repository instantiation in task service."""
        mock_notification_service = Mock(spec=NotificationService)
        
        # Call the dependency function
        task_service = await get_task_service(
            db=mock_db_session,
            notification_service=mock_notification_service
        )
        
        # Test that task service has repositories
        assert hasattr(task_service, 'task_repository')
        assert hasattr(task_service, 'task_list_repository')
        assert hasattr(task_service, 'user_repository')
        assert task_service.task_repository is not None
        assert task_service.task_list_repository is not None
        assert task_service.user_repository is not None

    def test_dependency_injection_structure(self):
        """Test dependency injection structure."""
        from fastapi import Depends
        import inspect
        
        # Test that functions use Depends correctly
        sig = inspect.signature(get_auth_service)
        db_param = sig.parameters['db']
        assert db_param.default is not None
        
        sig = inspect.signature(get_current_user)
        token_param = sig.parameters['token']
        auth_service_param = sig.parameters['auth_service']
        assert token_param.default is not None
        assert auth_service_param.default is not None 