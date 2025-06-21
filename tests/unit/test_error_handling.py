"""
Tests to improve exception handlers coverage (lines 22-35).
"""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.presentation.exception_handlers import add_exception_handlers
from src.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleViolationError,
    EntityNotFoundError,
    ValidationError,
    TaskManagerException
)


class TestExceptionHandlersCoverage:
    """Tests to cover exception handlers lines 22-35."""

    @pytest.fixture
    def app_with_handlers(self):
        """Create FastAPI app with exception handlers."""
        app = FastAPI()
        add_exception_handlers(app)
        return app

    @pytest.mark.asyncio
    async def test_entity_not_found_error_handler(self, app_with_handlers):
        """Test EntityNotFoundError handler (line 24-25)."""
        request = Mock()
        exc = EntityNotFoundError("Entity not found", entity_id=1)
        
        # Get the handler function
        handler = app_with_handlers.exception_handlers[TaskManagerException]
        
        # Call the handler
        response = await handler(request, exc)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        assert "Entity not found" in str(response.body)

    @pytest.mark.asyncio
    async def test_authentication_error_handler(self, app_with_handlers):
        """Test AuthenticationError handler (line 26-27)."""
        request = Mock()
        exc = AuthenticationError("Authentication failed")
        
        # Get the handler function
        handler = app_with_handlers.exception_handlers[TaskManagerException]
        
        # Call the handler
        response = await handler(request, exc)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 401
        assert "Authentication failed" in str(response.body)

    @pytest.mark.asyncio
    async def test_authorization_error_handler(self, app_with_handlers):
        """Test AuthorizationError handler (line 28-29)."""
        request = Mock()
        exc = AuthorizationError("Not authorized")
        
        # Get the handler function
        handler = app_with_handlers.exception_handlers[TaskManagerException]
        
        # Call the handler
        response = await handler(request, exc)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 403
        assert "Not authorized" in str(response.body)

    @pytest.mark.asyncio
    async def test_validation_error_handler(self, app_with_handlers):
        """Test ValidationError handler (line 30-31)."""
        request = Mock()
        exc = ValidationError("Validation failed")
        
        # Get the handler function
        handler = app_with_handlers.exception_handlers[TaskManagerException]
        
        # Call the handler
        response = await handler(request, exc)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        assert "Validation failed" in str(response.body)

    @pytest.mark.asyncio
    async def test_business_rule_violation_error_handler(self, app_with_handlers):
        """Test BusinessRuleViolationError handler (line 32-33)."""
        request = Mock()
        exc = BusinessRuleViolationError("Business rule violated")
        
        # Get the handler function
        handler = app_with_handlers.exception_handlers[TaskManagerException]
        
        # Call the handler
        response = await handler(request, exc)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 409
        assert "Business rule violated" in str(response.body)

    @pytest.mark.asyncio
    async def test_generic_task_manager_exception_handler(self, app_with_handlers):
        """Test generic TaskManagerException handler (line 22-23)."""
        request = Mock()
        exc = TaskManagerException("Generic error")
        
        # Get the handler function
        handler = app_with_handlers.exception_handlers[TaskManagerException]
        
        # Call the handler
        response = await handler(request, exc)
        
        # Verify response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400  # Default HTTP_400_BAD_REQUEST
        assert "Generic error" in str(response.body)

    @pytest.mark.asyncio
    async def test_json_response_content_structure(self, app_with_handlers):
        """Test that JSON response has correct structure (lines 34-39)."""
        request = Mock()
        exc = AuthenticationError("Auth error")
        
        # Get the handler function
        handler = app_with_handlers.exception_handlers[TaskManagerException]
        
        # Call the handler
        response = await handler(request, exc)
        
        # Verify response structure
        assert isinstance(response, JSONResponse)
        
        # Parse the response body to check content structure
        import json
        content = json.loads(response.body.decode())
        
        # Verify the content has the expected keys (lines 36-38)
        assert "message" in content
        assert "error_code" in content
        assert content["message"] == "Auth error"
        assert content["error_code"] == "AUTHENTICATION_ERROR"

    def test_add_exception_handlers_function(self):
        """Test that add_exception_handlers function works correctly."""
        app = FastAPI()
        
        # Get initial handler count (FastAPI may have default handlers)
        initial_count = len(app.exception_handlers)
        
        # Add handlers
        add_exception_handlers(app)
        
        # Verify handler was added
        assert len(app.exception_handlers) > initial_count
        assert TaskManagerException in app.exception_handlers

    @pytest.mark.asyncio
    async def test_all_status_code_branches(self, app_with_handlers):
        """Test all status code branches to ensure 100% coverage."""
        request = Mock()
        handler = app_with_handlers.exception_handlers[TaskManagerException]
        
        # Test all exception types and their status codes
        test_cases = [
            (EntityNotFoundError("Not found", entity_id=1), 404),
            (AuthenticationError("Auth failed"), 401),
            (AuthorizationError("Not authorized"), 403),
            (ValidationError("Validation failed"), 422),
            (BusinessRuleViolationError("Rule violated"), 409),
            (TaskManagerException("Generic error"), 400),  # Default case
        ]
        
        for exc, expected_status in test_cases:
            response = await handler(request, exc)
            assert response.status_code == expected_status
            
            # Verify content structure
            import json
            content = json.loads(response.body.decode())
            assert "message" in content
            assert "error_code" in content
            assert content["message"] == exc.message
            assert content["error_code"] == exc.error_code 