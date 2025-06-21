"""Pytest configuration and common fixtures."""

import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from src.config import settings
from src.infrastructure.database import Base, get_db_session
from src.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def postgres_container():
    """Start PostgreSQL container for testing."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="session")
async def test_db_engine(postgres_container):
    """Create test database engine."""
    # Get connection URL and ensure it uses asyncpg driver
    database_url = postgres_container.get_connection_url()
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    
    engine = create_async_engine(database_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_db_engine):
    """Create database session for testing."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """Create test client with database session override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db_session] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session):
    """Create a test user."""
    from src.domain.entities import User
    from src.infrastructure.repositories import SQLAlchemyUserRepository
    from src.application.auth_service import AuthService
    from src.application.dto import UserCreateDTO
    
    user_repo = SQLAlchemyUserRepository(db_session)
    auth_service = AuthService(
        user_repository=user_repo,
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )
    
    user_data = UserCreateDTO(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        password="testpassword123"
    )
    
    user = await auth_service.register_user(user_data)
    await db_session.commit()
    
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user, db_session):
    """Create authentication headers for test user."""
    from src.infrastructure.repositories import SQLAlchemyUserRepository
    from src.application.auth_service import AuthService
    from src.application.dto import LoginDTO
    
    user_repo = SQLAlchemyUserRepository(db_session)
    auth_service = AuthService(
        user_repository=user_repo,
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )
    
    login_data = LoginDTO(email="test@example.com", password="testpassword123")
    token_response = await auth_service.authenticate_user(login_data)
    
    return {"Authorization": f"Bearer {token_response.access_token}"} 