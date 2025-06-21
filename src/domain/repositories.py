"""Repository interfaces for the Task Manager domain."""

from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import Task, TaskList, TaskPriority, TaskStatus, User


class UserRepository(ABC):
    """Abstract repository for User entities."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update user."""
        pass

    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Delete user."""
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        pass


class TaskListRepository(ABC):
    """Abstract repository for TaskList entities."""

    @abstractmethod
    async def create(self, task_list: TaskList) -> TaskList:
        """Create a new task list."""
        pass

    @abstractmethod
    async def get_by_id(self, task_list_id: int) -> Optional[TaskList]:
        """Get task list by ID."""
        pass

    @abstractmethod
    async def get_by_owner(
        self, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[TaskList]:
        """Get task lists by owner."""
        pass

    @abstractmethod
    async def update(self, task_list: TaskList) -> TaskList:
        """Update task list."""
        pass

    @abstractmethod
    async def delete(self, task_list_id: int) -> bool:
        """Delete task list."""
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[TaskList]:
        """List all task lists with pagination."""
        pass


class TaskRepository(ABC):
    """Abstract repository for Task entities."""

    @abstractmethod
    async def create(self, task: Task) -> Task:
        """Create a new task."""
        pass

    @abstractmethod
    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        pass

    @abstractmethod
    async def get_by_task_list(
        self,
        task_list_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
    ) -> List[Task]:
        """Get tasks by task list with optional filters."""
        pass

    @abstractmethod
    async def get_by_assignee(
        self, assignee_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks by assignee."""
        pass

    @abstractmethod
    async def update(self, task: Task) -> Task:
        """Update task."""
        pass

    @abstractmethod
    async def delete(self, task_id: int) -> bool:
        """Delete task."""
        pass

    @abstractmethod
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """List all tasks with pagination."""
        pass

    @abstractmethod
    async def update_status(self, task_id: int, status: TaskStatus) -> Task:
        """Update task status."""
        pass

    @abstractmethod
    async def assign_to_user(self, task_id: int, user_id: int) -> Task:
        """Assign task to user."""
        pass 