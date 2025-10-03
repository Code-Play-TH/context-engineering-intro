#!/bin/bash

# Production Deployment Script for KOL Management System
# This script handles the complete deployment process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"

# Functions
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if running as root
check_permissions() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "Please do not run this script as root"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker installed: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose installed: $(docker-compose --version)"

    # Check if .env.production exists
    if [ ! -f "$ENV_FILE" ]; then
        print_error ".env.production file not found"
        print_info "Please create .env.production file from .env.production template"
        exit 1
    fi
    print_success "Environment file found"
}

# Load environment variables
load_env() {
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' $ENV_FILE | xargs)
    fi
}

# Check for sensitive defaults
check_security() {
    print_header "Checking Security Configuration"

    local warnings=0

    # Check for default passwords
    if grep -q "CHANGE_THIS" "$ENV_FILE"; then
        print_error "Found default passwords in .env.production"
        print_info "Please change all CHANGE_THIS placeholders before deployment"
        warnings=$((warnings + 1))
    fi

    # Check if SECRET_KEY is strong
    SECRET_KEY_LENGTH=$(grep "^SECRET_KEY=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '\n' | wc -c)
    if [ "$SECRET_KEY_LENGTH" -lt 32 ]; then
        print_error "SECRET_KEY is too short (minimum 32 characters)"
        warnings=$((warnings + 1))
    fi

    if [ $warnings -gt 0 ]; then
        print_error "Found $warnings security issue(s). Please fix before deployment."
        exit 1
    fi

    print_success "Security configuration looks good"
}

# Create necessary directories
create_directories() {
    print_header "Creating Directories"

    directories=(
        "logs"
        "logs/nginx"
        "uploads"
        "backups"
        "ssl"
        "nginx/conf.d"
        "monitoring/prometheus"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
    )

    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Created $dir"
        else
            print_info "$dir already exists"
        fi
    done
}

# Backup database
backup_database() {
    print_header "Creating Database Backup"

    if docker ps | grep -q kolsystem_postgres; then
        BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

        docker exec kolsystem_postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$BACKUP_FILE"

        if [ -f "$BACKUP_FILE" ]; then
            print_success "Database backed up to $BACKUP_FILE"

            # Compress backup
            gzip "$BACKUP_FILE"
            print_success "Backup compressed"
        else
            print_warning "Backup file not created"
        fi
    else
        print_info "Database container not running, skipping backup"
    fi
}

# Pull latest images
pull_images() {
    print_header "Pulling Latest Docker Images"

    docker-compose -f $COMPOSE_FILE pull
    print_success "Images pulled successfully"
}

# Build application image
build_app() {
    print_header "Building Application Image"

    docker-compose -f $COMPOSE_FILE build --no-cache api
    print_success "Application built successfully"
}

# Run database migrations
run_migrations() {
    print_header "Running Database Migrations"

    # Wait for database to be ready
    print_info "Waiting for database..."
    sleep 10

    docker-compose -f $COMPOSE_FILE run --rm api alembic upgrade head
    print_success "Migrations completed"
}

# Start services
start_services() {
    print_header "Starting Services"

    docker-compose -f $COMPOSE_FILE up -d

    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 15

    # Check health
    if docker ps | grep -q "kolsystem_api.*healthy\|kolsystem_api.*starting"; then
        print_success "Services started successfully"
    else
        print_error "Some services failed to start"
        docker-compose -f $COMPOSE_FILE ps
        exit 1
    fi
}

# Show service status
show_status() {
    print_header "Service Status"

    docker-compose -f $COMPOSE_FILE ps

    echo ""
    print_header "Access Information"
    print_info "API Server:        http://localhost:${APP_PORT:-8765}"
    print_info "API Docs:          http://localhost:${APP_PORT:-8765}/docs"
    print_info "Nginx Proxy:       http://localhost:${NGINX_PORT:-8766}"
    print_info "Celery Flower:     http://localhost:${CELERY_FLOWER_PORT:-5556}"
    print_info "Prometheus:        http://localhost:${PROMETHEUS_PORT:-9091}"
    print_info "Grafana:           http://localhost:${GRAFANA_PORT:-3001}"
    echo ""
    print_info "Logs location:     ./logs"
    print_info "Backups location:  ./backups"
}

# Show logs
show_logs() {
    print_header "Recent Logs"

    docker-compose -f $COMPOSE_FILE logs --tail=50
}

# Stop services
stop_services() {
    print_header "Stopping Services"

    docker-compose -f $COMPOSE_FILE down
    print_success "Services stopped"
}

# Full cleanup
cleanup() {
    print_header "Cleaning Up"

    print_warning "This will remove all containers, networks, and volumes"
    read -p "Are you sure? (yes/no): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f $COMPOSE_FILE down -v
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Restart services
restart_services() {
    print_header "Restarting Services"

    docker-compose -f $COMPOSE_FILE restart
    print_success "Services restarted"
}

# Update deployment
update() {
    backup_database
    pull_images
    build_app
    stop_services
    start_services
    run_migrations
    show_status
}

# Main deployment
deploy() {
    print_header "KOL Management System - Production Deployment"

    check_permissions
    check_prerequisites
    load_env
    check_security
    create_directories
    backup_database
    build_app
    start_services
    run_migrations
    show_status

    print_success "Deployment completed successfully!"
}

# Help message
show_help() {
    cat << EOF
KOL Management System - Deployment Script

Usage: ./deploy.sh [COMMAND]

Commands:
    deploy          Full deployment (build, migrate, start)
    update          Update deployment (backup, rebuild, restart)
    start           Start all services
    stop            Stop all services
    restart         Restart all services
    status          Show service status
    logs            Show service logs
    backup          Backup database
    migrate         Run database migrations
    build           Build application image
    cleanup         Stop and remove all containers and volumes
    help            Show this help message

Examples:
    ./deploy.sh deploy          # Full deployment
    ./deploy.sh update          # Update existing deployment
    ./deploy.sh logs            # View logs
    ./deploy.sh backup          # Create database backup

Port Configuration (in .env.production):
    APP_PORT=${APP_PORT:-8765}                # API Server
    NGINX_PORT=${NGINX_PORT:-8766}            # Nginx Proxy
    POSTGRES_PORT=${POSTGRES_PORT:-5433}      # PostgreSQL
    REDIS_PORT=${REDIS_PORT:-6380}            # Redis
    CELERY_FLOWER_PORT=${CELERY_FLOWER_PORT:-5556}  # Flower
    PROMETHEUS_PORT=${PROMETHEUS_PORT:-9091}  # Prometheus
    GRAFANA_PORT=${GRAFANA_PORT:-3001}        # Grafana

EOF
}

# Parse command
case "${1:-help}" in
    deploy)
        deploy
        ;;
    update)
        update
        ;;
    start)
        start_services
        show_status
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    backup)
        load_env
        backup_database
        ;;
    migrate)
        load_env
        run_migrations
        ;;
    build)
        build_app
        ;;
    cleanup)
        cleanup
        ;;
    help|*)
        show_help
        ;;
esac
