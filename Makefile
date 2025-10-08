# Makefile for KOL Management System
# Quick commands for common development tasks

.PHONY: help install dev test db-up db-down db-reset migrate seed clean

# Default target
help:
	@echo "KOL Management System - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install all dependencies"
	@echo "  make dev           Start development environment"
	@echo ""
	@echo "Database:"
	@echo "  make db-up         Start database containers"
	@echo "  make db-down       Stop database containers"
	@echo "  make db-reset      Reset database (drop & recreate)"
	@echo "  make migrate       Run database migrations"
	@echo "  make seed          Seed database with test data"
	@echo ""
	@echo "Testing:"
	@echo "  make test          Run all tests"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make test-watch    Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          Run linting (black, ruff)"
	@echo "  make format        Format code with black"
	@echo "  make type-check    Run type checking with mypy"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Clean up cache and temp files"

# ============================================================================
# Setup Commands
# ============================================================================

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "Creating .env file from .env.example..."
	@if not exist .env copy .env.example .env
	@echo "Done! Edit .env file with your configuration."

dev:
	@echo "Starting development server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ============================================================================
# Database Commands
# ============================================================================

db-up:
	@echo "Starting database containers..."
	docker-compose up -d postgres postgres_test redis
	@echo "Waiting for databases to be ready..."
	timeout /t 5 /nobreak
	@echo "Databases are ready!"

db-down:
	@echo "Stopping database containers..."
	docker-compose down

db-reset:
	@echo "Resetting database..."
	docker-compose down -v
	docker-compose up -d postgres postgres_test redis
	timeout /t 5 /nobreak
	alembic upgrade head
	@echo "Database reset complete!"

migrate:
	@echo "Running database migrations..."
	alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	alembic revision --autogenerate -m "$(name)"

migrate-rollback:
	@echo "Rolling back last migration..."
	alembic downgrade -1

seed:
	@echo "Seeding database..."
	python scripts/seed_admin.py
	@echo "Database seeded!"

# ============================================================================
# Testing Commands
# ============================================================================

test:
	@echo "Running all tests..."
	pytest

test-unit:
	@echo "Running unit tests..."
	pytest -m unit

test-integration:
	@echo "Running integration tests..."
	pytest -m integration

test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

test-watch:
	@echo "Running tests in watch mode..."
	pytest-watch

# ============================================================================
# Code Quality Commands
# ============================================================================

lint:
	@echo "Running linters..."
	black --check app tests
	ruff check app tests

format:
	@echo "Formatting code..."
	black app tests
	ruff check --fix app tests

type-check:
	@echo "Running type checker..."
	mypy app

# ============================================================================
# Cleanup Commands
# ============================================================================

clean:
	@echo "Cleaning up..."
	@if exist __pycache__ rmdir /s /q __pycache__
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@if exist .ruff_cache rmdir /s /q .ruff_cache
	@if exist htmlcov rmdir /s /q htmlcov
	@if exist .coverage del .coverage
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@echo "Cleanup complete!"
