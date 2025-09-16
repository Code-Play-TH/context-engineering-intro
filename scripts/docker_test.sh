#!/bin/bash
# Docker-based testing script for KOL Management System
# Runs comprehensive validation using Docker containers

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_DEV_FILE="docker-compose.dev.yml"

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

# Function to check Docker availability
check_docker() {
    log_info "Checking Docker availability..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Check Docker Compose
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

    log_success "Docker environment ready"
}

# Function to build development images
build_dev_images() {
    log_info "Building development Docker images..."

    $COMPOSE_CMD -f $COMPOSE_DEV_FILE build --no-cache

    if [ $? -eq 0 ]; then
        log_success "Development images built successfully"
    else
        log_error "Failed to build development images"
        exit 1
    fi
}

# Function to start test environment
start_test_environment() {
    log_info "Starting test environment..."

    # Start core services
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE up -d postgres redis

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 15

    # Check if services are healthy
    if ! $COMPOSE_CMD -f $COMPOSE_DEV_FILE ps postgres | grep -q "healthy"; then
        log_error "PostgreSQL service is not healthy"
        $COMPOSE_CMD -f $COMPOSE_DEV_FILE logs postgres
        exit 1
    fi

    if ! $COMPOSE_CMD -f $COMPOSE_DEV_FILE ps redis | grep -q "healthy"; then
        log_error "Redis service is not healthy"
        $COMPOSE_CMD -f $COMPOSE_DEV_FILE logs redis
        exit 1
    fi

    log_success "Test environment started successfully"
}

# Function to run system validation
run_system_validation() {
    log_info "Running system validation..."

    # Run the validation script in container
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python scripts/validate_system.py

    if [ $? -eq 0 ]; then
        log_success "System validation passed"
    else
        log_warning "System validation completed with warnings/issues"
    fi
}

# Function to run unit tests
run_unit_tests() {
    log_info "Running unit tests..."

    $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m pytest tests/ -v --tb=short

    if [ $? -eq 0 ]; then
        log_success "Unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Function to run specific test categories
run_test_category() {
    local category=$1
    log_info "Running $category tests..."

    case $category in
        "auth")
            $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m pytest tests/test_core/test_auth.py tests/test_api/test_auth.py tests/test_tasks/test_auth.py -v
            ;;
        "api")
            $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m pytest tests/test_api/ -v
            ;;
        "models")
            $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m pytest tests/test_models/ -v
            ;;
        "core")
            $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m pytest tests/test_core/ -v
            ;;
        "tasks")
            $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m pytest tests/test_tasks/ -v
            ;;
        *)
            log_error "Unknown test category: $category"
            return 1
            ;;
    esac

    if [ $? -eq 0 ]; then
        log_success "$category tests passed"
        return 0
    else
        log_error "$category tests failed"
        return 1
    fi
}

# Function to run code quality checks
run_code_quality() {
    log_info "Running code quality checks..."

    # Run linting
    log_info "Running flake8 linting..."
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m flake8 app tests --max-line-length=88 --extend-ignore=E203,W503

    # Run type checking
    log_info "Running mypy type checking..."
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m mypy app --ignore-missing-imports

    # Run security checks
    log_info "Running bandit security checks..."
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m bandit -r app -f json || true

    log_success "Code quality checks completed"
}

# Function to test application startup
test_application_startup() {
    log_info "Testing application startup..."

    # Start the web application
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE up -d web

    # Wait for application to start
    log_info "Waiting for application to start..."
    sleep 30

    # Check if application is responsive
    max_retries=10
    retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if $COMPOSE_CMD -f $COMPOSE_DEV_FILE exec web curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Application startup test passed"
            return 0
        fi

        retry_count=$((retry_count + 1))
        log_info "Startup test attempt $retry_count/$max_retries failed, retrying..."
        sleep 5
    done

    log_error "Application startup test failed"
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE logs web
    return 1
}

# Function to test database migrations
test_database_migrations() {
    log_info "Testing database migrations..."

    # Run migrations
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE run --rm web python -m alembic upgrade head

    if [ $? -eq 0 ]; then
        log_success "Database migrations test passed"
        return 0
    else
        log_error "Database migrations test failed"
        return 1
    fi
}

# Function to test Celery workers
test_celery_workers() {
    log_info "Testing Celery workers..."

    # Start a worker
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE up -d worker

    # Wait for worker to start
    sleep 10

    # Test worker connectivity
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE exec worker celery -A app.tasks.celery inspect ping

    if [ $? -eq 0 ]; then
        log_success "Celery workers test passed"
        return 0
    else
        log_error "Celery workers test failed"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    log_info "Running integration tests..."

    # Start full environment
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE up -d

    # Wait for all services
    sleep 45

    # Run integration tests
    $COMPOSE_CMD -f $COMPOSE_DEV_FILE exec web python -m pytest tests/ -m integration -v

    local result=$?

    if [ $result -eq 0 ]; then
        log_success "Integration tests passed"
    else
        log_warning "Integration tests completed with issues"
    fi

    return $result
}

