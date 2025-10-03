# Port Configuration Guide

## 🔌 Custom Ports Setup

This document explains the custom port configuration to avoid conflicts with other applications on your server.

---

## 📊 Port Mapping Table

### Production Ports (Customized)

| Service | Internal Port | External Port | Configurable In | Purpose |
|---------|---------------|---------------|-----------------|---------|
| **FastAPI Application** | 8000 | **8765** | `.env.production` → `APP_PORT` | Main API server |
| **Nginx Reverse Proxy** | 80 | **8766** | `.env.production` → `NGINX_PORT` | HTTP access |
| **Nginx SSL/TLS** | 443 | **8767** | `docker-compose.production.yml` | HTTPS access |
| **PostgreSQL** | 5432 | **5433** | `.env.production` → `POSTGRES_PORT` | Database |
| **Redis** | 6379 | **6382** | `.env.production` → `REDIS_PORT` | Cache & Queue |
| **Celery Flower** | 5555 | **5556** | `.env.production` → `CELERY_FLOWER_PORT` | Task monitoring |
| **Prometheus** | 9090 | **9091** | `.env.production` → `PROMETHEUS_PORT` | Metrics |
| **Grafana** | 3000 | **3001** | `.env.production` → `GRAFANA_PORT` | Dashboards |

---

## 🔧 How to Change Ports

### Option 1: Edit .env.production (Recommended)

```bash
# Open environment file
nano .env.production

# Change ports as needed
APP_PORT=8765            # Change to your preferred port
NGINX_PORT=8766          # Change to your preferred port
POSTGRES_PORT=5433       # Change to your preferred port
REDIS_PORT=6382          # Change to your preferred port
CELERY_FLOWER_PORT=5556  # Change to your preferred port
PROMETHEUS_PORT=9091     # Change to your preferred port
GRAFANA_PORT=3001        # Change to your preferred port
```

### Option 2: Override with Environment Variables

```bash
# Set before deployment
export APP_PORT=9000
export NGINX_PORT=9001

# Then deploy
./deploy.sh deploy
```

---

## 🎯 Port Selection Guidelines

### Recommended Port Ranges

1. **Custom Application Ports**: 8000-8999
   - Example: 8765, 8766, 8767

2. **Database Ports**: 5000-5999
   - Example: 5433 (PostgreSQL custom)

3. **Cache/Message Queue**: 6000-6999
   - Example: 6382 (Redis custom)

4. **Monitoring Tools**: 9000-9999
   - Example: 9091 (Prometheus), 3001 (Grafana)

### Avoid These Common Ports

```
❌ 80    - HTTP (commonly used)
❌ 443   - HTTPS (commonly used)
❌ 3000  - Common dev server port
❌ 5432  - Default PostgreSQL
❌ 6379  - Default Redis
❌ 8000  - Common API port
❌ 8080  - Common proxy port
❌ 9090  - Default Prometheus
```

### Check If Port Is Available

```bash
# Linux/Mac
sudo lsof -i :8765

# Or using netstat
netstat -tuln | grep 8765

# Windows
netstat -ano | findstr :8765
```

---

## 🔍 Finding Available Ports

### Automatic Port Scanner

```bash
# Check ports in range
for port in {8765..8770}; do
    if ! sudo lsof -i :$port > /dev/null 2>&1; then
        echo "Port $port is available"
    else
        echo "Port $port is in use"
    fi
done
```

### Suggested Alternative Ports

If default custom ports are taken, try these:

```bash
# API Server alternatives
8765, 8770, 8775, 8780, 8785

# Nginx alternatives
8766, 8771, 8776, 8781, 8786

# Database alternatives
5433, 5434, 5435, 5436, 5437

# Redis alternatives
6382, 6383, 6384, 6385, 6386

# Monitoring alternatives
9091, 9092, 9093, 9094, 9095
3001, 3002, 3003, 3004, 3005
```

---

## 🚀 Deployment with Custom Ports

### Step 1: Configure Ports

```bash
# Edit .env.production
nano .env.production

# Example configuration
APP_PORT=8765
NGINX_PORT=8766
POSTGRES_PORT=5433
REDIS_PORT=6382
CELERY_FLOWER_PORT=5556
PROMETHEUS_PORT=9091
GRAFANA_PORT=3001
```

### Step 2: Update Firewall

