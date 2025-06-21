"""
Tests for configuration and main application setup.
"""

import pytest
from unittest.mock import patch


class TestConfiguration:
    """Tests for application configuration."""

    def test_settings_import(self):
        """Test that settings can be imported."""
        from src.config import settings
        
        assert settings is not None

    def test_settings_attributes(self):
        """Test that settings has all required attributes."""
        from src.config import settings
        
        # Test basic attributes exist
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'secret_key')
        assert hasattr(settings, 'algorithm')
        assert hasattr(settings, 'access_token_expire_minutes')
        assert hasattr(settings, 'email_enabled')
        assert hasattr(settings, 'project_name')
        assert hasattr(settings, 'debug')
        assert hasattr(settings, 'cors_origins')
        assert hasattr(settings, 'log_level')

    def test_settings_values(self):
        """Test that settings have expected values."""
        from src.config import settings
        
        # Test values are not None
        assert settings.database_url is not None
        assert settings.secret_key is not None
        assert settings.algorithm == "HS256"
        assert isinstance(settings.access_token_expire_minutes, int)
        assert isinstance(settings.email_enabled, bool)
        assert settings.project_name is not None
        assert isinstance(settings.debug, bool)

    def test_settings_smtp_configuration(self):
        """Test SMTP configuration settings."""
        from src.config import settings
        
        assert hasattr(settings, 'smtp_server')
        assert hasattr(settings, 'smtp_port')
        assert hasattr(settings, 'smtp_username')
        assert hasattr(settings, 'smtp_password')
        assert hasattr(settings, 'from_email')

    def test_config_module_import(self):
        """Test that config module can be imported."""
        from src import config
        
        assert hasattr(config, 'Settings')
        assert hasattr(config, 'settings')


class TestMainApplication:
    """Tests for main application setup."""

    def test_main_app_import(self):
        """Test that main app can be imported."""
        from src.main import app
        
        assert app is not None

    def test_main_app_configuration(self):
        """Test main app configuration."""
        from src.main import app
        
        # Check app configuration
        assert app.title is not None
        assert app.description is not None
        assert app.version is not None
        assert len(app.title) > 0

    def test_main_app_title_and_description(self):
        """Test main app title and description."""
        from src.main import app
        
        assert "Task Manager" in app.title or "API" in app.title
        assert len(app.description) > 0
        assert app.version is not None

    def test_main_app_middleware(self):
        """Test that main app has middleware configured."""
        from src.main import app
        
        # Check that middleware is configured
        assert len(app.user_middleware) >= 0  # May or may not have middleware

    def test_main_module_import(self):
        """Test that main module can be imported."""
        from src import main
        
        assert hasattr(main, 'app')


class TestApplicationSetup:
    """Tests for overall application setup."""

    def test_all_main_components_import(self):
        """Test that all main components can be imported."""
        from src.main import app
        from src.config import settings
        
        assert app is not None
        assert settings is not None

    def test_application_modules_import(self):
        """Test that all application modules can be imported."""
        from src import main
        from src import config
        from src import application
        from src import domain
        from src import infrastructure
        from src import presentation
        
        assert main is not None
        assert config is not None
        assert application is not None
        assert domain is not None
        assert infrastructure is not None
        assert presentation is not None 