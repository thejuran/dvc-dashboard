# Domain Pitfalls: v1.1 Features

**Domain:** DVC Points Management Dashboard -- Docker packaging, booking impact preview, what-if scenario playground, booking window alerts, seasonal cost heatmap
**Researched:** 2026-02-10
**Confidence:** MEDIUM-HIGH (Docker+SQLite pitfalls are well-documented; DVC domain rules are verified against official sources; heatmap rendering patterns are established)

---

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or fundamentally broken features.

---

### Pitfall 1: SQLite Database Loss in Docker Due to Missing Volume Mount

**What goes wrong:**
The SQLite database file (`dvc.db`) is stored inside the container filesystem by default. When the container is rebuilt, updated, or restarted with `docker compose up --build`, all data disappears. The user enters their contracts and point balances, rebuilds the image after a code change, and everything is gone. This is the single most common Docker-with-SQLite failure and it will happen during development and in production.

**Why it happens:**
SQLite stores everything in a single file (plus WAL and SHM sidecar files when in WAL mode). Unlike PostgreSQL or MySQL which run as separate containers with their own volumes, SQLite lives inside the application container. Developers test with `docker run` and the data persists across container restarts (same container), but disappears on `docker compose up --build` (new container). The distinction between container restart and container recreation is subtle and catches everyone.

**Consequences:**
- Complete data loss on container rebuild
- User loses all contracts, point balances, and reservations
- If WAL/SHM files are separated from the main DB file (e.g., only the .db file is mounted but not the directory), the database can become corrupted

**Prevention:**
1. Mount the **directory containing the database**, not the database file itself. The WAL (`dvc.db-wal`) and shared-memory (`dvc.db-shm`) files must be co-located:
   ```yaml
   # docker-compose.yml -- CORRECT
   volumes:
     - ./data:/app/data  # Mount the directory

   # WRONG: mounting just the file
   volumes:
     - ./dvc.db:/app/dvc.db  # WAL/SHM files will be orphaned
   ```
2. Use a named volume for the database directory, not a bind mount, when distributing to others. Bind mounts have permission issues across different host OSes.
3. Set `DATABASE_URL` to point inside the mounted volume directory: `sqlite+aiosqlite:///./data/dvc.db`
4. The current code uses `DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dvc.db")` which puts the DB at the project root. For Docker, this must be overridden to a volume-mounted path.
5. Add a `docker-compose.yml` health check or startup log that confirms the database file exists and is writable.

**Detection:**
- Database is empty after `docker compose down && docker compose up`
- "database is locked" errors when WAL mode is enabled but only the .db file is mounted
- Alembic migrations run on every restart (because they see an empty DB)

**Phase to address:** Docker packaging phase. This must be tested as the very first Docker task before any other containerization work.

---

### Pitfall 2: What-If Scenario Engine Mutating Real Point Balances

**What goes wrong:**
The what-if scenario feature needs to answer "if I book Resort X on Date Y, what happens to my point balances?" This requires running the existing availability engine with hypothetical reservations added. If the implementation mutates the actual database or shared in-memory state to simulate the scenario, hypothetical bookings can leak into the real data. A user models 3 hypothetical trips, and now their dashboard shows 3 phantom reservations or their available points are reduced by bookings that don't exist.

**Why it happens:**
The existing engine functions (`get_contract_availability`, `find_affordable_options`) take plain dicts as input -- they are pure functions. The temptation is to add the what-if scenario by inserting temporary reservations into the database, running the availability calculation, then deleting them. This creates a race condition (what if the user views the dashboard mid-calculation?) and a cleanup failure mode (what if the deletion fails?).

**Consequences:**
- Phantom reservations appearing in the real dashboard
- Available point totals that don't match reality
- If using database transactions for scenarios, potential SQLite locking since it only supports one writer at a time
- Test suite may pass (tests use isolated DB) but production fails under concurrent access

**Prevention:**
1. The existing engine is **already designed for this**. Functions like `get_contract_availability()` and `find_affordable_options()` accept `reservations: list[dict]` as input parameters. The what-if implementation should create an augmented reservations list in memory:
   ```python
   # CORRECT: Pure function approach
   real_reservations = fetch_from_db()
   hypothetical = [{"contract_id": 1, "check_in": "2026-07-01", "points_cost": 200, "status": "confirmed"}]
   scenario_reservations = real_reservations + hypothetical
   result = get_contract_availability(..., reservations=scenario_reservations, ...)
   ```
2. Never insert hypothetical data into the database, not even in a transaction that gets rolled back. SQLite's single-writer constraint means a rollback-based approach would block real writes.
3. The what-if API endpoint should be a separate GET/POST that returns scenario results without side effects.
4. Frontend should store hypothetical bookings in Zustand (already in the project) or React state, never sending them to the reservations API.

