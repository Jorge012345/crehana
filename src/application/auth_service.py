"""Authentication service for the Task Manager."""

import logging
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.domain.entities import User
from src.domain.exceptions import (
    AuthenticationError,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
)
from src.domain.repositories import UserRepository

from .dto import LoginDTO, TokenResponseDTO, UserCreateDTO, UserResponseDTO

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication and authorization service."""

    def __init__(
        self,
        user_repository: UserRepository,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
    ):
        self.user_repository = user_repository
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _hash_password(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, data: dict) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    async def register_user(self, user_data: UserCreateDTO) -> UserResponseDTO:
        """Register a new user."""
        # Check if email already exists
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise EmailAlreadyExistsError(user_data.email)

        # Check if username already exists
        existing_username = await self.user_repository.get_by_username(user_data.username)
        if existing_username:
            raise UsernameAlreadyExistsError(user_data.username)

        # Create user
        hashed_password = self._hash_password(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            created_at=datetime.utcnow(),
        )

        created_user = await self.user_repository.create(user)
        logger.info(f"User registered: {created_user.email}")

        return UserResponseDTO(
            id=created_user.id,
            email=created_user.email,
            username=created_user.username,
            full_name=created_user.full_name,
            is_active=created_user.is_active,
            created_at=created_user.created_at,
            updated_at=created_user.updated_at,
        )

    async def authenticate_user(self, login_data: LoginDTO) -> TokenResponseDTO:
        """Authenticate user and return token."""
        # Try to find user by email first, then by username
        user = await self.user_repository.get_by_email(login_data.email)
        if not user:
            user = await self.user_repository.get_by_username(login_data.email)

        if not user or not self._verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        # Create access token
        access_token = self._create_access_token(data={"sub": str(user.id)})
        
        logger.info(f"User authenticated: {user.email}")
        
        return TokenResponseDTO(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60,
        )

    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise AuthenticationError("Invalid token")
        except JWTError:
            raise AuthenticationError("Invalid token")

        user = await self.user_repository.get_by_id(int(user_id))
        if user is None:
            raise AuthenticationError("User not found")

        return user 