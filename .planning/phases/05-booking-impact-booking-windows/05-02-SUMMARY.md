---
phase: 05-booking-impact-booking-windows
plan: 02
subsystem: frontend-booking-preview
tags: [booking-impact, booking-windows, expandable-cards, lazy-loading, trip-explorer]
dependency_graph:
  requires: [booking-impact-engine, booking-windows-engine, preview-endpoint]
  provides: [booking-preview-ui, expandable-trip-cards, booking-window-badges]
  affects: [frontend/src/components/TripExplorerResults.tsx, frontend/src/pages/TripExplorerPage.tsx]
tech_stack:
  added: []
  patterns: [lazy-query-loading, expandable-card-with-chevron, collapsible-details-table]
key_files:
  created:
    - frontend/src/hooks/useBookingPreview.ts
    - frontend/src/components/BookingImpactPanel.tsx
    - frontend/src/components/BookingWindowBadges.tsx
  modified:
    - frontend/src/types/index.ts
    - frontend/src/components/TripExplorerResults.tsx
    - frontend/src/pages/TripExplorerPage.tsx
decisions:
  - Inline expand/collapse via useState per card (not shadcn Collapsible)
  - Native HTML details/summary for nightly breakdown (no extra deps)
  - ChevronDown icon with CSS rotate for expand indicator
metrics:
  duration: 1m 58s
  completed: 2026-02-10
---

# Phase 5 Plan 2: Booking Impact & Booking Windows Frontend Summary

Expandable Trip Explorer result cards with lazy-loaded booking impact preview (before/after point balances, nightly breakdown, banking warning) and booking window date badges (11-month home resort, 7-month any resort).

## What Was Built

### Task 1: TypeScript types + preview hook
**Commit:** ad669ac

- **frontend/src/types/index.ts**: Added `BookingWindowInfo`, `BankingWarning`, `AvailabilitySnapshot`, and `ReservationPreview` interfaces after existing Trip Explorer types. `ReservationPreview` composes `NightlyCost[]` (already defined) for nightly breakdown.
- **frontend/src/hooks/useBookingPreview.ts**: React Query hook with `enabled: !!request` for lazy loading. Query only fires when request is non-null (card is expanded). `queryKey` includes `contract_id + resort + room_key + check_in` for per-card cache isolation. `staleTime: 30_000` prevents re-fetching on rapid expand/collapse.

### Task 2: BookingImpactPanel, BookingWindowBadges, and expandable TripExplorerResults
**Commit:** c6ac266

- **frontend/src/components/BookingImpactPanel.tsx**: Two-column before/after layout showing available points and per-allocation-type breakdown using `ALLOCATION_TYPE_LABELS`. Points delta shown in destructive color. Nightly breakdown in native `<details><summary>` collapsible with date/day/season/points table, weekend rows highlighted with `bg-muted/30`. Banking warning renders as amber alert box with `AlertTriangleIcon` matching UrgentAlerts pattern.
- **frontend/src/components/BookingWindowBadges.tsx**: Badge components for 11-month home resort and 7-month any-resort windows. Green variant when open, blue when upcoming. Pulsing ring animation (`ring-2 ring-blue-300 animate-pulse`) for windows opening within 14 days. Home resort badge only shown when `is_home_resort` is true.
- **frontend/src/components/TripExplorerResults.tsx**: Refactored to extract `TripExplorerResultCard` internal component managing its own `isExpanded` state. Each card calls `useBookingPreview` with `enabled` driven by expand state. ChevronDown icon rotates 180 degrees on expand with CSS transition. Expanded section renders `BookingImpactPanel` and `BookingWindowBadges` below a border separator. Props interface updated to accept `checkIn` and `checkOut`.
- **frontend/src/pages/TripExplorerPage.tsx**: Passes `checkIn` and `checkOut` props to `TripExplorerResults`.

## Verification Results

- TypeScript compilation: `npx tsc --noEmit` -- zero errors
- Vite production build: `npx vite build` -- succeeds (465.58 kB JS, 49.12 kB CSS)
- All preview types match backend ReservationPreviewResponse schema
- Lazy loading confirmed: useBookingPreview only enabled when isExpanded is true

## Deviations from Plan

### Auto-included Files

**1. [Rule 3 - Blocking] Task 2 commit included pre-staged backend files**
- **Found during:** Task 2 commit
- **Issue:** Files `backend/api/booking_windows.py`, `backend/api/schemas.py` changes, `backend/main.py` changes, and `tests/test_api_booking_windows.py` were already in the git index from prior work (plan 05-03 prep) and got included in the Task 2 commit.
- **Impact:** No negative impact -- additional backend code for upcoming booking window alerts endpoint. Does not conflict with plan 05-02 scope.

## Commits

| Task | Commit  | Message |
|------|---------|---------|
| 1    | ad669ac | feat(05-02): add booking preview types and useBookingPreview hook |
| 2    | c6ac266 | feat(05-02): add expandable Trip Explorer cards with booking impact and window badges |

## Self-Check: PASSED
