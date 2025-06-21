"""Custom exceptions for the Task Manager domain."""


class TaskManagerException(Exception):
    """Base exception for Task Manager application."""

    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class EntityNotFoundError(TaskManagerException):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: str | int):
        message = f"{entity_type} with id {entity_id} not found"
        super().__init__(message, "ENTITY_NOT_FOUND")


class ValidationError(TaskManagerException):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class AuthenticationError(TaskManagerException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(TaskManagerException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class DuplicateEntityError(TaskManagerException):
    """Raised when trying to create a duplicate entity."""

    def __init__(self, entity_type: str, field: str, value: str):
        message = f"{entity_type} with {field} '{value}' already exists"
        super().__init__(message, "DUPLICATE_ENTITY")


class BusinessRuleViolationError(TaskManagerException):
    """Raised when a business rule is violated."""

    def __init__(self, message: str):
        super().__init__(message, "BUSINESS_RULE_VIOLATION")


class InvalidOperationError(TaskManagerException):
    """Raised when an invalid operation is attempted."""

    def __init__(self, message: str):
        super().__init__(message, "INVALID_OPERATION")


# Specific domain exceptions
class TaskListNotFoundError(EntityNotFoundError):
    """Raised when a task list is not found."""

    def __init__(self, task_list_id: int):
        super().__init__("TaskList", task_list_id)


class TaskNotFoundError(EntityNotFoundError):
    """Raised when a task is not found."""

    def __init__(self, task_id: int):
        super().__init__("Task", task_id)


class UserNotFoundError(EntityNotFoundError):
    """Raised when a user is not found."""

    def __init__(self, user_id: int):
        super().__init__("User", user_id)


class EmailAlreadyExistsError(DuplicateEntityError):
    """Raised when trying to register with an existing email."""

    def __init__(self, email: str):
        super().__init__("User", "email", email)


class UsernameAlreadyExistsError(DuplicateEntityError):
    """Raised when trying to register with an existing username."""

    def __init__(self, username: str):
        super().__init__("User", "username", username)


class TaskAssignmentError(BusinessRuleViolationError):
    """Raised when task assignment violates business rules."""

    def __init__(self, message: str):
        super().__init__(f"Task assignment error: {message}")


class TaskStatusTransitionError(BusinessRuleViolationError):
    """Raised when invalid task status transition is attempted."""

    def __init__(self, current_status: str, new_status: str):
        message = f"Invalid status transition from {current_status} to {new_status}"
        super().__init__(message) 