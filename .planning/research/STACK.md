# Technology Stack: v1.1 Additions

**Project:** DVC Dashboard v1.1 (Share & Plan)
**Researched:** 2026-02-10
**Scope:** NEW libraries/tools only. Existing stack (FastAPI, React 19, Vite 7, Tailwind 4, shadcn/ui, TanStack Query, SQLAlchemy, SQLite) is validated and unchanged.

## What v1.1 Needs That v1.0 Doesn't Have

| Feature | Gap in Current Stack | Solution |
|---------|---------------------|----------|
| Docker packaging | No Dockerfile, no compose config | Dockerfile + docker-compose.yml |
| FastAPI serves React in production | Vite dev proxy only (`/api` -> localhost:8000) | `StaticFiles(html=True)` mount in FastAPI |
| Seasonal cost heatmap | No visualization library installed | Two options: extend existing SeasonCalendar.tsx OR add @nivo/heatmap |
| What-if scenario state | Zustand in package.json but unused; no client-side ephemeral state management | Use Zustand (already a dependency) |
| Booking window date math | `date-fns` already installed, `python-dateutil` already installed | No new libraries needed |
| Configurable borrowing policy | No settings/preferences API or storage | Small backend API addition, no new libraries |

## Recommended Stack Additions

### Docker & Deployment

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Docker** (multi-stage Dockerfile) | Engine 27+ | Package entire app as a single container | Single container is correct for a single-user SQLite app. Multi-stage build keeps image small: Node stage builds frontend, Python stage serves everything. No nginx needed -- FastAPI serves the built React assets directly via `StaticFiles`. | HIGH |
| **Docker Compose** | v2 (Compose Specification) | One-command startup with volume for database persistence | `docker compose up` is the simplest self-hosting experience. Named volume for `dvc.db` ensures data persists across container rebuilds. No external database service needed since SQLite is a file. | HIGH |

**Why a single container (not two):** The app is a monolith with a single SQLite file. Running separate frontend and backend containers adds networking complexity, CORS configuration, and a reverse proxy requirement -- all for zero benefit. FastAPI serving the Vite build output (`dist/`) via `StaticFiles(directory="dist", html=True)` eliminates the need for nginx or a separate frontend container. The `html=True` parameter enables SPA catch-all routing so React Router deep links work.

**Why NOT nginx:** For a single-user personal tool, uvicorn serves static files perfectly well. Nginx adds a second process, a second config file, and container complexity for marginal performance gains that are irrelevant at this scale.

**Base image:** Use `python:3.12-slim` (not `python:3.12` which includes build tools, compilers, and extra weight). The slim variant is ~150MB vs ~1GB for the full image. The deprecated `tiangolo/uvicorn-gunicorn-fastapi` image should NOT be used -- build from scratch per current FastAPI docs.

### Visualization: Seasonal Cost Heatmap

There are two viable approaches. The recommendation depends on which visualization format is chosen.

**Option A: Extend existing SeasonCalendar.tsx (NO new dependency)**

The codebase already has `SeasonCalendar.tsx` -- a custom 12-month calendar grid that renders per-day cells with color-coded seasons, weekend indicators, and tooltips. The cost heatmap could reuse this exact pattern, replacing categorical season colors with a continuous point-cost color scale.

| Aspect | Detail |
|--------|--------|
| **Best for** | Day-by-day calendar view ("when is the cheapest time to visit?") |
| **Effort** | LOW -- clone SeasonCalendar, change color logic from season-based to value-based |
| **New dependencies** | None |
| **Limitation** | Shows one room type at a time (user selects room via dropdown) |

**Option B: Add @nivo/heatmap (NEW dependency)**

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **@nivo/heatmap** | 0.99.x | Matrix heatmap (rooms x seasons) | For a grid visualization where rows = room types and columns = seasons/months, cells colored by point cost. Nivo's `ResponsiveHeatMap` provides built-in color scales, tooltips, labels, and responsive sizing. React 19 support confirmed in v0.98+ (react-spring upgrade). | HIGH |
| **@nivo/core** | 0.99.x | Required peer dependency for @nivo/heatmap | All @nivo packages require @nivo/core. Provides theming, responsive wrappers, and shared utilities. | HIGH |

