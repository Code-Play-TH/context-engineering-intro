#!/bin/bash
# Server startup script for Factory ERP System
# Configures and starts the FastAPI application with Gunicorn

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[SERVER]${NC} $1" >&2
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

# Set default values
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
export WORKERS=${WORKERS:-4}
export WORKER_CLASS=${WORKER_CLASS:-uvicorn.workers.UvicornWorker}
export WORKER_CONNECTIONS=${WORKER_CONNECTIONS:-1000}
export MAX_REQUESTS=${MAX_REQUESTS:-1000}
export MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}
export TIMEOUT=${TIMEOUT:-30}
export KEEP_ALIVE=${KEEP_ALIVE:-2}
export LOG_LEVEL=${LOG_LEVEL:-info}
export ACCESS_LOG=${ACCESS_LOG:-}
export ERROR_LOG=${ERROR_LOG:-}
export APP_MODULE=${APP_MODULE:-app.main:app}
export PRELOAD=${PRELOAD:-true}

# Calculate optimal worker count based on CPU cores
if [ "$WORKERS" = "auto" ]; then
    cpu_cores=$(nproc 2>/dev/null || echo 1)
    export WORKERS=$((cpu_cores * 2 + 1))
    log "Auto-detected $cpu_cores CPU cores, setting workers to $WORKERS"
fi

# Configure logging
setup_logging() {
    log "Configuring application logging..."
    
    # Create log directory if it doesn't exist
    mkdir -p /app/logs
    
    # Set log file paths if not specified
    if [ -z "$ACCESS_LOG" ]; then
        export ACCESS_LOG="/app/logs/access.log"
    fi
    
    if [ -z "$ERROR_LOG" ]; then
        export ERROR_LOG="/app/logs/error.log"
    fi
    
    # Create log files
    touch "$ACCESS_LOG" "$ERROR_LOG"
    
    info "Access log: $ACCESS_LOG"
    info "Error log: $ERROR_LOG"
}

# Display startup configuration
show_config() {
    log "Factory ERP Server Configuration:"
    info "  Host: $HOST"
    info "  Port: $PORT"
    info "  Workers: $WORKERS"
    info "  Worker Class: $WORKER_CLASS"
    info "  Worker Connections: $WORKER_CONNECTIONS"
    info "  Max Requests: $MAX_REQUESTS"
    info "  Max Requests Jitter: $MAX_REQUESTS_JITTER"
    info "  Timeout: $TIMEOUT seconds"
    info "  Keep Alive: $KEEP_ALIVE seconds"
    info "  Log Level: $LOG_LEVEL"
    info "  App Module: $APP_MODULE"
    info "  Preload: $PRELOAD"
    
    # Show environment info
    if [ -n "$DATABASE_URL" ]; then
        # Mask password in database URL for logging
        masked_db_url=$(echo "$DATABASE_URL" | sed 's/:\/\/[^:]*:[^@]*@/:\/\/***:***@/')
        info "  Database: $masked_db_url"
    fi
    
    if [ -n "$ERPNEXT_BASE_URL" ]; then
        info "  ERPNext URL: $ERPNEXT_BASE_URL"
    fi
}

# Health check function
health_check() {
    log "Running health check..."
    
    # Wait a moment for server to start
    sleep 2
    
    # Simple health check
    if curl -f -s "http://localhost:$PORT/health" > /dev/null; then
        log "Health check passed"
        return 0
    else
        log "Health check failed"
        return 1
    fi
}

# Start server with hot reload (development mode)
start_dev_server() {
    log "Starting development server with hot reload..."
    
    exec uvicorn "$APP_MODULE" \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --reload-dir /app \
        --log-level "$LOG_LEVEL"
}

# Start production server with Gunicorn
start_production_server() {
    log "Starting production server with Gunicorn..."
    
    # Build Gunicorn command
    gunicorn_cmd="gunicorn"
    gunicorn_args=(
        "$APP_MODULE"
        --bind "$HOST:$PORT"
        --workers "$WORKERS"
        --worker-class "$WORKER_CLASS"
        --worker-connections "$WORKER_CONNECTIONS"
        --max-requests "$MAX_REQUESTS"
        --max-requests-jitter "$MAX_REQUESTS_JITTER"
        --timeout "$TIMEOUT"
        --keep-alive "$KEEP_ALIVE"
        --log-level "$LOG_LEVEL"
        --access-logfile "$ACCESS_LOG"
        --error-logfile "$ERROR_LOG"
        --capture-output
        --enable-stdio-inheritance
    )
    
    # Add preload option if enabled
    if [ "$PRELOAD" = "true" ]; then
        gunicorn_args+=(--preload)
    fi
    
    # Add graceful timeout
    gunicorn_args+=(--graceful-timeout 30)
    
    # Execute Gunicorn
    exec "$gunicorn_cmd" "${gunicorn_args[@]}"
}

# Main startup function
main() {
    log "Factory ERP System - Starting server..."
    
    setup_logging
    show_config
    
    # Check if running in development mode
    if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ] || [ "$ENVIRONMENT" = "development" ]; then
        log "Development mode detected"
        start_dev_server
    else
        log "Production mode - using Gunicorn"
        start_production_server
    fi
}

# Handle shutdown signals gracefully
shutdown_handler() {
    log "Received shutdown signal, gracefully stopping server..."
    # Gunicorn handles graceful shutdown automatically
    exit 0
}

# Set up signal handlers
trap shutdown_handler SIGTERM SIGINT

# Start the server
main "$@"