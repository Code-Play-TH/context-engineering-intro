#!/bin/bash
set -e

# KOL Management System Development Docker Entrypoint Script
# Optimized for development with hot reloading and debugging

echo "🚀 Starting KOL Management System (Development Mode)..."

# Wait for database to be ready
wait_for_db() {
    echo "⏳ Waiting for database connection..."

    DB_HOST=${DATABASE_HOST:-localhost}
    DB_PORT=${DATABASE_PORT:-5432}

    timeout=60
    count=0

    while ! nc -z "$DB_HOST" "$DB_PORT" >/dev/null 2>&1; do
        count=$((count + 1))
        if [ $count -gt $timeout ]; then
            echo "❌ Database connection timeout after ${timeout} seconds"
            exit 1
        fi
        echo "⏳ Database not ready, waiting... (${count}/${timeout})"
        sleep 1
    done

    echo "✅ Database connection established"
}

# Wait for Redis to be ready
wait_for_redis() {
    echo "⏳ Waiting for Redis connection..."

    REDIS_HOST=${REDIS_HOST:-localhost}
    REDIS_PORT=${REDIS_PORT:-6379}

    timeout=60
    count=0

    while ! nc -z "$REDIS_HOST" "$REDIS_PORT" >/dev/null 2>&1; do
        count=$((count + 1))
        if [ $count -gt $timeout ]; then
            echo "❌ Redis connection timeout after ${timeout} seconds"
            exit 1
        fi
        echo "⏳ Redis not ready, waiting... (${count}/${timeout})"
        sleep 1
    done

    echo "✅ Redis connection established"
}

# Run database migrations
run_migrations() {
    echo "🗄️  Running database migrations..."

    if [ -f "alembic.ini" ]; then
        alembic upgrade head
        echo "✅ Database migrations completed"
    else
        echo "⚠️  No alembic.ini found, skipping migrations"
    fi
}

# Seed development data
seed_dev_data() {
    echo "🌱 Seeding development data..."

    if [ -f "scripts/seed_dev_data.py" ]; then
        python scripts/seed_dev_data.py
        echo "✅ Development data seeding completed"
    else
        echo "ℹ️  No development seed data script found, skipping"
    fi
}

# Install development dependencies if needed
install_dev_deps() {
    if [ -f "requirements-dev.txt" ] && [ "$INSTALL_DEV_DEPS" = "true" ]; then
        echo "📦 Installing development dependencies..."
        pip install -r requirements-dev.txt
        echo "✅ Development dependencies installed"
    fi
}

# Set up pre-commit hooks
setup_precommit() {
    if [ -f ".pre-commit-config.yaml" ] && [ "$SETUP_PRECOMMIT" = "true" ]; then
        echo "🪝 Setting up pre-commit hooks..."
        pre-commit install
        echo "✅ Pre-commit hooks installed"
    fi
}

# Development initialization
dev_initialize() {
    echo "🔧 Initializing development environment..."

    # Install dependencies
    install_dev_deps

    # Wait for external services
    if [ "$SKIP_DB_WAIT" != "true" ]; then
        wait_for_db
    fi

    if [ "$SKIP_REDIS_WAIT" != "true" ]; then
        wait_for_redis
    fi

    # Run migrations
    if [ "$SKIP_MIGRATIONS" != "true" ]; then
        run_migrations
    fi

    # Seed development data
    if [ "$SKIP_SEED_DATA" != "true" ]; then
        seed_dev_data
    fi

    # Setup pre-commit
    setup_precommit

    echo "🎉 Development initialization completed!"
}