# Function to cleanup test environment
cleanup_test_environment() {
    log_info "Cleaning up test environment..."

    $COMPOSE_CMD -f $COMPOSE_DEV_FILE down -v

    # Clean up Docker images if requested
    if [ "$CLEANUP_IMAGES" = "true" ]; then
        log_info "Cleaning up Docker images..."
        docker system prune -f
    fi

    log_success "Test environment cleaned up"
}

# Function to show test summary
show_test_summary() {
    local total_tests=$1
    local passed_tests=$2
    local failed_tests=$3

    echo
    echo "=" * 60
    echo "TEST SUMMARY"
    echo "=" * 60
    echo "Total Tests: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $failed_tests"
    echo "Success Rate: $(echo "scale=2; $passed_tests * 100 / $total_tests" | bc)%"

    if [ $failed_tests -eq 0 ]; then
        log_success "🎉 All tests passed!"
    else
        log_warning "⚠️  $failed_tests test(s) failed"
    fi
    echo "=" * 60
}

# Main test function
run_comprehensive_tests() {
    log_info "Starting comprehensive Docker-based testing..."

    local total_tests=0
    local passed_tests=0
    local failed_tests=0

    # Array of test functions
    declare -a test_functions=(
        "run_system_validation:System Validation"
        "test_database_migrations:Database Migrations"
        "test_application_startup:Application Startup"
        "test_celery_workers:Celery Workers"
        "run_unit_tests:Unit Tests"
        "run_code_quality:Code Quality"
    )

    for test_func in "${test_functions[@]}"; do
        IFS=':' read -r func_name test_name <<< "$test_func"
        total_tests=$((total_tests + 1))

        echo
        log_info "Running: $test_name"
        echo "-" * 50

        if $func_name; then
            passed_tests=$((passed_tests + 1))
        else
            failed_tests=$((failed_tests + 1))
        fi
    done

    show_test_summary $total_tests $passed_tests $failed_tests

    return $failed_tests
}

# Parse command line arguments
case "${1:-all}" in
    "all"|"comprehensive")
        check_docker
        build_dev_images
        start_test_environment
        run_comprehensive_tests
        exit_code=$?
        cleanup_test_environment
        exit $exit_code
        ;;
    "quick")
        check_docker
        build_dev_images
        start_test_environment
        run_unit_tests
        exit_code=$?
        cleanup_test_environment
        exit $exit_code
        ;;
    "validation")
        check_docker
        build_dev_images
        start_test_environment
        run_system_validation
        cleanup_test_environment
        ;;
    "unit")
        check_docker
        build_dev_images
        start_test_environment
        run_unit_tests
        exit_code=$?
        cleanup_test_environment
        exit $exit_code
        ;;
    "integration")
        check_docker
        build_dev_images
        run_integration_tests
        exit_code=$?
        cleanup_test_environment
        exit $exit_code
        ;;
    "startup")
        check_docker
        build_dev_images
        start_test_environment
        test_application_startup
        exit_code=$?
        cleanup_test_environment
        exit $exit_code
        ;;
    "auth"|"api"|"models"|"core"|"tasks")
        check_docker
        build_dev_images
        start_test_environment
        run_test_category "$1"
        exit_code=$?
        cleanup_test_environment
        exit $exit_code
        ;;
    "quality")
        check_docker
        build_dev_images
        start_test_environment
        run_code_quality
        cleanup_test_environment
        ;;
    "cleanup")
        cleanup_test_environment
        ;;
    "help"|"--help")
        echo "KOL Management System - Docker Testing Script"
        echo
        echo "Usage: $0 [COMMAND]"
        echo
        echo "Commands:"
        echo "  all, comprehensive  - Run all tests (default)"
        echo "  quick              - Run unit tests only"
        echo "  validation         - Run system validation"
        echo "  unit               - Run unit tests"
        echo "  integration        - Run integration tests"
        echo "  startup            - Test application startup"
        echo "  auth               - Run authentication tests"
        echo "  api                - Run API tests"
        echo "  models             - Run model tests"
        echo "  core               - Run core tests"
        echo "  tasks              - Run task tests"
        echo "  quality            - Run code quality checks"
        echo "  cleanup            - Clean up test environment"
        echo "  help               - Show this help"
        echo
        echo "Environment variables:"
        echo "  CLEANUP_IMAGES=true - Clean up Docker images after tests"
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Use '$0 help' for available commands"
        exit 1
        ;;
esac