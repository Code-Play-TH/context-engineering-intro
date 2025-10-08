# Quick Start Guide

## Prerequisites

-   Python 3.10+
-   PostgreSQL 15+
-   Git

## Installation (5 minutes)

### 1. Clone and Setup Virtual Environment

```bash
# Clone repository
git clone <repository-url>
cd kol-management

# Create virtual environment
python -m venv venv_linux

# Activate virtual environment
# On Windows:
venv_linux\Scripts\activate
# On Linux/Mac:
source venv_linux/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Create PostgreSQL database:

```sql
CREATE DATABASE kol_management;
```

Copy and configure environment file:

```bash
cp .env.example .env
```

Edit `.env` and update:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/kol_management
SECRET_KEY=generate-a-random-secret-key-here
```

### 4. Run Migrations

```bash
alembic upgrade head
```

Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 001
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003
INFO  [alembic.runtime.migration] Running upgrade 003 -> 004
INFO  [alembic.runtime.migration] Running upgrade 004 -> 005
```

### 5. Seed Default Users

```bash
python scripts/seed_admin.py
```

Expected output:

```
✓ Created admin user: admin@kolmanagement.com / Admin@123
✓ Created campaign manager: manager@kolmanagement.com / Manager@123
✓ Created account executive: ae@kolmanagement.com / AccountExec@123
✓ Created viewer: viewer@kolmanagement.com / Viewer@123

