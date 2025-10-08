# Project Structure

## Directory Organization

```
project-root/
├── .claude/              # Claude Code configuration
│   ├── commands/         # Custom slash commands
│   └── settings.local.json
├── .kiro/                # Kiro AI configuration
│   └── steering/         # AI steering rules (this file)
├── alembic/              # Database migrations
│   └── versions/         # Migration version files
├── app/                  # Backend application code
│   ├── api/              # API routes
│   │   └── v1/           # API version 1 endpoints
│   │       ├── auth.py   # Authentication endpoints
│   │       ├── campaigns.py
│   │       ├── kols.py
│   │       └── users.py
│   ├── core/             # Core application modules
│   │   ├── auth.py       # JWT authentication logic
│   │   ├── config.py     # Configuration settings
│   │   ├── database.py   # Database connection
│   │   └── security.py   # Security utilities
│   ├── models/           # SQLModel database models
│   ├── schemas/          # Pydantic schemas for API
│   ├── services/         # Business logic layer
│   ├── tasks/            # Celery background tasks
│   └── worker.py         # Celery worker configuration
├── frontend/             # Next.js frontend application
│   ├── public/           # Static assets
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # React components
│   │   │   ├── ui/       # Reusable UI components (shadcn/ui)
│   │   │   ├── campaigns/
│   │   │   ├── kols/
│   │   │   └── layout/
│   │   ├── hooks/        # Custom React hooks
│   │   ├── lib/          # Utility functions and API clients
│   │   ├── types/        # TypeScript type definitions
│   │   └── utils/        # Helper functions
│   ├── .env.local        # Frontend environment variables
│   └── package.json
├── docker/               # Docker configurations
│   └── grafana/          # Grafana monitoring setup
├── examples/             # Code examples and patterns
├── logs/                 # Application logs
├── PRPs/                 # Product Requirements Prompts
│   └── templates/        # PRP templates
├── tests/                # Pytest unit tests
├── uploads/              # File upload storage
│   ├── imports/          # KOL import files (CSV/Excel)
│   │   ├── pending/      # Files awaiting processing
│   │   ├── processed/    # Successfully imported files
│   │   └── failed/       # Failed imports with error logs
│   ├── templates/        # Report templates (PowerPoint/PDF)
│   │   ├── pptx/         # PowerPoint template files
│   │   ├── pdf/          # PDF template definitions
│   │   └── samples/      # Sample reports uploaded by users
│   └── reports/          # Generated report files
├── .env                  # Backend environment variables
└── .env.example          # Environment variables template
```

## Code Organization Principles

### Module Structure

Organize code by feature/responsibility with clear separation:

```
feature/
├── agent.py      # Main agent definition and execution logic
├── tools.py      # Tool functions used by the agent
└── prompts.py    # System prompts
```

### File Size Limits

-   **Maximum 500 lines per file** - refactor into modules if approaching this limit
-   Split large files by logical responsibility or feature grouping

### Import Conventions

-   Prefer relative imports within packages
-   Use consistent import ordering (stdlib, third-party, local)
-   Always use python-dotenv for environment variables

### Testing Structure

-   Tests live in `/tests` folder mirroring the main app structure
-   Each test file should include:
    -   At least 1 test for expected use case
    -   At least 1 edge case test
    -   At least 1 failure case test

## Backend Structure Details

### API Versioning

-   All API endpoints must be versioned under `/api/v1/`
-   Example: `/api/v1/campaigns`, `/api/v1/kols`, `/api/v1/auth/login`
-   Future versions will be `/api/v2/` without breaking existing clients
-   Version is defined in the router prefix, not in individual route paths

### Authentication Flow

-   JWT tokens stored in HTTP-only cookies or Authorization header
-   OAuth2 password flow for login (`/api/v1/auth/login`)
-   Token refresh endpoint (`/api/v1/auth/refresh`)
-   Protected routes use `Depends(get_current_user)` dependency

### Background Tasks

-   Social media scraping tasks run via Celery workers
-   Scheduled tasks (follow-ups, stat collection) use Celery Beat
-   Report generation tasks (PowerPoint/PDF) run asynchronously
-   Task results stored in Redis with TTL
-   Task status endpoints for monitoring progress

### KOL Import System

-   **Import Sources**:
    -   CSV/Excel file upload with column mapping
    -   API-based import from social media platforms
    -   Third-party influencer database API integration