**Detection:**
- Any SQL INSERT statement in the what-if code path
- Reservation count in DB increases after using the scenario feature
- `git grep` for "commit" or "session.add" in what-if related files

**Phase to address:** What-if scenario playground phase. The pure-function architecture was designed to support this; the risk is bypassing it.

---

### Pitfall 3: `lru_cache` on `load_point_chart` Breaking Docker Deployments

**What goes wrong:**
The existing `load_point_chart()` and `load_resorts()` functions use `@lru_cache` decorators. These cache results in memory after the first call. In Docker, the data files (`data/point_charts/*.json`, `data/resorts.json`) are baked into the image at build time. If a user updates point chart JSON files on the host and expects them to be reflected (via a bind mount), the `lru_cache` will serve stale data until the container is restarted. More critically, the `lru_cache` uses `Path(__file__).parent.parent.parent / "data"` as the file path -- this path resolution depends on the working directory and Python package structure, which may differ between the development layout and the Docker container layout.

**Why it happens:**
`lru_cache` is permanent for the process lifetime. The file path is computed relative to the Python source file location. In Docker, the source files may be at `/app/backend/data/resorts.py`, making the data path `/app/data/`, which is correct -- but only if the `COPY` in the Dockerfile preserves the relative directory structure. A common multi-stage build mistake is copying only `backend/` without `data/`, or flattening the directory structure.

**Consequences:**
- Point charts show zeroes or errors because the JSON files aren't found at the expected path
- Updating a JSON file on the host has no effect until container restart
- `FileNotFoundError` on startup if directory structure is wrong

**Prevention:**
1. In the Dockerfile, preserve the project directory structure:
   ```dockerfile
   COPY backend/ /app/backend/
   COPY data/ /app/data/
   WORKDIR /app
   ```
2. Verify the `Path(__file__)` resolution in Docker by adding a startup log or health check that confirms the data directory is populated.
3. For the heatmap feature (which reads all point charts), consider whether `lru_cache` is appropriate or whether the cache should be invalidated when new chart files are added. For v1.1 where charts are static JSON, `lru_cache` is fine -- but document this behavior.
4. Add a test that imports `load_point_chart` and verifies it can find at least one chart file.

**Detection:**
- `/api/point-charts` returns empty list in Docker but works locally
- `FileNotFoundError` in container logs
- Health check passes but point chart endpoints return no data

**Phase to address:** Docker packaging phase. Must be verified during the initial Dockerfile build, before shipping.

---

### Pitfall 4: Booking Window Alert Dates Calculated Wrong Due to Use Year Confusion

**What goes wrong:**
The booking window alerts feature needs to tell users "Your 11-month home resort window opens on [date] for a [check-in date] trip." The 11-month and 7-month windows are calculated from the CHECK-IN date of the desired trip, NOT from the use year start date. Developers confuse these two date systems: the use year system (which controls point availability) and the booking window system (which controls reservation timing). A February use year owner with a December check-in date has their 11-month window open in January -- which is still within their PREVIOUS use year's banking deadline window. These two systems interact but are computed independently.

**Why it happens:**
The existing codebase is built around use year calculations (`get_use_year_start`, `get_banking_deadline`, etc.). Developers naturally try to reuse these functions for booking windows. But booking windows have nothing to do with use years -- they are purely a function of the check-in date:
- 11-month window: `check_in - 11 months` (home resort advantage)
- 7-month window: `check_in - 7 months` (any resort)

**Consequences:**
- Alerts fire on the wrong date, either too early ("window opens in -30 days") or too late (missing the actual opening)
- User misses prime booking opportunities because the alert system said "not yet"
- Confusing overlap: alert says "your window opens tomorrow" while dashboard says "banking deadline in 5 days" for the same contract -- these are about different date systems and the UI doesn't clarify

**Prevention:**
1. Implement booking window calculation as a **new, independent engine function** that does not call any use year functions:
   ```python
   def get_booking_window_open(check_in: date, window_months: int) -> date:
       """When does the booking window open for a given check-in date?"""
       return check_in - relativedelta(months=window_months)
   ```
2. The alert system should accept a list of desired check-in dates (from the user's trip goals or from existing reservations' vicinity) and compute windows independently of point availability.
3. In the UI, clearly label alerts as "Booking Window" alerts vs "Point Deadline" alerts. These are different systems that happen to both involve dates and contracts.
4. Test edge case: a check-in date of January 15 has its 11-month window open on February 15 of the **previous year**. Make sure the year arithmetic is correct.

**Detection:**
- Alert dates that don't match the DVC website's booking window calculator
- Alerts referencing use year months when they should reference check-in months
- Any import of `use_year.py` functions in the booking window code

**Phase to address:** Booking window alerts phase. This is a new calculation, not an extension of the existing use year engine.

---

