# Factory ERP System - Makefile
# Simplified deployment and development commands

# Variables
APP_NAME := factory-erp
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := $(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.override.yml
DOCKER_COMPOSE_PROD := $(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.production.yml

# Default target
.DEFAULT_GOAL := help

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

.PHONY: help
help: ## Show this help message
	@echo "$(GREEN)Factory ERP System - Available Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# Development Commands
.PHONY: dev-setup
dev-setup: ## Setup development environment
	@echo "$(GREEN)Setting up development environment...$(NC)"
	mkdir -p dev-data/{logs,uploads,postgres,redis}
	cp .env.example .env
	@echo "$(YELLOW)Please edit .env file with your configuration$(NC)"

.PHONY: dev-up
dev-up: ## Start development environment
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE_DEV) up -d
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "Application: http://localhost:8000"
	@echo "Database: localhost:5433"
	@echo "Redis: localhost:6380"

.PHONY: dev-logs
dev-logs: ## View development logs
	$(DOCKER_COMPOSE_DEV) logs -f

.PHONY: dev-down
dev-down: ## Stop development environment
	@echo "$(GREEN)Stopping development environment...$(NC)"
	$(DOCKER_COMPOSE_DEV) down

.PHONY: dev-clean
dev-clean: ## Clean development environment (remove volumes)
	@echo "$(RED)Warning: This will remove all development data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(DOCKER_COMPOSE_DEV) down -v; \
		rm -rf dev-data; \
		echo "$(GREEN)Development environment cleaned$(NC)"; \
	fi

# Production Commands
.PHONY: prod-setup
prod-setup: ## Setup production environment
	@echo "$(GREEN)Setting up production environment...$(NC)"
	cp .env.example .env.production
	@echo "$(YELLOW)Please edit .env.production file with your production configuration$(NC)"
	@echo "$(RED)Remember to set strong passwords and secrets!$(NC)"

.PHONY: prod-build
prod-build: ## Build production images
	@echo "$(GREEN)Building production images...$(NC)"
	$(DOCKER_COMPOSE_PROD) build --no-cache

.PHONY: prod-up
prod-up: ## Start production environment
	@echo "$(GREEN)Starting production environment...$(NC)"
	$(DOCKER_COMPOSE_PROD) --env-file .env.production up -d
	@echo "$(GREEN)Production environment started!$(NC)"

.PHONY: prod-logs
prod-logs: ## View production logs
	$(DOCKER_COMPOSE_PROD) --env-file .env.production logs -f

.PHONY: prod-down
prod-down: ## Stop production environment
	@echo "$(GREEN)Stopping production environment...$(NC)"
	$(DOCKER_COMPOSE_PROD) --env-file .env.production down

.PHONY: prod-restart
prod-restart: prod-down prod-up ## Restart production environment

# Database Commands
.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(DOCKER_COMPOSE) exec factory-erp alembic upgrade head

.PHONY: db-rollback
db-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	$(DOCKER_COMPOSE) exec factory-erp alembic downgrade -1

.PHONY: db-seed
db-seed: ## Seed database with test data
	@echo "$(GREEN)Seeding database...$(NC)"
	$(DOCKER_COMPOSE) exec factory-erp python -c "import asyncio; from app.core.seed_data import create_seed_data; asyncio.run(create_seed_data())"

.PHONY: db-backup
db-backup: ## Backup database
	@echo "$(GREEN)Creating database backup...$(NC)"
	mkdir -p backups
	$(DOCKER_COMPOSE) exec postgres pg_dump -U postgres factory_erp > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created in backups/ directory$(NC)"

# Testing Commands
.PHONY: test
test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(DOCKER_COMPOSE) exec factory-erp python -m pytest tests/ -v

.PHONY: test-coverage
test-coverage: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(DOCKER_COMPOSE) exec factory-erp python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

.PHONY: lint
lint: ## Run code linting
	@echo "$(GREEN)Running code linting...$(NC)"
	$(DOCKER_COMPOSE) exec factory-erp flake8 app/
	$(DOCKER_COMPOSE) exec factory-erp black --check app/
	$(DOCKER_COMPOSE) exec factory-erp isort --check-only app/

.PHONY: format
format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	$(DOCKER_COMPOSE) exec factory-erp black app/
	$(DOCKER_COMPOSE) exec factory-erp isort app/

# Maintenance Commands
.PHONY: logs
logs: ## View application logs
	$(DOCKER_COMPOSE) logs -f factory-erp

.PHONY: shell
shell: ## Open application shell
	$(DOCKER_COMPOSE) exec factory-erp /bin/bash

.PHONY: db-shell
db-shell: ## Open database shell
	$(DOCKER_COMPOSE) exec postgres psql -U postgres -d factory_erp

.PHONY: health
health: ## Check application health
	@echo "$(GREEN)Checking application health...$(NC)"
	curl -s http://localhost:8000/health | jq || echo "Application not responding"

.PHONY: stats
stats: ## Show container stats
	$(DOCKER_COMPOSE) ps
	docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"

# Monitoring Commands (requires monitoring profile)
.PHONY: monitoring-up
monitoring-up: ## Start monitoring stack
	@echo "$(GREEN)Starting monitoring stack...$(NC)"
	$(DOCKER_COMPOSE_PROD) --profile monitoring up -d
	@echo "$(GREEN)Monitoring started!$(NC)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000 (admin/admin)"

.PHONY: monitoring-down
monitoring-down: ## Stop monitoring stack
	$(DOCKER_COMPOSE_PROD) --profile monitoring down

# Utility Commands
.PHONY: clean-images
clean-images: ## Clean unused Docker images
	@echo "$(GREEN)Cleaning unused Docker images...$(NC)"
	docker image prune -f
	docker system prune -f

.PHONY: update
update: ## Update application (pull latest images)
	@echo "$(GREEN)Updating application...$(NC)"
	$(DOCKER_COMPOSE) pull
	$(DOCKER_COMPOSE) up -d

.PHONY: reset
reset: ## Reset entire environment (DANGER: removes all data)
	@echo "$(RED)WARNING: This will remove all data and containers!$(NC)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(DOCKER_COMPOSE) down -v; \
		docker system prune -af; \
		rm -rf dev-data; \
		echo "$(GREEN)Environment reset complete$(NC)"; \
	else \
		echo "$(YELLOW)Reset cancelled$(NC)"; \
	fi

# Security Commands
.PHONY: security-scan
security-scan: ## Run security scan on Docker images
	@echo "$(GREEN)Running security scan...$(NC)"
	docker scan $(APP_NAME):latest || echo "Docker scan not available"

# SSL/Certificate Commands (for production)
.PHONY: generate-ssl
generate-ssl: ## Generate self-signed SSL certificates (development only)
	@echo "$(GREEN)Generating self-signed SSL certificates...$(NC)"
	mkdir -p docker/ssl
	openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout docker/ssl/key.pem \
		-out docker/ssl/cert.pem \
		-config <(echo "[req]"; echo "distinguished_name=req"; echo "[san]"; echo "subjectAltName=DNS:localhost,IP:127.0.0.1") \
		-extensions san
	@echo "$(YELLOW)Self-signed certificates generated in docker/ssl/$(NC)"
	@echo "$(RED)WARNING: Only use for development! Use proper certificates in production.$(NC)"