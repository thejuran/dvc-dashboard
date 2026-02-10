---
phase: 04-docker-settings
plan: 01
subsystem: infrastructure
tags: [docker, configuration, spa-serving, persistence]
dependency_graph:
  requires: []
  provides: [dockerfile, docker-compose, config-layer, spa-serving, env-config]
  affects: [backend/main.py, backend/db/database.py, backend/db/migrations/env.py]
tech_stack:
  added: [pydantic-settings, python-dotenv]
  patterns: [multi-stage-docker-build, pydantic-basesettings, spa-static-files]
key_files:
  created:
    - backend/config.py
    - backend/spa.py
    - Dockerfile
    - docker-compose.yml
    - entrypoint.sh
    - .dockerignore
    - .env.example
    - data/db/.gitkeep
  modified:
    - backend/main.py
    - backend/db/database.py
    - backend/db/migrations/env.py
    - backend/requirements.txt
    - .gitignore
decisions:
  - Pydantic BaseSettings for env-based configuration (not raw os.getenv)
  - SPAStaticFiles subclass with API path redirect guard
  - Shell entrypoint for Alembic migrations before uvicorn
  - Named volume mounts data/db directory (not file) for WAL support
metrics:
  duration: 5m 25s
  completed: 2026-02-10
---

# Phase 4 Plan 1: Docker Infrastructure and Backend Configuration Summary

Docker packaging with Pydantic BaseSettings config layer, multi-stage build (node:22-slim + python:3.12-slim), SPA catch-all serving, and SQLite persistence via named volume.

## What Was Built

### Task 1: Backend Configuration Layer
**Commit:** c81a7f7

- **backend/config.py**: Pydantic BaseSettings reading DATABASE_URL, CORS_ORIGINS, PORT, HOST from environment variables with sensible defaults and .env file support
- **backend/spa.py**: SPAStaticFiles subclass that catches 404s and serves index.html for client-side routing, with API path guard to prevent intercepting API routes
- **backend/main.py**: Updated to use Settings for CORS origins (supports comma-separated list or wildcard), mounts SPA last after all API routers
- **backend/db/database.py**: Switched from `os.getenv` to `get_settings().database_url` for consistent configuration
- **backend/db/migrations/env.py**: Added DATABASE_URL env var override so Alembic uses the same database as runtime
- **backend/requirements.txt**: Added pydantic-settings and python-dotenv dependencies

### Task 2: Docker Files
**Commit:** a9c307b

- **Dockerfile**: Multi-stage build -- Stage 1 builds React frontend with node:22-slim, Stage 2 runs everything with python:3.12-slim. Point chart JSON data baked into image.
- **docker-compose.yml**: Single service with named volume `dvc-data:/app/data/db` for SQLite persistence, healthcheck via /api/health, optional .env file
- **entrypoint.sh**: Runs `alembic upgrade head` then `exec uvicorn` for clean signal handling
- **.dockerignore**: Excludes .git, venvs, node_modules, .env, .planning, tests, DB files
- **.env.example**: Documented template for PORT, DATABASE_URL, CORS_ORIGINS configuration
- **data/db/.gitkeep**: Ensures volume mount target directory exists in git
- **.gitignore**: Added Docker/DB artifact patterns (data/db/*.db, *.db-wal, *.db-shm)

## Verification Results

All verification checks passed:
- `docker compose up --build` completes successfully
- Health endpoint returns `{"status": "ok", "version": "0.1.0"}`
- 17 resorts loaded from baked-in data/resorts.json
- 2 point charts loaded (polynesian 2026, riviera 2026)
- SPA root (/) returns HTTP 200 with React HTML
- SPA client routes (/contracts) return HTTP 200 (catch-all works)
- Contract created via API, container restarted, contract survived (persistence confirmed)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SPA mount intercepting API route redirects**
- **Found during:** Task 2 verification
- **Issue:** The SPA mount at `/` intercepted requests to API paths without trailing slashes (e.g., `/api/point-charts`). FastAPI's `redirect_slashes` behavior was being bypassed because the SPA mount caught the request first and served index.html instead of allowing the redirect to `/api/point-charts/`.
- **Fix:** Updated SPAStaticFiles.get_response to detect `api/` paths and return a RedirectResponse to the trailing-slash version, mimicking FastAPI's normal redirect_slashes behavior. Non-API 404s still serve index.html for SPA routing.
- **Files modified:** backend/spa.py
- **Commit:** a9c307b (included in Task 2 commit)

## Commits

| Task | Commit  | Message |
|------|---------|---------|
| 1    | c81a7f7 | feat(04-01): add backend configuration layer with Pydantic Settings and SPA support |
| 2    | a9c307b | feat(04-01): add Docker infrastructure for single-command self-hosting |

## Self-Check: PASSED

All 13 files verified present on disk. Both commits (c81a7f7, a9c307b) verified in git log.
