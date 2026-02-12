# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-11)

**Core value:** For any future date, clearly show available points across all contracts and what resorts/rooms those points can actually book.
**Current focus:** Phase 10 - Open Source & Documentation (v1.2)

## Current Position

Phase: 10 of 10 (Open Source & Documentation)
Plan: 2 of 3 in current phase
Status: Executing
Last activity: 2026-02-12 — Completed 10-02 (CI pipeline)

Progress: [█████████░] 90%

## Performance Metrics

**Velocity:**
- Total plans completed: 26 (across v1.0 + v1.1 + v1.2 phases 8-9)
- Average duration: carried from prior milestones
- Total execution time: carried from prior milestones

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 8. Code Hardening | 5/5 | 36min | 7.2min |
| 9. UX & Security Polish | 3/3 | 14min | 4.7min |
| 10. Open Source & Docs | 1/3 | 3min | 3min |

*Updated after each plan completion*

## Accumulated Context

### Decisions

All v1.0 decisions archived in milestones/v1.0-ROADMAP.md.
All v1.1 decisions archived in milestones/v1.1-ROADMAP.md.

Phase 10 decisions:
- 4 parallel CI jobs (backend-test, backend-lint, frontend-lint, docker-build) for fast PR feedback
- No pip/npm caching in CI -- simplicity over speed for now
- CI requires no repository secrets or special permissions

Key architectural decisions carrying forward:
- Monorepo: FastAPI backend + React/Vite frontend
- SQLite for storage (single-user)
- Pure-function engine layer (no DB coupling)
- Docker single-container: FastAPI serves React build
- GPL v3 license for open-source release (pending)
- ApiError class in api.ts for structured field-level error propagation from backend to forms
- Per-section error boundaries (not app-level) for crash isolation
- Blur-triggered form validation with inline red text pattern across all form components
- Ruff lint config in pyproject.toml (E, W, F, I, UP, B, SIM, RUF rules; B008 ignored for FastAPI)
- ESLint: set-state-in-effect disabled globally, react-refresh off for shadcn ui/ files
- StrEnum for all Python enums (Python 3.12+), explicit re-exports in models __init__.py
- _strip_str whitespace sanitization on all user-facing string fields in Pydantic schemas
- Numeric caps: points le=4000, string limits (name 100, notes 500, confirmation 50)
- Indexed field names in scenario validation: hypothetical_bookings[N].field
- Engine edge case tests are pure-function (no DB, no async) for fast execution
- All API error tests verify structured error format (type + fields), not just status codes
- Frontend deps pinned to exact versions (no ^ or ~); backend deps use upper-bounded ranges
- .env* gitignore pattern with !.env.example exception for comprehensive secret exclusion
- Shared LoadingSkeleton/ErrorAlert/EmptyState components for consistent UX across all pages
- ErrorAlert wired to react-query refetch for retry; DashboardPage combines 3 refetches into refetchAll
- Pure Tailwind responsive classes for mobile sidebar (md:hidden / hidden md:flex, no JS media queries)
- Separate mobile overlay + desktop sidebar elements for layout clarity
- Route-change auto-close of mobile sidebar via useLocation + useEffect
- Responsive pattern: flex-col gap-3 sm:flex-row for page headers and form layouts
- Table scroll pattern: overflow-x-auto wrapper on all Table components

### Pending Todos

None.

### Blockers/Concerns

None open.

## Session Continuity

Last session: 2026-02-12
Stopped at: Completed 10-02-PLAN.md (CI pipeline)
Resume file: None
Next: Execute 10-03-PLAN.md (remaining plan)
