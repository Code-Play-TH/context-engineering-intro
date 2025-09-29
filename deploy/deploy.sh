#!/bin/bash
set -euo pipefail

# KOL Management System Deployment Script
# This script deploys the KOL Management System to Kubernetes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
NAMESPACE="kol-system"
if [ "$ENVIRONMENT" = "staging" ]; then
    NAMESPACE="kol-system-staging"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
K8S_DIR="$PROJECT_ROOT/k8s"

# Functions
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

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    # Check if Docker images exist (you might want to customize this)
    log_info "Checking Docker images..."
    # docker pull kolsystem/api:latest || log_warning "Could not pull latest API image"

    log_success "Prerequisites check completed"
}

create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    kubectl apply -f "$K8S_DIR/namespace.yaml"
    log_success "Namespace created/updated"
}

setup_secrets() {
    log_info "Setting up secrets..."

    # Check if secrets file exists
    if [ ! -f "$K8S_DIR/secrets.yaml" ]; then
        log_error "secrets.yaml not found. Please create it from secrets.yaml.template"
        exit 1
    fi

    # Warn about default values
    if grep -q "CHANGE_ME" "$K8S_DIR/secrets.yaml"; then
        log_warning "Found default values in secrets.yaml. Please update them for production!"
        if [ "$ENVIRONMENT" = "production" ]; then
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    kubectl apply -f "$K8S_DIR/secrets.yaml"
    log_success "Secrets applied"
}

setup_configmaps() {
    log_info "Setting up configuration..."
    kubectl apply -f "$K8S_DIR/configmap.yaml"
    log_success "ConfigMaps applied"
}

deploy_database() {
    log_info "Deploying PostgreSQL database..."
    kubectl apply -f "$K8S_DIR/postgres.yaml"

    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s

    log_success "PostgreSQL deployed successfully"
}

deploy_redis() {
    log_info "Deploying Redis cache..."
    kubectl apply -f "$K8S_DIR/redis.yaml"

    # Wait for Redis to be ready
    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=300s

    log_success "Redis deployed successfully"
}

run_migrations() {
    log_info "Running database migrations..."

    # Create a migration job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: kol-migrations-$(date +%s)
  namespace: $NAMESPACE
  labels:
    app: kol-migrations
spec:
  template:
    spec:
      containers:
      - name: migrations
        image: kolsystem/api:latest
        command: ["python", "-m", "alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: kol-system-secrets
              key: DATABASE_URL
      restartPolicy: Never
  backoffLimit: 3
EOF

    # Wait for migration to complete
    log_info "Waiting for migrations to complete..."
    kubectl wait --for=condition=complete job -l app=kol-migrations -n "$NAMESPACE" --timeout=300s

    log_success "Database migrations completed"
}

deploy_api() {
    log_info "Deploying API service..."
    kubectl apply -f "$K8S_DIR/api-deployment.yaml"

    # Wait for API to be ready
    log_info "Waiting for API service to be ready..."
    kubectl wait --for=condition=available deployment/kol-api -n "$NAMESPACE" --timeout=300s

    log_success "API service deployed successfully"
}

deploy_celery() {
    log_info "Deploying Celery workers and scheduler..."
    kubectl apply -f "$K8S_DIR/celery-deployment.yaml"

    # Wait for Celery workers to be ready
    log_info "Waiting for Celery workers to be ready..."
    kubectl wait --for=condition=available deployment/celery-worker -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=available deployment/celery-beat -n "$NAMESPACE" --timeout=300s

    log_success "Celery services deployed successfully"
}

deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    kubectl apply -f "$K8S_DIR/monitoring.yaml"

    log_success "Monitoring stack deployed"
}

setup_ingress() {
    log_info "Setting up ingress..."
    kubectl apply -f "$K8S_DIR/ingress.yaml"

    log_success "Ingress configured"
}