| Aspect | Detail |
|--------|--------|
| **Best for** | Room-type comparison matrix ("which room is cheapest in which season?") |
| **Effort** | MEDIUM -- new component + data transformation from chart JSON to nivo format |
| **New dependencies** | @nivo/core, @nivo/heatmap (+2 npm packages) |
| **Advantage** | Shows ALL room types simultaneously in one view |

**Recommendation: Start with Option A, add Option B if needed.**

Option A delivers the highest-value visualization (day-by-day cost calendar showing when to visit) with zero new dependencies by extending an existing, proven component. Option B adds a complementary view (room comparison matrix) and can be added later as a separate enhancement if the cross-room comparison proves valuable.

**Comparison of alternatives considered (for either approach):**

| Option | Verdict | Reasoning |
|--------|---------|-----------|
| Extend SeasonCalendar.tsx | START HERE | Zero dependencies. Proven pattern in the codebase. Same visual language as existing UI. Covers the primary use case ("when is cheapest to visit"). |
| @nivo/heatmap | ADD LATER IF NEEDED | Purpose-built matrix heatmap for room-type comparison. Worth adding if users need to compare ALL room types at once. React 19 compatible (v0.98+). |
| Recharts (ScatterChart hack) | Rejected | Recharts has no native heatmap. The workaround uses `ReferenceArea` on a `ScatterChart` -- fragile, undocumented. GitHub issue #237 open since 2016 with no implementation. |
| @nivo/calendar | Wrong shape | GitHub-contribution-graph layout (weeks in columns). Not a standard month-grid calendar. Does not match the existing SeasonCalendar visual language. |
| react-heatmap-grid | Rejected | Last published 6 years ago. 40 weekly downloads. Not maintained. No React 19 support. |
| MUI X Heatmap | Overkill | Requires the entire MUI ecosystem. Paid license for heatmap features. |

### State Management: What-If Scenarios

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **Zustand** | 5.0.x | Client-side ephemeral state for hypothetical bookings | Already in `package.json` (v5.0.11) but not yet used in v1.0 code. The scenario playground needs to manage a list of hypothetical bookings that exist only in the browser -- not persisted to the backend. Zustand is the right tool: lightweight (1.1kB), no boilerplate, subscription-based re-rendering that works well with React 19's concurrent features. | HIGH |

**Why Zustand for scenarios (not just React state):**

The what-if scenario playground manages a _list_ of hypothetical bookings that affect a shared _derived calculation_ (remaining available points). Multiple components need to read and modify this list:
- The "add hypothetical booking" form
- The booking list with remove/edit
- The running point balance summary
- The "can I still afford X?" indicator

With plain `useState`, this state would need to be lifted to a common ancestor and prop-drilled down. Zustand provides a store that any component can subscribe to directly, and with `useShallow` prevents unnecessary re-renders. This is exactly the use case it was included in the project for.

**Scenario store shape (design guidance):**

```typescript
interface ScenarioStore {
  // Hypothetical bookings (not saved to backend)
  bookings: HypotheticalBooking[];
  addBooking: (booking: HypotheticalBooking) => void;
  removeBooking: (id: string) => void;
  clearAll: () => void;

  // Derived: total points committed by scenarios
  // (computed by combining with real availability from TanStack Query)
}
```

**What NOT to use Zustand for:** Server state (contracts, reservations, point balances, point charts) stays in TanStack Query. Zustand only holds the ephemeral what-if scenario state that lives in the browser session and disappears on page reload.

