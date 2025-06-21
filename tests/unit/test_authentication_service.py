"""Simple tests for AuthService to increase coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.application.services import AuthService
from src.application.dto import UserCreateDTO, LoginDTO
from src.domain.entities import User
from src.domain.exceptions import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    AuthenticationError,
)


class TestAuthServiceSimple:
    """Simple tests for AuthService."""
    
    @pytest.fixture
    def auth_service(self):
        """Create AuthService instance."""
        user_repo = AsyncMock()
        return AuthService(
            user_repository=user_repo,
            secret_key="test-secret-key",
            algorithm="HS256",
            access_token_expire_minutes=30
        )

    @pytest.fixture
    def sample_user(self):
        """Create a sample user."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password="$2b$12$hash",
            is_active=True,
            created_at=datetime.utcnow()
        )

    def test_hash_password(self, auth_service):
        """Test password hashing."""
        password = "testpassword123"
        hashed = auth_service._hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20  # Bcrypt hashes are long
        assert hashed.startswith("$2b$")

    def test_verify_password(self, auth_service):
        """Test password verification."""
        password = "testpassword123"
        hashed = auth_service._hash_password(password)
        
        # Correct password
        assert auth_service._verify_password(password, hashed) is True
        
        # Wrong password
        assert auth_service._verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self, auth_service):
        """Test JWT token creation."""
        data = {"sub": "1", "role": "user"}
        token = auth_service._create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are long
        assert "." in token  # JWT tokens have dots

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, sample_user):
        """Test successful user registration."""
        # Mock repository
        auth_service.user_repository.get_by_email.return_value = None
        auth_service.user_repository.get_by_username.return_value = None
        auth_service.user_repository.create.return_value = sample_user
        
        user_data = UserCreateDTO(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="testpassword123"
        )
        
        result = await auth_service.register_user(user_data)
        
        assert result.id == 1
        assert result.email == "test@example.com"
        assert result.username == "testuser"
        assert result.full_name == "Test User"
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, auth_service, sample_user):
        """Test user registration with existing email."""
        # Mock repository
        auth_service.user_repository.get_by_email.return_value = sample_user
        
        user_data = UserCreateDTO(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="testpassword123"
        )
        
        with pytest.raises(EmailAlreadyExistsError):
            await auth_service.register_user(user_data)

    @pytest.mark.asyncio
    async def test_register_user_username_exists(self, auth_service, sample_user):
        """Test user registration with existing username."""
        # Mock repository
        auth_service.user_repository.get_by_email.return_value = None
        auth_service.user_repository.get_by_username.return_value = sample_user
        
        user_data = UserCreateDTO(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="testpassword123"
        )
        
        with pytest.raises(UsernameAlreadyExistsError):
            await auth_service.register_user(user_data)

    @pytest.mark.asyncio
    async def test_authenticate_user_by_email_success(self, auth_service):
        """Test successful authentication by email."""
        # Create user with hashed password
        password = "testpassword123"
        hashed_password = auth_service._hash_password(password)
        
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Mock repository
        auth_service.user_repository.get_by_email.return_value = user
        
        login_data = LoginDTO(
            email="test@example.com",
            password=password
        )
        
        result = await auth_service.authenticate_user(login_data)
        
        assert result.access_token is not None
        assert result.token_type == "bearer"
        assert result.expires_in == 1800  # 30 minutes * 60 seconds

    @pytest.mark.asyncio
    async def test_authenticate_user_by_username_success(self, auth_service):
        """Test successful authentication by username."""
        # Create user with hashed password
        password = "testpassword123"
        hashed_password = auth_service._hash_password(password)
        
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Mock repository - no email match, but username match
        auth_service.user_repository.get_by_email.return_value = None
        auth_service.user_repository.get_by_username.return_value = user
        
        login_data = LoginDTO(
            email="testuser",  # Using username in email field
            password=password
        )
        
        result = await auth_service.authenticate_user(login_data)
        
        assert result.access_token is not None
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_credentials(self, auth_service):
        """Test authentication with invalid credentials."""
        # Mock repository - user not found
        auth_service.user_repository.get_by_email.return_value = None
        auth_service.user_repository.get_by_username.return_value = None
        
        login_data = LoginDTO(
            email="nonexistent@example.com",
            password="somepassword"
        )
        
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(login_data)

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service):
        """Test authentication with wrong password."""
        # Create user with hashed password
        password = "testpassword123"
        hashed_password = auth_service._hash_password(password)
        
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Mock repository
        auth_service.user_repository.get_by_email.return_value = user
        
        login_data = LoginDTO(
            email="test@example.com",
            password="wrongpassword"
        )
        
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(login_data)

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive_account(self, auth_service):
        """Test authentication with inactive account."""
        # Create inactive user
        password = "testpassword123"
        hashed_password = auth_service._hash_password(password)
        
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password=hashed_password,
            is_active=False,  # Inactive
            created_at=datetime.utcnow()
        )
        
        # Mock repository
        auth_service.user_repository.get_by_email.return_value = user
        
        login_data = LoginDTO(
            email="test@example.com",
            password=password
        )
        
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(login_data)

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, auth_service, sample_user):
        """Test getting current user from valid token."""
        # Create a token
        token = auth_service._create_access_token({"sub": "1"})
        
        # Mock repository
        auth_service.user_repository.get_by_id.return_value = sample_user
        
        result = await auth_service.get_current_user(token)
        
        assert result.id == 1
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, auth_service):
        """Test getting current user with invalid token."""
        with pytest.raises(AuthenticationError):
            await auth_service.get_current_user("invalid-token")

    @pytest.mark.asyncio
    async def test_get_current_user_no_user_id(self, auth_service):
        """Test getting current user with token missing user ID."""
        # Create token without 'sub' claim
        token = auth_service._create_access_token({"role": "user"})
        
        with pytest.raises(AuthenticationError):
            await auth_service.get_current_user(token)

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, auth_service):
        """Test getting current user when user doesn't exist."""
        # Create a token
        token = auth_service._create_access_token({"sub": "999"})
        
        # Mock repository - user not found
        auth_service.user_repository.get_by_id.return_value = None
        
        with pytest.raises(AuthenticationError):
            await auth_service.get_current_user(token) 