verify_deployment() {
    log_info "Verifying deployment..."

    # Check pod status
    echo "Pod status:"
    kubectl get pods -n "$NAMESPACE"

    # Check service status
    echo -e "\nService status:"
    kubectl get services -n "$NAMESPACE"

    # Check ingress status
    echo -e "\nIngress status:"
    kubectl get ingress -n "$NAMESPACE"

    # Test API health endpoint
    log_info "Testing API health endpoint..."
    if [ "$ENVIRONMENT" = "production" ]; then
        API_URL="https://api.kolsystem.com"
    else
        API_URL="https://staging-api.kolsystem.com"
    fi

    # Wait a bit for ingress to be ready
    sleep 30

    if curl -f "$API_URL/health" &> /dev/null; then
        log_success "API health check passed"
    else
        log_warning "API health check failed - this might be normal if DNS/ingress is still propagating"
    fi

    log_success "Deployment verification completed"
}

rollback_deployment() {
    log_warning "Rolling back deployment..."

    kubectl rollout undo deployment/kol-api -n "$NAMESPACE"
    kubectl rollout undo deployment/celery-worker -n "$NAMESPACE"

    log_success "Rollback completed"
}

print_access_info() {
    log_info "Deployment completed successfully!"
    echo
    echo "Access Information:"
    echo "=================="

    if [ "$ENVIRONMENT" = "production" ]; then
        echo "API: https://api.kolsystem.com"
        echo "Web App: https://app.kolsystem.com"
        echo "Monitoring: https://monitoring.kolsystem.com"
    else
        echo "API: https://staging-api.kolsystem.com"
        echo "Web App: https://staging.kolsystem.com"
        echo "Monitoring: https://staging-monitoring.kolsystem.com"
    fi

    echo
    echo "Kubernetes Resources:"
    echo "===================="
    echo "Namespace: $NAMESPACE"
    echo "View pods: kubectl get pods -n $NAMESPACE"
    echo "View logs: kubectl logs -f deployment/kol-api -n $NAMESPACE"
    echo "View services: kubectl get services -n $NAMESPACE"
    echo
    echo "Monitoring:"
    echo "==========="
    echo "Flower (Celery): kubectl port-forward service/flower-service -n $NAMESPACE 5555:5555"
    echo "Grafana: kubectl port-forward service/grafana-service -n $NAMESPACE 3000:3000"
    echo "Prometheus: kubectl port-forward service/prometheus-service -n $NAMESPACE 9090:9090"
}

# Main execution
main() {
    echo "=========================================="
    echo "KOL Management System Deployment"
    echo "Environment: $ENVIRONMENT"
    echo "Namespace: $NAMESPACE"
    echo "=========================================="

    # Parse command line arguments
    SKIP_PREREQS=false
    ROLLBACK=false
    SKIP_MIGRATIONS=false

    while [[ $# -gt 1 ]]; do
        case $1 in
            --skip-prereqs)
                SKIP_PREREQS=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --skip-migrations)
                SKIP_MIGRATIONS=true
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Handle rollback
    if [ "$ROLLBACK" = true ]; then
        rollback_deployment
        exit 0
    fi

    # Run deployment steps
    if [ "$SKIP_PREREQS" != true ]; then
        check_prerequisites
    fi

    create_namespace
    setup_secrets
    setup_configmaps

    # Deploy infrastructure
    deploy_database
    deploy_redis

    # Run migrations
    if [ "$SKIP_MIGRATIONS" != true ]; then
        run_migrations
    fi

    # Deploy application
    deploy_api
    deploy_celery

    # Deploy monitoring (optional)
    if [ "$ENVIRONMENT" = "production" ]; then
        deploy_monitoring
    fi

    # Setup networking
    setup_ingress

    # Verify and provide access info
    verify_deployment
    print_access_info
}

# Trap errors and provide cleanup
trap 'log_error "Deployment failed! Check the logs above for details."' ERR

# Run main function
main "$@"