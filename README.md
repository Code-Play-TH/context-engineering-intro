# KOL Influencer Management System

A comprehensive platform for managing Key Opinion Leader (KOL) campaigns from initial contact through final reporting.

## Features

-   **User Authentication & Authorization**: JWT-based authentication with role-based access control (Admin, Campaign Manager, Account Executive, Viewer)
-   **Campaign Management**: Create and manage campaigns with KPIs, deliverables, and budget tracking
-   **KOL Database**: Manage influencer profiles with social media handles and performance metrics
-   **Brief Management**: Template-based brief creation and distribution
-   **Multi-Channel Communication**: Email, Line, Discord, and social media DM integration
-   **Analytics & Reporting**: Automated report generation with customizable templates

## Tech Stack

### Backend

-   **Framework**: FastAPI
-   **Database**: PostgreSQL 15+
-   **ORM**: SQLModel
-   **Authentication**: JWT with OAuth2 password flow
-   **Migrations**: Alembic

### Frontend (Coming Soon)

-   **Framework**: Next.js (React)
-   **Language**: TypeScript
-   **Styling**: Tailwind CSS

## Setup Instructions

### Prerequisites

-   Python 3.10+
-   PostgreSQL 15+
-   Virtual environment (venv)

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd kol-management
```

2. **Create and activate virtual environment**

```bash
python -m venv venv_linux
# On Windows
venv_linux\Scripts\activate
# On Linux/Mac
source venv_linux/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

5. **Run database migrations**

```bash
alembic upgrade head
```

6. **Seed default users**

```bash
python scripts/seed_admin.py
```

### Running the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

### Default Users

After running the seed script, you can login with:

-   **Admin**: admin@kolmanagement.com / Admin@123
-   **Campaign Manager**: manager@kolmanagement.com / Manager@123
-   **Account Executive**: ae@kolmanagement.com / AccountExec@123
-   **Viewer**: viewer@kolmanagement.com / Viewer@123

## API Endpoints

### Authentication

-   `POST /api/v1/auth/login` - Login with email/password
-   `POST /api/v1/auth/refresh` - Refresh access token
-   `POST /api/v1/auth/logout` - Logout and invalidate token
-   `GET /api/v1/auth/me` - Get current user info

### User Management

-   `POST /api/v1/users` - Create user (Admin only)
-   `GET /api/v1/users` - List users with pagination
-   `GET /api/v1/users/{id}` - Get user details
-   `PUT /api/v1/users/{id}` - Update user
-   `DELETE /api/v1/users/{id}` - Deactivate user (Admin only)

## Development

### Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback migration:

```bash
alembic downgrade -1
```

### Testing

Run tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app tests/
```

### Code Quality

Format code with Black:

```bash
black app/ tests/
```

## Project Structure

```
project-root/
├── app/                  # Backend application
│   ├── api/             # API routes
│   │   └── v1/          # API version 1
│   ├── core/            # Core modules (auth, config, database)
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   └── services/        # Business logic
├── alembic/             # Database migrations
├── scripts/             # Utility scripts
├── tests/               # Test files
└── uploads/             # File uploads
```

## License

Proprietary - All rights reserved

## Support

For support, please contact the development team.
