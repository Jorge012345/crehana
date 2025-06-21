"""
Tests for the presentation layer.
Includes tests for routers, dependencies, and exception handlers.
"""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI

from src.presentation.dependencies import get_current_user
from src.presentation.exception_handlers import add_exception_handlers
from src.presentation.routers import auth, task_lists, tasks


class TestRouters:
    """Tests for API routers."""

    def test_auth_router_configuration(self):
        """Test auth router configuration."""
        assert hasattr(auth, 'router')
        assert len(auth.router.routes) > 0
        
        # Check that router has expected routes
        route_paths = [route.path for route in auth.router.routes]
        assert any('/register' in path for path in route_paths)
        assert any('/login' in path for path in route_paths)

    def test_task_lists_router_configuration(self):
        """Test task lists router configuration."""
        assert hasattr(task_lists, 'router')
        assert len(task_lists.router.routes) > 0
        
        # Check that router has routes
        route_paths = [route.path for route in task_lists.router.routes]
        assert len(route_paths) > 0

    def test_tasks_router_configuration(self):
        """Test tasks router configuration."""
        assert hasattr(tasks, 'router')
        assert len(tasks.router.routes) > 0
        
        # Check that router has routes
        route_paths = [route.path for route in tasks.router.routes]
        assert len(route_paths) > 0

    def test_router_imports(self):
        """Test that all routers can be imported."""
        # Test imports work without errors
        from src.presentation.routers import auth as auth_router
        from src.presentation.routers import task_lists as task_lists_router
        from src.presentation.routers import tasks as tasks_router
        
        assert auth_router is not None
        assert task_lists_router is not None
        assert tasks_router is not None


class TestDependencies:
    """Tests for dependency injection functions."""

    def test_get_current_user_function_exists(self):
        """Test that get_current_user function exists."""
        assert callable(get_current_user)

    def test_dependencies_module_import(self):
        """Test that dependencies module can be imported."""
        from src.presentation import dependencies
        
        assert hasattr(dependencies, 'get_current_user')


class TestExceptionHandlers:
    """Tests for exception handlers."""

    def test_add_exception_handlers_function(self):
        """Test add_exception_handlers function."""
        assert callable(add_exception_handlers)

    def test_add_exception_handlers_to_app(self):
        """Test adding exception handlers to FastAPI app."""
        app = FastAPI()
        
        # Should not raise an exception
        add_exception_handlers(app)
        
        # App should have exception handlers registered
        assert len(app.exception_handlers) > 0

    def test_exception_handlers_module_import(self):
        """Test that exception handlers module can be imported."""
        from src.presentation import exception_handlers
        
        assert hasattr(exception_handlers, 'add_exception_handlers')


class TestPresentationLayer:
    """Tests for overall presentation layer functionality."""

    def test_presentation_module_imports(self):
        """Test that all presentation modules can be imported."""
        from src.presentation import dependencies
        from src.presentation import exception_handlers
        from src.presentation import routers
        
        assert dependencies is not None
        assert exception_handlers is not None
        assert routers is not None

    def test_presentation_layer_components(self):
        """Test that presentation layer has all expected components."""
        # Test routers
        from src.presentation.routers import auth, task_lists, tasks
        assert all(hasattr(router, 'router') for router in [auth, task_lists, tasks])
        
        # Test dependencies
        from src.presentation.dependencies import get_current_user
        assert callable(get_current_user)
        
        # Test exception handlers
        from src.presentation.exception_handlers import add_exception_handlers
        assert callable(add_exception_handlers) 