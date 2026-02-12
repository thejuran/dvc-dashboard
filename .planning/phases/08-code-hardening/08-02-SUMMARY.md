---
phase: 08-code-hardening
plan: 02
subsystem: api
tags: [pydantic, validation, fastapi, input-sanitization, structured-errors]

# Dependency graph
requires:
  - phase: 08-01
    provides: "Structured error infrastructure (AppError hierarchy, exception handlers, error_response helper)"
provides:
  - "Comprehensive Pydantic validators on all request models: whitespace stripping, length limits, numeric caps, date format validation"
  - "Route-level validation with indexed field names for scenario bookings"
  - "Target date range validation on availability endpoint"
  - "Zero raise HTTPException in any route file"
affects: [08-03, 08-04, frontend-forms, api-consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Shared _strip_str helper for whitespace sanitization across all request models"
    - "Indexed field names in validation errors: hypothetical_bookings[N].field"
    - "Before-mode validators for string sanitization, after-mode for business logic"

key-files:
  created: []
  modified:
    - backend/api/schemas.py
    - backend/api/scenarios.py
    - backend/api/availability.py
    - tests/test_api_scenarios.py

key-decisions:
  - "Points cap at 4000 (2x max annual points of 2000) for banked+current balance and reservation cost"
  - "Contract name max 100 chars, confirmation number max 50, notes max 500, setting value max 50"
  - "Scenario bookings capped at 10 per request (per user decision from what-if scenarios)"
  - "Availability target_date restricted to 2020-2040 year range"
  - "PointCostRequest dates validated as ISO format at schema level before route parsing"

patterns-established:
  - "All user-facing string fields stripped via _strip_str before-mode validator"
  - "Scenario validation errors include booking array index: hypothetical_bookings[0].resort"
  - "Numeric fields have both lower and upper bounds (ge/le)"

# Metrics
duration: 5min
completed: 2026-02-12
---

# Phase 08 Plan 02: Input Validation Hardening Summary

**Comprehensive Pydantic validators with whitespace stripping, length limits, numeric caps, and route-level validation with indexed field names across all API endpoints**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-12T15:07:28Z
- **Completed:** 2026-02-12T15:11:57Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Added _strip_str helper and whitespace stripping validators on all user-facing string fields across all request models
- Added length limits (name 100, confirmation_number 50, notes 500, resort 50, room_key 100, setting value 50) and numeric caps (points le=4000, points_cost le=4000)
- Added max 14 nights constraint to ReservationPreviewRequest, ISO date format validation to PointCostRequest, max 10 hypothetical bookings to ScenarioEvaluateRequest
- Added indexed field names in scenario validation errors (hypothetical_bookings[0].resort)
- Added target_date year range validation (2020-2040) to availability endpoint
- Verified zero raise HTTPException in any route file

## Task Commits

Each task was committed atomically:

1. **Task 1: Tighten Pydantic schema validators** - `16d0d59` (feat)
2. **Task 2: Route-level validation and indexed field names** - `69dda3d` (feat)
3. **Task 2 fix: Correct test assertions for indexed field names** - `119e4a3` (fix)

## Files Created/Modified
- `backend/api/schemas.py` - Added _strip_str helper, whitespace stripping on all string fields, length limits, numeric caps, date format validation, max bookings validator
- `backend/api/scenarios.py` - Added booking index to validation error field names (hypothetical_bookings[N].field)
- `backend/api/availability.py` - Added target_date year range validation (2020-2040)
- `tests/test_api_scenarios.py` - Updated assertions for indexed field names
- `tests/test_api_contracts.py` - Added structured error format tests (previously uncommitted)
- `tests/test_api_reservations.py` - Added structured error format tests (previously uncommitted)
- `tests/test_api_points.py` - Added structured error format tests (previously uncommitted)
- `tests/test_api_availability.py` - Added structured error format tests (previously uncommitted)
- `tests/test_api_trip_explorer.py` - New test file for trip explorer endpoint (previously uncommitted)
- `.planning/config.json` - Config update (previously uncommitted)
- `.planning/phases/08-code-hardening/08-CONTEXT.md` - Context file (previously untracked)

## Decisions Made
- Points cap at 4000 (2x max annual points) for point balance and reservation cost fields
- String length limits chosen conservatively: name 100, confirmation_number 50, notes 500, resort slug 50, room_key 100
- Scenario bookings capped at 10 per the user's existing what-if scenarios design decision
- Target date year range 2020-2040 covers DVC contract historical and future planning needs
- Whitespace stripping applied via before-mode validators to catch " polynesian " before resort slug validation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pre-commit hook reverted test assertions**
- **Found during:** Task 2 commit
- **Issue:** Pre-commit hook modified test_api_scenarios.py during commit, reverting the indexed field name assertions
- **Fix:** Created a follow-up commit with the correct assertions
- **Files modified:** tests/test_api_scenarios.py
- **Verification:** All 204 tests pass
- **Committed in:** 119e4a3

**2. [Rule 3 - Blocking] Uncommitted test improvements from prior plans**
- **Found during:** Task 2 (git status showed modified test files)
- **Issue:** Test files had uncommitted improvements from Plan 01/03 execution validating structured error format
- **Fix:** Included in Task 2 commit since they validate the hardening work
- **Files modified:** tests/test_api_contracts.py, tests/test_api_reservations.py, tests/test_api_points.py, tests/test_api_availability.py, tests/test_api_trip_explorer.py
- **Verification:** All 204 tests pass
- **Committed in:** 69dda3d

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both auto-fixes necessary for test correctness. No scope creep.

## Issues Encountered
- Pre-commit hook silently reverted test changes in the initial Task 2 commit, requiring a follow-up fix commit

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All API inputs are now validated and sanitized server-side before processing
- Every validation error includes field-level detail
- Zero raise HTTPException in any route file
- All 204 tests pass
- Ready for Plan 03 (Error Boundaries and Form Validation) or subsequent plans

## Self-Check: PASSED

- backend/api/schemas.py exists and contains _strip_str, field_validator, le=4000
- backend/api/scenarios.py exists and contains hypothetical_bookings[{idx}]
- backend/api/availability.py exists and contains year validation (2020, 2040)
- All 3 commits exist (16d0d59, 69dda3d, 119e4a3)
- All 204 tests pass
- Zero raise HTTPException in route files

---
*Phase: 08-code-hardening*
*Completed: 2026-02-12*