### Pitfall 5: Borrowing Policy Toggle Not Propagating to All Calculation Paths

**What goes wrong:**
The v1.1 plan includes a configurable borrowing policy (100% vs 50%). The current codebase has borrowing validation only in one place -- the `create_point_balance` API endpoint, where it logs a warning if borrowed points exceed annual points. But the what-if scenario engine, the trip explorer, the availability calculator, and the booking impact preview ALL need to respect the borrowing limit when computing "how many points could I borrow?" If the policy toggle only gates the API validation but doesn't propagate to the calculation engine, the what-if scenario will show "you can borrow 200 points" while the API rejects the actual entry because the policy is set to 50% (100 points max).

**Why it happens:**
The borrowing limit is currently not enforced in the engine layer at all. The engine functions take `point_balances` as input and don't know about borrowing limits. The API layer does the validation. When adding the policy toggle, the natural place is the API layer (where validation already exists), but the scenario engine and impact preview need the same constraint.

**Consequences:**
- What-if scenarios show impossible states (borrowing more than allowed)
- Trip explorer shows options requiring more borrowing than the policy permits
- User believes they can afford a trip, tries to set up the borrowing in reality, and gets rejected by Disney
- Different parts of the app give contradictory answers about available points

**Prevention:**
1. Add the borrowing limit as a parameter to the engine functions, not just the API validation:
   ```python
   def get_max_borrowable(annual_points: int, borrow_pct: float = 1.0) -> int:
       """Maximum points that can be borrowed from next use year."""
       return int(annual_points * borrow_pct)
   ```
2. Store the borrowing policy as a system-level setting (in the database or a config endpoint), not a frontend-only toggle.
3. The what-if scenario engine must accept the borrowing policy as input and cap borrowable amounts accordingly.
4. Write a cross-cutting test: set policy to 50%, create a scenario that requires borrowing 75% of annual points, verify the scenario reports insufficient points.

**Detection:**
- What-if scenario allows borrowing more points than the policy setting permits
- Trip explorer and scenario playground give different answers for the same inputs
- No test that sets borrowing policy to 50% and verifies enforcement in calculations

**Phase to address:** Must be designed in the what-if scenario phase but the engine function must be created before the scenario phase starts. The borrowing policy setting should be a prerequisite of both the scenario playground and the configurable policy feature.

---

## Moderate Pitfalls

---

### Pitfall 6: Heatmap Rendering Performance with Full Resort Grid

**What goes wrong:**
A seasonal cost heatmap for one resort has: ~11 room types x 365 days = ~4,015 cells. If the user wants to compare across resorts (the whole point of a heatmap), even 3 resorts means ~12,000 cells. Rendering this as individual React components (one `<div>` per cell) causes the initial render to take 1-2 seconds and scrolling to lag. SVG rendering is worse for grids this size. The heatmap feature feels broken even though the data is correct.

**Why it happens:**
React re-renders the entire grid when any state changes (hovering over a cell, changing the color scale, filtering rooms). Each cell is a separate React component with its own props, event handlers, and styling. For a 4,000+ cell grid, React's diffing algorithm becomes the bottleneck.

