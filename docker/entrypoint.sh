#!/bin/bash
set -e

# KOL Management System Docker Entrypoint Script
# Handles initialization, database migrations, and application startup

echo "🚀 Starting KOL Management System..."

# Wait for database to be ready
wait_for_db() {
    echo "⏳ Waiting for database connection..."

    # Extract database connection info from environment
    DB_HOST=${DATABASE_HOST:-localhost}
    DB_PORT=${DATABASE_PORT:-5432}

    # Wait for database with timeout
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

    # Check if alembic is configured
    if [ -f "alembic.ini" ]; then
        # Run migrations
        alembic upgrade head
        echo "✅ Database migrations completed"
    else
        echo "⚠️  No alembic.ini found, skipping migrations"
    fi
}

# Seed initial data
seed_data() {
    echo "🌱 Seeding initial data..."

    # Run data seeding script if it exists
    if [ -f "scripts/seed_data.py" ]; then
        python scripts/seed_data.py
        echo "✅ Initial data seeding completed"
    else
        echo "ℹ️  No seed data script found, skipping"
    fi
}

# Collect static files (if needed)
collect_static() {
    echo "📁 Collecting static files..."

    # Create static directory if it doesn't exist
    mkdir -p /app/static

    # Copy any static assets
    if [ -d "app/static" ]; then
        cp -r app/static/* /app/static/
        echo "✅ Static files collected"
    else
        echo "ℹ️  No static files to collect"
    fi
}

# Health check function
health_check() {
    echo "🏥 Running health check..."

    # Simple health check
    python -c "
import sys
try:
    from app.core.config import get_settings
    from app.core.database import check_database_connection
    settings = get_settings()
    print('✅ Application configuration loaded')
    print('✅ Health check passed')
except Exception as e:
    print(f'❌ Health check failed: {e}')
    sys.exit(1)
    "
}

# Main initialization function
initialize() {
    echo "🔧 Initializing KOL Management System..."

    # Wait for external services
    if [ "$SKIP_DB_WAIT" != "true" ]; then
        wait_for_db
    fi

    if [ "$SKIP_REDIS_WAIT" != "true" ]; then
        wait_for_redis
    fi

    # Run initialization tasks
    if [ "$SKIP_MIGRATIONS" != "true" ]; then
        run_migrations
    fi

    if [ "$SKIP_SEED_DATA" != "true" ]; then
        seed_data
    fi

    collect_static
    health_check

    echo "🎉 Initialization completed successfully!"
}

# Handle different commands
case "$1" in
    "web"|"uvicorn"|"gunicorn")
        initialize
        echo "🌐 Starting web server..."
        exec "$@"
        ;;
    "worker"|"celery")
        # Wait for dependencies but skip migrations for workers
        if [ "$SKIP_DB_WAIT" != "true" ]; then
            wait_for_db
        fi
        if [ "$SKIP_REDIS_WAIT" != "true" ]; then
            wait_for_redis
        fi

        echo "👷 Starting Celery worker..."
        exec celery -A app.tasks.celery worker --loglevel=info
        ;;
    "beat"|"scheduler")
        if [ "$SKIP_DB_WAIT" != "true" ]; then
            wait_for_db
        fi
        if [ "$SKIP_REDIS_WAIT" != "true" ]; then
            wait_for_redis
        fi

        echo "⏰ Starting Celery beat scheduler..."
        exec celery -A app.tasks.celery beat --loglevel=info
        ;;
    "flower")
        if [ "$SKIP_REDIS_WAIT" != "true" ]; then
            wait_for_redis
        fi

        echo "🌸 Starting Flower monitoring..."
        exec celery -A app.tasks.celery flower
        ;;
    "migrate")
        wait_for_db
        run_migrations
        exit 0
        ;;
    "seed")
        wait_for_db
        seed_data
        exit 0
        ;;
    "shell")
        echo "🐚 Starting interactive shell..."
        exec python -c "
import asyncio
from app.core.database import get_session
from app.models import *
print('KOL Management System - Interactive Shell')
print('Available imports: get_session, models')
"
        ;;
    "test")
        echo "🧪 Running tests..."
        exec python -m pytest tests/ -v
        ;;
    "help"|"--help")
        echo "KOL Management System Docker Entrypoint"
        echo ""
        echo "Available commands:"
        echo "  web, uvicorn, gunicorn  - Start web server (default)"
        echo "  worker, celery          - Start Celery worker"
        echo "  beat, scheduler         - Start Celery beat scheduler"
        echo "  flower                  - Start Flower monitoring"
        echo "  migrate                 - Run database migrations"
        echo "  seed                    - Seed initial data"
        echo "  shell                   - Start interactive shell"
        echo "  test                    - Run tests"
        echo "  help                    - Show this help"
        echo ""
        echo "Environment variables:"
        echo "  SKIP_DB_WAIT=true       - Skip waiting for database"
        echo "  SKIP_REDIS_WAIT=true    - Skip waiting for Redis"
        echo "  SKIP_MIGRATIONS=true    - Skip database migrations"
        echo "  SKIP_SEED_DATA=true     - Skip data seeding"
        echo "  DATABASE_HOST           - Database hostname"
        echo "  DATABASE_PORT           - Database port"
        echo "  REDIS_HOST              - Redis hostname"
        echo "  REDIS_PORT              - Redis port"
        exit 0
        ;;
    *)
        # If no specific command, run initialization and then execute the command
        initialize
        echo "🚀 Starting: $*"
        exec "$@"
        ;;
esac