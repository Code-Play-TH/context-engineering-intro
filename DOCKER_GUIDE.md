# 🐳 Docker Setup Guide

## Quick Start (1 Command!)

```bash
docker-compose up --build
```

Wait 1-2 minutes for everything to start, then:

-   **Frontend**: http://localhost:3000
-   **Backend API**: http://localhost:8000
-   **API Docs**: http://localhost:8000/docs

---

## 🚀 What Happens

### 1. PostgreSQL Database

-   Starts on port 5432
-   Creates database: `kol_management`
-   User: `postgres` / Password: `postgres`

### 2. Backend (FastAPI)

-   Runs migrations automatically
-   Seeds default users
-   Starts on port 8000
-   Auto-reload enabled

### 3. Frontend (Next.js)

-   Installs dependencies
-   Starts dev server on port 3000
-   Hot reload enabled

---

## 🔐 Login Credentials

```
Admin: admin@kolmanagement.com / Admin@123
Manager: manager@kolmanagement.com / Manager@123
AE: ae@kolmanagement.com / AccountExec@123
Viewer: viewer@kolmanagement.com / Viewer@123
```

---

## 📋 Docker Commands

### Start Everything

```bash
docker-compose up
```

### Start in Background

```bash
docker-compose up -d
```

### Rebuild and Start

```bash
docker-compose up --build
```

### Stop Everything

```bash
docker-compose down
```

### Stop and Remove Volumes (Clean Start)

```bash
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

### Restart Service

```bash
docker-compose restart backend
docker-compose restart frontend
```

### Execute Commands in Container

```bash
# Backend shell
docker-compose exec backend bash

# Run migrations
docker-compose exec backend alembic upgrade head

# Seed database
docker-compose exec backend python scripts/seed_admin.py

# Frontend shell
docker-compose exec frontend sh
```

---

## 🔧 Troubleshooting

### Port Already in Use

**Error**: `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution**:

```bash
# Stop conflicting services
# Or change ports in docker-compose.yml
ports:
  - "3001:3000"  # Use port 3001 instead
```

### Database Connection Error

**Error**: `could not connect to server`

**Solution**:

```bash
# Wait for database to be ready
docker-compose logs postgres

# Or restart
docker-compose restart backend
```

### Frontend Module Not Found

**Error**: `Module not found: Can't resolve...`

**Solution**:

```bash
# Rebuild frontend
docker-compose up --build frontend
```

### Clean Start

```bash
# Remove everything and start fresh
docker-compose down -v
docker-compose up --build
```

---

## 📊 Service Status

Check if services are running:

```bash
docker-compose ps
```

Expected output:

```
NAME            STATUS    PORTS
kol-postgres    Up        0.0.0.0:5432->5432/tcp
kol-backend     Up        0.0.0.0:8000->8000/tcp
kol-frontend    Up        0.0.0.0:3000->3000/tcp
```

---

## 🔍 Health Checks

### Backend

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### Frontend

```bash
curl http://localhost:3000
# Expected: HTML response
```

### Database

```bash
docker-compose exec postgres psql -U postgres -d kol_management -c "SELECT 1;"
# Expected: 1
```

---

## 💾 Data Persistence

Data is stored in Docker volumes:

-   `postgres_data` - Database data

To backup:

```bash
docker-compose exec postgres pg_dump -U postgres kol_management > backup.sql
```

To restore:

```bash
docker-compose exec -T postgres psql -U postgres kol_management < backup.sql
```

---

## 🎯 Development Workflow

### 1. Start Services

```bash
docker-compose up -d
```

### 2. Watch Logs

```bash
docker-compose logs -f backend frontend
```

### 3. Make Changes

-   Backend: Edit files in `app/`
-   Frontend: Edit files in `frontend/src/`
-   Changes auto-reload!

### 4. Test

-   Frontend: http://localhost:3000
-   API: http://localhost:8000/docs

### 5. Stop When Done

```bash
docker-compose down
```

---

## 🚀 Production Deployment

For production, create `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
    postgres:
        # Same as dev

    backend:
        build:
            context: .
            dockerfile: Dockerfile.backend
        environment:
            DATABASE_URL: ${DATABASE_URL}
            SECRET_KEY: ${SECRET_KEY}
        command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

    frontend:
        build:
            context: .
            dockerfile: Dockerfile.frontend
        command: npm run build && npm start
```

Run with:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📝 Environment Variables

Edit `docker-compose.yml` to change:

```yaml
environment:
    DATABASE_URL: postgresql://user:pass@host:5432/db
    SECRET_KEY: your-secret-key
    NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
```

---

## 🎉 Success!

If you see:

```
kol-postgres    | database system is ready to accept connections
kol-backend     | INFO:     Uvicorn running on http://0.0.0.0:8000
kol-frontend    | ready - started server on 0.0.0.0:3000
```

**You're ready to go!** 🚀

Open: http://localhost:3000

---

## 📞 Need Help?

1. Check logs: `docker-compose logs -f`
2. Check status: `docker-compose ps`
3. Restart: `docker-compose restart`
4. Clean start: `docker-compose down -v && docker-compose up --build`

---

**Happy Dockering! 🐳**
