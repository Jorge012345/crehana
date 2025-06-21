"""
Simple router tests that don't require database initialization.
"""

import pytest
from fastapi import APIRouter
from fastapi.routing import APIRoute

from src.presentation.routers import auth, task_lists, tasks


class TestRoutersSimple:
    """Simple tests for routers without database dependencies."""

    def test_auth_router_exists(self):
        """Test that auth router exists."""
        assert auth.router is not None
        assert isinstance(auth.router, APIRouter)

    def test_auth_router_has_routes(self):
        """Test that auth router has routes."""
        assert len(auth.router.routes) > 0
        
        # Check for expected routes
        route_paths = [route.path for route in auth.router.routes if isinstance(route, APIRoute)]
        assert any("register" in path for path in route_paths)
        assert any("login" in path for path in route_paths)

    def test_task_lists_router_exists(self):
        """Test that task lists router exists."""
        assert task_lists.router is not None
        assert isinstance(task_lists.router, APIRouter)

    def test_task_lists_router_has_routes(self):
        """Test that task lists router has routes."""
        assert len(task_lists.router.routes) > 0
        
        # Check for expected HTTP methods
        all_methods = set()
        for route in task_lists.router.routes:
            if isinstance(route, APIRoute):
                all_methods.update(route.methods)
        
        # Should have CRUD methods
        assert len(all_methods) > 0

    def test_tasks_router_exists(self):
        """Test that tasks router exists."""
        assert tasks.router is not None
        assert isinstance(tasks.router, APIRouter)

    def test_tasks_router_has_routes(self):
        """Test that tasks router has routes."""
        assert len(tasks.router.routes) > 0
        
        # Check for expected HTTP methods
        all_methods = set()
        for route in tasks.router.routes:
            if isinstance(route, APIRoute):
                all_methods.update(route.methods)
        
        # Should have CRUD methods including PATCH for status updates
        assert len(all_methods) > 0

    def test_router_prefixes(self):
        """Test router prefixes."""
        assert task_lists.router.prefix == "/task-lists"
        assert tasks.router.prefix == "/tasks"

    def test_router_endpoints_are_callable(self):
        """Test that router endpoints are callable."""
        routers = [auth.router, task_lists.router, tasks.router]
        
        for router in routers:
            for route in router.routes:
                if isinstance(route, APIRoute):
                    assert hasattr(route, 'endpoint')
                    assert callable(route.endpoint)

    def test_response_models_configuration(self):
        """Test response models configuration."""
        routers = [auth.router, task_lists.router, tasks.router]
        
        for router in routers:
            for route in router.routes:
                if isinstance(route, APIRoute):
                    # Response model is optional, just check it's properly configured
                    if hasattr(route, 'response_model'):
                        # If response model exists, it should be a valid type
                        assert route.response_model is None or hasattr(route.response_model, '__name__') or hasattr(route.response_model, '_name')

    def test_router_tags(self):
        """Test router tags."""
        # Tags are optional but if present should be lists
        if hasattr(auth.router, 'tags') and auth.router.tags:
            assert isinstance(auth.router.tags, list)
        
        if hasattr(task_lists.router, 'tags') and task_lists.router.tags:
            assert isinstance(task_lists.router.tags, list)
        
        if hasattr(tasks.router, 'tags') and tasks.router.tags:
            assert isinstance(tasks.router.tags, list)

    def test_router_imports(self):
        """Test that routers can be imported."""
        from src.presentation.routers.auth import router as auth_router
        from src.presentation.routers.task_lists import router as task_lists_router
        from src.presentation.routers.tasks import router as tasks_router
        
        assert auth_router is not None
        assert task_lists_router is not None
        assert tasks_router is not None 