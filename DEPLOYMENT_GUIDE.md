# Production Deployment Guide

## 🚀 KOL Management System - Production Deployment

This guide will help you deploy the KOL Management System to a production server with custom ports to avoid conflicts with other applications.

---

## 📋 Custom Ports Configuration

All ports are configured in `.env.production` to avoid conflicts:

| Service | Default Port | Custom Port | Description |
|---------|--------------|-------------|-------------|
| **API Server** | 8000 | **8765** | Main FastAPI application |
| **Nginx Proxy** | 80 | **8766** | Reverse proxy |
| **PostgreSQL** | 5432 | **5433** | Database |
| **Redis** | 6379 | **6382** | Cache & message broker |
| **Celery Flower** | 5555 | **5556** | Task monitoring |
| **Prometheus** | 9090 | **9091** | Metrics collection |
| **Grafana** | 3000 | **3001** | Dashboards |

**💡 Tip**: You can change these ports in `.env.production` if needed!

---

## 🔧 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows Server
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk**: Minimum 20GB free space
- **CPU**: 2+ cores

### Software Requirements
```bash
# Docker
docker --version        # 24.0+

# Docker Compose
docker-compose --version  # 2.0+

# curl (for health checks)
curl --version
```

---

## 📦 Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd /path/to/KOLs\ Project

# Make deploy script executable
chmod +x deploy.sh

# Copy environment template
cp .env.production .env.production.local

# Edit configuration
nano .env.production.local
```

### 2. Configure Environment

**⚠️ IMPORTANT**: Change all `CHANGE_THIS` placeholders in `.env.production`:

```bash
# Database
POSTGRES_PASSWORD=your_strong_password_here

# Redis
REDIS_PASSWORD=your_redis_password_here

# Security
SECRET_KEY=your_random_secret_key_at_least_32_characters
JWT_SECRET_KEY=your_jwt_secret_key_here

# Grafana
GRAFANA_ADMIN_PASSWORD=your_grafana_password
```

### 3. Deploy

```bash
# Full deployment
./deploy.sh deploy
```

This will:
1. ✅ Check prerequisites
2. ✅ Validate security configuration
3. ✅ Create necessary directories
4. ✅ Build Docker images
5. ✅ Start all services
6. ✅ Run database migrations
7. ✅ Show service status

---

## 🎯 Deployment Commands

### Basic Commands

```bash
# Full deployment
./deploy.sh deploy

# Update existing deployment
./deploy.sh update

# Start services
./deploy.sh start

# Stop services
./deploy.sh stop

# Restart services
./deploy.sh restart

# View service status
./deploy.sh status

# View logs
./deploy.sh logs

# Backup database
./deploy.sh backup

# Run migrations
./deploy.sh migrate

# Clean up (removes all data!)
./deploy.sh cleanup
```

### Manual Docker Compose Commands

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Stop all services
docker-compose -f docker-compose.production.yml down

# View logs
docker-compose -f docker-compose.production.yml logs -f

# View specific service logs
docker-compose -f docker-compose.production.yml logs -f api

# Rebuild and restart
docker-compose -f docker-compose.production.yml up -d --build
```

---

## 🌐 Access Your Application

After deployment, access the application at:

### Main Services
- **API Server**: `http://your-server-ip:8765`
- **API Documentation**: `http://your-server-ip:8765/docs`
- **Nginx Proxy**: `http://your-server-ip:8766`

### Monitoring
- **Celery Flower**: `http://your-server-ip:5556`
  - Username: `admin` (configure in .env)
  - Password: `admin` (configure in .env)

- **Grafana**: `http://your-server-ip:3001`
  - Username: `admin`
  - Password: (set in GRAFANA_ADMIN_PASSWORD)

- **Prometheus**: `http://your-server-ip:9091`

### Health Check
```bash
curl http://your-server-ip:8765/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-03T..."
}
```

---

## 🔐 Security Configuration

### 1. Change Default Passwords

Edit `.env.production`:

```bash
# Generate strong passwords
openssl rand -base64 32  # For SECRET_KEY
openssl rand -base64 32  # For JWT_SECRET_KEY
openssl rand -base64 16  # For passwords

# Update .env.production
POSTGRES_PASSWORD=<generated_password>
REDIS_PASSWORD=<generated_password>
SECRET_KEY=<generated_key>
JWT_SECRET_KEY=<generated_key>
```

### 2. Configure Firewall

```bash
# Allow only necessary ports
sudo ufw allow 8765/tcp   # API
sudo ufw allow 8766/tcp   # Nginx
sudo ufw allow 5556/tcp   # Flower (optional, only for admins)
sudo ufw allow 3001/tcp   # Grafana (optional, only for admins)

# Enable firewall
sudo ufw enable
```

### 3. Setup SSL/TLS (Recommended)

```bash
# Install certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/key.pem

# Update nginx configuration (uncomment HTTPS server block)
nano nginx/conf.d/api.conf
```

---

## 📊 Monitoring

### View Service Status

```bash
# All services
docker-compose -f docker-compose.production.yml ps

# Specific service
docker ps | grep kolsystem_api
```

### View Logs

```bash
# All logs
docker-compose -f docker-compose.production.yml logs

# Follow logs
docker-compose -f docker-compose.production.yml logs -f

# Specific service
docker-compose -f docker-compose.production.yml logs -f api

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100 api
```

### Check Resource Usage

```bash
# Docker stats
docker stats

# Specific container
docker stats kolsystem_api
```

