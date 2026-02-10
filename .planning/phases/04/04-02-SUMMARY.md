---
phase: 04-docker-settings
plan: 02
subsystem: settings
tags: [app-settings, borrowing-policy, configuration, ui]
dependency_graph:
  requires: [04-01]
  provides: [app-settings-model, settings-api, borrowing-enforcement, settings-ui]
  affects: [backend/api/points.py, backend/main.py, frontend/src/App.tsx]
tech_stack:
  added: []
  patterns: [key-value-settings, configurable-business-rules]
key_files:
  created:
    - backend/models/app_setting.py
    - backend/api/settings.py
    - backend/db/migrations/versions/ac1df6fa81e8_add_app_settings_table.py
    - frontend/src/pages/SettingsPage.tsx
  modified:
    - backend/models/__init__.py
    - backend/db/migrations/env.py
    - backend/api/schemas.py
    - backend/api/points.py
    - backend/main.py
    - frontend/src/components/Layout.tsx
    - frontend/src/App.tsx
decisions:
  - Key-value AppSetting model for extensible settings storage
  - Borrowing policy enforced on both create and update of borrowed point balances
  - Settings API validates allowed values server-side (only 50 or 100 accepted)
  - Toggle-style UI cards for policy selection (not dropdown)
metrics:
  duration: 4m 23s
  completed: 2026-02-10
---

# Phase 4 Plan 2: App Settings with Borrowing Policy Summary

Key-value AppSetting model with settings API, borrowing policy enforcement (50%/100% of annual points), and Settings page with toggle UI for CONF-01.

## What Was Built

### Task 1: AppSetting model, migration, settings API, and borrowing policy enforcement
**Commit:** d3edf8d

- **backend/models/app_setting.py**: AppSetting SQLAlchemy model with `key` (primary key) and `value` columns for extensible key-value settings storage
- **backend/db/migrations/versions/ac1df6fa81e8_add_app_settings_table.py**: Alembic migration creating `app_settings` table with seed data (`borrowing_limit_pct=100`)
- **backend/api/settings.py**: Settings CRUD router with GET /api/settings (list all), GET /api/settings/{key}, PUT /api/settings/{key} with value validation against allowed values schema
- **backend/api/schemas.py**: Added AppSettingResponse and AppSettingUpdate Pydantic schemas
- **backend/api/points.py**: Replaced warning-only borrowed points check with enforcement -- queries `borrowing_limit_pct` setting and raises 422 if borrowed points exceed `annual_points * limit_pct / 100`. Applied to both create_point_balance (POST) and update_point_balance (PUT)
- **backend/main.py**: Registered settings_router before SPA mount
- **backend/models/__init__.py**: Added AppSetting export
- **backend/db/migrations/env.py**: Added AppSetting to Alembic model imports

### Task 2: Frontend settings page with borrowing policy toggle
**Commit:** e21d08c

- **frontend/src/pages/SettingsPage.tsx**: Settings page using react-query for data fetching, Card component for layout, and toggle-style buttons for 100%/50% selection. Active option highlighted with `bg-primary text-primary-foreground` matching sidebar active state pattern
- **frontend/src/components/Layout.tsx**: Added "Settings" as last nav item in sidebar
- **frontend/src/App.tsx**: Added /settings route with SettingsPage component after /point-charts

## Verification Results

### Task 1 (Backend)
- GET /api/settings returns `[{"key": "borrowing_limit_pct", "value": "100"}]`
- PUT to 50% succeeds, PUT to 75% correctly returns 422
- At 50% policy: borrowing 150 points on 200 annual contract rejected (150 > 100)
- At 100% policy: borrowing 150 points on 200 annual contract accepted (150 <= 200)

### Task 2 (Frontend)
- TypeScript compilation: zero errors
- Vite production build: succeeds (461KB JS bundle)
- Docker build: succeeds with new frontend included

### Task 3 (Checkpoint)
- Awaiting human verification of end-to-end flow in Docker

## Deviations from Plan

None -- plan executed exactly as written.

## Commits

| Task | Commit  | Message |
|------|---------|---------|
| 1    | d3edf8d | feat(04-02): add AppSetting model, settings API, and borrowing policy enforcement |
| 2    | e21d08c | feat(04-02): add Settings page with borrowing policy toggle |

## Self-Check: PASSED

All 11 files verified present on disk. Both commits (d3edf8d, e21d08c) verified in git log.
