"""Exception handlers for FastAPI application."""

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from src.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    EntityNotFoundError,
    TaskManagerException,
    ValidationError,
)


def add_exception_handlers(app: FastAPI) -> None:
    """Add exception handlers to FastAPI app."""

    @app.exception_handler(TaskManagerException)
    async def task_manager_exception_handler(request, exc: TaskManagerException):
        """Handle custom task manager exceptions."""
        status_code = status.HTTP_400_BAD_REQUEST
        
        if isinstance(exc, EntityNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(exc, AuthenticationError):
            status_code = status.HTTP_401_UNAUTHORIZED
        elif isinstance(exc, AuthorizationError):
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exc, ValidationError):
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(exc, BusinessRuleViolationError):
            status_code = status.HTTP_409_CONFLICT
        
        return JSONResponse(
            status_code=status_code,
            content={
                "message": exc.message,
                "error_code": exc.error_code,
            }
        ) 