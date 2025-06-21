"""Domain entities for the Task Manager application."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class User(BaseModel):
    """User domain entity."""

    id: Optional[int] = None
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    hashed_password: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class TaskList(BaseModel):
    """Task list domain entity."""

    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    owner_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Relationships
    tasks: List["Task"] = Field(default_factory=list)
    owner: Optional[User] = None

    def calculate_completion_percentage(self) -> float:
        """Calculate completion percentage based on completed tasks."""
        if not self.tasks:
            return 0.0
        
        completed_tasks = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        return (completed_tasks / len(self.tasks)) * 100.0

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class Task(BaseModel):
    """Task domain entity."""

    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    task_list_id: int
    assigned_to: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    
    # Relationships
    task_list: Optional[TaskList] = None
    assignee: Optional[User] = None

    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date and self.status != TaskStatus.COMPLETED

    def can_be_assigned_to(self, user_id: int) -> bool:
        """Check if task can be assigned to a specific user."""
        # Business rule: Task can only be assigned to active users
        # This would need to be validated at the service layer
        return user_id > 0

    def mark_as_completed(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def change_priority(self, new_priority: TaskPriority) -> None:
        """Change task priority."""
        self.priority = new_priority
        self.updated_at = datetime.utcnow()

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# Update forward references
TaskList.model_rebuild()
Task.model_rebuild() 