# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-10)

**Core value:** For any future date, clearly show available points across all contracts and what resorts/rooms those points can actually book.
**Current focus:** Phase 4 -- Docker Packaging + Settings

## Current Position

Phase: 4 of 7 (Docker Packaging + Settings)
Plan: --
Status: Ready to plan
Last activity: 2026-02-10 -- v1.1 roadmap created (4 phases, 23 requirements)

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

### Pending Todos

None.

### Blockers/Concerns

- Docker StaticFiles mount ordering: API routes must register before SPA catch-all
- SQLite volume mount: must mount directory (not file) to include WAL/SHM sidecars

## Session Continuity

Last session: 2026-02-10
Stopped at: v1.1 roadmap created. Ready to plan Phase 4.
Resume file: None
