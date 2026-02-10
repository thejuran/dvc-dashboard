# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-10)

**Core value:** For any future date, clearly show available points across all contracts and what resorts/rooms those points can actually book.
**Current focus:** Phase 4 -- Docker Packaging + Settings

## Current Position

Phase: 4 of 7 (Docker Packaging + Settings)
Plan: Ready to execute (2 plans, verified)
Status: Planning complete
Last activity: 2026-02-10 -- Phase 4 planned (research + 2 plans + verification pass)

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0 (v1.1)
- Average duration: --
- Total execution time: --

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

*Updated after each plan completion*

## Accumulated Context

### Decisions

All v1.0 decisions archived in milestones/v1.0-ROADMAP.md.

Key architectural decisions carrying forward:
- Monorepo: FastAPI backend + React/Vite frontend
- SQLite for storage (single-user)
- Pure-function engine layer (no DB coupling)
- Point charts as versioned JSON data

v1.1 decisions:
- Docker for sharing (not Railway) -- open-source self-hosted tool
- Single container: FastAPI serves React build via StaticFiles mount
- Zustand for ephemeral scenario state (already installed, first activation)
- Server-side computation, client-side state for scenarios

Phase 4 decisions (from planning):
- Multi-stage Dockerfile: node:22-slim builds frontend, python:3.12-slim runs everything
- SPAStaticFiles subclass (not catch-all route) for React SPA serving
- Shell entrypoint for Alembic migrations (not lifespan approach)
- Pydantic BaseSettings for env configuration (not raw os.getenv)
- Borrowing policy stored in DB app_settings table (not env var) -- UI-toggleable
- SQLite volume: mount directory /app/data/db (not file) for WAL sidecar support

### Pending Todos

None.

### Blockers/Concerns

- Docker StaticFiles mount ordering: API routes must register before SPA catch-all (addressed in plan)
- SQLite volume mount: must mount directory (not file) to include WAL/SHM sidecars (addressed in plan)
- Port mapping: entrypoint uses ${PORT} but compose hardcodes container port to 8000 -- will self-correct during execution verification

## Session Continuity

Last session: 2026-02-10
Stopped at: Phase 4 planning complete. Ready to execute.
Resume file: None
Next: `/gsd:execute-phase 4`
