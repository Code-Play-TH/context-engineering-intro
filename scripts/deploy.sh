#!/bin/bash
# KOL Management System Deployment Script
# Automated deployment script for production environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Change to project directory
cd "$PROJECT_ROOT"

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Set compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi

    log_success "Prerequisites check passed"
}

# Function to create backup
create_backup() {
    log_info "Creating backup before deployment..."

    # Create backup directory
    mkdir -p "$BACKUP_DIR"

    # Backup database if running
    if $COMPOSE_CMD ps postgres | grep -q "Up"; then
        BACKUP_FILE="$BACKUP_DIR/database_backup_$(date +%Y%m%d_%H%M%S).sql"
        log_info "Backing up database to $BACKUP_FILE"

        $COMPOSE_CMD exec -T postgres pg_dump -U koluser kolsystem > "$BACKUP_FILE"

        if [ $? -eq 0 ]; then
            log_success "Database backup created: $BACKUP_FILE"
        else
            log_error "Database backup failed"
            return 1
        fi
    else
        log_info "Database container not running, skipping backup"
    fi

    # Backup uploaded files
    if [ -d "uploads" ]; then
        UPLOADS_BACKUP="$BACKUP_DIR/uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
        log_info "Backing up uploads to $UPLOADS_BACKUP"
        tar -czf "$UPLOADS_BACKUP" uploads/
        log_success "Uploads backup created: $UPLOADS_BACKUP"
    fi

    log_success "Backup completed"
}

# Function to validate environment file
validate_env() {
    log_info "Validating environment configuration..."

    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file $ENV_FILE not found"
        if [ -f ".env.example" ]; then
            log_info "Copying .env.example to $ENV_FILE"
            cp .env.example "$ENV_FILE"
            log_warning "Please edit $ENV_FILE with your production values before continuing"
            exit 1
        else
            log_error "No environment file or example found"
            exit 1
        fi
    fi

    # Check for required environment variables
    required_vars=(
        "DATABASE_PASSWORD"
        "REDIS_PASSWORD"
        "JWT_SECRET_KEY"
        "SECRET_KEY"
    )

    missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=.*change.*production" "$ENV_FILE"; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "The following required environment variables are missing or have default values:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        log_error "Please update $ENV_FILE with production values"
        exit 1
    fi

    log_success "Environment validation passed"
}

# Function to build images
build_images() {
    log_info "Building Docker images..."

    $COMPOSE_CMD build --no-cache

    if [ $? -eq 0 ]; then
        log_success "Docker images built successfully"
    else
        log_error "Failed to build Docker images"
        exit 1
    fi
}

# Function to deploy services
deploy_services() {
    log_info "Deploying services..."

    # Start core services first
    log_info "Starting core services (database, redis)..."
    $COMPOSE_CMD up -d postgres redis

    # Wait for core services to be healthy
    log_info "Waiting for core services to be healthy..."
    timeout=120
    count=0
    while [ $count -lt $timeout ]; do
        if $COMPOSE_CMD ps postgres | grep -q "healthy" && $COMPOSE_CMD ps redis | grep -q "healthy"; then
            break
        fi
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    echo

    if [ $count -ge $timeout ]; then
        log_error "Core services failed to become healthy within $timeout seconds"
        $COMPOSE_CMD logs postgres redis
        exit 1
    fi

    log_success "Core services are healthy"

    # Start application services
    log_info "Starting application services..."
    $COMPOSE_CMD up -d web worker scheduler

    # Wait for application services
    log_info "Waiting for application services to be ready..."
    sleep 30

    # Start monitoring services if enabled
    if grep -q "profiles:" docker-compose.yml; then
        log_info "Starting monitoring services..."
        $COMPOSE_CMD --profile monitoring up -d
    fi

    log_success "Services deployed successfully"
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."

    # Check web service health
    max_retries=10
    retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Web service health check passed"
            break
        fi

        retry_count=$((retry_count + 1))
        log_info "Health check attempt $retry_count/$max_retries failed, retrying in 10 seconds..."
        sleep 10
    done

    if [ $retry_count -ge $max_retries ]; then
        log_error "Web service health check failed after $max_retries attempts"
        log_info "Checking service logs..."
        $COMPOSE_CMD logs web
        exit 1
    fi

    # Check other services
    services=("postgres" "redis" "worker")
    for service in "${services[@]}"; do
        if $COMPOSE_CMD ps "$service" | grep -q "Up"; then
            log_success "$service is running"
        else
            log_warning "$service is not running"
            $COMPOSE_CMD logs "$service"
        fi
    done

    log_success "Health checks completed"
}

