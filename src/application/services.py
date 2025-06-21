"""Application services for the Task Manager."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from passlib.context import CryptContext
from jose import JWTError, jwt

from src.domain.entities import Task, TaskList, TaskPriority, TaskStatus, User
from src.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    EmailAlreadyExistsError,
    TaskAssignmentError,
    TaskListNotFoundError,
    TaskNotFoundError,
    UserNotFoundError,
    UsernameAlreadyExistsError,
)
from src.domain.repositories import TaskListRepository, TaskRepository, UserRepository

from .dto import (
    EmailNotificationDTO,
    LoginDTO,
    PaginationDTO,
    TaskAssignmentDTO,
    TaskCreateDTO,
    TaskFilterDTO,
    TaskListCreateDTO,
    TaskListResponseDTO,
    TaskListUpdateDTO,
    TaskListWithTasksDTO,
    TaskResponseDTO,
    TaskStatusUpdateDTO,
    TaskUpdateDTO,
    TokenResponseDTO,
    UserCreateDTO,
    UserResponseDTO,
    UserUpdateDTO,
)

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


class TaskListService:
    """Service for task list operations."""

    def __init__(
        self,
        task_list_repository: TaskListRepository,
        task_repository: TaskRepository,
        notification_service: "NotificationService",
    ):
        self.task_list_repository = task_list_repository
        self.task_repository = task_repository
        self.notification_service = notification_service

    async def create_task_list(
        self, task_list_data: TaskListCreateDTO, owner_id: int
    ) -> TaskListResponseDTO:
        """Create a new task list."""
        task_list = TaskList(
            name=task_list_data.name,
            description=task_list_data.description,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
        )

        created_task_list = await self.task_list_repository.create(task_list)
        logger.info(f"Task list created: {created_task_list.id} by user {owner_id}")

        return TaskListResponseDTO(
            id=created_task_list.id,
            name=created_task_list.name,
            description=created_task_list.description,
            owner_id=created_task_list.owner_id,
            created_at=created_task_list.created_at,
            updated_at=created_task_list.updated_at,
            completion_percentage=0.0,
        )

    async def get_task_list(self, task_list_id: int, user_id: int) -> TaskListWithTasksDTO:
        """Get a task list with its tasks."""
        task_list = await self.task_list_repository.get_by_id(task_list_id)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)

        # Check if user has access to this task list
        if task_list.owner_id != user_id:
            raise AuthorizationError("You don't have access to this task list")

        # Get tasks for this list
        tasks = await self.task_repository.get_by_task_list(task_list_id)
        task_responses = []
        
        for task in tasks:
            task_responses.append(
                TaskResponseDTO(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    priority=task.priority,
                    task_list_id=task.task_list_id,
                    assigned_to=task.assigned_to,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    due_date=task.due_date,
                    is_overdue=task.is_overdue(),
                )
            )

        # Calculate completion percentage
        completion_percentage = 0.0
        if tasks:
            completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
            completion_percentage = (completed_tasks / len(tasks)) * 100.0

        return TaskListWithTasksDTO(
            id=task_list.id,
            name=task_list.name,
            description=task_list.description,
            owner_id=task_list.owner_id,
            created_at=task_list.created_at,
            updated_at=task_list.updated_at,
            completion_percentage=completion_percentage,
            tasks=task_responses,
        )

    async def update_task_list(
        self, task_list_id: int, update_data: TaskListUpdateDTO, user_id: int
    ) -> TaskListResponseDTO:
        """Update a task list."""
        task_list = await self.task_list_repository.get_by_id(task_list_id)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)

        if task_list.owner_id != user_id:
            raise AuthorizationError("You don't have access to this task list")

        # Update fields
        if update_data.name is not None:
            task_list.name = update_data.name
        if update_data.description is not None:
            task_list.description = update_data.description
        
        task_list.updated_at = datetime.utcnow()

        updated_task_list = await self.task_list_repository.update(task_list)
        logger.info(f"Task list updated: {task_list_id} by user {user_id}")

        return TaskListResponseDTO(
            id=updated_task_list.id,
            name=updated_task_list.name,
            description=updated_task_list.description,
            owner_id=updated_task_list.owner_id,
            created_at=updated_task_list.created_at,
            updated_at=updated_task_list.updated_at,
            completion_percentage=updated_task_list.calculate_completion_percentage(),
        )

    async def delete_task_list(self, task_list_id: int, user_id: int) -> bool:
        """Delete a task list."""
        task_list = await self.task_list_repository.get_by_id(task_list_id)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)

        if task_list.owner_id != user_id:
            raise AuthorizationError("You don't have access to this task list")

        result = await self.task_list_repository.delete(task_list_id)
        if result:
            logger.info(f"Task list deleted: {task_list_id} by user {user_id}")
        
        return result

    async def list_user_task_lists(
        self, user_id: int, pagination: PaginationDTO
    ) -> List[TaskListResponseDTO]:
        """List task lists for a user."""
        task_lists = await self.task_list_repository.get_by_owner(
            user_id, pagination.skip, pagination.limit
        )

        results = []
        for task_list in task_lists:
            # Get task count and completion percentage
            tasks = await self.task_repository.get_by_task_list(task_list.id)
            completion_percentage = 0.0
            if tasks:
                completed_tasks = sum(1 for task in tasks if task.status == TaskStatus.COMPLETED)
                completion_percentage = (completed_tasks / len(tasks)) * 100.0

            results.append(
                TaskListResponseDTO(
                    id=task_list.id,
                    name=task_list.name,
                    description=task_list.description,
                    owner_id=task_list.owner_id,
                    created_at=task_list.created_at,
                    updated_at=task_list.updated_at,
                    completion_percentage=completion_percentage,
                    task_count=len(tasks),
                )
            )

        return results


class TaskService:
    """Service for task operations."""

    def __init__(
        self,
        task_repository: TaskRepository,
        task_list_repository: TaskListRepository,
        user_repository: UserRepository,
        notification_service: "NotificationService",
    ):
        self.task_repository = task_repository
        self.task_list_repository = task_list_repository
        self.user_repository = user_repository
        self.notification_service = notification_service

    async def create_task(
        self, task_list_id: int, task_data: TaskCreateDTO, user_id: int
    ) -> TaskResponseDTO:
        """Create a new task."""
        # Verify task list exists and user has access
        task_list = await self.task_list_repository.get_by_id(task_list_id)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)

        if task_list.owner_id != user_id:
            raise AuthorizationError("You don't have access to this task list")

        # Verify assignee exists if provided
        if task_data.assigned_to:
            assignee = await self.user_repository.get_by_id(task_data.assigned_to)
            if not assignee:
                raise UserNotFoundError(task_data.assigned_to)
            if not assignee.is_active:
                raise TaskAssignmentError("Cannot assign task to inactive user")

        task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            task_list_id=task_list_id,
            assigned_to=task_data.assigned_to,
            due_date=task_data.due_date,
            created_at=datetime.utcnow(),
        )

        created_task = await self.task_repository.create(task)
        logger.info(f"Task created: {created_task.id} in list {task_list_id}")

        # Send notification if task is assigned
        if created_task.assigned_to:
            await self._send_assignment_notification(created_task)

        return TaskResponseDTO(
            id=created_task.id,
            title=created_task.title,
            description=created_task.description,
            status=created_task.status,
            priority=created_task.priority,
            task_list_id=created_task.task_list_id,
            assigned_to=created_task.assigned_to,
            created_at=created_task.created_at,
            updated_at=created_task.updated_at,
            due_date=created_task.due_date,
            is_overdue=created_task.is_overdue(),
        )

    async def get_task(self, task_id: int, user_id: int) -> TaskResponseDTO:
        """Get a task by ID."""
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        # Check if user has access (owner of task list or assignee)
        task_list = await self.task_list_repository.get_by_id(task.task_list_id)
        if task_list.owner_id != user_id and task.assigned_to != user_id:
            raise AuthorizationError("You don't have access to this task")

        # Get assignee info if available
        assignee = None
        if task.assigned_to:
            assignee_user = await self.user_repository.get_by_id(task.assigned_to)
            if assignee_user:
                assignee = UserResponseDTO(
                    id=assignee_user.id,
                    email=assignee_user.email,
                    username=assignee_user.username,
                    full_name=assignee_user.full_name,
                    is_active=assignee_user.is_active,
                    created_at=assignee_user.created_at,
                    updated_at=assignee_user.updated_at,
                )

        return TaskResponseDTO(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            task_list_id=task.task_list_id,
            assigned_to=task.assigned_to,
            created_at=task.created_at,
            updated_at=task.updated_at,
            due_date=task.due_date,
            is_overdue=task.is_overdue(),
            assignee=assignee,
        )

    async def update_task(
        self, task_id: int, update_data: TaskUpdateDTO, user_id: int
    ) -> TaskResponseDTO:
        """Update a task."""
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        # Check access
        task_list = await self.task_list_repository.get_by_id(task.task_list_id)
        if task_list.owner_id != user_id:
            raise AuthorizationError("You don't have access to this task")

        # Verify assignee if provided
        if update_data.assigned_to:
            assignee = await self.user_repository.get_by_id(update_data.assigned_to)
            if not assignee:
                raise UserNotFoundError(update_data.assigned_to)
            if not assignee.is_active:
                raise TaskAssignmentError("Cannot assign task to inactive user")

        # Update fields
        old_assignee = task.assigned_to
        if update_data.title is not None:
            task.title = update_data.title
        if update_data.description is not None:
            task.description = update_data.description
        if update_data.priority is not None:
            task.priority = update_data.priority
        if update_data.assigned_to is not None:
            task.assigned_to = update_data.assigned_to
        if update_data.due_date is not None:
            task.due_date = update_data.due_date
        
        task.updated_at = datetime.utcnow()

        updated_task = await self.task_repository.update(task)
        logger.info(f"Task updated: {task_id} by user {user_id}")

        # Send notification if assignment changed
        if old_assignee != updated_task.assigned_to and updated_task.assigned_to:
            await self._send_assignment_notification(updated_task)

        return TaskResponseDTO(
            id=updated_task.id,
            title=updated_task.title,
            description=updated_task.description,
            status=updated_task.status,
            priority=updated_task.priority,
            task_list_id=updated_task.task_list_id,
            assigned_to=updated_task.assigned_to,
            created_at=updated_task.created_at,
            updated_at=updated_task.updated_at,
            due_date=updated_task.due_date,
            is_overdue=updated_task.is_overdue(),
        )

    async def update_task_status(
        self, task_id: int, status_data: TaskStatusUpdateDTO, user_id: int
    ) -> TaskResponseDTO:
        """Update task status."""
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        # Check access (owner or assignee can update status)
        task_list = await self.task_list_repository.get_by_id(task.task_list_id)
        if task_list.owner_id != user_id and task.assigned_to != user_id:
            raise AuthorizationError("You don't have access to this task")

        updated_task = await self.task_repository.update_status(task_id, status_data.status)
        logger.info(f"Task status updated: {task_id} to {status_data.status} by user {user_id}")

        return TaskResponseDTO(
            id=updated_task.id,
            title=updated_task.title,
            description=updated_task.description,
            status=updated_task.status,
            priority=updated_task.priority,
            task_list_id=updated_task.task_list_id,
            assigned_to=updated_task.assigned_to,
            created_at=updated_task.created_at,
            updated_at=updated_task.updated_at,
            due_date=updated_task.due_date,
            is_overdue=updated_task.is_overdue(),
        )

    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete a task."""
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise TaskNotFoundError(task_id)

        # Check access
        task_list = await self.task_list_repository.get_by_id(task.task_list_id)
        if task_list.owner_id != user_id:
            raise AuthorizationError("You don't have access to this task")

        result = await self.task_repository.delete(task_id)
        if result:
            logger.info(f"Task deleted: {task_id} by user {user_id}")
        
        return result

    async def list_tasks(
        self,
        task_list_id: int,
        filters: TaskFilterDTO,
        pagination: PaginationDTO,
        user_id: int,
    ) -> List[TaskResponseDTO]:
        """List tasks with filters."""
        # Verify access to task list
        task_list = await self.task_list_repository.get_by_id(task_list_id)
        if not task_list:
            raise TaskListNotFoundError(task_list_id)

        if task_list.owner_id != user_id:
            raise AuthorizationError("You don't have access to this task list")

        tasks = await self.task_repository.get_by_task_list(
            task_list_id,
            pagination.skip,
            pagination.limit,
            filters.status,
            filters.priority,
        )

        # Apply additional filters
        if filters.overdue_only:
            tasks = [task for task in tasks if task.is_overdue()]
        
        if filters.assigned_to:
            tasks = [task for task in tasks if task.assigned_to == filters.assigned_to]

        results = []
        for task in tasks:
            results.append(
                TaskResponseDTO(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    priority=task.priority,
                    task_list_id=task.task_list_id,
                    assigned_to=task.assigned_to,
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    due_date=task.due_date,
                    is_overdue=task.is_overdue(),
                )
            )

        return results

    async def _send_assignment_notification(self, task: Task) -> None:
        """Send notification when task is assigned."""
        if not task.assigned_to:
            return

        assignee = await self.user_repository.get_by_id(task.assigned_to)
        if not assignee:
            return

        notification = EmailNotificationDTO(
            to_email=assignee.email,
            subject=f"Task Assigned: {task.title}",
            body=f"You have been assigned a new task: {task.title}\n\nDescription: {task.description or 'No description'}",
            task_id=task.id,
            user_id=assignee.id,
        )

        await self.notification_service.send_email_notification(notification)


class NotificationService:
    """Service for handling notifications."""

    def __init__(self, email_enabled: bool = True):
        self.email_enabled = email_enabled

    async def send_email_notification(self, notification: EmailNotificationDTO) -> bool:
        """Send email notification (simulated)."""
        if not self.email_enabled:
            logger.info("Email notifications are disabled")
            return False

        # Simulate email sending
        logger.info(
            f"Sending email to {notification.to_email}: {notification.subject}"
        )
        
        # In a real implementation, this would integrate with an email service
        # like SendGrid, AWS SES, or SMTP server
        
        return True 