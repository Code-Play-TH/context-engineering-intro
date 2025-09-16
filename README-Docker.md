# KOL Management System - Docker Deployment Guide

This guide provides comprehensive instructions for deploying the KOL Management System using Docker and Docker Compose.

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose V2
- At least 4GB RAM available
- 20GB free disk space

### Production Deployment

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd kol-management-system
   cp .env.example .env
   ```

2. **Configure Environment**
   Edit `.env` file with your production values:
   ```bash
   # Essential settings to change
   JWT_SECRET_KEY=your-super-secret-jwt-key
   DATABASE_PASSWORD=your-secure-db-password
   REDIS_PASSWORD=your-redis-password

   # Add your API keys
   OPENAI_API_KEY=your-openai-key
   SMTP_USER=your-email@domain.com
   SMTP_PASSWORD=your-email-password
   ```

3. **Deploy**
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```

### Development Environment

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f web

# Run tests
docker-compose -f docker-compose.dev.yml exec web test
```

## 🏗️ Architecture

### Services Overview

| Service | Description | Port | Health Check |
|---------|-------------|------|--------------|
| **web** | FastAPI application | 8000 | `/health` |
| **worker** | Celery background tasks | - | Celery inspect |
| **scheduler** | Celery beat scheduler | - | Process check |
| **postgres** | PostgreSQL database | 5432 | `pg_isready` |
| **redis** | Cache and message broker | 6379 | Redis ping |
| **flower** | Task monitoring | 5555 | HTTP check |
| **nginx** | Reverse proxy (optional) | 80/443 | HTTP check |

### Optional Services

| Service | Description | Port | Profile |
|---------|-------------|------|---------|
| **prometheus** | Metrics collection | 9090 | monitoring |
| **grafana** | Metrics visualization | 3000 | monitoring |

## 📁 Directory Structure

```
docker/
├── entrypoint.sh          # Production entrypoint
├── entrypoint-dev.sh      # Development entrypoint
├── nginx.conf             # Nginx configuration
├── init-db.sql           # Database initialization
├── prometheus.yml         # Prometheus config
└── grafana/
    ├── dashboards/        # Grafana dashboards
    └── datasources/       # Data source configs
```

## ⚙️ Configuration

### Environment Files

- `.env.example` - Template with all options
- `.env` - Production configuration (create from example)

### Key Configuration Sections

#### Database Settings
```env
DATABASE_URL=postgresql+asyncpg://koluser:kolpassword@postgres:5432/kolsystem
DATABASE_NAME=kolsystem
DATABASE_USER=koluser
DATABASE_PASSWORD=kolpassword
```

#### Security Settings
```env
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
ALLOWED_HOSTS=localhost,yourdomain.com
```

#### External APIs
```env
# AI Services
OPENAI_API_KEY=your-openai-api-key

# Social Media APIs
INSTAGRAM_CLIENT_ID=your-instagram-client-id
YOUTUBE_API_KEY=your-youtube-api-key
TWITTER_API_KEY=your-twitter-api-key

# Communication
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 🛠️ Management Commands

### Using Deploy Script

```bash
# Full deployment
./scripts/deploy.sh

# Other commands
./scripts/deploy.sh backup      # Create backup
./scripts/deploy.sh rollback    # Rollback deployment
./scripts/deploy.sh status      # Show status
./scripts/deploy.sh logs web    # View logs
./scripts/deploy.sh stop        # Stop services
./scripts/deploy.sh restart     # Restart services
```

### Using Docker Compose Directly

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Scale workers
docker-compose up -d --scale worker=3

# Execute commands in container
docker-compose exec web python -m alembic upgrade head
docker-compose exec web python scripts/seed_data.py

# Stop services
docker-compose down

# Remove volumes (DANGEROUS)
docker-compose down -v
```

### Database Operations

```bash
# Run migrations
docker-compose exec web alembic upgrade head

# Create migration
docker-compose exec web alembic revision --autogenerate -m "Description"

# Seed data
docker-compose exec web python scripts/seed_data.py

# Database backup
docker-compose exec postgres pg_dump -U koluser kolsystem > backup.sql

# Database restore
cat backup.sql | docker-compose exec -T postgres psql -U koluser kolsystem
```

### Development Commands

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Run tests
docker-compose -f docker-compose.dev.yml exec web test

# Format code
docker-compose -f docker-compose.dev.yml exec web format

# Run linting
docker-compose -f docker-compose.dev.yml exec web lint

# Access development shell
docker-compose -f docker-compose.dev.yml exec web shell

# Watch test files
docker-compose -f docker-compose.dev.yml exec web test-watch
```

## 🔒 Security Considerations