✅ Database seeded successfully!
```

### 6. Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Testing the API (2 minutes)

### 1. Open API Documentation

Visit: http://localhost:8000/docs

You should see the Swagger UI with all available endpoints.

### 2. Login

Click on `POST /api/v1/auth/login` → Try it out

Request body:

```json
{
    "email": "admin@kolmanagement.com",
    "password": "Admin@123"
}
```

Click "Execute"

Response (200 OK):

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

### 3. Authorize

1. Copy the `access_token` value
2. Click the "Authorize" button at the top right
3. Paste token in the "Value" field
4. Click "Authorize"
5. Click "Close"

### 4. Test Protected Endpoint

Click on `GET /api/v1/auth/me` → Try it out → Execute

Response (200 OK):

```json
{
    "email": "admin@kolmanagement.com",
    "full_name": "System Administrator",
    "role": "admin",
    "id": 1,
    "is_active": true,
    "created_at": "2025-01-09T...",
    "updated_at": "2025-01-09T...",
    "last_login_at": "2025-01-09T..."
}
```

### 5. Create a KOL

Click on `POST /api/v1/kols` → Try it out

Request body:

```json
{
    "name": "John Influencer",
    "email": "john@example.com",
    "phone": "+1234567890",
    "location": "Bangkok, Thailand",
    "niche": ["fashion", "lifestyle"],
    "tags": ["micro-influencer", "fashion"],
    "notes": "Great engagement rate",
    "social_handles": [
        {
            "platform": "instagram",
            "handle": "@johninfluencer",
            "url": "https://instagram.com/johninfluencer",
            "follower_count": 50000,
            "is_verified": true
        }
    ]
}
```

Click "Execute"

Response (201 Created):

```json
{
    "name": "John Influencer",
    "email": "john@example.com",
    "phone": "+1234567890",
    "location": "Bangkok, Thailand",
    "niche": ["fashion", "lifestyle"],
    "tags": ["micro-influencer", "fashion"],
    "notes": "Great engagement rate",
    "id": 1,
    "tier": "micro",
    "status": "active",
    "created_at": "2025-01-09T...",
    "updated_at": "2025-01-09T...",
    "social_handles": [
        {
            "platform": "instagram",
            "handle": "@johninfluencer",
            "url": "https://instagram.com/johninfluencer",
            "follower_count": 50000,
            "is_verified": true,
            "id": 1,
            "kol_id": 1,
            "is_active": true,
            "last_enriched_at": null,
            "created_at": "2025-01-09T..."
        }
    ]
}
```

### 6. Create a Campaign

Click on `POST /api/v1/campaigns` → Try it out

Request body:

```json
{
    "name": "Summer Fashion Campaign 2025",
    "start_date": "2025-06-01",
    "end_date": "2025-08-31",
    "total_budget": 50000,
    "currency": "USD",
    "objectives": "Increase brand awareness and drive sales",
    "target_audience": {
        "age_range": "18-35",
        "gender": "all",
        "interests": ["fashion", "lifestyle"]
    },
    "kpis": [
        {
            "kpi_type": "reach",
            "target_value": 1000000,
            "unit": "impressions"
        },
        {
            "kpi_type": "engagement",
            "target_value": 5,
            "unit": "percentage"
        }
    ],
    "deliverables": [
        {
            "deliverable_type": "instagram_post",
            "quantity": 10,
            "deadline": "2025-07-15"
        },
        {
            "deliverable_type": "instagram_story",
            "quantity": 20,
            "deadline": "2025-08-15"
        }
    ]
}
```

Click "Execute"

Response (201 Created) - Campaign created with KPIs and deliverables!

## Common Commands

### Run Migrations

```bash
alembic upgrade head
```

### Create New Migration

```bash
alembic revision --autogenerate -m "description"
```

### Rollback Migration

```bash
alembic downgrade -1
```

### Start Development Server

```bash
uvicorn app.main:app --reload
```

### Run Tests (when implemented)

```bash
pytest
pytest --cov=app tests/
```

## Default User Credentials

| Role              | Email                     | Password        |
| ----------------- | ------------------------- | --------------- |
| Admin             | admin@kolmanagement.com   | Admin@123       |
| Campaign Manager  | manager@kolmanagement.com | Manager@123     |
| Account Executive | ae@kolmanagement.com      | AccountExec@123 |
| Viewer            | viewer@kolmanagement.com  | Viewer@123      |

## API Endpoints Summary

### Authentication

-   `POST /api/v1/auth/login` - Login
-   `POST /api/v1/auth/refresh` - Refresh token
-   `POST /api/v1/auth/logout` - Logout
-   `GET /api/v1/auth/me` - Get current user

### Users

-   `POST /api/v1/users` - Create user (Admin only)
-   `GET /api/v1/users` - List users
-   `GET /api/v1/users/{id}` - Get user
-   `PUT /api/v1/users/{id}` - Update user
-   `DELETE /api/v1/users/{id}` - Deactivate user

### KOLs

-   `POST /api/v1/kols` - Create KOL
-   `GET /api/v1/kols` - List KOLs (with filters)
-   `GET /api/v1/kols/{id}` - Get KOL
-   `PUT /api/v1/kols/{id}` - Update KOL
-   `DELETE /api/v1/kols/{id}` - Delete KOL
-   `POST /api/v1/kols/{id}/social-handles` - Add social handle
-   `POST /api/v1/kols/{id}/tags/{tag}` - Add tag
-   `DELETE /api/v1/kols/{id}/tags/{tag}` - Remove tag

### Campaigns

-   `POST /api/v1/campaigns` - Create campaign
-   `GET /api/v1/campaigns` - List campaigns
-   `GET /api/v1/campaigns/{id}` - Get campaign
-   `PUT /api/v1/campaigns/{id}` - Update campaign
-   `DELETE /api/v1/campaigns/{id}` - Delete campaign
-   `PUT /api/v1/campaigns/{id}/status` - Change status
-   `POST /api/v1/campaigns/{id}/kpis` - Add KPI
-   `POST /api/v1/campaigns/{id}/deliverables` - Add deliverable
-   `POST /api/v1/campaigns/{id}/duplicate` - Duplicate campaign

## Troubleshooting

### Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**: Check PostgreSQL is running and DATABASE_URL in .env is correct

### Migration Error

```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solution**: Run `alembic upgrade head`

### Import Error

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution**: Activate virtual environment and run `pip install -r requirements.txt`

### Port Already in Use

```
ERROR: [Errno 48] Address already in use
```

**Solution**: Change port: `uvicorn app.main:app --reload --port 8001`

## Next Steps

1. ✅ You now have a working KOL Management System!
2. 📖 Read `IMPLEMENTATION_SUMMARY.md` for detailed feature list
3. 🔧 Customize for your needs
4. 🚀 Deploy to production

## Support

For issues or questions:

1. Check `README.md` for detailed documentation
2. Review `IMPLEMENTATION_SUMMARY.md` for feature status
3. Contact the development team

---

**Congratulations! Your KOL Management System is ready to use! 🎉**
