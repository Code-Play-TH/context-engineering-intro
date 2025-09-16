#!/bin/bash
# Docker entrypoint script for Factory ERP System
# Handles database migrations and application startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[ENTRYPOINT]${NC} $1" >&2
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

# Wait for database to be ready
wait_for_db() {
    log "Waiting for database to be ready..."
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import asyncio
import asyncpg
import os
from urllib.parse import urlparse

async def check_db():
    try:
        db_url = os.environ.get('DATABASE_URL', '')
        if not db_url:
            return False
        
        parsed = urlparse(db_url)
        if parsed.scheme not in ['postgresql', 'postgresql+asyncpg']:
            return True  # Skip check for non-PostgreSQL databases
        
        # Extract connection parameters
        host = parsed.hostname or 'localhost'
        port = parsed.port or 5432
        user = parsed.username or 'postgres'
        password = parsed.password or ''
        database = parsed.path.lstrip('/') or 'factory_erp'
        
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            timeout=5
        )
        await conn.close()
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(check_db())
exit(0 if result else 1)
"; then
            log "Database is ready!"
            break
        else
            warn "Database not ready, attempt $attempt/$max_attempts"
            sleep 2
            attempt=$((attempt + 1))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "Database failed to become ready after $max_attempts attempts"
        exit 1
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    if [ -f "alembic.ini" ]; then
        # Check if migrations directory exists
        if [ -d "migrations" ]; then
            log "Running Alembic migrations..."
            alembic upgrade head
            if [ $? -eq 0 ]; then
                log "Database migrations completed successfully"
            else
                error "Database migrations failed"
                exit 1
            fi
        else
            warn "Migrations directory not found, skipping migrations"
        fi
    else
        warn "Alembic configuration not found, skipping migrations"
    fi
}

# Validate environment variables
validate_environment() {
    log "Validating environment variables..."
    
    required_vars=("DATABASE_URL" "SECRET_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            error "  - $var"
        done
        error "Please set these variables and restart the container"
        exit 1
    fi
    
    # Validate secret key length
    if [ ${#SECRET_KEY} -lt 32 ]; then
        error "SECRET_KEY must be at least 32 characters long"
        exit 1
    fi
    
    log "Environment validation completed"
}

# Setup application directories
setup_directories() {
    log "Setting up application directories..."
    
    directories=("logs" "uploads" "static")
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
    
    # Ensure proper permissions (ignore if volumes are mounted)
    chmod 755 logs uploads static 2>/dev/null || warn "Could not change permissions (likely mounted volumes)"
    
    log "Directory setup completed"
}

# Initialize database with seed data (optional)
init_seed_data() {
    if [ "$RUN_SEED_DATA" = "true" ] || [ "$RUN_SEED_DATA" = "1" ]; then
        log "Initializing seed data..."
        
        python -c "
import asyncio
import sys
sys.path.append('/app')

async def run_seed():
    try:
        from app.database import engine, init_db
        from app.core.seed_data import create_seed_data
        
        await init_db()
        await create_seed_data()
        print('Seed data initialized successfully')
        return True
    except Exception as e:
        print(f'Seed data initialization failed: {e}')
        return False

result = asyncio.run(run_seed())
exit(0 if result else 1)
"
        if [ $? -eq 0 ]; then
            log "Seed data initialization completed"
        else
            error "Seed data initialization failed"
            # Don't exit on seed data failure, just warn
            warn "Continuing without seed data..."
        fi
    fi
}

# Pre-flight checks
preflight_checks() {
    log "Running pre-flight checks..."
    
    # Check Python version
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    log "Python version: $python_version"
    
    # Check disk space
    disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        warn "Disk usage is high: ${disk_usage}%"
    fi
    
    # Check memory
    if [ -f /proc/meminfo ]; then
        total_mem=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        available_mem=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        mem_usage=$((100 - (available_mem * 100 / total_mem)))
        
        if [ "$mem_usage" -gt 90 ]; then
            warn "Memory usage is high: ${mem_usage}%"
        fi
        
        log "Memory usage: ${mem_usage}%"
    fi
    
    log "Pre-flight checks completed"
}

# Handle termination signals
cleanup() {
    log "Received termination signal, performing cleanup..."
    # Add any cleanup tasks here
    log "Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main execution
main() {
    log "Factory ERP System - Starting initialization..."
    log "Image version: ${APP_VERSION:-unknown}"
    log "Build date: ${BUILD_DATE:-unknown}"
    
    # Run initialization steps
    validate_environment
    setup_directories
    preflight_checks
    wait_for_db
    run_migrations
    # init_seed_data  # TEMPORARILY DISABLED - missing MaterialCode model
    
    log "Initialization completed successfully"
    log "Starting application..."
    
    # Execute the main command
    exec "$@"
}

# Run main function
main "$@"