"""Repository implementations using SQLAlchemy."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities import Task, TaskList, TaskPriority, TaskStatus, User
from src.domain.repositories import TaskListRepository, TaskRepository, UserRepository

from .database import TaskListModel, TaskModel, UserModel


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: UserModel) -> User:
        """Convert SQLAlchemy model to domain entity."""
        return User(
            id=model.id,
            email=model.email,
            username=model.username,
            full_name=model.full_name,
            hashed_password=model.hashed_password,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        """Convert domain entity to SQLAlchemy model."""
        return UserModel(
            id=entity.id,
            email=entity.email,
            username=entity.username,
            full_name=entity.full_name,
            hashed_password=entity.hashed_password,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, user: User) -> User:
        """Create a new user."""
        model = self._to_model(user)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, user: User) -> User:
        """Update user."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user.id)
        )
        model = result.scalar_one()
        
        model.email = user.email
        model.username = user.username
        model.full_name = user.full_name
        model.hashed_password = user.hashed_password
        model.is_active = user.is_active
        model.updated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, user_id: int) -> bool:
        """Delete user."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            return True
        return False

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        result = await self.session.execute(
            select(UserModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]


class SQLAlchemyTaskListRepository(TaskListRepository):
    """SQLAlchemy implementation of TaskListRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: TaskListModel) -> TaskList:
        """Convert SQLAlchemy model to domain entity."""
        task_list = TaskList(
            id=model.id,
            name=model.name,
            description=model.description,
            owner_id=model.owner_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
        
        # Only convert tasks if they are explicitly loaded to avoid lazy loading issues
        try:
            # Check if tasks relationship is loaded without triggering lazy load
            from sqlalchemy.inspection import inspect
            state = inspect(model)
            if 'tasks' in state.loaded_attributes and model.tasks is not None:
                tasks = []
                for task_model in model.tasks:
                    task = Task(
                        id=task_model.id,
                        title=task_model.title,
                        description=task_model.description,
                        status=task_model.status,
                        priority=task_model.priority,
                        task_list_id=task_model.task_list_id,
                        assigned_to=task_model.assigned_to,
                        created_at=task_model.created_at,
                        updated_at=task_model.updated_at,
                        due_date=task_model.due_date,
                    )
                    tasks.append(task)
                task_list.tasks = tasks
        except Exception:
            # If there's any issue with accessing tasks, just skip it
            pass
        
        return task_list

    def _to_model(self, entity: TaskList) -> TaskListModel:
        """Convert domain entity to SQLAlchemy model."""
        return TaskListModel(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            owner_id=entity.owner_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    async def create(self, task_list: TaskList) -> TaskList:
        """Create a new task list."""
        model = self._to_model(task_list)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, task_list_id: int) -> Optional[TaskList]:
        """Get task list by ID."""
        result = await self.session.execute(
            select(TaskListModel)
            .options(selectinload(TaskListModel.tasks))
            .where(TaskListModel.id == task_list_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_owner(
        self, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[TaskList]:
        """Get task lists by owner."""
        result = await self.session.execute(
            select(TaskListModel)
            .where(TaskListModel.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def update(self, task_list: TaskList) -> TaskList:
        """Update task list."""
        result = await self.session.execute(
            select(TaskListModel).where(TaskListModel.id == task_list.id)
        )
        model = result.scalar_one()
        
        model.name = task_list.name
        model.description = task_list.description
        model.updated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, task_list_id: int) -> bool:
        """Delete task list."""
        result = await self.session.execute(
            select(TaskListModel).where(TaskListModel.id == task_list_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            return True
        return False

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[TaskList]:
        """List all task lists with pagination."""
        result = await self.session.execute(
            select(TaskListModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]


class SQLAlchemyTaskRepository(TaskRepository):
    """SQLAlchemy implementation of TaskRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: TaskModel) -> Task:
        """Convert SQLAlchemy model to domain entity."""
        return Task(
            id=model.id,
            title=model.title,
            description=model.description,
            status=model.status,
            priority=model.priority,
            task_list_id=model.task_list_id,
            assigned_to=model.assigned_to,
            created_at=model.created_at,
            updated_at=model.updated_at,
            due_date=model.due_date,
        )

    def _to_model(self, entity: Task) -> TaskModel:
        """Convert domain entity to SQLAlchemy model."""
        return TaskModel(
            id=entity.id,
            title=entity.title,
            description=entity.description,
            status=entity.status,
            priority=entity.priority,
            task_list_id=entity.task_list_id,
            assigned_to=entity.assigned_to,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            due_date=entity.due_date,
        )

    async def create(self, task: Task) -> Task:
        """Create a new task."""
        model = self._to_model(task)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_task_list(
        self,
        task_list_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
    ) -> List[Task]:
        """Get tasks by task list with optional filters."""
        query = select(TaskModel).where(TaskModel.task_list_id == task_list_id)
        
        if status:
            query = query.where(TaskModel.status == status)
        if priority:
            query = query.where(TaskModel.priority == priority)
            
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def get_by_assignee(
        self, assignee_id: int, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks by assignee."""
        result = await self.session.execute(
            select(TaskModel)
            .where(TaskModel.assigned_to == assignee_id)
            .offset(skip)
            .limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def update(self, task: Task) -> Task:
        """Update task."""
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task.id)
        )
        model = result.scalar_one()
        
        model.title = task.title
        model.description = task.description
        model.status = task.status
        model.priority = task.priority
        model.assigned_to = task.assigned_to
        model.due_date = task.due_date
        model.updated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, task_id: int) -> bool:
        """Delete task."""
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one_or_none()
        if model:
            await self.session.delete(model)
            return True
        return False

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """List all tasks with pagination."""
        result = await self.session.execute(
            select(TaskModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def update_status(self, task_id: int, status: TaskStatus) -> Task:
        """Update task status."""
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one()
        
        model.status = status
        model.updated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def assign_to_user(self, task_id: int, user_id: int) -> Task:
        """Assign task to user."""
        result = await self.session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one()
        
        model.assigned_to = user_id
        model.updated_at = datetime.utcnow()
        
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model) 