### Celery Tasks Monitoring

Access Flower at `http://your-server-ip:5556`

Features:
- Active tasks
- Task history
- Worker status
- Task statistics

---

## 💾 Backup & Restore

### Automated Backups

Backups are automatically created in `./backups/` before:
- Updates
- Migrations
- Manual backup command

### Manual Backup

```bash
# Create backup
./deploy.sh backup

# Backup location
ls -lh backups/

# Output: backup_20251003_120000.sql.gz
```

### Restore from Backup

```bash
# Stop application
./deploy.sh stop

# Restore database
gunzip < backups/backup_20251003_120000.sql.gz | \
docker exec -i kolsystem_postgres psql -U $POSTGRES_USER $POSTGRES_DB

# Start application
./deploy.sh start
```

### Backup Schedule (Automated)

Configure in `docker-compose.production.yml`:

```yaml
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"     # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

---

## 🔄 Updates & Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Update deployment
./deploy.sh update
```

This will:
1. Backup database
2. Pull latest images
3. Rebuild application
4. Restart services
5. Run migrations

### Update Dependencies

```bash
# Update requirements
nano requirements-prod.txt

# Rebuild image
docker-compose -f docker-compose.production.yml build --no-cache api

# Restart
docker-compose -f docker-compose.production.yml up -d api
```

### Database Migrations

```bash
# Run migrations
./deploy.sh migrate

# Or manually
docker-compose -f docker-compose.production.yml run --rm api alembic upgrade head

# Create new migration
docker-compose -f docker-compose.production.yml run --rm api \
  alembic revision --autogenerate -m "description"
```

---

## 🐛 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs

# Check specific service
docker-compose -f docker-compose.production.yml logs api

# Check Docker daemon
systemctl status docker
```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8765

# Kill process
sudo kill -9 <PID>

# Or change port in .env.production
nano .env.production
# Change APP_PORT=8765 to APP_PORT=8770
```

### Database Connection Error

```bash
# Check PostgreSQL container
docker-compose -f docker-compose.production.yml logs postgres

# Check if running
docker ps | grep kolsystem_postgres

# Connect to database
docker exec -it kolsystem_postgres psql -U kolsystem_user -d kolsystem_prod
```

### API Returns 502 Bad Gateway

```bash
# Check API logs
docker-compose -f docker-compose.production.yml logs api

# Check API health
curl http://localhost:8765/health

# Restart API
docker-compose -f docker-compose.production.yml restart api
```

### High Memory Usage

```bash
# Check stats
docker stats

# Adjust worker count in .env.production
WORKERS=2                    # Reduce from 4 to 2
CELERY_WORKER_CONCURRENCY=2  # Reduce from 4 to 2

# Restart
./deploy.sh restart
```

---

## 📈 Performance Tuning

### PostgreSQL

Edit `docker-compose.production.yml`:

```yaml
postgres:
  command:
    - "postgres"
    - "-c"
    - "max_connections=200"      # Adjust based on load
    - "-c"
    - "shared_buffers=512MB"     # 25% of RAM
    - "-c"
    - "effective_cache_size=2GB" # 50-75% of RAM
```

### Redis

```yaml
redis:
  command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

### Gunicorn Workers

```bash
# In .env.production
WORKERS=4                    # (2 × CPU cores) + 1
WORKER_CLASS=uvicorn.workers.UvicornWorker
TIMEOUT=60
```

### Nginx

Edit `nginx/nginx.conf`:

```nginx
worker_processes auto;       # Auto-detect CPU cores
worker_connections 2048;     # Connections per worker
keepalive_timeout 65;        # Keep-alive timeout
```

---

## 🔍 Health Checks

### Automated Health Checks

```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8765/health || exit 1
EOF

chmod +x monitor.sh

# Add to crontab (check every 5 minutes)
crontab -e
*/5 * * * * /path/to/monitor.sh || systemctl restart docker-compose
```

### Manual Health Checks

```bash
# API health
curl http://localhost:8765/health

# Database health
docker exec kolsystem_postgres pg_isready -U kolsystem_user

# Redis health
docker exec kolsystem_redis redis-cli ping
```

---

## 📞 Support

### Get Help

```bash
# View deployment help
./deploy.sh help

# Check service status
./deploy.sh status

# View logs
./deploy.sh logs
```

### Common Issues

1. **Port conflicts**: Change ports in `.env.production`
2. **Permission errors**: Check file ownership
3. **Out of memory**: Reduce worker count
4. **Database errors**: Check PostgreSQL logs
5. **Network issues**: Check firewall settings

---

## ✅ Post-Deployment Checklist

- [ ] Changed all default passwords
- [ ] Configured firewall rules
- [ ] Setup SSL/TLS certificates
- [ ] Verified all services are running
- [ ] Checked API health endpoint
- [ ] Tested API documentation
- [ ] Configured automated backups
- [ ] Setup monitoring alerts
- [ ] Reviewed security headers
- [ ] Tested database connections
- [ ] Verified Celery tasks are running
- [ ] Checked disk space
- [ ] Configured log rotation

---

## 📚 Additional Resources

- **API Documentation**: `http://your-server:8765/docs`
- **Project README**: `README.md`
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Session Summary**: `SESSION_SUMMARY.md`

---

**Deployment successful! 🎉**

Your KOL Management System is now running in production with custom ports to avoid conflicts.

For support or questions, check the logs or refer to the documentation files.
