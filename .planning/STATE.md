# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-09)

**Core value:** For any future date, clearly show available points across all contracts and what resorts/rooms those points can actually book.
**Current focus:** Phase 3 complete -- Dashboard & Trip Explorer

## Current Position

Phase: 3 of 3 (Dashboard & Trip Explorer)
Plan: 3 of 3 in current phase (all plans complete)
Status: Phase 3 Complete -- All plans executed
Last activity: 2026-02-10 -- Completed Plan 03-03 (Trip Explorer UI + Navigation)

Progress: [==============================] 100% (9/9 plans)

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
- Dashboard is the new home route (/) replacing redirect to /contracts
- NavLink end prop added for "/" to prevent always-active highlighting
- Trip explorer uses check_in date (not today) for use year calculation -- correct point year for future trips
- Trip explorer is a pure composition function (no DB access in engine layer)
- Dashboard stays at "/" (no redirect) -- 03-02 placed it directly, 03-03 preserved this
- "Point Calculator" renamed to "Availability" in nav to avoid confusion with Trip Explorer
- Trip Explorer auto-fires search via useQuery enabled flag (no submit button)

### Pending Todos

None yet.

### Blockers/Concerns

- Research gap: DVC borrowing policy may revert from 100% to 50% -- make borrowing percentage configurable
- ~Research gap: Point chart JSON schema must accommodate resort-specific view category variations (3 to 10+ types)~ (RESOLVED: composite room key format handles all variations)
- ~Research gap: Holding account points need a point allocation type in schema~ (RESOLVED: implemented in PointBalance model with "holding" allocation type)

## Session Continuity

Last session: 2026-02-10
Stopped at: Completed 03-03-PLAN.md (Trip Explorer UI + Navigation). All Phase 3 plans done. Project v1.0 feature-complete.
Resume file: None