**Prevention:**
1. Use CSS Grid with a flat data structure, not nested React components. Each cell is a plain `<div>` with `background-color` set via inline style (not a Tailwind class -- dynamic colors can't use Tailwind purging).
2. For the DVC use case, ~4,000 cells per resort is manageable with CSS Grid. Do NOT reach for Canvas or WebGL for this dataset size. Canvas makes tooltips and click handlers much harder to implement.
3. Use `React.memo` on the grid container and derive cell colors from a memoized computation (point cost -> color). Avoid recomputing colors on every hover.
4. Lazy-load resort tabs: only compute and render the heatmap for the currently visible resort, not all resorts simultaneously.
5. For the color scale: use a sequential color palette (light to dark) with 5-7 discrete buckets, not a continuous gradient. This makes the heatmap readable and reduces the unique color count.

**Detection:**
- Lighthouse performance score drops below 80 on the heatmap page
- Visible jank when hovering over cells or scrolling the grid
- React DevTools Profiler shows >16ms render times for the grid component

**Phase to address:** Seasonal cost heatmap phase. Build a performance benchmark with a full resort's data (11 rooms x 365 days) before choosing the rendering approach.

---

### Pitfall 7: Heatmap Date Gaps at Season Boundaries Causing Blank Cells

**What goes wrong:**
The existing point chart JSON data uses explicit date ranges for each season (e.g., Adventure: Jan 1-31 and Sep 1-30; Choice: Feb 1-14). If there's a gap between season ranges (even one day), the heatmap will show blank/zero-cost cells for those dates. The existing `get_season_for_date()` function returns `None` for dates not covered by any season range. A heatmap with random blank cells in the middle of the year looks like a bug, not missing data.

**Why it happens:**
Point chart JSON files are manually transcribed from the DVC website. It's easy to make a transcription error that leaves a gap. For example, if Adventure season ends Jan 31 and Choice starts Feb 1, that's gap-free. But if the transcription says Adventure ends Jan 30, February 1 is covered but January 31 is not. The existing `calculate_stay_cost()` function returns `None` when it hits a gap, which the Trip Explorer handles (skips the option), but the heatmap needs to display every day of the year.

**Consequences:**
- Random blank cells in the heatmap, destroying trust in the data
- `calculate_stay_cost` returns `None` for stays that span a gap date, which the heatmap might show as "0 points" instead of "no data"
- Users can't figure out why certain dates have no data

**Prevention:**
1. Add a validation function that checks point chart JSON files for date coverage:
   ```python
   def validate_chart_coverage(chart: dict, year: int) -> list[date]:
       """Return list of dates NOT covered by any season."""
       covered = set()
       for season in chart["seasons"]:
           for start_str, end_str in season["date_ranges"]:
               current = date.fromisoformat(start_str)
               end = date.fromisoformat(end_str)
               while current <= end:
                   covered.add(current)
                   current += timedelta(days=1)
       all_dates = set()
       current = date(year, 1, 1)
       end = date(year, 12, 31)
       while current <= end:
           all_dates.add(current)
           current += timedelta(days=1)
       return sorted(all_dates - covered)
   ```
2. Run this validation as a test case for every point chart JSON file. This test already exists implicitly (the test suite would catch missing data) but should be explicit.
3. In the heatmap UI, display uncovered dates with a distinct "no data" indicator (hatched pattern or gray), not as zero-cost cells.
4. Add the validation to the point chart upload/edit flow if one is built.

**Detection:**
- Heatmap has blank or zero-valued cells in the middle of a month
- `get_season_for_date()` returns `None` for dates that should have data
- Inconsistent cell count across months in the heatmap grid

**Phase to address:** Seasonal cost heatmap phase. Should be a pre-check before rendering.

---

### Pitfall 8: FastAPI StaticFiles Mount Ordering Breaks API Routes

**What goes wrong:**
To serve the React SPA from the same container as the FastAPI backend, the built frontend is served via `StaticFiles` mount. If the mount is registered before the API routers, or if it's mounted at `/` without proper configuration, it intercepts API requests. All `/api/*` requests return the React `index.html` instead of JSON responses. The app appears to load (the React shell renders) but all data is missing because API calls are getting HTML responses.

**Why it happens:**
FastAPI processes routes in registration order. A `StaticFiles` mount at `/` with `html=True` acts as a catch-all. If registered before `include_router(api_router)`, it catches `/api/health` and serves `index.html`. The current code registers routers before any static mount (good), but when adding the SPA mount, the order matters:

```python
# WRONG: SPA mount catches everything including /api/*
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="spa")
app.include_router(contracts_router)  # Never reached

# CORRECT: API routes first, SPA mount last
app.include_router(contracts_router)
app.include_router(points_router)
# ... all API routers ...
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="spa")
```

**Consequences:**
- API calls return 200 OK but with HTML content instead of JSON
- Frontend shows loading spinners forever or cryptic JSON parse errors
- Health check endpoint returns HTML, breaking monitoring

**Prevention:**
1. Register all API routers BEFORE the StaticFiles mount. The current `main.py` already includes all routers -- the SPA mount must be added after all of them.
2. Verify with a curl test in the Docker build process:
   ```bash
   curl -s http://localhost:8000/api/health | jq .status
   # Must return "ok", not HTML
   ```
3. Consider using a sub-application or path prefix to isolate the SPA mount:
   ```python
   # Even safer: mount SPA on a specific path or use a catch-all route
   @app.get("/{full_path:path}")
   async def serve_spa(full_path: str):
       # Only if no API route matched
       return FileResponse("frontend/dist/index.html")
   ```
4. The `CORSMiddleware` currently allows only `http://localhost:5173` (Vite dev server). In Docker, the frontend is served from the same origin -- CORS is not needed. But if someone runs the dev frontend against the Docker backend, CORS will block. Update the allowed origins to include the Docker host or use environment-variable-driven CORS configuration.

**Detection:**
- `curl http://localhost:8000/api/health` returns HTML (look for `<!DOCTYPE` in the response)
- Frontend console shows `SyntaxError: Unexpected token '<'` (HTML in JSON response)
- All API hooks (`useContracts`, `useAvailability`, etc.) show error states

**Phase to address:** Docker packaging phase. Must be tested before shipping the Docker image.

---

### Pitfall 9: What-If Scenario State Going Stale When Real Data Changes

**What goes wrong:**
The user builds a what-if scenario: "If I book Polynesian in July and Riviera in December, here's what my points look like." Then they go to the Reservations page and add a real booking. When they return to the scenario playground, the scenario still shows the old point balances because the hypothetical was computed against the previous state. The scenario now shows they have enough points for both hypothetical trips, but in reality, their real booking has consumed points that the scenario doesn't know about.

**Why it happens:**
The what-if scenario is computed at a point in time using current data. If the scenario state is cached (in Zustand, in React Query, or in local state), it doesn't automatically invalidate when the underlying real data changes. React Query has a `staleTime` of 5 minutes in the current config, meaning cached availability data can be up to 5 minutes old.

**Consequences:**
- Scenario shows more available points than actually exist
- User makes real booking decisions based on stale scenario results
- Confusing discrepancy between dashboard (shows current state) and scenario (shows old state)

**Prevention:**
1. The scenario playground should re-fetch real data (point balances, reservations) every time the user returns to it or clicks "recalculate". Do not cache scenario results across page navigations.
2. Invalidate the scenario React Query cache whenever a real mutation occurs (reservation created/updated/deleted, point balance changed):
   ```typescript
   // After a successful reservation mutation
   queryClient.invalidateQueries({ queryKey: ["availability"] });
   queryClient.invalidateQueries({ queryKey: ["scenario"] });
   ```
3. Display a "last calculated" timestamp on the scenario results.
4. If implementing the scenario as a client-side calculation (to avoid API calls), pass the latest React Query data into the calculation, not a snapshot from when the user first opened the page.

**Detection:**
- Scenario results don't change after adding a real reservation on another page
- Available points in scenario don't match the availability page for the same date
- No `invalidateQueries` calls in mutation `onSuccess` handlers

**Phase to address:** What-if scenario playground phase. Design the cache invalidation strategy before building the UI.

---

### Pitfall 10: Docker Image Serving Hardcoded `localhost` CORS and API URLs

**What goes wrong:**
The current `main.py` has `allow_origins=["http://localhost:5173"]` for CORS. The current `frontend/vite.config.ts` proxies `/api` to `http://localhost:8000`. In a Docker deployment, the frontend is served by FastAPI (same origin), so the proxy config is irrelevant -- but the CORS setting may block requests if someone accesses the app from a different hostname (e.g., `http://192.168.1.50:8000` on a home network, or `http://my-nas:8000`). The API returns CORS errors and the app appears broken.

**Why it happens:**
CORS is origin-based. The browser sends the actual URL it's using, not `localhost`. If the user accesses the Docker container from any hostname other than what's in `allow_origins`, the browser blocks the response. In a single-container setup where FastAPI serves both the API and the SPA, CORS is technically unnecessary (same origin), but the middleware is still active and evaluating.

**Consequences:**
- App works at `http://localhost:8000` but not at `http://192.168.1.50:8000`
- No error in the terminal logs -- CORS failures are client-side only (visible in browser console)
- User thinks the Docker image is broken when it's just a CORS misconfiguration

**Prevention:**
1. When the frontend is served from the same origin as the API (Docker single-container), CORS middleware is unnecessary. Make it environment-driven:
   ```python
   CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
   if CORS_ORIGINS and CORS_ORIGINS[0]:  # Only add CORS if origins are configured
       app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, ...)
   ```
2. For development (frontend on port 5173, backend on port 8000), set `CORS_ORIGINS=http://localhost:5173`.
3. For Docker production, either omit CORS entirely (same origin) or set `CORS_ORIGINS=*` if the app needs to be accessed from multiple hostnames.
4. Document the `CORS_ORIGINS` environment variable in the Docker README.

**Detection:**
- Browser console shows "Access-Control-Allow-Origin" errors
- App loads the React shell but all API calls fail
- Works from `localhost` but not from the machine's IP address

**Phase to address:** Docker packaging phase. Must be addressed when configuring the production container.

---

## Minor Pitfalls

---

### Pitfall 11: Booking Impact Preview Double-Counting Existing Reservations

**What goes wrong:**
The booking impact preview should show "if you book this trip, your available points go from X to Y." It does this by running the availability calculator with the hypothetical reservation added. But if the user is viewing a Trip Explorer result for dates that overlap with an existing reservation (e.g., extending a trip), the impact preview might double-count the overlapping nights.

**Prevention:**
1. The impact preview should take the current availability (with existing reservations already accounted for) as the baseline, then subtract only the new trip's point cost.
2. Use the same engine path: `current_availability - new_trip_cost = projected_availability`. Do not re-run the full availability with both old and new reservations unless the engine properly deduplicates.
3. Test with overlapping date scenarios explicitly.

---

### Pitfall 12: Alembic Migrations Path Breaking in Docker

**What goes wrong:**
The current `alembic.ini` has `script_location = backend/db/migrations` and `sqlalchemy.url = sqlite+aiosqlite:///./dvc.db`. Both are relative paths. In Docker, the working directory may differ, causing Alembic to not find the migrations folder or to create the database in the wrong location.

**Prevention:**
1. In the Docker entrypoint or startup command, ensure WORKDIR is set to `/app` (the project root) before running Alembic.
2. Override `sqlalchemy.url` via environment variable or `alembic.ini` configuration to use the volume-mounted database path.
3. The current `main.py` creates tables on startup via `Base.metadata.create_all`. This works for development but should be supplemented with Alembic migrations for schema changes. In Docker, decide on ONE approach and document it.
4. Test that `alembic upgrade head` works in the container before the app starts.

---

### Pitfall 13: Heatmap Missing Weekday/Weekend Cost Distinction

**What goes wrong:**
Each point chart cell has both `weekday` and `weekend` costs (Friday and Saturday are weekend in DVC terms). The heatmap needs to show the correct cost for each specific date. If the heatmap naively uses `weekday` cost for all cells, weekend costs will be understated. If it averages them, neither cost is correct.

**Prevention:**
1. The heatmap should call `get_point_cost(chart, room_key, specific_date)` for each cell, which already handles the weekday/weekend distinction based on the day of week.
2. Visually distinguish weekend columns (Friday/Saturday) in the grid with a subtle background or border, so users can see why certain days cost more.
3. Consider a weekly aggregation view that shows average or max cost per week, which smooths out the weekday/weekend difference while still being useful for comparison.

---

### Pitfall 14: Docker Multi-Stage Build Producing Oversized Images

**What goes wrong:**
A naive Dockerfile that installs Node.js, builds the frontend, installs Python dependencies, and runs the app can produce a 2GB+ image. Users sharing via Docker Hub or GitHub Container Registry will have slow pulls and waste storage.

**Prevention:**
1. Use a multi-stage build: Stage 1 (Node) builds the frontend, Stage 2 (Python) copies only the built static files and installs Python deps:
   ```dockerfile
   # Stage 1: Build frontend
   FROM node:22-alpine AS frontend-build
   WORKDIR /app/frontend
   COPY frontend/package*.json ./
   RUN npm ci
   COPY frontend/ ./
   RUN npm run build

   # Stage 2: Python app
   FROM python:3.12-slim
   WORKDIR /app
   COPY backend/requirements.txt ./
   RUN pip install --no-cache-dir -r requirements.txt
   COPY backend/ ./backend/
   COPY data/ ./data/
   COPY --from=frontend-build /app/frontend/dist ./frontend/dist
   COPY alembic.ini ./
   ```
2. Use `python:3.12-slim` not `python:3.12` (saves ~700MB).
3. Use `--no-cache-dir` with pip to avoid caching wheels in the image.
4. Do NOT copy `node_modules`, `.venv`, `__pycache__`, or `.git` into the image. Use a `.dockerignore` file.

---

## DVC Domain-Specific Edge Cases

These are domain logic traps specific to how DVC rules interact with the new features.

---

### Edge Case 1: Borrowing Points Affects NEXT Year's Available Points

**What goes wrong:**
When the what-if scenario includes borrowing points from next year, the borrowed points must be subtracted from next year's annual allocation. If the scenario only shows the impact on the CURRENT year (available points increase) without showing the impact on NEXT year (available points decrease), the user gets an incomplete picture. They borrow 150 points for this year's trip, not realizing that leaves only 50 points for all of next year.

**Impact:** User makes a borrowing decision based on incomplete information.

**Prevention:** The scenario result must show a multi-year impact: "Current year: +150 points borrowed, Next year: -150 points committed." The existing `build_use_year_timeline` function builds timelines for current and next year -- extend this to show projected balances for both years in the scenario.

---

### Edge Case 2: Banked Points Cannot Be Re-Banked -- Scenario Must Track Point Origin

**What goes wrong:**
If a user banked 100 points from 2025 into 2026, those banked points expire at the end of the 2026 use year -- they CANNOT be banked again into 2027. The what-if scenario must respect this constraint. If the scenario shows "you'll have 100 unused points at the end of 2026" without distinguishing that they're banked points that will expire, the user might assume they can bank them into 2027.

**Impact:** User loses points they thought they could save.

**Prevention:** The scenario output must label each point bucket with its origin year and bankability status. The existing `PointAllocationType` enum already distinguishes `current`, `banked`, `borrowed`, and `holding`. The scenario engine must preserve these labels and enforce the "banked points cannot be re-banked" rule.

---

### Edge Case 3: Reservations Spanning Use Year Boundaries

**What goes wrong:**
DVC rules require that reservations spanning a use year boundary (e.g., check-in Nov 28, check-out Dec 3 for a December use year) split points across two use years. The current `get_contract_availability` function assigns reservations to a use year based on check-in date only. This is correct for most cases but may mis-assign a cross-boundary reservation.

**Impact:** The booking impact preview shows points deducted from only one use year when they should be split across two.

**Prevention:** For v1.1, document this limitation. The correct handling requires splitting a reservation into two point deductions at the use year boundary, which is complex. Since this is a personal tool with manual entry, the user can enter the split as two separate reservations. For v2, consider adding automatic split detection.

---

### Edge Case 4: 11-Month Window Varies by Home Resort, Not by Contract Count

**What goes wrong:**
If a user owns contracts at Polynesian (resale) and Riviera (resale), they get the 11-month home resort advantage at their respective home resorts only. The booking window alert must be per-contract-per-resort, not per-user. A user with a Polynesian contract gets the 11-month window at Polynesian but only the 7-month window at Riviera (and vice versa for the Riviera contract, but the Riviera resale contract can ONLY book at Riviera anyway).

**Impact:** Alert says "11-month window opens for Riviera" but the user's resale contract can't book there in the first place (unless it's the Riviera contract).

**Prevention:** Booking window alerts must cross-reference the contract's eligible resorts (from `get_eligible_resorts()`) with the window type. 11-month alerts should only fire for the home resort of each contract. 7-month alerts should only fire for resorts the contract can actually book.

---

### Edge Case 5: Cost Heatmap Data Only Exists for Loaded Resorts

**What goes wrong:**
Currently only 2 resorts have point chart data (Polynesian and Riviera for 2026). The heatmap UI might offer a dropdown of all 16 DVC resorts (from `resorts.json`) but only 2 have actual data. Selecting a resort without data results in a blank heatmap, which looks like a bug.

**Impact:** User thinks the heatmap is broken for 14 out of 16 resorts.

**Prevention:** The resort dropdown should only include resorts that have chart data. Use the existing `get_available_charts()` function to filter the resort list. Show a clear "No point chart data loaded for this resort" message rather than an empty grid. Provide a link or explanation for how to add chart data for additional resorts.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Docker packaging | SQLite data loss on rebuild (Pitfall 1) | Volume mount the database directory; test with `docker compose down && up` |
| Docker packaging | StaticFiles mount breaking API (Pitfall 8) | Mount SPA after all API routers; curl-test the health endpoint |
| Docker packaging | CORS blocking non-localhost access (Pitfall 10) | Environment-driven CORS config; test from a different hostname |
| Docker packaging | lru_cache path resolution (Pitfall 3) | Verify data directory in container; add startup file check |
| Docker packaging | Alembic migrations path (Pitfall 12) | Set WORKDIR correctly; test migration in container |
| Docker packaging | Oversized image (Pitfall 14) | Multi-stage build; .dockerignore; python:slim base |
| Booking impact preview | Mutating real data (Pitfall 2) | Pure function approach; no DB writes in preview path |
| Booking impact preview | Double-counting overlapping reservations (Pitfall 11) | Use current availability as baseline, subtract only new cost |
| What-if scenario | Stale state after real mutations (Pitfall 9) | Invalidate scenario cache on mutations; show "last calculated" |
| What-if scenario | Borrowing policy not enforced (Pitfall 5) | Add borrowing limit to engine functions, not just API validation |
| What-if scenario | Not showing next year impact of borrowing (Edge Case 1) | Multi-year impact display in scenario results |
| What-if scenario | Ignoring banked point re-banking restriction (Edge Case 2) | Preserve allocation type labels; enforce "no re-bank" rule |
| Booking window alerts | Confusing booking windows with use year dates (Pitfall 4) | Independent calculation function; no use year imports |
| Booking window alerts | Alerting for ineligible resorts (Edge Case 4) | Cross-reference eligibility before generating alerts |
| Seasonal cost heatmap | Performance with large grids (Pitfall 6) | CSS Grid, not nested components; lazy-load per resort tab |
| Seasonal cost heatmap | Date gaps in season data (Pitfall 7) | Add chart validation; show "no data" indicator for gaps |
| Seasonal cost heatmap | Missing weekday/weekend distinction (Pitfall 13) | Use per-date cost function; visually mark weekend columns |
| Seasonal cost heatmap | Empty heatmap for resorts without data (Edge Case 5) | Filter dropdown to resorts with chart data |
| Configurable borrowing | Toggle not propagating to all calculation paths (Pitfall 5) | Engine-level parameter; cross-cutting test at 50% setting |

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| SQLite data loss in Docker (Pitfall 1) | HIGH if no backup, LOW if caught early | Add volume mount to docker-compose.yml; user must re-enter data if lost. Add backup instructions to README. |
| Scenario mutates real data (Pitfall 2) | MEDIUM | Remove spurious DB entries; refactor to pure-function approach. Existing tests should catch regressions. |
| lru_cache path issues (Pitfall 3) | LOW | Fix Dockerfile COPY structure; rebuild image. No data loss. |
| Wrong booking window dates (Pitfall 4) | LOW | Fix calculation function; no data model changes needed. |
| Borrowing policy not enforced (Pitfall 5) | MEDIUM | Add engine parameter and propagate to all callers; requires touching 3-4 files. |
| Heatmap performance (Pitfall 6) | MEDIUM | Refactor rendering approach; may need to replace component library choice. |
| Season date gaps (Pitfall 7) | LOW | Fix JSON data; add validation test. No code changes needed. |
| StaticFiles breaking API (Pitfall 8) | LOW | Reorder mounts in main.py; rebuild Docker image. |
| Stale scenario state (Pitfall 9) | LOW | Add cache invalidation to mutation handlers. |
| CORS blocking (Pitfall 10) | LOW | Update environment variable; no rebuild needed if env-driven. |

---

## Sources

- [SQLite WAL Mode Documentation](https://sqlite.org/wal.html) -- WAL mode filesystem requirements and corruption risks
- [How to Corrupt an SQLite Database File](https://www.sqlite.org/howtocorrupt.html) -- Official SQLite documentation on corruption scenarios
- [Docker Docs: Persist the DB](https://docs.docker.com/get-started/workshop/05_persisting_data/) -- Named volumes vs bind mounts
- [SQLite in Docker: When and How (OneUptime)](https://github.com/oneuptime/blog/tree/master/posts/2026-02-08-how-to-run-sqlite-in-docker-when-and-how) -- SQLite Docker best practices
- [Sharing SQLite Across Containers (Medium)](https://rbranson.medium.com/sharing-sqlite-databases-across-containers-is-surprisingly-brilliant-bacb8d753054) -- Volume mount strategies
- [Docker Bind Mounts vs Named Volumes (OneUptime)](https://oneuptime.com/blog/post/2026-01-16-docker-bind-mounts-vs-volumes/view) -- macOS vs Linux performance differences
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/) -- Official FastAPI Docker guide
- [FastAPI + React Single Container (Medium)](https://dakdeniz.medium.com/fastapi-react-dockerize-in-single-container-e546e80b4e4d) -- Multi-stage build pattern
- [Serving React Frontend with FastAPI (Muraya)](https://davidmuraya.com/blog/serving-a-react-frontend-application-with-fastapi/) -- SPA routing with StaticFiles
- [FastAPI StaticFiles + React Router (GitHub Gist)](https://gist.github.com/ultrafunkamsterdam/b1655b3f04893447c3802453e05ecb5e) -- Catch-all route pattern
- [DVC Banking and Borrowing (DVC Field Guide)](https://dvcfieldguide.com/blog/how-to-bank-and-borrow-dvc-points) -- Banking deadlines, borrowing limits, point lifecycle rules
- [DVC Banking FAQ (Official)](https://disneyvacationclub.disney.go.com/faq/bank-points/) -- Banking restrictions and finality
- [DVC Bank/Borrow Overview (Official)](https://disneyvacationclub.disney.go.com/points/bank-borrow/) -- Current borrowing policy
- [DVC Borrowing Restriction Removed (DVC Fan)](https://dvcfan.com/news/disney-vacation-club-removes-member-point-borrowing-restriction/) -- July 2022 return to 100% borrowing
- [DVC Borrowing Restriction History (Disney Tourist Blog)](https://www.disneytouristblog.com/dvc-point-policy-updates/) -- April 2020 50% restriction timeline
- [DVC Use Year Guide (DVCinfo)](https://dvcinfo.com/dvc-information/buying-dvc/understanding-use-year/) -- Use year boundary reservation splitting
- [DVC Point Charts 2026 (DVC Fan)](https://dvcfan.com/general-dvc/2026-disney-vacation-club-points-charts/) -- Season structure and date ranges
- [React Heatmap Performance (Apache ECharts)](https://apache.github.io/echarts-handbook/en/best-practices/canvas-vs-svg/) -- Canvas vs SVG rendering for large grids
- [React Heatmap Libraries (LogRocket)](https://blog.logrocket.com/best-heatmap-libraries-react/) -- Library comparison and performance
- [React Stale State (Medium)](https://medium.com/@shanakaprince/understanding-stale-state-in-react-and-how-to-avoid-it-a74cc4655c43) -- Stale closure and state patterns
- [React Query as State Manager (TkDodo)](https://tkdodo.eu/blog/react-query-as-a-state-manager) -- Cache invalidation patterns
- [Refactoring Pure Function Composition (Ploeh)](https://blog.ploeh.dk/2023/05/01/refactoring-pure-function-composition-without-breaking-existing-tests/) -- Extending pure function engines safely

---
*Pitfalls research for: DVC Dashboard v1.1 -- Docker packaging, booking impact preview, what-if scenarios, booking window alerts, seasonal cost heatmap*
*Researched: 2026-02-10*