### Booking Window Date Calculations

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| **python-dateutil** | 2.9.x (existing) | 11-month / 7-month booking window calculations on backend | Already installed. `relativedelta(months=-11)` from a check-in date gives the exact home-resort booking open date. Already used in `use_year.py` for banking deadline calculations. No new dependency needed. | HIGH |
| **date-fns** | 4.1.x (existing) | Format/display booking window dates on frontend | Already installed. `subMonths()`, `format()`, and `differenceInDays()` handle all frontend date display needs. No new dependency needed. | HIGH |

**Booking window logic belongs in the backend engine**, not the frontend. The pattern is:
- Backend: `engine/booking_windows.py` -- pure function that takes a check-in date and contract's home resort, returns booking open dates and days-until-open
- API: Endpoint returns computed booking window data
- Frontend: Displays the dates with `date-fns` formatting

This follows the existing Pattern 3 (Pure Function Calculation Engine) from the v1.0 architecture.

## No New Libraries Needed

These v1.1 features are achievable with the existing stack:

| Feature | Why No New Library |
|---------|-------------------|
| **Booking impact preview** | Reuses existing `trip_explorer.py` engine. Frontend adds a "What happens to my points?" display using data already returned by the trip explorer API. UI built with existing shadcn/ui components. |
| **Configurable borrowing policy** | Small settings table in SQLite + API endpoint + Pydantic model. Single boolean/enum field. No library for this. |
| **Booking window alerts** | Date math with `python-dateutil` (backend) + display with `date-fns` (frontend). Alert UI with existing shadcn/ui `Alert` component. |
| **Docker packaging** | Dockerfile + docker-compose.yml are configuration files, not library dependencies. |
| **Cost heatmap (Option A)** | Extend existing `SeasonCalendar.tsx` with value-based colors instead of season-based colors. No new dependencies. |

## What NOT to Add

| Avoid | Why Suggested | Why Wrong for This Project |
|-------|---------------|---------------------------|
| **nginx** | "Proper" static file serving in production | Uvicorn serves static files fine for a single-user app. Nginx adds container complexity (second process, config file, supervisor/entrypoint script) for zero measurable benefit. |
| **Recharts** | Listed in v1.0 STACK.md as recommended | v1.0 never installed it. The cost heatmap is the first visualization need. Recharts cannot do heatmaps natively. If future phases need line/bar charts, consider Recharts then. |
| **Redux / Redux Toolkit** | "Proper" state management for complex scenario modeling | Zustand already in the project, scenario state is a simple list of hypothetical bookings. Redux would add 15kB+ and boilerplate for no benefit. |
| **React Context for scenarios** | "Built in, no dependency" | Context re-renders all consumers on any change. Zustand's subscription model is more efficient and the API is simpler. Zustand is already a dependency. |
| **D3.js directly** | Maximum visualization flexibility | Imperative DOM manipulation inside React components is an anti-pattern. If a charting library is needed, use a React wrapper like @nivo. For the calendar heatmap, the existing SeasonCalendar pattern is simpler. |
| **Celery / task queue** | Background processing for scenarios | Scenarios are client-side calculations. No async backend work needed. The engine's pure functions return instantly for the data volumes in this app. |
| **PostgreSQL** | "Docker usually means Postgres" | SQLite is simpler for a single-container single-user app. Named volume persistence works perfectly. No database container needed. |
| **Multi-container docker-compose** | Separate frontend, backend, and database containers | Over-engineering. One container, one process, one database file. Docker Compose is used solely for volume persistence and environment config, not orchestration. |

## Installation

### New Frontend Dependencies

If pursuing Option A (extend SeasonCalendar) -- the recommended starting approach:

```bash
# No new npm installs needed
```

If pursuing Option B (add @nivo/heatmap for room comparison matrix):

```bash
cd frontend
npm install @nivo/core@^0.99.0 @nivo/heatmap@^0.99.0
```

### New Backend Dependencies

None. All backend needs are met by existing dependencies.

### Docker Files (new, at project root)