### Production Security Checklist

- [ ] Change all default passwords in `.env`
- [ ] Generate strong JWT secret keys
- [ ] Configure proper CORS origins
- [ ] Set up SSL certificates in nginx
- [ ] Enable firewall rules
- [ ] Configure proper backup strategy
- [ ] Set up monitoring and alerting
- [ ] Review and secure API keys

### SSL/TLS Setup

1. **Generate certificates:**
   ```bash
   # Self-signed for testing
   openssl req -x509 -newkey rsa:4096 -keyout docker/ssl/private.key -out docker/ssl/cert.pem -days 365 -nodes

   # Or use Let's Encrypt
   certbot certonly --webroot -w /var/www/certbot -d yourdomain.com
   ```

2. **Configure nginx:**
   ```env
   SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
   SSL_KEY_PATH=/etc/nginx/ssl/private.key
   SSL_REDIRECT=true
   ```

3. **Start with proxy profile:**
   ```bash
   docker-compose --profile proxy up -d
   ```

## 📊 Monitoring Setup

### Enable Monitoring Stack

```bash
# Start with monitoring profile
docker-compose --profile monitoring up -d

# Access monitoring services
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/grafanapassword)
```

### Grafana Setup

1. Login to Grafana (admin/grafanapassword)
2. Prometheus datasource is pre-configured
3. Import dashboards from `docker/grafana/dashboards/`
4. Create alerts for critical metrics

### Custom Metrics

The application exposes metrics at `/metrics` endpoint for Prometheus scraping.

## 🔧 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check logs
docker-compose logs [service_name]

# Check service health
docker-compose ps

# Restart specific service
docker-compose restart [service_name]
```

#### Database Connection Issues
```bash
# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U koluser kolsystem -c "SELECT 1;"

# Reset database
docker-compose down
docker volume rm kol_postgres_data
docker-compose up -d postgres
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Scale workers
docker-compose up -d --scale worker=4

# Check Redis memory usage
docker-compose exec redis redis-cli info memory
```

#### SSL Certificate Issues
```bash
# Verify certificate
openssl x509 -in docker/ssl/cert.pem -text -noout

# Check nginx config
docker-compose exec nginx nginx -t

# Restart nginx
docker-compose restart nginx
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database health
docker-compose exec postgres pg_isready -U koluser

# Redis health
docker-compose exec redis redis-cli ping

# Celery workers
docker-compose exec worker celery -A app.tasks.celery inspect ping
```

### Log Analysis

```bash
# Follow all logs
docker-compose logs -f

# Filter by service
docker-compose logs -f web worker

# Search logs
docker-compose logs web | grep ERROR

# Export logs
docker-compose logs --no-color > system.log
```

## 📈 Performance Tuning

### Resource Limits

Update `docker-compose.yml` with resource limits:

```yaml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### Database Optimization

```bash
# Tune PostgreSQL settings
docker-compose exec postgres psql -U koluser kolsystem -c "
SHOW shared_buffers;
SHOW work_mem;
SHOW effective_cache_size;
"
```

### Redis Configuration

```bash
# Monitor Redis performance
docker-compose exec redis redis-cli info stats
docker-compose exec redis redis-cli info memory
```

## 🔄 Backup and Recovery

### Automated Backups

```bash
# Create backup script
cat > backup_cron.sh << 'EOF'
#!/bin/bash
cd /path/to/project
./scripts/deploy.sh backup
EOF

# Add to crontab
crontab -e
0 2 * * * /path/to/backup_cron.sh
```

### Manual Backup

```bash
# Full backup
./scripts/deploy.sh backup

# Database only
docker-compose exec postgres pg_dump -U koluser kolsystem > db_backup.sql

# Files only
tar -czf uploads_backup.tar.gz uploads/
```

### Recovery

```bash
# Restore from backup
./scripts/deploy.sh rollback

# Restore database manually
cat db_backup.sql | docker-compose exec -T postgres psql -U koluser kolsystem

# Restore files
tar -xzf uploads_backup.tar.gz
```

## 🆙 Updates and Maintenance

### Update Process

```bash
# Update with deploy script
./scripts/deploy.sh update

# Manual update
git pull
docker-compose build --no-cache
docker-compose up -d
```

### Maintenance Tasks

```bash
# Clean up Docker
docker system prune -a

# Update images
docker-compose pull
docker-compose up -d

# Database maintenance
docker-compose exec postgres psql -U koluser kolsystem -c "VACUUM ANALYZE;"
```

## 📞 Support

For deployment issues:

1. Check this documentation
2. Review application logs
3. Check service health endpoints
4. Consult troubleshooting section
5. Open GitHub issue with logs and configuration