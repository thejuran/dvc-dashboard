# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-10)

**Core value:** For any future date, clearly show available points across all contracts and what resorts/rooms those points can actually book.
**Current state:** v1.0 shipped. No active milestone.

## Current Position

Milestone: v1.0 COMPLETE (archived to .planning/milestones/)
Status: Between milestones
Last activity: 2026-02-10 -- v1.0 milestone archived

## Accumulated Context

### Decisions

All v1.0 decisions archived in milestones/v1.0-ROADMAP.md.

Key architectural decisions carrying forward:
- Monorepo: FastAPI backend + React/Vite frontend
- SQLite for storage (single-user)
- Pure-function engine layer (no DB coupling)
- Point charts as versioned JSON data
- Eligibility computed at read time

### Pending Todos

None.

### Blockers/Concerns

- DVC borrowing policy may revert from 100% to 50% -- make configurable in v2

## Session Continuity

Last session: 2026-02-10
Stopped at: v1.0 milestone complete and archived. Next: `/gsd:new-milestone` for v2.
Resume file: None