```
DVC/
  Dockerfile          # NEW - multi-stage build
  docker-compose.yml  # NEW - single service + volume
  .dockerignore       # NEW - exclude node_modules, __pycache__, .git
```

## Docker Architecture

### Multi-Stage Dockerfile Pattern

```dockerfile
# Stage 1: Build frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python image
FROM python:3.12-slim
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY data/ ./data/
COPY alembic.ini ./

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Database volume mount point
VOLUME ["/app/db"]

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose Pattern

```yaml
services:
  dvc-dashboard:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - dvc-data:/app/db
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///db/dvc.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

volumes:
  dvc-data:
```

### Key Decisions in Docker Setup

| Decision | Rationale |
|----------|-----------|
| `python:3.12-slim` base | Matches existing Python version. Slim keeps image ~200MB vs ~1GB for full. |
| `node:22-alpine` for build only | Node is only needed to build the frontend. Alpine keeps the build stage fast. Not in final image. |
| Named volume for `/app/db` | SQLite database persists across container rebuilds. Named volume (not bind mount) is Docker best practice for data persistence. |
| Single `CMD` with uvicorn | No process manager needed. Single user, single process. Uvicorn handles async well. FastAPI docs confirm uvicorn-only is fine for non-clustered deployment. |
| `curl` healthcheck | Simple HTTP check against existing `/api/health` endpoint. Note: `python:3.12-slim` does NOT include curl. Either install it (`RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*`) or use a Python-based healthcheck (`test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]`). |
| No `.env` file in image | Environment variables set in docker-compose.yml or at runtime. Database path is the only config needed. |

### Backend Changes for Docker (StaticFiles)

The only backend code change needed for Docker is mounting the frontend build output:

```python
# In backend/main.py -- add AFTER all API routes
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Serve React SPA in production (when dist/ exists)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="spa")
```

The `html=True` parameter makes `StaticFiles`:
1. Serve `index.html` for the root path `/`
2. Serve static assets (JS, CSS, images) from their actual paths
3. Fall back to `index.html` for any unmatched path (SPA catch-all)

This means React Router deep links (e.g., `/trips`, `/contracts`) work correctly -- the server returns `index.html` and React Router handles the routing client-side.

The conditional `if frontend_dist.is_dir()` means this code is harmless during development (when `dist/` does not exist and Vite dev server handles frontend serving via proxy).

**CRITICAL: Mount order matters.** The `app.mount("/", ...)` call MUST be the LAST thing in main.py, after all `app.include_router()` calls. Because `html=True` creates a catch-all, it would intercept `/api/*` requests if registered before API routes.

### CORS Update for Docker

In Docker, frontend and backend are on the same origin (both served from port 8000). The existing CORS middleware allowing `localhost:5173` is only needed for development. In production (Docker), no CORS configuration is needed because there are no cross-origin requests. The existing setup is fine as-is -- CORS middleware with `localhost:5173` has no effect when requests come from the same origin.

## Version Compatibility Matrix

All additions verified compatible with the existing stack:

| New Package / Tool | Compatible With | Verification |
|--------------------|----------------|--------------|
| @nivo/core 0.99.x (if used) | React 19.2.x | React 19 support added in nivo 0.98.0 (react-spring upgrade). Confirmed via GitHub issue #2618. |
| @nivo/heatmap 0.99.x (if used) | @nivo/core 0.99.x | Same release, always matched versions. |
| @nivo/heatmap 0.99.x (if used) | TypeScript 5.9 | Nivo ships TypeScript types. Compatible. |
| Docker multi-stage | Vite 7 build | Standard `npm run build` produces `dist/` directory. No Vite-specific Docker concerns. |
| StaticFiles(html=True) | React Router 7 | Standard SPA catch-all pattern. React Router handles client-side routing from the served index.html. |
| Zustand 5.0.x | React 19.2.x | Already in package.json, already verified compatible. Zustand 5.x has first-class React 19 support. |

## Dependency Impact Summary

| Category | Before v1.1 | After v1.1 (Option A) | After v1.1 (Option B) |
|----------|-------------|----------------------|----------------------|
| Frontend npm packages | 13 deps, 11 devDeps | 13 deps, 11 devDeps | 15 deps, 11 devDeps |
| Backend pip packages | 7 packages | 7 packages | 7 packages |
| New config files | 0 | 3 | 3 |
| New npm packages | -- | +0 | +2 (@nivo/core, @nivo/heatmap) |
| Backend code changes | -- | 1 file modified (main.py) | 1 file modified (main.py) |

## Sources

### Docker & Deployment
- [FastAPI Docker Deployment Docs](https://fastapi.tiangolo.com/deployment/docker/) -- Official Dockerfile pattern, slim image recommendation (HIGH)
- [FastAPI Static Files Docs](https://fastapi.tiangolo.com/tutorial/static-files/) -- StaticFiles mount pattern (HIGH)
- [Docker Multi-Stage Build Docs](https://docs.docker.com/build/building/multi-stage/) -- Multi-stage build patterns (HIGH)
- [Docker Volumes Docs](https://docs.docker.com/engine/storage/volumes/) -- Named volume best practices (HIGH)
- [Setting Up SQLite with Docker Compose](https://www.hibit.dev/posts/215/setting-up-sqlite-with-docker-compose) -- SQLite volume mount pattern (MEDIUM)
- [FastAPI + React Single Container](https://dakdeniz.medium.com/fastapi-react-dockerize-in-single-container-e546e80b4e4d) -- Monolith Docker pattern (MEDIUM)
- [FastAPI + React SPA Serving](https://github.com/fastapi/fastapi/discussions/5134) -- Community patterns for SPA serving (MEDIUM)
- [Deprecated tiangolo Docker Image](https://github.com/tiangolo/uvicorn-gunicorn-fastapi-docker) -- Confirmed deprecated, build from scratch (HIGH)
- [FastAPI Docker Best Practices](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/) -- Production Docker patterns (MEDIUM)
- [Docker Compose Health Checks](https://last9.io/blog/docker-compose-health-checks/) -- Health check configuration (MEDIUM)

### Visualization
- [@nivo/heatmap npm](https://www.npmjs.com/package/@nivo/heatmap) -- v0.99.0 confirmed (HIGH)
- [Nivo HeatMap Docs](https://nivo.rocks/heatmap/) -- Component API and data format (HIGH)
- [Nivo React 19 Support Issue #2618](https://github.com/plouc/nivo/issues/2618) -- React 19 compatibility confirmed by maintainer (HIGH)
- [Recharts Heatmap Issue #237](https://github.com/recharts/recharts/issues/237) -- No native heatmap support, open since 2016 (HIGH)
- [Nivo Calendar Docs](https://nivo.rocks/calendar/) -- Calendar heatmap alternative evaluated (MEDIUM)

### State Management
- [Zustand GitHub](https://github.com/pmndrs/zustand) -- v5 API, React 19 compatibility (HIGH)
- [Zustand npm](https://www.npmjs.com/package/zustand) -- v5.0.11 confirmed (HIGH)
- [Zustand Best Practices Discussion](https://github.com/pmndrs/zustand/discussions/2886) -- Non-reactive state patterns (MEDIUM)
- [React 19 + Zustand Guide](https://medium.com/@reactjsbd/react-19-state-management-with-zustand-a-developers-guide-to-modern-state-handling-8b6192c1e306) -- Integration patterns (MEDIUM)

### Date Calculations
- [date-fns npm](https://www.npmjs.com/package/date-fns) -- v4.1.0, subMonths/differenceInDays confirmed (HIGH)
- [python-dateutil](https://pypi.org/project/python-dateutil/) -- relativedelta for month arithmetic (HIGH)

---
*Stack research for: DVC Dashboard v1.1 (Share & Plan)*
*Researched: 2026-02-10*
*Scope: Additions only -- existing stack unchanged*
