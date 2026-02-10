# Architecture Research: v1.1 Feature Integration

**Domain:** DVC Dashboard -- planning tools and Docker deployment
**Researched:** 2026-02-10
**Confidence:** HIGH -- existing architecture is well-understood, new features integrate cleanly with established patterns

## Current Architecture (Baseline)

The v1.0 architecture follows a clean three-layer pattern that v1.1 features integrate into:

```
┌────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React 19)                            │
│  Pages ──> Components ──> Hooks (TanStack Query) ──> API Client        │
│                                                                        │
│  DashboardPage    AvailabilityPage    TripExplorerPage                  │
│  ContractsPage    ReservationsPage    PointChartsPage                   │
└────────────────────────────┬───────────────────────────────────────────┘
                             │ HTTP /api/*
┌────────────────────────────┴───────────────────────────────────────────┐
│                         BACKEND (FastAPI)                              │
│  API Routes ──> Engine (pure functions) ──> Data Layer                  │
│                                                                        │
│  api/availability.py    engine/availability.py    models/contract.py    │
│  api/trip_explorer.py   engine/eligibility.py     models/reservation.py │
│  api/contracts.py       engine/trip_explorer.py   models/point_balance.py│
│  api/point_charts.py    engine/use_year.py        db/database.py       │
│  api/reservations.py                                                    │
└────────────────────────────┬───────────────────────────────────────────┘
                             │
┌────────────────────────────┴───────────────────────────────────────────┐
│                         DATA LAYER                                     │
│  SQLite (dvc.db)         data/point_charts/*.json    data/resorts.json  │
│  - contracts             - polynesian_2026.json                         │
│  - point_balances        - riviera_2026.json                            │
│  - reservations          - schema.json                                  │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Properties

1. **Pure-function engine layer:** Engine functions take plain dicts and dates as arguments, return computed dicts. No DB access, no side effects. API routes handle DB reads, convert ORM objects to dicts, then call engine functions.

2. **Frontend is a display layer:** All business logic is server-side. Frontend hooks call API endpoints, components render results. No DVC rule computation in JavaScript.

3. **Static data for point charts:** Versioned JSON files loaded with `lru_cache`. No database storage for chart data.

4. **Zustand is installed but unused.** Package exists in `package.json` but no stores have been created. Available for client-side state management when needed.

## v1.1 Feature Integration Map

### Feature 1: Docker Deployment

**Scope:** Multi-stage Dockerfile, docker-compose.yml, FastAPI static file serving

**New Files:**
| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build: Node.js stage builds frontend, Python stage serves everything |
| `docker-compose.yml` | Single-service with volume mount for SQLite persistence |
| `.dockerignore` | Exclude node_modules, __pycache__, .git, etc. |

**Modified Files:**
| File | Change |
|------|--------|
| `backend/main.py` | Add StaticFiles mount for React build output + SPA fallback |
| `backend/db/database.py` | Ensure DATABASE_URL env var works for Docker volume path |

**Architecture Pattern: Single-Container SPA Serving**

FastAPI serves both the API (`/api/*` routes) and the compiled React frontend (all other paths). This eliminates CORS entirely in production and requires only one container.

```
┌───────────────────────────────────────────────────┐
│                Docker Container                     │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │            FastAPI (uvicorn)                   │  │
│  │                                               │  │
│  │  /api/*  ──> API Router (existing routes)     │  │
│  │  /*      ──> StaticFiles(frontend/dist)       │  │
│  │              with SPA fallback to index.html  │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  /app/data/      ──> volume mount for dvc.db        │
│  /app/data/point_charts/ ──> bundled in image       │
└───────────────────────────────────────────────────┘
```

**Dockerfile Multi-Stage Strategy:**

```dockerfile
# Stage 1: Build frontend
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY data/ ./data/
COPY alembic.ini ./
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**SPA Fallback Pattern for FastAPI:**

```python
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            # Fall back to index.html for client-side routing
            return FileResponse(self.directory / "index.html")

# Mount AFTER all /api/* routes
app.mount("/", SPAStaticFiles(directory="frontend/dist", html=True))
```

**SQLite Volume Persistence:**

```yaml
# docker-compose.yml
services:
  dvc-dashboard:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - dvc-data:/app/data/db
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/db/dvc.db

volumes:
  dvc-data:
```

The database file must live in a named volume so data survives container recreation. The `data/point_charts/` directory is baked into the image since charts are part of the application, not user data.

**Integration with existing code:** The `DATABASE_URL` env var is already read by `backend/db/database.py` with a default fallback. Docker just sets it to a volume-mounted path. No engine changes needed.

---

### Feature 2: Booking Impact Preview

**Scope:** Show "what happens to my points if I book this?" inline in Trip Explorer results

**New Files:**
| File | Purpose |
|------|---------|
| `backend/engine/booking_impact.py` | Pure function: given current state + hypothetical reservation, compute impact |
| `frontend/src/components/BookingImpactPanel.tsx` | Expandable panel showing point impact breakdown |

**Modified Files:**
| File | Change |
|------|--------|
| `backend/api/trip_explorer.py` | Add optional `?include_impact=true` param to enrich results |
| `backend/engine/trip_explorer.py` | Call `booking_impact` engine to compute per-option impact |
| `frontend/src/components/TripExplorerResults.tsx` | Add expand/collapse for BookingImpactPanel per result card |
| `frontend/src/types/index.ts` | Add `BookingImpact` type to `TripExplorerOption` |

**Engine Function Design:**

```python
# backend/engine/booking_impact.py

def compute_booking_impact(
    contract: dict,
    point_balances: list[dict],
    reservations: list[dict],
    hypothetical_reservation: dict,  # {check_in, check_out, points_cost}
) -> dict:
    """
    Compute the impact of a hypothetical booking on a contract's point balance.

    Returns:
        {
            "points_before": int,
            "points_after": int,
            "points_cost": int,
            "use_year_charged": int,
            "remaining_by_type": {"current": int, "banked": int, ...},
            "banking_risk": bool,      # True if remaining banked points are at risk
            "borrowing_needed": bool,   # True if hypothetical needs borrowed points
            "warnings": [str],          # e.g., "Only 15 points remain after booking"
        }
    """
```

This follows the established pattern: pure function, takes dicts, returns a dict. No DB access. The API route fetches data from DB, passes to engine, returns enriched results.

**Data Flow:**

```
User clicks "Show Impact" on a Trip Explorer result
    │
    ▼
TripExplorerResults ──> (already has the data from trip-explorer response)
    │                    impact data is computed server-side and included
    ▼
BookingImpactPanel renders:
  - "This booking costs 156 pts from your 2026 Polynesian contract"
  - "Available: 230 → 74 pts remaining"
  - Warning: "Only 74 pts remaining -- not enough for another studio stay"
```

**Integration with existing code:** The `find_affordable_options()` function in `engine/trip_explorer.py` already iterates over contracts and computes availability. The booking impact function receives the same data plus the hypothetical reservation parameters. It reuses `get_contract_availability()` internally. No schema changes needed since this is read-only computation.

---

### Feature 3: What-If Scenario Playground

**Scope:** Standalone page where user builds a list of hypothetical bookings and sees cumulative impact on all contracts

**New Files:**
| File | Purpose |
|------|---------|
| `backend/engine/scenario.py` | Pure function: given state + list of hypothetical reservations, compute cascading impact |
| `backend/api/scenarios.py` | POST endpoint accepting scenario payload |
| `backend/api/schemas.py` | New Pydantic schemas for scenario request/response (add to existing file) |
| `frontend/src/pages/ScenarioPage.tsx` | New page with scenario builder UI |
| `frontend/src/components/ScenarioBuilder.tsx` | Form to add/remove hypothetical bookings |
| `frontend/src/components/ScenarioResults.tsx` | Shows cumulative impact across all contracts |
| `frontend/src/hooks/useScenario.ts` | TanStack Query mutation for scenario computation |

**Modified Files:**
| File | Change |
|------|--------|
| `frontend/src/App.tsx` | Add `/scenarios` route |
| `frontend/src/components/Layout.tsx` | Add "Scenarios" nav item |
| `backend/main.py` | Include scenarios router |
| `frontend/src/types/index.ts` | Add scenario types |

**Key Architectural Decision: Server-Side Computation, Client-Side State**

Scenario state (the list of hypothetical bookings the user is building) lives in the frontend. This is where Zustand earns its place. The user adds/removes hypothetical bookings in the UI, and the accumulated list is sent to the backend for computation.

```
┌─────────────────────────────────────────────────┐
│                  Frontend                        │
│                                                  │
│  Zustand Store (useScenarioStore)                │
│  ┌────────────────────────────────────────────┐  │
│  │ hypotheticals: [                           │  │
│  │   {resort, room_key, check_in, check_out,  │  │
│  │    contract_id, points_cost},               │  │
│  │   ...                                       │  │
│  │ ]                                           │  │
│  └──────────────────┬─────────────────────────┘  │
│                     │ POST /api/scenarios         │
│                     ▼                             │
│  TanStack Query mutation ──> ScenarioResults      │
└─────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│                  Backend                         │
│                                                  │
│  api/scenarios.py                                │
│  ┌────────────────────────────────────────────┐  │
│  │ 1. Load contracts, balances, reservations  │  │
│  │ 2. Call engine/scenario.py with real data  │  │
│  │    + hypothetical list                     │  │
│  │ 3. Return per-contract impact              │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  engine/scenario.py                              │
│  ┌────────────────────────────────────────────┐  │
│  │ For each hypothetical (in order):          │  │
│  │   1. Compute availability with prior       │  │
│  │      hypotheticals treated as committed    │  │
│  │   2. Record impact delta                    │  │
│  │ Return cumulative snapshot per contract     │  │
│  └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

**Engine Function Design:**

```python
# backend/engine/scenario.py

def evaluate_scenario(
    contracts: list[dict],
    point_balances: list[dict],
    reservations: list[dict],         # real, existing reservations
    hypotheticals: list[dict],        # user's what-if bookings
    borrowing_policy: float = 1.0,    # 1.0 = 100%, 0.5 = 50%
) -> dict:
    """
    Evaluate a scenario of hypothetical bookings against real contract state.

    Each hypothetical is processed in order, with prior hypotheticals
    treated as committed reservations for availability calculation.

    Returns:
        {
            "baseline": {per-contract availability without hypotheticals},
            "scenario": {per-contract availability with all hypotheticals},
            "per_booking": [{impact of each hypothetical booking}],
            "feasible": bool,     # True if all bookings fit within available points
            "warnings": [str],
            "total_points_used": int,
            "total_points_remaining": int,
        }
    """
```

The critical insight is that hypotheticals must be evaluated **sequentially** -- booking #2's availability depends on booking #1 being "committed." The engine treats hypotheticals as additional entries in the reservations list, then recalculates availability after each addition.

**Why Zustand for scenario state:** The scenario builder needs local state that persists across re-renders and can be shared between the builder form and the results panel. React's built-in `useState` could work for simple cases, but Zustand provides cleaner ergonomics for list manipulation (add, remove, reorder hypotheticals) without prop drilling. It is already installed in the project.

**Why server-side computation instead of client-side:** The existing engine is in Python. Duplicating availability calculations in TypeScript would violate the "no business logic in frontend" principle and create divergence risk. The POST payload is small (a few hypothetical bookings), so network overhead is negligible.

---

### Feature 4: Booking Window Alerts

**Scope:** For each contract, show when the 11-month (home resort) and 7-month (all resorts) booking windows open for upcoming dates

**New Files:**
| File | Purpose |
|------|---------|
| `backend/engine/booking_windows.py` | Pure function: compute booking window open dates |
| `frontend/src/components/BookingWindowAlerts.tsx` | Alert cards showing upcoming window openings |

**Modified Files:**
| File | Change |
|------|--------|
| `backend/api/availability.py` | Enrich availability response with booking window data |
| `backend/engine/availability.py` | Optionally include booking window calculations |
| `frontend/src/pages/DashboardPage.tsx` | Add BookingWindowAlerts section |
| `frontend/src/components/UrgentAlerts.tsx` | Extend to include booking window urgency |
| `frontend/src/types/index.ts` | Add `BookingWindow` type |

**Domain Rules for Booking Windows:**

The booking window calculation is date arithmetic based on DVC rules:

- **11-month window (home resort):** Opens exactly 11 months before check-in date. Only for the contract's home resort.
- **7-month window (all eligible resorts):** Opens exactly 7 months before check-in date. For any resort the contract is eligible to book (per resale rules).

Example: For a check-in of March 15, 2027:
- 11-month window opens: April 15, 2026
- 7-month window opens: August 15, 2026

**Engine Function Design:**

```python
# backend/engine/booking_windows.py

from dateutil.relativedelta import relativedelta
from datetime import date

def compute_booking_windows(
    contract: dict,
    target_check_in: date,
    as_of: date = None,
) -> dict:
    """
    Compute booking window dates for a target check-in date.

    Returns:
        {
            "check_in": "2027-03-15",
            "home_resort_window": {
                "opens": "2026-04-15",
                "days_until_open": 64,
                "is_open": False,
                "resort": "polynesian",
            },
            "all_resorts_window": {
                "opens": "2026-08-15",
                "days_until_open": 186,
                "is_open": False,
            },
        }
    """
    if as_of is None:
        as_of = date.today()

    eleven_month_open = target_check_in - relativedelta(months=11)
    seven_month_open = target_check_in - relativedelta(months=7)
    # ...
```

**Integration approach:** The booking window data is derived entirely from dates and contract info -- no DB queries beyond what the availability endpoint already loads. The cleanest integration point is enriching the existing availability API response with optional booking window data, since that endpoint already loads all contracts and can compute windows for significant upcoming dates (e.g., next 6 months of check-in possibilities).

However, a **dedicated endpoint** is simpler to implement and test:

```
GET /api/booking-windows?months_ahead=6
```

This returns upcoming booking window openings across all contracts for the next N months. The dashboard page calls this endpoint separately and renders alerts.

---

### Feature 5: Seasonal Cost Heatmap

**Scope:** Visual calendar-style heatmap showing point costs by date for a selected resort and room type

**New Files:**
| File | Purpose |
|------|---------|
| `backend/api/heatmap.py` | Endpoint returning per-day point costs for a resort/room/year |
| `frontend/src/pages/HeatmapPage.tsx` | New page with resort/room selector + heatmap grid |
| `frontend/src/components/CostHeatmap.tsx` | Calendar grid with color-coded costs |
| `frontend/src/hooks/useHeatmap.ts` | TanStack Query hook for heatmap data |

**Modified Files:**
| File | Change |
|------|--------|
| `frontend/src/App.tsx` | Add `/heatmap` route |
| `frontend/src/components/Layout.tsx` | Add "Cost Heatmap" nav item |
| `backend/main.py` | Include heatmap router |
| `frontend/src/types/index.ts` | Add heatmap types |

**Backend Endpoint Design:**

```python
# backend/api/heatmap.py

@router.get("/api/heatmap/{resort}/{year}/{room_key}")
async def get_cost_heatmap(resort: str, year: int, room_key: str):
    """
    Return per-day point cost for every day of the year.

    Response: {
        "resort": "polynesian",
        "year": 2026,
        "room_key": "deluxe_studio_standard",
        "days": [
            {"date": "2026-01-01", "points": 14, "season": "Adventure", "is_weekend": false},
            {"date": "2026-01-02", "points": 14, "season": "Adventure", "is_weekend": false},
            ...365 entries
        ],
        "min_points": 14,
        "max_points": 36,
    }
    """
```

This endpoint iterates through every day of the year, calling the existing `get_point_cost()` function from `backend/data/point_charts.py`. The response includes min/max points so the frontend can compute a color scale.

**Frontend Visualization Strategy: Custom SVG Component (No Library)**

The existing `SeasonCalendar.tsx` component already renders a 12-month calendar grid with per-day color coding by season. The cost heatmap needs the same layout but with continuous color intensity instead of categorical colors.

Use the existing `SeasonCalendar.tsx` pattern as a template. Build a new `CostHeatmap.tsx` that:
1. Renders 12 month grids (same layout as `SeasonCalendar`)
2. Colors each day cell on a gradient from green (cheapest) to red (most expensive)
3. Shows point cost on hover (tooltip)
4. Optionally highlights the user's available points threshold

**Why no library:** The existing codebase already has the calendar grid rendering pattern in `SeasonCalendar.tsx`. A heatmap library like `react-calendar-heatmap` renders a GitHub-style contribution graph (one row per day-of-week, columns for weeks), which is not the right layout. The month-grid calendar layout already exists and just needs color-by-value instead of color-by-category. Building on the existing pattern keeps the UI consistent and avoids adding a dependency.

**Color Scale Implementation:**

```typescript
function getCostColor(points: number, min: number, max: number): string {
  const ratio = (points - min) / (max - min);
  // Green (low cost) -> Yellow (mid) -> Red (high cost)
  if (ratio < 0.5) {
    return `bg-green-${Math.round(ratio * 2 * 4 + 1)}00`;
  }
  return `bg-red-${Math.round((ratio - 0.5) * 2 * 4 + 1)}00`;
}
```

In practice, use Tailwind's built-in color palette with a discrete scale (5-7 levels). Avoid continuous CSS gradients since Tailwind's JIT does not support arbitrary color interpolation cleanly.

---

### Feature 6: Configurable Borrowing Policy

**Scope:** Setting to toggle between 100% and 50% borrowing limits

**New Files:**
| File | Purpose |
|------|---------|
| `backend/models/settings.py` | Settings model (key-value store for app settings) |
| `backend/api/settings.py` | GET/PUT endpoint for settings |
| `frontend/src/components/SettingsDialog.tsx` | Settings UI (dialog or dedicated section) |
| `frontend/src/hooks/useSettings.ts` | TanStack Query hook for settings |

**Modified Files:**
| File | Change |
|------|--------|
| `backend/engine/availability.py` | Accept `borrowing_policy` parameter |
| `backend/engine/scenario.py` | Accept `borrowing_policy` parameter |
| `backend/api/availability.py` | Read borrowing policy from settings, pass to engine |
| `backend/main.py` | Include settings router |
| `frontend/src/types/index.ts` | Add settings types |

**Architecture Decision: Database Settings Table**

Use a simple key-value settings table in SQLite rather than a config file, because:
1. Settings persist across container recreation (stored in the volume-mounted DB)
2. The API can read/write settings without filesystem access
3. Single source of truth for both backend and frontend

```python
# backend/models/settings.py
class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Integration with engine:** The borrowing policy is a parameter to engine functions, not a global variable. This keeps functions pure and testable:

```python
# Engine function signature -- borrowing_policy is an explicit parameter
def get_contract_availability(
    ...,
    borrowing_policy: float = 1.0,  # 1.0 = 100%, 0.5 = 50%
) -> dict:
```

The API route reads the setting from the DB and passes it as a parameter. No engine function reads settings directly.

---

## Component Boundaries Summary

### New Backend Components

| Component | Layer | Depends On | Depended On By |
|-----------|-------|------------|----------------|
| `engine/booking_impact.py` | Engine | `engine/availability.py` | `api/trip_explorer.py` |
| `engine/scenario.py` | Engine | `engine/availability.py`, `engine/booking_impact.py` | `api/scenarios.py` |
| `engine/booking_windows.py` | Engine | (date math only) | `api/booking_windows.py` or `api/availability.py` |
| `api/scenarios.py` | API | `engine/scenario.py`, DB models | Frontend |
| `api/heatmap.py` | API | `data/point_charts.py` | Frontend |
| `api/settings.py` | API | `models/settings.py` | Frontend |
| `models/settings.py` | Model | `db/database.py` | `api/settings.py`, `api/availability.py` |

### New Frontend Components

| Component | Type | Depends On |
|-----------|------|------------|
| `pages/ScenarioPage.tsx` | Page | `ScenarioBuilder`, `ScenarioResults`, `useScenario` |
| `pages/HeatmapPage.tsx` | Page | `CostHeatmap`, `useHeatmap` |
| `components/BookingImpactPanel.tsx` | Component | types only |
| `components/ScenarioBuilder.tsx` | Component | Zustand store, contract/resort data |
| `components/ScenarioResults.tsx` | Component | types only |
| `components/CostHeatmap.tsx` | Component | `SeasonCalendar.tsx` pattern reference |
| `components/BookingWindowAlerts.tsx` | Component | types only |
| `components/SettingsDialog.tsx` | Component | `useSettings` |
| `hooks/useScenario.ts` | Hook | `api.ts` |
| `hooks/useHeatmap.ts` | Hook | `api.ts` |
| `hooks/useSettings.ts` | Hook | `api.ts` |

### Modified Existing Components

| Component | Modification Scope |
|-----------|-------------------|
| `backend/main.py` | Add 3 routers (scenarios, heatmap, settings) + StaticFiles mount |
| `backend/api/trip_explorer.py` | Add impact enrichment option |
| `backend/engine/trip_explorer.py` | Call booking_impact for each result |
| `backend/engine/availability.py` | Add borrowing_policy parameter |
| `frontend/src/App.tsx` | Add 2 routes (/scenarios, /heatmap) |
| `frontend/src/components/Layout.tsx` | Add 2 nav items |
| `frontend/src/components/TripExplorerResults.tsx` | Add expand/collapse for impact panels |
| `frontend/src/pages/DashboardPage.tsx` | Add booking window alerts section |
| `frontend/src/components/UrgentAlerts.tsx` | Extend for booking window urgency |
| `frontend/src/types/index.ts` | Add 5-6 new type interfaces |

## Data Flow Changes

### Scenario Computation Flow (New)

```
[User builds hypothetical list in ScenarioBuilder]
    │
    │  Zustand store holds: [{resort, room, dates, contract_id, points_cost}, ...]
    │
    ▼
[POST /api/scenarios with hypothetical list]
    │
    ▼
[api/scenarios.py]
    │
    ├── Load contracts, balances, reservations from DB (same pattern as trip_explorer)
    │
    ├── Convert to dicts (same ORM-to-dict pattern used everywhere)
    │
    └── Call engine/scenario.py with real data + hypotheticals
         │
         ├── For hypothetical #1: compute availability with real reservations only
         │   └── Record: points_before, points_after, delta
         │
         ├── For hypothetical #2: compute availability with real + hypothetical #1
         │   └── Record: points_before, points_after, delta
         │
         └── Return cumulative snapshot
              │
              ▼
[ScenarioResults renders per-booking impact + cumulative summary]
```

### Heatmap Data Flow (New)

```
[User selects resort + room type on HeatmapPage]
    │
    ▼
[GET /api/heatmap/{resort}/{year}/{room_key}]
    │
    ▼
[api/heatmap.py]
    │
    ├── Load point chart (existing load_point_chart function)
    │
    ├── Iterate through every day of the year
    │   └── For each day: call get_point_cost() (existing function)
    │
    └── Return array of 365 {date, points, season, is_weekend} objects
         │
         ▼
[CostHeatmap renders 12-month calendar grid with color intensity by cost]
```

### Booking Window Alert Flow (New)

```
[DashboardPage loads]
    │
    ├── Existing: GET /api/availability?target_date=today
    │
    └── New: GET /api/booking-windows?months_ahead=6
         │
         ▼
    [api/booking_windows.py]
         │
         ├── Load contracts from DB
         │
         ├── For each contract, compute:
         │   - 11-month window open dates for next 6 months of check-ins
         │   - 7-month window open dates for next 6 months of check-ins
         │
         └── Return list of upcoming window openings, sorted by date
              │
              ▼
    [BookingWindowAlerts renders on dashboard]
    "Polynesian 11-month window opens in 3 days for Dec 15 check-in"
```

## Suggested Build Order

The build order is driven by dependency chains between features and the ability to validate each step independently.

### Phase 1: Docker Deployment + Configurable Borrowing Policy

**Rationale:** Docker is infrastructure that enables all other work to be shared. Borrowing policy is a small engine change that establishes the settings pattern used elsewhere.

**Build sequence:**
1. Borrowing policy engine parameter (modify `engine/availability.py`) -- small, testable
2. Settings model + API endpoint -- establishes the pattern
3. Settings UI (simple dialog or section)
4. Dockerfile + docker-compose.yml
5. FastAPI static file serving (SPA fallback)
6. `.dockerignore`
7. Test: `docker compose up` serves the full app with persistent SQLite

**Dependencies satisfied:** None needed. This is foundational.
**Dependencies created:** Docker setup enables deployment of all subsequent features.

### Phase 2: Booking Impact Preview + Booking Window Alerts

**Rationale:** These are the smallest new engine features and they enrich existing pages (Trip Explorer, Dashboard) rather than creating new ones. Booking impact is a prerequisite for the scenario playground.

**Build sequence:**
1. `engine/booking_impact.py` -- pure function, tested independently
2. Enrich Trip Explorer API response with impact data
3. `BookingImpactPanel.tsx` component
4. Integrate into `TripExplorerResults.tsx`
5. `engine/booking_windows.py` -- pure function, date math only
6. Booking windows API endpoint
7. `BookingWindowAlerts.tsx` component
8. Integrate into `DashboardPage.tsx` and `UrgentAlerts.tsx`

**Dependencies satisfied:** Booking impact engine is prerequisite for scenarios.
**Dependencies created:** Scenario playground can reuse booking impact logic.

### Phase 3: What-If Scenario Playground

**Rationale:** This is the most complex new feature. It depends on the booking impact engine from Phase 2 and introduces the first Zustand store.

**Build sequence:**
1. `engine/scenario.py` -- composes booking impact for multiple hypotheticals
2. `api/scenarios.py` + Pydantic schemas
3. Zustand store for scenario state (`useScenarioStore`)
4. `ScenarioBuilder.tsx` -- form to add hypothetical bookings
5. `ScenarioResults.tsx` -- cumulative impact display
6. `ScenarioPage.tsx` + routing + nav
7. Wire up `useScenario.ts` hook

**Dependencies satisfied:** Uses `engine/booking_impact.py` from Phase 2.

### Phase 4: Seasonal Cost Heatmap

**Rationale:** This is a standalone visualization feature with no dependencies on other v1.1 features. It can be built last since it is additive and does not block other features.

**Build sequence:**
1. `api/heatmap.py` -- endpoint using existing `get_point_cost()`
2. `CostHeatmap.tsx` -- adapted from `SeasonCalendar.tsx` pattern
3. `HeatmapPage.tsx` + routing + nav
4. `useHeatmap.ts` hook

**Dependencies satisfied:** None needed. Uses only existing point chart data layer.

### Build Order Rationale

```
Phase 1: Docker + Settings     ──> Infrastructure foundation
    │
    ▼
Phase 2: Impact + Windows      ──> Engine extensions, existing page enrichment
    │
    ▼
Phase 3: Scenario Playground   ──> Depends on Phase 2 engine work
    │
    ▼
Phase 4: Cost Heatmap          ──> Independent, additive, no dependencies
```

- **Docker first** because every subsequent feature should be testable in the Docker environment.
- **Impact before Scenarios** because the scenario engine composes the booking impact engine.
- **Booking windows with impact** because both are small engine features that enrich existing pages.
- **Heatmap last** because it is standalone and purely additive -- it does not affect or depend on any other v1.1 feature.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Computing Scenarios Client-Side

**What:** Implementing availability calculations in TypeScript so scenarios can be computed locally without API calls.
**Why bad:** Duplicates the Python engine logic. When DVC rules change (e.g., borrowing policy), you must update two codebases. The engine has 141 tests -- would need to duplicate those too.
**Instead:** POST hypotheticals to the backend. The round-trip is <100ms for this payload size. Keep all DVC math in Python.

### Anti-Pattern 2: Storing Scenario State in the Database

**What:** Creating a `scenarios` table to persist hypothetical bookings.
**Why bad:** Scenarios are ephemeral planning exercises, not persisted data. Adding DB tables, migrations, and CRUD for temporary data is over-engineering.
**Instead:** Hold scenario state in Zustand (frontend memory). The backend is stateless -- it receives the scenario payload, computes, and returns results. If the user refreshes, the scenario is gone. That is acceptable for a planning tool.

### Anti-Pattern 3: Nginx Reverse Proxy in Docker

**What:** Adding an Nginx container in docker-compose to serve frontend static files and proxy API calls.
**Why bad:** This is a single-user personal tool. An extra container adds complexity to the Docker setup without meaningful performance benefit at this scale. FastAPI's StaticFiles middleware serves static files adequately for a single user.
**Instead:** Single container. FastAPI serves both API and static files. One container to deploy, one container to debug.

### Anti-Pattern 4: Using a Charting Library for the Heatmap

**What:** Adding D3.js, Chart.js, or a heavy heatmap library for the cost visualization.
**Why bad:** The calendar grid rendering is already implemented in `SeasonCalendar.tsx`. A library adds bundle size and forces a different visual style than the rest of the app. The heatmap is a colored calendar grid -- not a complex chart.
**Instead:** Extend the existing `SeasonCalendar` pattern. Same grid layout, same Tailwind styling, but with value-based colors instead of category-based colors.

## Scalability Considerations

| Concern | At Current Scale (1 user, 2-3 contracts) | If Scale Grew (5 users) |
|---------|------------------------------------------|------------------------|
| Scenario computation | Instantaneous (<10ms) | Still instantaneous -- at most 20 hypotheticals against 15 contracts |
| Heatmap endpoint | 365 iterations, cached point chart data. <50ms | Same. Data is static JSON, cached. |
| Docker SQLite concurrency | Single user, no concurrency issues | SQLite WAL mode handles concurrent reads. Multiple simultaneous writers would need PostgreSQL. |
| Booking window alerts | Date math for 6 months * N contracts. Trivial. | Still trivial. |
| Static file serving from FastAPI | Adequate for single user. Vite builds are small. | Adequate. Add Nginx only if serving hundreds of concurrent requests. |

## Sources

- [FastAPI Docker Deployment (official docs)](https://fastapi.tiangolo.com/deployment/docker/)
- [FastAPI Static Files (official docs)](https://fastapi.tiangolo.com/tutorial/static-files/)
- [FastAPI support for React with working react-router (GitHub gist)](https://gist.github.com/ultrafunkamsterdam/b1655b3f04893447c3802453e05ecb5e)
- [FastAPI + React Dockerize in single container (Medium)](https://dakdeniz.medium.com/fastapi-react-dockerize-in-single-container-e546e80b4e4d)
- [Docker Persisting Data (official docs)](https://docs.docker.com/get-started/workshop/05_persisting_data/)
- [Docker Volumes & Data Persistence Guide](https://www.bibekgupta.com/blog/2025/04/docker-volumes-data-persistence-guide)
- [DVC Booking Windows -- When to Book (official)](https://disneyvacationclub.disney.go.com/faq/resort-reservations/booking-window/)
- [DVC Home Resort Priority Period (official)](https://disneyvacationclub.disney.go.com/faq/resort-reservations/home-resort-priority/)
- [DVC 7 and 11-Month Booking Windows Explained (DVC Shop)](https://dvcshop.com/the-7-and-11-month-booking-windows-explained/)
- [Key DVC Membership Dates Calculation (DVC Field Guide)](https://dvcfieldguide.com/blog/key-membership-dateshow-to-calculate)
- [react-calendar-heatmap (npm)](https://www.npmjs.com/package/react-calendar-heatmap)
- [react-heat-map (GitHub)](https://github.com/uiwjs/react-heat-map)
- [Best heatmap libraries for React (LogRocket)](https://blog.logrocket.com/best-heatmap-libraries-react/)

---
*Architecture research for: DVC Dashboard v1.1 Feature Integration*
*Researched: 2026-02-10*
