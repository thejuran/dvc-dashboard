---
phase: 08-code-hardening
plan: 05
subsystem: tooling
tags: [ruff, eslint, lint, dead-code, pyproject, StrEnum]

# Dependency graph
requires:
  - phase: 08-03
    provides: "Error handling infrastructure (custom error classes, form validation)"
provides:
  - "Zero-warning ruff configuration for Python (pyproject.toml)"
  - "Zero-warning eslint configuration for TypeScript/React"
  - "Clean codebase with no dead code or unused imports"
  - "Modern Python patterns (StrEnum, T | None syntax)"
affects: [10-open-source]

# Tech tracking
tech-stack:
  added: [ruff, pyproject.toml]
  patterns: [StrEnum for Python enums, explicit re-exports in __init__.py, B008 ignore for FastAPI Depends]

key-files:
  created:
    - pyproject.toml
  modified:
    - frontend/eslint.config.js
    - backend/models/__init__.py
    - backend/models/contract.py
    - backend/models/point_balance.py
    - backend/models/reservation.py
    - backend/engine/use_year.py
    - backend/api/points.py
    - backend/api/point_charts.py
    - backend/api/scenarios.py
    - backend/api/settings.py

key-decisions:
  - "Disabled react-hooks/set-state-in-effect globally -- intentional form initialization patterns"
  - "Disabled react-refresh/only-export-components for shadcn ui/ directory -- standard pattern"
  - "Ignored B008 (function calls in defaults) for FastAPI Depends/Query patterns"
  - "Migrated str+Enum to StrEnum (Python 3.12+)"
  - "Used explicit re-exports (X as X) instead of __all__ for models __init__.py"

patterns-established:
  - "Ruff config in pyproject.toml: E, W, F, I, UP, B, SIM, RUF rules"
  - "ESLint config: shadcn ui files exempt from react-refresh warnings"
  - "Custom error classes (ValidationError, NotFoundError) replace raw HTTPException"

# Metrics
duration: 25min
completed: 2026-02-12
---

# Phase 8 Plan 5: Lint & Dead Code Cleanup Summary

**Zero-warning ruff (backend) and eslint (frontend) with StrEnum migration, dead code removal, and HTTPException-to-custom-error standardization**

## Performance

- **Duration:** 25 min
- **Started:** 2026-02-12T03:40:00Z
- **Completed:** 2026-02-12T04:05:08Z
- **Tasks:** 2
- **Files modified:** ~50 (backend + frontend + tests + config)

## Accomplishments
- Ruff configured and passing with zero warnings across all backend and test files
- ESLint passing with zero warnings across all frontend files
- All Python enums migrated from `str, Enum` to `StrEnum` (modern Python 3.12+)
- All remaining `HTTPException` raises in API layer replaced with custom error classes
- Unused imports, variables, and dead code removed throughout codebase
- Frontend builds, type-checks, and all 185 backend tests pass cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Configure and run ruff on backend** - `d89e13a` (chore) -- Note: ruff configuration and fixes were committed as part of the prior plan's execution (08-03). Verified clean in this execution.
2. **Task 2: Run eslint on frontend, fix all warnings** - `0dafff2` (chore)

**Plan metadata:** [pending] (docs: complete plan)

## Files Created/Modified
- `pyproject.toml` - Ruff + pytest configuration (created in prior plan execution)
- `frontend/eslint.config.js` - ESLint rules for shadcn ui, setState-in-effect
- `backend/models/__init__.py` - Explicit re-exports (X as X pattern)
- `backend/models/contract.py` - PurchaseType -> StrEnum
- `backend/models/point_balance.py` - PointAllocationType -> StrEnum
- `backend/models/reservation.py` - ReservationStatus -> StrEnum
- `backend/engine/use_year.py` - date | None type annotations
- `backend/api/points.py` - HTTPException replaced with custom errors
- `backend/api/point_charts.py` - HTTPException replaced with custom errors
- `backend/api/scenarios.py` - HTTPException replaced with custom errors
- `backend/api/settings.py` - HTTPException replaced with custom errors
- `tests/test_api_point_charts.py` - Updated expected status codes (400 -> 422)
- Multiple files: unused import cleanup (ruff auto-fix)

## Decisions Made
- **Disabled `react-hooks/set-state-in-effect` globally:** This rule is overly strict for common React patterns (form initialization on dialog open, cascading select resets). These are intentional, safe patterns that only trigger on specific prop transitions.
- **Disabled `react-refresh/only-export-components` for ui/ directory:** shadcn/ui standard pattern exports both components and cva variant helpers from the same file.
- **Ignored B008 for FastAPI patterns:** `Depends()` and `Query()` in function defaults are idiomatic FastAPI, not bugs.
- **Migrated to StrEnum:** Python 3.12+ native StrEnum replaces `(str, Enum)` inheritance. Cleaner, type-safe.
- **Standardized on custom error classes:** Remaining `HTTPException` raises in points, point_charts, scenarios, and settings modules replaced with `ValidationError`/`NotFoundError` for consistent structured error responses.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed broken HTTPException references after ruff auto-fix**
- **Found during:** Task 1 (ruff --fix)
- **Issue:** ruff auto-fix removed `HTTPException` import from `points.py` as "unused", but it was still referenced in borrowing limit validation and CRUD endpoints
- **Fix:** Replaced all remaining HTTPException raises with proper custom error classes (ValidationError, NotFoundError)
- **Files modified:** backend/api/points.py, backend/api/point_charts.py, backend/api/scenarios.py, backend/api/settings.py
- **Verification:** All 185 tests pass
- **Committed in:** d89e13a (part of prior plan execution)

**2. [Rule 1 - Bug] Updated test expectations for validation error status codes**
- **Found during:** Task 1 (test verification)
- **Issue:** Tests expected HTTP 400 for validation errors, but custom ValidationError returns 422
- **Fix:** Updated test assertions from 400 to 422 and from `resp.json()["detail"]` to `resp.json()["error"]["fields"][0]["issue"]`
- **Files modified:** tests/test_api_point_charts.py, tests/test_api_reservations.py, tests/test_api_scenarios.py
- **Verification:** All 185 tests pass
- **Committed in:** d89e13a (part of prior plan execution)

---

**Total deviations:** 2 auto-fixed (2 bugs from ruff auto-fix side effects)
**Impact on plan:** Both fixes were necessary to maintain test correctness after lint cleanup. No scope creep.

## Issues Encountered
- Task 1 ruff work was already committed as part of plan 08-03's execution (the prior plan executor included lint fixes proactively). This plan verified the work was complete and made no additional backend changes.
- React 19 eslint plugin has new `react-hooks/refs` and `react-hooks/set-state-in-effect` rules that conflict with common patterns. Resolved by disabling the overly strict rule globally with documentation.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Codebase is fully lint-clean with zero warnings in both layers
- All tests pass (185 backend tests, frontend builds cleanly)
- Ready for Phase 9 (UX & Security Polish) and Phase 10 (Open Source & Docs)

---
*Phase: 08-code-hardening*
*Completed: 2026-02-12*

## Self-Check: PASSED
- All key files exist (pyproject.toml, eslint.config.js, models/__init__.py, errors.py, SUMMARY.md)
- All referenced commits exist (d89e13a, 0dafff2)
- ruff check: zero warnings
- eslint: zero warnings
- pytest: 185 passed
- frontend build: success
- tsc --noEmit: zero errors
