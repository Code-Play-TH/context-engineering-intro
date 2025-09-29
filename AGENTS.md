# Repository Guidelines

## Project Structure & Module Organization
The FastAPI backend lives in `app/` with subpackages for API endpoints, core config, models, services, tasks, and utilities. Database migrations sit in `alembic/`, helper scripts in `scripts/`, and tests mirror the backend in `tests/`. The Next.js client resides in `frontend/` (`src/` features, `public/` assets), while guiding docs and prompts stay in `docs/`, `PRPs/`, and `examples/`. Container assets live in `docker/` alongside the root compose files.

## Build, Test, and Development Commands
- `python -m uvicorn app.main:app --reload`: start the API locally with hot reload (activate your venv first).
- `python run_tests.py full`: format, lint, security-scan, and run the Pytest suite with coverage; swap the keyword for `unit`, `integration`, `fast`, or `lint` as needed.
- `docker compose -f docker-compose.dev.yml up`: bring up Postgres, Redis, the API, Celery workers, and monitoring helpers.
- `npm install && npm run dev` inside `frontend/`: serve the Next.js UI; use `npm run build` and `npm run lint` for CI parity.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, type hints, and Google-style docstrings on public functions. Modules and files stay `snake_case`; classes use PascalCase; pydantic schemas live in `schemas/`. Run `python -m black app tests` and `python -m isort app tests`, then gate with `python -m flake8 app tests` and `python -m mypy app` before committing. Frontend code is TypeScript-first: components PascalCase, hooks camelCase, and co-locate UI helpers inside `src/`.

## Testing Guidelines
Pytest (see `pytest.ini`) enforces `--cov=app` with an 80% floor. Tag cases with `unit`, `integration`, or `slow` so focused runs like `python run_tests.py unit` or `python -m pytest tests/test_api/test_kols.py -m "not slow"` stay quick. Share fixtures through `tests/conftest.py` and mirror new backend modules with matching test directories. Frontend updates should at least pass `npm run lint`; add Jest or Playwright coverage when UI logic shifts.

## Commit & Pull Request Guidelines
Write imperative, one-line commit messages (e.g., `Add campaign analytics endpoint`) and split backend versus frontend changes when practical. PRs should include a brief rationale, the verification commands you ran, links to supporting INITIAL or PRP docs, and UI snapshots or API examples when behavior shifts. Update collateral like migrations, seed scripts, and monitoring configs together with code so reviewers see a complete slice.
