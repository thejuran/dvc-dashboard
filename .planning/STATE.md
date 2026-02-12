# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-11)

**Core value:** For any future date, clearly show available points across all contracts and what resorts/rooms those points can actually book.
**Current focus:** v1.2 Harden & Open Source -- defining requirements

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-02-11 — Milestone v1.2 started

Progress: [░░░░░░░░░░] 0%

## Accumulated Context

### Decisions

All v1.0 decisions archived in milestones/v1.0-ROADMAP.md.
All v1.1 decisions archived in milestones/v1.1-ROADMAP.md.

Key architectural decisions carrying forward:
- Monorepo: FastAPI backend + React/Vite frontend
- SQLite for storage (single-user)
- Pure-function engine layer (no DB coupling)
- Point charts as versioned JSON data
- Docker single-container: FastAPI serves React build via StaticFiles
- Zustand for ephemeral client-side state

### Pending Todos

None.

### Blockers/Concerns

None open.

## Session Continuity

Last session: 2026-02-11
Stopped at: Defining v1.2 requirements
Resume file: None
Next: Complete requirements and roadmap definition
