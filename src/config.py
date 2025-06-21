"""Application configuration using Pydantic Settings."""

import logging
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://taskmanager:taskmanager123@localhost:5432/taskmanager",
        description="Database URL for async connection"
    )
    test_database_url: str = Field(
        default="postgresql+asyncpg://taskmanager:taskmanager123@localhost:5432/taskmanager_test",
        description="Test database URL"
    )

    # JWT
    secret_key: str = Field(
        default="your-super-secret-key-change-this-in-production",
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration time in minutes"
    )

    # Email
    email_enabled: bool = Field(default=True, description="Enable email notifications")
    smtp_server: str = Field(default="localhost", description="SMTP server")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_username: str = Field(default="", description="SMTP username")
    smtp_password: str = Field(default="", description="SMTP password")
    from_email: str = Field(
        default="noreply@taskmanager.com", description="From email address"
    )

    # API
    api_v1_str: str = Field(default="/api/v1", description="API v1 prefix")
    project_name: str = Field(default="Task Manager API", description="Project name")
    debug: bool = Field(default=False, description="Debug mode")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="CORS origins"
    )

    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    class Config:
        """Pydantic configuration."""
        
        env_file = ".env"
        case_sensitive = False

    def setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)
        
        if self.log_format == "json":
            # JSON logging format for production
            logging.basicConfig(
                level=log_level,
                format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        else:
            # Human-readable format for development
            logging.basicConfig(
                level=log_level,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )


# Global settings instance
settings = Settings() 