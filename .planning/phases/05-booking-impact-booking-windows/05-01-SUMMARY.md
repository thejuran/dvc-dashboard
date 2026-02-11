---
phase: 05-booking-impact-booking-windows
plan: 01
subsystem: booking-engine
tags: [booking-impact, booking-windows, preview-api, banking-warning, pure-functions]
dependency_graph:
  requires: []
  provides: [booking-impact-engine, booking-windows-engine, preview-endpoint]
  affects: [backend/api/reservations.py, backend/api/schemas.py]
tech_stack:
  added: []
  patterns: [availability-diff-preview, dvc-month-subtraction, conservative-banking-warning]
key_files:
  created:
    - backend/engine/booking_windows.py
    - backend/engine/booking_impact.py
    - tests/test_booking_windows.py
    - tests/test_booking_impact.py
  modified:
    - backend/api/schemas.py
    - backend/api/reservations.py
    - tests/test_api_reservations.py
decisions:
  - DVC end-of-month roll-forward rule for booking window dates (not relativedelta clip-backward)
  - Conservative banking warning fires when booking COULD consume bankable points
  - Bundle booking impact + booking windows + banking warning in single preview endpoint
metrics:
  duration: 5m 4s
  completed: 2026-02-10
---

# Phase 5 Plan 1: Booking Impact & Booking Windows Backend Summary

Pure-function booking impact engine (before/after availability diff via get_contract_availability) + booking windows with DVC end-of-month roll-forward rule + POST /api/reservations/preview endpoint composing all three.

## What Was Built

### Task 1: Booking windows engine + booking impact engine with tests
**Commit:** 6772d50

- **backend/engine/booking_windows.py**: `_dvc_subtract_months()` with DVC end-of-month correction (rolls forward to 1st of next month instead of clipping backward when day doesn't exist in target month). `compute_booking_windows()` returning 11-month home resort and 7-month any-resort window dates with open status relative to today.
- **backend/engine/booking_impact.py**: `compute_booking_impact()` computing before/after availability diff by calling `get_contract_availability()` twice (once without, once with proposed reservation appended). `compute_banking_warning()` with conservative logic: warns when booking must dip into current-year bankable points (deadline not passed, current points > 0, cost exceeds non-bankable portion).
- **tests/test_booking_windows.py**: 11 tests covering standard subtraction, end-of-month edge cases (Sept 30, Sept 29 non-leap, Sept 29 leap year, Oct 31, Jan 31), December boundary, and compute_booking_windows field verification.
- **tests/test_booking_impact.py**: 8 tests covering basic impact, existing reservations, no point chart error, contract filtering, and banking warning (fires, deadline passed, no current points, covered by non-current).

### Task 2: Preview API endpoint with schemas and integration tests
**Commit:** 625eaff

- **backend/api/schemas.py**: Added ReservationPreviewRequest, BookingWindowInfo, BankingWarning, AvailabilitySnapshot, and ReservationPreviewResponse schemas. Preview request includes check_out > check_in validation.
- **backend/api/reservations.py**: POST /api/reservations/preview endpoint. Loads contract + balances + reservations from DB, converts to dicts, calls compute_booking_impact(), compute_banking_warning(), and compute_booking_windows(). Returns 404 for missing contract, 422 when point chart unavailable. Route placed before /{reservation_id} routes to avoid path parameter capture.
- **tests/test_api_reservations.py**: 5 new integration tests: valid preview (200 with all fields), invalid contract (404), no point chart (422), nightly breakdown count verification, and booking windows field type verification.

## Verification Results

- 19 engine tests pass (11 booking windows + 8 booking impact)
- 21 reservation API tests pass (16 existing + 5 new preview)
- Full test suite: 165 tests pass, 0 failures, no regressions
- Engine modules are pure: no DB imports in booking_windows.py or booking_impact.py
- Schema import verified: `from backend.api.schemas import ReservationPreviewResponse` succeeds

## Deviations from Plan

None -- plan executed exactly as written.

## Commits

| Task | Commit  | Message |
|------|---------|---------|
| 1    | 6772d50 | feat(05-01): add booking windows and booking impact engine modules |
| 2    | 625eaff | feat(05-01): add POST /api/reservations/preview endpoint with schemas |

## Self-Check: PASSED