# Handle different commands
case "$1" in
    "web"|"uvicorn"|"dev"|"development")
        dev_initialize
        echo "🌐 Starting development web server..."

        # Start with hot reloading
        if [ "$ENABLE_DEBUGGER" = "true" ]; then
            echo "🐛 Starting with debugger support on port 5678..."
            python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        else
            exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
        fi
        ;;
    "worker"|"celery")
        # Wait for dependencies but skip migrations for workers
        if [ "$SKIP_DB_WAIT" != "true" ]; then
            wait_for_db
        fi
        if [ "$SKIP_REDIS_WAIT" != "true" ]; then
            wait_for_redis
        fi

        echo "👷 Starting Celery worker (development)..."
        exec celery -A app.tasks.celery worker --loglevel=debug --autoreload
        ;;
    "beat"|"scheduler")
        if [ "$SKIP_DB_WAIT" != "true" ]; then
            wait_for_db
        fi
        if [ "$SKIP_REDIS_WAIT" != "true" ]; then
            wait_for_redis
        fi

        echo "⏰ Starting Celery beat scheduler (development)..."
        exec celery -A app.tasks.celery beat --loglevel=debug
        ;;
    "flower")
        if [ "$SKIP_REDIS_WAIT" != "true" ]; then
            wait_for_redis
        fi

        echo "🌸 Starting Flower monitoring (development)..."
        exec celery -A app.tasks.celery flower --debug
        ;;
    "test")
        echo "🧪 Running tests in development mode..."
        exec python -m pytest tests/ -v --tb=short
        ;;
    "test-watch")
        echo "👀 Running tests with file watching..."
        exec ptw tests/ --runner "python -m pytest tests/ -v --tb=short"
        ;;
    "lint")
        echo "🔍 Running code quality checks..."
        echo "Running black..."
        black --check app tests
        echo "Running isort..."
        isort --check-only app tests
        echo "Running flake8..."
        flake8 app tests
        echo "Running mypy..."
        mypy app
        echo "✅ All linting checks passed"
        ;;
    "format")
        echo "🎨 Formatting code..."
        black app tests
        isort app tests
        echo "✅ Code formatting completed"
        ;;
    "shell")
        echo "🐚 Starting interactive development shell..."
        exec python -c "
import asyncio
from app.core.database import get_session
from app.models import *
from app.core.config import get_settings
print('KOL Management System - Development Shell')
print('Available imports: get_session, models, get_settings')
"
        ;;
    "migrate")
        wait_for_db
        run_migrations
        exit 0
        ;;
    "makemigrations")
        wait_for_db
        echo "📝 Creating new migration..."
        alembic revision --autogenerate -m "${2:-Auto migration}"
        exit 0
        ;;
    "seed")
        wait_for_db
        seed_dev_data
        exit 0
        ;;
    "debug")
        dev_initialize
        echo "🐛 Starting debug server..."
        python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    "jupyter")
        echo "📓 Starting Jupyter notebook..."
        exec jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
        ;;
    "help"|"--help")
        echo "KOL Management System - Development Docker Entrypoint"
        echo ""
        echo "Available commands:"
        echo "  web, uvicorn, dev       - Start development web server with hot reload"
        echo "  worker, celery          - Start Celery worker with autoreload"
        echo "  beat, scheduler         - Start Celery beat scheduler"
        echo "  flower                  - Start Flower monitoring"
        echo "  test                    - Run tests"
        echo "  test-watch              - Run tests with file watching"
        echo "  lint                    - Run code quality checks"
        echo "  format                  - Format code with black and isort"
        echo "  shell                   - Start interactive shell"
        echo "  migrate                 - Run database migrations"
        echo "  makemigrations [msg]    - Create new migration"
        echo "  seed                    - Seed development data"
        echo "  debug                   - Start with debugger support"
        echo "  jupyter                 - Start Jupyter notebook"
        echo "  help                    - Show this help"
        echo ""
        echo "Environment variables:"
        echo "  SKIP_DB_WAIT=true       - Skip waiting for database"
        echo "  SKIP_REDIS_WAIT=true    - Skip waiting for Redis"
        echo "  SKIP_MIGRATIONS=true    - Skip database migrations"
        echo "  SKIP_SEED_DATA=true     - Skip data seeding"
        echo "  ENABLE_DEBUGGER=true    - Enable debugpy for debugging"
        echo "  INSTALL_DEV_DEPS=true   - Install development dependencies"
        echo "  SETUP_PRECOMMIT=true    - Setup pre-commit hooks"
        exit 0
        ;;
    *)
        # Default to development mode
        dev_initialize
        echo "🚀 Starting development mode: $*"
        exec "$@"
        ;;
esac