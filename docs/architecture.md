# Architecture

## Overview

DVC Dashboard is a monorepo with a **FastAPI backend** and **React frontend**. In production, the frontend is built as static files and served by FastAPI. In development, they run as separate servers.

```
Browser --> FastAPI (port 8000)
              |-- /api/* --> Route handlers --> Engine --> SQLAlchemy --> SQLite
              |-- /*     --> React SPA (static files)
```

The backend handles all data persistence and business logic. The frontend is a single-page application that communicates exclusively through the REST API.

## Backend

### Layer Architecture

Three layers with strict dependency direction: API -> Engine -> Data.

1. **API Layer** (`backend/api/`) -- FastAPI route handlers. Receives HTTP requests, validates input via Pydantic schemas (`schemas.py`), calls engine functions or queries the database, and returns JSON responses. Structured error handling via the `AppError` class hierarchy in `errors.py`.

2. **Engine Layer** (`backend/engine/`) -- Pure business logic functions. No database imports, no async. Takes plain data (dicts, dates, ints) in, returns plain data out. This makes the core logic testable without database fixtures.

   - `availability.py` -- Point availability calculations (banking, borrowing, expirations)
   - `use_year.py` -- Use year period calculations and date math
   - `eligibility.py` -- Resort eligibility based on contract type (resale vs direct)
   - `booking_impact.py` -- Before/after point balance impact of a proposed booking
   - `booking_windows.py` -- 11-month home resort and 7-month any-resort window dates
   - `trip_explorer.py` -- What-can-I-book search across resorts and room types
   - `scenario.py` -- What-if scenario evaluation with multiple hypothetical bookings

3. **Data Layer** (`backend/models/`, `backend/db/`) -- SQLAlchemy ORM models and async database setup. Uses async SQLite via `aiosqlite`. Alembic manages schema migrations.

### Data Model

Four core models:

- **Contract** (`contracts` table) -- A DVC ownership contract. Fields: home resort (slug), points per year, use year month (Feb/Mar/Apr/Jun/Aug/Sep/Oct/Dec), purchase type (resale or direct), optional friendly name. Has cascade-delete relationships to point balances and reservations.

- **PointBalance** (`point_balances` table) -- Points for a specific contract and use year. Each row represents one allocation type: `current` (annual allocation), `banked` (from prior year), `borrowed` (from next year), or `holding` (late cancellation). Uniquely identified by contract + use year + allocation type.

- **Reservation** (`reservations` table) -- A booking with check-in/out dates, resort, room type, points cost, status (confirmed/pending/cancelled), optional confirmation number and notes. Linked to a contract via foreign key.

- **AppSetting** (`app_settings` table) -- Key-value configuration store. Currently stores the borrowing limit percentage (50% or 100% of annual points).

Point chart data lives in JSON files under `data/point_charts/`, loaded at startup. Charts are version-controlled and not stored in the database, making them easy to update and diff.

### Error Handling

All API errors return a consistent JSON structure:

```json
{
  "error": {
    "type": "VALIDATION_ERROR",
    "message": "Validation failed",
    "fields": [{"field": "name", "issue": "Name cannot be empty"}]
  }
}
```

Four error types:

| Type | Status | When |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `NOT_FOUND` | 404 | Requested resource does not exist |
| `CONFLICT` | 409 | Duplicate or conflicting resource |
| `SERVER_ERROR` | 500 | Unhandled exception (generic message to client, real error logged server-side) |

Pydantic request validation errors are also caught and reformatted into the same structure, returning all invalid fields at once rather than failing on the first error.

## Frontend

### Structure

- **Pages** (`pages/`) -- One component per route. Each page is a top-level composition of components and hooks: Dashboard, Contracts, Reservations, Availability, Trip Explorer, Point Charts, Scenarios, Settings.
- **Components** (`components/`) -- Reusable UI pieces. Domain components (ContractCard, ReservationCard, AvailabilityCard, BookingImpactPanel, ScenarioComparison, TripExplorerResults) and shared utilities (LoadingSkeleton, ErrorAlert, EmptyState, ErrorBoundary).
- **Hooks** (`hooks/`) -- TanStack Query wrappers for each API resource: useContracts, useReservations, usePoints, useAvailability, usePointCharts, useTripExplorer, useBookingPreview, useBookingWindows, useScenarioEvaluation. Handle loading, error, and cache states.
- **UI** (`components/ui/`) -- shadcn/ui primitives (Button, Card, Dialog, Table, etc.).

### State Management

- **Server state:** TanStack Query (react-query) for all API data. Automatic caching with 5-minute stale time, refetching, and error handling.
- **Client state:** Zustand for ephemeral scenario form state (not persisted).
- **No global app state** -- each page fetches what it needs via hooks.

### Routing

React Router v7 with a shared Layout component. All routes are wrapped in per-section ErrorBoundary components for crash isolation.

| Route | Page |
|---|---|
| `/` | Dashboard |
| `/contracts` | Contracts |
| `/reservations` | Reservations |
| `/availability` | Availability |
| `/trip-explorer` | Trip Explorer |
| `/point-charts` | Point Charts |
| `/scenarios` | Scenarios |
| `/settings` | Settings |

## Deployment

Single Docker container via multi-stage Dockerfile:

1. **Stage 1 (Node.js):** Builds the React frontend with `npm run build`, producing static files in `frontend/dist/`.
2. **Stage 2 (Python):** Installs backend dependencies, copies backend code, baked-in point chart data, and the built frontend from stage 1.

The `entrypoint.sh` script runs Alembic migrations (`alembic upgrade head`) then starts uvicorn on the configured port. Docker Compose maps the port and mounts a named volume (`dvc-data`) for SQLite database persistence.

```yaml
services:
  dvc:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    volumes:
      - dvc-data:/app/data/db
```
