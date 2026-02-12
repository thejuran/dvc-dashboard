# Contributing to DVC Dashboard

Thanks for considering contributing! This guide helps you get set up and submit changes.

## Development Setup

**Prerequisites:** Python 3.12+, Node.js 22+, npm

Clone and set up the backend:

```bash
git clone https://github.com/thejuran/dvc-dashboard.git
cd dvc-dashboard
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements-dev.txt
```

Set up the frontend:

```bash
cd frontend
npm install
cd ..
```

Copy the environment config:

```bash
cp .env.example .env
```

Run the backend:

```bash
uvicorn backend.main:app --reload
```

Run the frontend (separate terminal):

```bash
cd frontend && npm run dev
```

Run tests:

```bash
pytest
```

The app runs at http://localhost:5173 (frontend dev server) with the API at http://localhost:8000.

## Code Style

**Python:** Ruff handles linting and import sorting. Run before committing:

```bash
ruff check .
ruff format --check .
```

Config lives in `pyproject.toml`.

**TypeScript:** ESLint configured for React. Run:

```bash
cd frontend && npm run lint
```

**General rules:**
- No `any` types in TypeScript
- Pydantic models for all API request/response schemas
- Pure functions in `backend/engine/` (no DB imports)

## Project Structure

```
backend/
  api/        # FastAPI route handlers
  engine/     # Pure business logic (no DB)
  models/     # SQLAlchemy models
  db/         # Database setup + migrations
  data/       # Static data loaders
frontend/
  src/
    pages/      # Route-level page components
    components/ # Reusable UI components
    hooks/      # React Query data hooks
    lib/        # API client, utilities
    types/      # TypeScript type definitions
tests/          # pytest test suite
data/           # Point chart JSON data
```

## Making Changes

1. Fork the repo and create a feature branch: `git checkout -b feature/your-feature`
2. Make changes, add tests if applicable
3. Run lint and tests: `ruff check . && pytest && cd frontend && npm run lint`
4. Commit with a descriptive message
5. Open a PR against `main` with a description of what changed and why

## Reporting Issues

Use GitHub Issues. Include: what happened, what you expected, steps to reproduce, and browser/OS if it's a UI issue.

## License

By contributing, you agree that your contributions will be licensed under the GPL v3.
