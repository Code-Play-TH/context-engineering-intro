# Factory ERP System - Deployment Guide

This guide covers deploying the Factory ERP System in both development and production environments using Docker Compose.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Environment Configuration](#environment-configuration)
- [Database Management](#database-management)
- [Security Considerations](#security-considerations)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Development Environment

```bash
# 1. Clone the repository
git clone <repository-url>
cd erp-factory

# 2. Setup development environment
make dev-setup

# 3. Edit .env file with your configuration
vim .env

# 4. Start development environment
make dev-up

# 5. Access the application
open http://localhost:8000
```

### Production Deployment

```bash
# 1. Setup production environment
make prod-setup

# 2. Edit .env.production with secure configuration
vim .env.production

# 3. Build and start production environment
make prod-build
make prod-up
```

## Development Setup

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Make (optional, for using Makefile commands)
- Git

### Development Environment Features

- **Hot Reload**: Code changes automatically reload the application
- **Debug Mode**: Enhanced logging and error details
- **Development Tools**: pgAdmin, Redis Commander
- **Seed Data**: Automatic test data population
- **Direct Access**: Application accessible on localhost:8000

### Starting Development Environment

```bash
# Start all services
docker-compose up -d

# Or using Makefile
make dev-up
```

### Development Services

- **Application**: http://localhost:8000
- **Database**: localhost:5433 (postgres/dev_password)
- **Redis**: localhost:6380
- **pgAdmin**: http://localhost:5050 (admin@factory-erp.dev/admin)
- **Redis Commander**: http://localhost:8081 (admin/admin)

### Development Commands

```bash
# View logs
make dev-logs

# Stop services
make dev-down

# Clean environment (removes all data)
make dev-clean

# Run tests
make test

# Open application shell
make shell
```

## Production Deployment

### Production Environment Features

- **Security Hardening**: Non-root users, read-only filesystems
- **Resource Limits**: CPU and memory constraints
- **High Availability**: Automatic restarts, health checks
- **Reverse Proxy**: Nginx with SSL termination
- **Monitoring**: Prometheus and Grafana (optional)
- **Optimized Performance**: Production-tuned database and application settings

### Production Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Sufficient system resources:
  - Minimum: 2 CPU cores, 4GB RAM, 20GB disk
  - Recommended: 4 CPU cores, 8GB RAM, 100GB disk
- SSL certificates (for HTTPS)
- Domain name (for production access)

### Production Deployment Steps

#### 1. Environment Setup

```bash
# Create production environment file
cp .env.example .env.production

# Edit with production values
vim .env.production
```

#### 2. Security Configuration

Ensure the following in `.env.production`:

```env
# Strong secret key (32+ characters)
SECRET_KEY=your-super-secure-secret-key-at-least-32-characters

# Secure database password
POSTGRES_PASSWORD=your-very-secure-database-password

# Production settings
DEBUG=false
ENVIRONMENT=production

# Domain configuration
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com
```

#### 3. SSL Certificate Setup

```bash
# Option 1: Generate self-signed certificates (development/testing)
make generate-ssl

# Option 2: Use Let's Encrypt (recommended for production)
# Place certificates in docker/ssl/
cp /path/to/cert.pem docker/ssl/cert.pem
cp /path/to/key.pem docker/ssl/key.pem
```

#### 4. Build and Deploy

```bash
# Build production images
make prod-build

# Start production environment
make prod-up

# Run database migrations
make db-migrate
```

#### 5. Verify Deployment

```bash
# Check health
make health

# View logs
make prod-logs

# Check container stats
make stats
```

### Production Architecture

```
Internet → Nginx (Port 80/443) → FastAPI App (Port 8000)
                ↓
             PostgreSQL (Internal) + Redis (Internal)
```

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|----------|
| `SECRET_KEY` | JWT signing key (32+ chars) | `your-secret-key-32-chars-minimum` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/db` |
| `POSTGRES_PASSWORD` | Database password | `secure-db-password` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|----------|
| `DEBUG` | Enable debug mode | `false` |
| `WORKERS` | Number of worker processes | `4` |
| `LOG_LEVEL` | Logging level | `info` |
| `ERPNEXT_BASE_URL` | ERPNext server URL | None |

See `.env.example` for complete configuration options.

## Database Management

### Migrations

```bash
# Run migrations
make db-migrate

# Rollback last migration
make db-rollback

# Create new migration
docker-compose exec factory-erp alembic revision --autogenerate -m "Description"
```

### Backups

```bash
# Create backup
make db-backup

# Manual backup
docker-compose exec postgres pg_dump -U postgres factory_erp > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres factory_erp < backup.sql
```

### Seed Data

```bash
# Load seed data
make db-seed

# Or set in environment
RUN_SEED_DATA=true docker-compose up -d
```

## Security Considerations

### Production Security Checklist

- [ ] Strong, unique `SECRET_KEY` (32+ characters)
- [ ] Secure database passwords
- [ ] `DEBUG=false` in production
- [ ] HTTPS enabled with valid certificates
- [ ] Firewall configured (only necessary ports open)
- [ ] Regular security updates
- [ ] Database not exposed to public internet
- [ ] Application logs monitored
- [ ] Regular backups configured

### Network Security

- Application and database communicate over internal Docker network
- Only Nginx exposed to internet (ports 80/443)
- Database and Redis not accessible from outside
- Internal services use container names for communication

### Container Security

- Non-root user inside containers
- Read-only filesystem where possible
- Resource limits applied
- Security options enabled (no-new-privileges)
- Regular image updates

## Monitoring

### Built-in Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Detailed health check
HEALTH_CHECK_VERBOSE=true docker-compose exec factory-erp python /healthcheck.py
```

### Optional Monitoring Stack

```bash
# Start monitoring services
make monitoring-up

# Access monitoring
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000 (admin/admin)
```

### Log Management

```bash
# View application logs
make logs

# View all service logs
docker-compose logs -f

# Log rotation is configured automatically
```

## Troubleshooting

### Common Issues

#### Application Won't Start

```bash
# Check logs
make logs

# Verify environment variables
docker-compose config

# Check database connection
make db-shell
```

#### Database Connection Issues

```bash
# Check database status
docker-compose exec postgres pg_isready

# Check database logs
docker-compose logs postgres

# Verify connection string
echo $DATABASE_URL
```

#### Performance Issues

```bash
# Check resource usage
make stats

# Increase worker count
WORKERS=8 docker-compose up -d factory-erp

# Check database performance
docker-compose exec postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

#### SSL Certificate Issues

```bash
# Verify certificate files
ls -la docker/ssl/

# Test certificate
openssl x509 -in docker/ssl/cert.pem -text -noout

# Check certificate expiration
openssl x509 -in docker/ssl/cert.pem -noout -dates
```

### Debug Commands

```bash
# Open application shell
make shell

# Run database shell
make db-shell

# View container processes
docker-compose top

# Inspect container
docker inspect factory-erp-app
```

### Getting Help

1. Check application logs first
2. Verify environment configuration
3. Test database connectivity
4. Check resource availability
5. Review Docker and Docker Compose versions
6. Consult application documentation

## Maintenance

### Regular Tasks

```bash
# Update application
make update

# Clean unused images
make clean-images

# Backup database
make db-backup

# Check security updates
docker scan factory-erp:latest
```

### Scaling

To scale the application:

```bash
# Scale application instances
docker-compose up -d --scale factory-erp=3

# Update worker count
WORKERS=auto docker-compose up -d factory-erp
```

### Updates and Upgrades

1. Backup database
2. Test in staging environment
3. Update during maintenance window
4. Monitor application after update
5. Have rollback plan ready

---

For additional help or specific deployment scenarios, please refer to the application documentation or contact the development team.