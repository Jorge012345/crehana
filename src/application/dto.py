"""Data Transfer Objects for the application layer."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.domain.entities import TaskPriority, TaskStatus


class UserCreateDTO(BaseModel):
    """DTO for creating a user."""

    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class UserResponseDTO(BaseModel):
    """DTO for user response."""

    id: int
    email: str
    username: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]


class UserUpdateDTO(BaseModel):
    """DTO for updating a user."""

    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class LoginDTO(BaseModel):
    """DTO for user login."""

    email: str = Field(..., description="User email or username")
    password: str = Field(..., min_length=1)


class TokenResponseDTO(BaseModel):
    """DTO for token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TaskListCreateDTO(BaseModel):
    """DTO for creating a task list."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TaskListUpdateDTO(BaseModel):
    """DTO for updating a task list."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TaskListResponseDTO(BaseModel):
    """DTO for task list response."""

    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    completion_percentage: float
    task_count: int = 0


class TaskCreateDTO(BaseModel):
    """DTO for creating a task."""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    task_list_id: int = Field(..., description="ID of the task list")
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskUpdateDTO(BaseModel):
    """DTO for updating a task."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None


class TaskResponseDTO(BaseModel):
    """DTO for task response."""

    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    task_list_id: int
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    due_date: Optional[datetime]
    is_overdue: bool = False
    assignee: Optional[UserResponseDTO] = None


class TaskStatusUpdateDTO(BaseModel):
    """DTO for updating task status."""

    status: TaskStatus


class TaskAssignmentDTO(BaseModel):
    """DTO for task assignment."""

    assigned_to: int


class TaskListWithTasksDTO(BaseModel):
    """DTO for task list with tasks."""

    id: int
    name: str
    description: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    completion_percentage: float
    tasks: List[TaskResponseDTO] = Field(default_factory=list)


class PaginationDTO(BaseModel):
    """DTO for pagination parameters."""

    skip: int = Field(0, ge=0, description="Number of items to skip")
    limit: int = Field(100, ge=1, le=1000, description="Number of items to return")


class TaskFilterDTO(BaseModel):
    """DTO for task filtering."""

    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None
    overdue_only: bool = False


class EmailNotificationDTO(BaseModel):
    """DTO for email notifications."""

    to_email: str
    subject: str
    body: str
    task_id: Optional[int] = None
    user_id: Optional[int] = None 