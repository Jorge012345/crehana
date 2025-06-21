"""
Tests for the infrastructure layer.
Includes tests for database and repository implementations.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from src.infrastructure.database import Base
from src.infrastructure.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyTaskListRepository,
    SQLAlchemyTaskRepository
)


class TestDatabase:
    """Tests for database infrastructure."""

    def test_database_base_model(self):
        """Test database base model."""
        assert Base is not None

    def test_database_models_import(self):
        """Test that database models can be imported."""
        from src.infrastructure.database import UserModel, TaskListModel, TaskModel
        
        assert UserModel is not None
        assert TaskListModel is not None
        assert TaskModel is not None

    def test_database_module_import(self):
        """Test that database module can be imported."""
        from src.infrastructure import database
        
        assert hasattr(database, 'Base')
        assert hasattr(database, 'UserModel')
        assert hasattr(database, 'TaskListModel')
        assert hasattr(database, 'TaskModel')
        assert hasattr(database, 'DatabaseManager')


class TestRepositories:
    """Tests for repository implementations."""

    def test_sqlalchemy_user_repository_initialization(self):
        """Test SQLAlchemyUserRepository initialization."""
        mock_session = Mock()
        
        repo = SQLAlchemyUserRepository(mock_session)
        
        assert repo.session == mock_session

    def test_sqlalchemy_task_list_repository_initialization(self):
        """Test SQLAlchemyTaskListRepository initialization."""
        mock_session = Mock()
        
        repo = SQLAlchemyTaskListRepository(mock_session)
        
        assert repo.session == mock_session

    def test_sqlalchemy_task_repository_initialization(self):
        """Test SQLAlchemyTaskRepository initialization."""
        mock_session = Mock()
        
        repo = SQLAlchemyTaskRepository(mock_session)
        
        assert repo.session == mock_session

    def test_repository_classes_exist(self):
        """Test that repository classes exist and can be imported."""
        from src.infrastructure.repositories import (
            SQLAlchemyUserRepository,
            SQLAlchemyTaskListRepository,
            SQLAlchemyTaskRepository
        )
        
        assert SQLAlchemyUserRepository is not None
        assert SQLAlchemyTaskListRepository is not None
        assert SQLAlchemyTaskRepository is not None

    def test_repositories_module_import(self):
        """Test that repositories module can be imported."""
        from src.infrastructure import repositories
        
        assert hasattr(repositories, 'SQLAlchemyUserRepository')
        assert hasattr(repositories, 'SQLAlchemyTaskListRepository')
        assert hasattr(repositories, 'SQLAlchemyTaskRepository')


class TestInfrastructureLayer:
    """Tests for overall infrastructure layer."""

    def test_infrastructure_module_imports(self):
        """Test that all infrastructure modules can be imported."""
        from src.infrastructure import database
        from src.infrastructure import repositories
        
        assert database is not None
        assert repositories is not None

    def test_infrastructure_layer_components(self):
        """Test that infrastructure layer has all expected components."""
        # Test database components
        from src.infrastructure.database import Base, DatabaseManager
        assert Base is not None
        assert DatabaseManager is not None
        
        # Test repository components
        from src.infrastructure.repositories import (
            SQLAlchemyUserRepository,
            SQLAlchemyTaskListRepository,
            SQLAlchemyTaskRepository
        )
        assert SQLAlchemyUserRepository is not None
        assert SQLAlchemyTaskListRepository is not None
        assert SQLAlchemyTaskRepository is not None 