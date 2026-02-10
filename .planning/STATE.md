# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-09)

**Core value:** For any future date, clearly show available points across all contracts and what resorts/rooms those points can actually book.
**Current focus:** Phase 1 - Data Foundation

## Current Position

Phase: 1 of 3 (Data Foundation) -- COMPLETE
Plan: 3 of 3 in current phase (all done)
Status: Phase 1 Complete
Last activity: 2026-02-10 -- Completed Plan 01-03 (Point Chart Data System)

Progress: [==========....................] 33% (3/9 plans)

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 6m 47s
- Total execution time: ~20 minutes

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3/3 | 20m 01s | 6m 47s |

**Recent Trend:**
- Last 5 plans: 01-01 (6m 44s), 01-02 (6m 52s), 01-03 (6m 25s)
- Trend: Consistent ~7min per plan

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Scraping deferred to v2 (all data entry is manual in v1)
- Monorepo pattern: FastAPI backend + React/Vite frontend (per research, mirrors NephSched)
- SQLite for storage (single-user, zero-config, trivial backups)
- Point charts stored as versioned data, not code
- Used Python 3.12 venv (system Python 3.9 too old for modern type hints)
- pytest-asyncio 1.x strict mode requires @pytest_asyncio.fixture for async fixtures
- selectinload required for async relationship testing in SQLAlchemy
- Pydantic schemas defined separately in schemas.py (not inline in router)
- Points router uses full path routes (no prefix) for mixed /api/contracts and /api/points paths
- Eligibility computed at read time, not stored (immediate update on purchase_type change)
- API integration tests use dependency override with in-memory SQLite per fixture
- 6 seasons used for 2026 charts (Adventure, Choice, Dream, Magic, Premier, Select) -- schema supports any number
- Room key format: {room_type}_{view_category} parsed via longest-match view_category suffix
- Point chart JSON schema accommodates 3 to 30+ room/view combos per resort (view_category concern RESOLVED)

### Pending Todos

None yet.

### Blockers/Concerns

- Research gap: DVC borrowing policy may revert from 100% to 50% -- make borrowing percentage configurable
- ~Research gap: Point chart JSON schema must accommodate resort-specific view category variations (3 to 10+ types)~ (RESOLVED: composite room key format handles all variations)
- ~Research gap: Holding account points need a point allocation type in schema~ (RESOLVED: implemented in PointBalance model with "holding" allocation type)

## Session Continuity

Last session: 2026-02-10
Stopped at: Completed 01-03-PLAN.md (Phase 1 complete)
Resume file: None