```bash
# Allow custom ports
sudo ufw allow 8765/tcp  # API
sudo ufw allow 8766/tcp  # Nginx
sudo ufw allow 5556/tcp  # Flower (optional)
sudo ufw allow 9091/tcp  # Prometheus (optional)
sudo ufw allow 3001/tcp  # Grafana (optional)

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### Step 3: Deploy

```bash
# Deploy with custom ports
./deploy.sh deploy
```

### Step 4: Verify

```bash
# Check services
./deploy.sh status

# Test API
curl http://localhost:8765/health

# Test Nginx proxy
curl http://localhost:8766/health
```

---

## 📡 Accessing Services

### From Same Server

```bash
# API directly
curl http://localhost:8765/api/v1/...

# Through Nginx
curl http://localhost:8766/api/v1/...

# API Documentation
http://localhost:8765/docs

# Celery Flower
http://localhost:5556

# Grafana
http://localhost:3001

# Prometheus
http://localhost:9091
```

### From Remote Client

```bash
# Replace with your server IP
SERVER_IP=192.168.1.100

# API
curl http://$SERVER_IP:8765/health

# Nginx
curl http://$SERVER_IP:8766/health
```

### Domain Configuration

```nginx
# Configure domain to point to custom port
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8765;
        # ... other proxy settings
    }
}
```

---

## 🔐 Security Considerations

### Internal vs External Ports

**Recommended Setup**:

```yaml
# docker-compose.production.yml

# ✅ SECURE: Only expose what's needed
api:
  ports:
    - "8765:8000"    # Expose API

nginx:
  ports:
    - "8766:80"      # Expose Nginx
    - "8767:443"     # Expose HTTPS

# ✅ SECURE: Don't expose database externally
postgres:
  # No external port mapping
  # Only accessible within Docker network

redis:
  # No external port mapping
  # Only accessible within Docker network

# ⚠️ OPTIONAL: Monitoring (restrict access)
prometheus:
  ports:
    - "127.0.0.1:9091:9090"  # Only localhost

grafana:
  ports:
    - "127.0.0.1:3001:3000"  # Only localhost
```

### Firewall Rules

```bash
# Only allow necessary external access
sudo ufw allow 8765/tcp  # API
sudo ufw allow 8766/tcp  # Nginx
sudo ufw allow 8767/tcp  # HTTPS

# Deny direct database access
sudo ufw deny 5433/tcp

# Deny direct cache access
sudo ufw deny 6382/tcp

# Allow monitoring only from specific IP
sudo ufw allow from 192.168.1.0/24 to any port 3001
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :8765

# Kill the process
sudo kill -9 <PID>

# Or change the port in .env.production
```

### Connection Refused

```bash
# Check if service is running
docker-compose -f docker-compose.production.yml ps

# Check if port is exposed
docker port kolsystem_api

# Check firewall
sudo ufw status
```

### Can't Access from External

```bash
# Check if bound to 0.0.0.0 (not 127.0.0.1)
netstat -tuln | grep 8765

# Should show: 0.0.0.0:8765 (not 127.0.0.1:8765)

# Check firewall allows external access
sudo ufw status | grep 8765
```

---

## 📝 Port Configuration Checklist

Before deployment:

- [ ] Checked all ports are available
- [ ] Updated `.env.production` with custom ports
- [ ] Configured firewall rules
- [ ] Tested port accessibility
- [ ] Updated documentation with actual ports
- [ ] Configured reverse proxy (if using domain)
- [ ] Setup SSL/TLS for HTTPS port
- [ ] Restricted sensitive ports (database, cache)
- [ ] Documented port changes for team
- [ ] Tested all service connections

---

## 🔄 Port Migration

If you need to change ports after deployment:

```bash
# 1. Stop services
./deploy.sh stop

# 2. Update .env.production
nano .env.production

# 3. Update firewall
sudo ufw delete allow 8765/tcp  # Old port
sudo ufw allow 8770/tcp         # New port

# 4. Restart services
./deploy.sh start

# 5. Verify
curl http://localhost:8770/health
```

---

## 📞 Support

If you encounter port conflicts or issues:

1. Check port availability: `sudo lsof -i :<port>`
2. Review firewall rules: `sudo ufw status`
3. Check Docker port mappings: `docker ps`
4. Review logs: `./deploy.sh logs`
5. Check service status: `./deploy.sh status`

---

## 📚 Additional Resources

- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Environment Configuration**: `.env.production`
- **Docker Compose**: `docker-compose.production.yml`
- **Nginx Configuration**: `nginx/conf.d/api.conf`

---

**Port Configuration Complete! 🎉**

Your services are now running on custom ports to avoid conflicts with other applications.
