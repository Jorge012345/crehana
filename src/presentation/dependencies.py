"""Common dependencies for FastAPI endpoints."""

from fastapi import Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth_service import AuthService
from src.application.services import TaskListService, TaskService, NotificationService
from src.config import settings
from src.domain.entities import User
from src.infrastructure.database import get_db_session
from src.infrastructure.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyTaskListRepository,
    SQLAlchemyTaskRepository,
)

# Initialize security
security = HTTPBearer()


async def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    """Get authentication service."""
    user_repo = SQLAlchemyUserRepository(db)
    return AuthService(
        user_repository=user_repo,
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )


async def get_notification_service() -> NotificationService:
    """Get notification service."""
    return NotificationService(email_enabled=True)


async def get_task_list_service(
    db: AsyncSession = Depends(get_db_session),
    notification_service: NotificationService = Depends(get_notification_service),
) -> TaskListService:
    """Get task list service."""
    task_list_repo = SQLAlchemyTaskListRepository(db)
    task_repo = SQLAlchemyTaskRepository(db)
    return TaskListService(
        task_list_repository=task_list_repo,
        task_repository=task_repo,
        notification_service=notification_service,
    )


async def get_task_service(
    db: AsyncSession = Depends(get_db_session),
    notification_service: NotificationService = Depends(get_notification_service),
) -> TaskService:
    """Get task service."""
    task_repo = SQLAlchemyTaskRepository(db)
    task_list_repo = SQLAlchemyTaskListRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    return TaskService(
        task_repository=task_repo,
        task_list_repository=task_list_repo,
        user_repository=user_repo,
        notification_service=notification_service,
    )


async def get_current_user(
    token: str = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Get current authenticated user."""
    return await auth_service.get_current_user(token.credentials) 