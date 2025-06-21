# Task Manager API Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Run development server"
	@echo "  test        - Run all tests"
	@echo "  test-unit   - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-cov    - Run tests with coverage"
	@echo "  lint        - Run linting (flake8)"
	@echo "  format      - Format code (black + isort)"
	@echo "  format-check - Check code formatting"
	@echo "  clean       - Clean cache and temp files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up   - Start services with Docker Compose"
	@echo "  docker-down - Stop Docker Compose services"
	@echo "  docker-logs - Show Docker logs"

# Development setup
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pre-commit install

# Development server
dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Testing
test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 src/ tests/

format:
	black src/ tests/
	isort src/ tests/

format-check:
	black --check src/ tests/
	isort --check-only src/ tests/

# Cleanup
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Docker commands
docker-build:
	docker build -t task-manager-api .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-restart:
	docker-compose restart

# Database commands
db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-revision:
	alembic revision --autogenerate -m "$(MESSAGE)"

# Quality checks (run all)
check: format-check lint test

# CI pipeline simulation
ci: format-check lint test-cov

# Setup for new developers
setup: install
	@echo "Setup complete! Run 'make dev' to start the development server." 