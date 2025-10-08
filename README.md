# KOL Influencer Management System

A comprehensive platform for managing Key Opinion Leader (KOL) campaigns from initial contact through final reporting.

## 🚀 Quick Start

### Prerequisites

-   Python 3.10+
-   Docker & Docker Compose
-   PostgreSQL 15+ (via Docker)

### Setup

1. **Clone and setup environment:**

```bash
# Copy environment variables
copy .env.example .env
# Edit .env with your configuration
```

2. **Start databases:**

```bash
make db-up
# or
docker-compose up -d
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. **Run migrations:**

```bash
make migrate
# or
alembic upgrade head
```

5. **Seed database:**

```bash
make seed
# or
python scripts/seed_admin.py
```

6. **Start development server:**

```bash
make dev
# or
uvicorn app.main:app --reload
```

7. **Access API:**

-   API: http://localhost:8000
-   Docs: http://localhost:8000/api/v1/docs
-   Health: http://localhost:8000/health

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run in watch mode
make test-watch
```

## 📚 Documentation

-   [Project Overview](.kiro/specs/project-overview.md)
-   [Requirements](.kiro/specs/)
-   [Design Documents](.kiro/specs/)
-   [API Documentation](http://localhost:8000/api/v1/docs)

## 🛠️ Development

### Useful Commands

```bash
make help          # Show all available commands
make db-up         # Start databases
make db-reset      # Reset database
make migrate       # Run migrations
make test          # Run tests
make format        # Format code
make lint          # Check code quality
```

### Project Structure

```
app/
├── api/v1/        # API endpoints
├── core/          # Core modules (config, database, security)
├── models/        # Database models
├── schemas/       # Pydantic schemas
├── services/      # Business logic
└── main.py        # FastAPI application

tests/             # Test files
alembic/           # Database migrations
scripts/           # Utility scripts
```

## 📝 License

Proprietary - All rights reserved

## 👥 Team

Development Team