# Function to show deployment status
show_status() {
    log_info "Deployment Status:"
    echo
    $COMPOSE_CMD ps
    echo
    log_info "Service URLs:"
    echo "  🌐 API: http://localhost:8000"
    echo "  📊 API Docs: http://localhost:8000/docs"
    echo "  🌸 Flower (Task Monitor): http://localhost:5555"

    if $COMPOSE_CMD ps prometheus | grep -q "Up"; then
        echo "  📈 Prometheus: http://localhost:9090"
    fi

    if $COMPOSE_CMD ps grafana | grep -q "Up"; then
        echo "  📋 Grafana: http://localhost:3000"
    fi

    if $COMPOSE_CMD ps nginx | grep -q "Up"; then
        echo "  🔒 Nginx: http://localhost:80"
    fi

    echo
    log_info "To view logs: $COMPOSE_CMD logs [service_name]"
    log_info "To scale workers: $COMPOSE_CMD up -d --scale worker=N"
}

# Function to rollback deployment
rollback() {
    log_warning "Rolling back deployment..."

    # Stop current services
    $COMPOSE_CMD down

    # Restore database backup if available
    latest_backup=$(ls -t "$BACKUP_DIR"/database_backup_*.sql 2>/dev/null | head -n1)
    if [ -n "$latest_backup" ]; then
        log_info "Restoring database from $latest_backup"
        $COMPOSE_CMD up -d postgres
        sleep 10
        cat "$latest_backup" | $COMPOSE_CMD exec -T postgres psql -U koluser kolsystem
        log_success "Database restored from backup"
    fi

    log_warning "Rollback completed"
}

# Main deployment function
main_deploy() {
    log_info "Starting KOL Management System deployment..."

    check_prerequisites
    validate_env

    # Create backup if services are running
    if $COMPOSE_CMD ps | grep -q "Up"; then
        create_backup
    fi

    build_images
    deploy_services
    run_health_checks
    show_status

    log_success "🎉 Deployment completed successfully!"
    log_info "The KOL Management System is now running."
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy"|"")
        main_deploy
        ;;
    "backup")
        check_prerequisites
        create_backup
        ;;
    "rollback")
        rollback
        ;;
    "status")
        show_status
        ;;
    "health")
        run_health_checks
        ;;
    "logs")
        $COMPOSE_CMD logs "${2:-}"
        ;;
    "stop")
        log_info "Stopping services..."
        $COMPOSE_CMD down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting services..."
        $COMPOSE_CMD restart "${2:-}"
        log_success "Services restarted"
        ;;
    "update")
        log_info "Updating deployment..."
        git pull
        main_deploy
        ;;
    "help"|"--help")
        echo "KOL Management System Deployment Script"
        echo
        echo "Usage: $0 [COMMAND]"
        echo
        echo "Commands:"
        echo "  deploy          - Deploy the system (default)"
        echo "  backup          - Create backup of database and files"
        echo "  rollback        - Rollback to previous deployment"
        echo "  status          - Show deployment status"
        echo "  health          - Run health checks"
        echo "  logs [service]  - Show service logs"
        echo "  stop            - Stop all services"
        echo "  restart [service] - Restart services"
        echo "  update          - Update code and redeploy"
        echo "  help            - Show this help"
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Use '$0 help' for available commands"
        exit 1
        ;;
esac