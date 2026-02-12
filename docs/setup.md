# Setup Guide

## Docker Deployment (Recommended)

The fastest way to run DVC Dashboard. Requirements: [Docker](https://docs.docker.com/get-docker/) and Docker Compose.

```bash
git clone https://github.com/thejuran/seedsync.git && cd seedsync
```

Optionally configure settings before starting:

```bash
cp .env.example .env   # then edit .env as needed
```

Start the application:

```bash
docker compose up -d
```

Visit **http://localhost:8000** -- the app auto-runs database migrations and pre-loads point chart data on first start.

**Stopping:** `docker compose down` (data persists in a Docker volume).

**Resetting:** `docker compose down -v` (deletes the database volume and all data).

**Updating:** `git pull && docker compose up -d --build`

## Configuration

All settings are optional. Defaults work out of the box. See `.env.example` for the full template.

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Server bind address. Set to `127.0.0.1` to restrict to local connections only. |
| `PORT` | `8000` | Server port. Docker Compose maps `${PORT:-8000}:8000`. |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/db/dvc.db` | SQLite connection string. Only change for advanced setups. |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed origins for CORS (comma-separated). Docker sets this to `*` since FastAPI serves the frontend. |

## Local Development

For contributors who want to modify the code.

**Prerequisites:** Python 3.12+, Node.js 22+, npm.

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

API available at **http://localhost:8000**.

### Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server at **http://localhost:5173**. CORS is configured for the dev server origin, so API calls work without a proxy.

## Running Tests

```bash
pytest                          # all tests
pytest --tb=short -q            # concise output
pytest tests/test_edge_cases.py # specific file
```

## Linting

```bash
ruff check .               # Python lint
ruff format --check .      # Python format check
cd frontend && npm run lint # TypeScript/React lint
```

## Database

- **Storage:** SQLite database at `data/db/dvc.db`.
- **Migrations:** Managed by Alembic. Run `alembic upgrade head` to apply pending migrations.
- **Point charts:** Pre-seeded from JSON files in `data/point_charts/` on first startup. Charts live in version-controlled JSON, not in the database.
- **Docker volume:** In Docker, the database lives in a named volume (`dvc-data`) for persistence across container restarts.

## Troubleshooting

- **Port already in use:** Change `PORT` in `.env` or override the port mapping: `PORT=3000 docker compose up -d`.
- **Database errors after update:** Run `alembic upgrade head` (local dev) or recreate the container: `docker compose down -v && docker compose up -d`.
- **Frontend build fails:** Delete `frontend/node_modules` and run `npm install` again.
- **CORS errors in local dev:** Ensure `CORS_ORIGINS` in `.env` includes `http://localhost:5173`.