-   **Import Workflow**:
    1. Upload file to `uploads/imports/pending/`
    2. Validate data format and required fields
    3. Check for duplicates using fuzzy matching (name, social handles)
    4. Preview import with validation errors highlighted
    5. User confirms or fixes errors
    6. Background task processes import in batches
    7. Move file to `processed/` or `failed/` with error log
-   **Data Validation**:
    -   Required fields: name, at least one social media handle
    -   Optional fields: email, phone, niche, location, engagement rate
    -   Format validation: email, URLs, numeric values
    -   Duplicate detection: match by social handles or name similarity (>85%)
-   **API Discovery**:
    -   Search by username/handle across platforms
    -   Fetch profile data and metrics automatically
    -   Enrich existing profiles with latest data
    -   Rate limit handling per platform

### Report Template System

-   **Template Storage**: Templates stored in `uploads/templates/`
-   **Template Types**:
    -   PowerPoint templates (.pptx files with placeholder tags)
    -   PDF templates (JSON definitions with layout specifications)
-   **Template Builder**: Web UI for AEs to create/edit templates
-   **AI Template Generation**:
    -   Upload sample report (PowerPoint/PDF)
    -   AI analyzes structure, layout, and data placeholders
    -   Generates template definition automatically
    -   AE reviews and adjusts before saving
-   **Template Variables**: `{{campaign_name}}`, `{{kol_count}}`, `{{total_reach}}`, `{{engagement_rate}}`, etc.
-   **Dynamic Charts**: Chart placeholders automatically populated with campaign data
-   **Template Library**: Reusable templates shared across campaigns/clients

## Frontend Structure Details

### Next.js App Router

-   Use App Router (not Pages Router) for new development
-   Server Components by default, Client Components when needed (`'use client'`)
-   API routes in `frontend/src/app/api/` for BFF (Backend for Frontend) pattern

### Component Organization

-   `components/ui/` - Reusable UI primitives (buttons, inputs, cards)
-   `components/[feature]/` - Feature-specific components (campaigns, kols)
-   `components/layout/` - Layout components (navbar, sidebar, footer)

### Custom Hooks

-   `hooks/useAuth.ts` - Authentication state and methods
-   `hooks/useCampaigns.ts` - Campaign data fetching with React Query
-   `hooks/useKOLs.ts` - KOL data fetching and filtering

### Type Safety

-   Generate TypeScript types from backend Pydantic models
-   Use Zod schemas for form validation matching backend validation
-   Strict TypeScript configuration (`strict: true`)

## Environment Files

### Backend (.env)

```
DATABASE_URL=postgresql://user:password@localhost:5432/kol_management
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Social Media API Keys
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
INSTAGRAM_ACCESS_TOKEN=
TIKTOK_API_KEY=
YOUTUBE_API_KEY=
TWITTER_API_KEY=

# Communication API Keys
LINE_CHANNEL_ACCESS_TOKEN=
DISCORD_BOT_TOKEN=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# Influencer Database APIs (optional)
HYPEAUDITOR_API_KEY=
UPFLUENCE_API_KEY=
ASPIREIQ_API_KEY=

# AI/LLM API Keys (for report template generation)
OPENAI_API_KEY=
# or
ANTHROPIC_API_KEY=

# File Storage
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=50
ALLOWED_IMPORT_EXTENSIONS=csv,xlsx,xls
```

### Frontend (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### Template (.env.example)

-   Copy of `.env` with placeholder values
-   Committed to repository as documentation
-   Developers copy to `.env` and fill in real values

## Key Files

-   `PLANNING.md` - Project architecture, goals, style, and constraints (read at conversation start)
-   `TASK.md` - Current tasks and TODOs (check before starting work, update when complete)
-   `CLAUDE.md` - Global rules for AI assistants
-   `README.md` - Project documentation and setup instructions
-   `.env.example` - Environment variables template with descriptions

## Naming Conventions

-   Use snake_case for Python files, functions, and variables
-   Use PascalCase for class names
-   Use UPPER_CASE for constants
-   Descriptive names that clearly indicate purpose

## Documentation Requirements

-   Google-style docstrings for every function
-   Inline `# Reason:` comments for complex logic explaining the "why"
-   Update README.md when features, dependencies, or setup steps change
