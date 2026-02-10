# Feature Landscape: v1.1 Planning Tools & Docker Packaging

**Domain:** DVC (Disney Vacation Club) points management -- planning tools and Docker packaging
**Researched:** 2026-02-10
**Overall Confidence:** HIGH (features are incremental additions to proven v1.0 engines; DVC domain rules well-documented across multiple sources)

**Scope:** NEW features only. v1.0 core (contracts, balances, reservations, availability engine, Trip Explorer, point charts with season calendar/stay cost calculator, dashboard with urgent alerts) is already shipped and working.

---

## Feature Area 1: Booking Impact Preview

**Purpose:** Before confirming a reservation, show the user exactly how this booking changes their point balances, banking deadlines, and remaining trip-booking capacity.

### Table Stakes

| Feature | Why Expected | Complexity | Existing Code Dependency |
|---------|--------------|------------|--------------------------|
| Before/after point balance | Core value -- "what will I have left?" | Low | `get_contract_availability()` in `availability.py` |
| Per-contract breakdown | Multi-contract owners need to know which contract is debited | Low | Existing contract + reservation models |
| Points remaining after booking | Answers "can I still book something else this year?" | Low | Same availability engine, subtract proposed cost |
| Season label for the stay dates | Context for whether the cost is high or low for these dates | Low | `get_season_for_date()` in `point_charts.py` |
| Nightly point breakdown | Already computed by `calculate_stay_cost()`; users expect it in the preview | Low | `calculate_stay_cost()` returns `nightly_breakdown` |
| Banking deadline awareness | If this booking uses points that could still be banked, warn the user | Med | `get_banking_deadline()` + `allocation_type` tracking on `PointBalance` model |
| Eligibility validation | Confirm contract can actually book at this resort before showing preview | Low | `get_eligible_resorts()` in `eligibility.py` |

### Differentiators

| Feature | Value Proposition | Complexity | Existing Code Dependency |
|---------|-------------------|------------|--------------------------|
| "Points at risk" callout | Highlight if unbanked points would expire unused after this booking | Med | Use year timeline + availability engine |
| Alternative room suggestions | "Save X points by choosing room Y instead" shown in preview | Med | `find_affordable_options()` already computes all alternatives for same dates |
| Undo preview (cancel impact) | For existing reservations, show what cancelling would restore | Low | Inverse of the same availability diff |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Auto-booking from preview | No DVC API exists; user books on Disney's site | Show preview, user confirms manually, then saves reservation locally |
| Real-time DVC room availability | No public API for Disney's room inventory; this app tracks YOUR points | Label clearly: "your point budget impact" not "room availability" |
| Optimized contract selection | Which contract to debit is a personal decision (banking/borrowing preferences) | Show impact per eligible contract; let user choose |

### Implementation Notes

The booking impact preview is a **dry-run of the existing availability engine**. The `get_contract_availability()` function is already pure -- it takes `contract_id`, `use_year_month`, `annual_points`, `point_balances`, and `reservations` as arguments with no DB access. The preview workflow:

1. Fetch current state via existing `/api/availability?date=<check_in>`
2. Compute proposed cost via existing `calculate_stay_cost(resort, room_key, check_in, check_out)`
3. Add the proposed reservation to the committed list and recompute availability
4. Diff the two results to produce before/after

**Recommended approach:** A dedicated `POST /api/reservations/preview` endpoint that accepts a proposed reservation body and returns the impact. This centralizes warning logic (banking risk, expiration risk, eligibility) server-side and keeps the frontend thin. The endpoint wraps existing engine functions -- no new computation logic needed.

**Backend effort:** ~1 new endpoint wrapping existing functions. **Frontend effort:** New preview panel/dialog in the reservation creation flow (extends existing `ReservationFormDialog.tsx`). Also integrable into `TripExplorerResults.tsx` as an expandable "impact" row for each option.

---

## Feature Area 2: What-If Scenario Playground

**Purpose:** Let the user explore hypothetical futures. "If I book Trip A, can I still afford Trip B?" / "What if I bank these points?"

### Table Stakes

| Feature | Why Expected | Complexity | Existing Code Dependency |
|---------|--------------|------------|--------------------------|
| Add hypothetical reservation(s) | Core use case -- "if I book this, what's left?" | Med | Availability engine + temporary frontend state |
| See cumulative impact of multiple hypotheticals | "Trip A + Trip B together" | Med | Stack proposed reservations in a single availability calculation |
| Clear/reset scenarios | Start fresh without modifying real data | Low | Frontend state management (Zustand already in `package.json`) |
| Compare scenario vs current reality | Side-by-side or diff view: "now" vs "with these trips" | Med | Two parallel availability computations |

### Differentiators

| Feature | Value Proposition | Complexity | Existing Code Dependency |
|---------|-------------------|------------|--------------------------|
| Named/saved scenarios | "Spring Break Plan" vs "Summer Plan" -- save and compare | Med | `localStorage` (simplest) or new DB table |
| Banking simulation | "What if I bank 50 points from current UY?" | High | Must modify `allocation_type` balances in-memory; complex UY rules (8-month deadline, no re-banking banked points) |
| Add hypothetical contract | "If I buy 100 more points at Riviera, what could I book?" | Med | Add temporary contract to data passed to availability engine |
| Timeline visualization | Point balance over 12-18 months with scenario overlaid | High | New charting component; underlying data available from availability engine run at multiple dates |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Scenario persistence to DB by default | Scenarios are exploratory; saving as "real" data causes confusion | Keep in Zustand store; disappears on reload. Offer explicit "save as draft" only if demanded. |
| Auto-optimization ("best plan") | Too many subjective factors (preferred resorts, travel dates, family size) | Show the numbers; let the user decide |
| Multi-year scenario modeling | Complexity explosion with UY banking/borrowing/expiration across 2+ years | Limit to current + next use year; flag multi-year as future enhancement |

### Implementation Notes

**Key insight from codebase review:** Both `get_contract_availability()` and `find_affordable_options()` are already pure functions that accept contracts, balances, and reservations as arguments. They have zero DB access. This means the what-if engine is architecturally the same code with different input data. No new computation engine is needed.

The playground workflow:
1. Fetch real data from existing endpoints (contracts, balances, reservations)
2. User modifies data in Zustand store (add/remove hypothetical reservations, adjust balances)
3. Send modified data to `POST /api/scenarios/evaluate` (wraps existing engine functions)
4. Display results alongside baseline

**Frontend complexity is the bottleneck**, not backend. The UI needs:
- A scenario workspace page that clones current state into editable Zustand store
- Ability to add/remove hypothetical reservations (reuse `TripExplorerForm` component pattern)
- Running total display showing remaining points with all hypotheticals applied
- Diff view: baseline vs. scenario side-by-side

**Build sequence:** Build booking impact preview first (single hypothetical). The scenario playground extends this to multiple hypotheticals with a dedicated workspace UI.

---

## Feature Area 3: Booking Window Alerts

**Purpose:** Show the user when their 11-month (home resort) and 7-month (non-home) booking windows open for desired travel dates.

### DVC Booking Window Rules (HIGH confidence -- verified across official DVC FAQ, DVC Shop, DVC Field Guide, planDisney)

| Rule | Detail |
|------|--------|
| **11-month window** | Opens exactly 11 months before check-in, same day of month. Home resort only. |
| **7-month window** | Opens exactly 7 months before check-in, same day of month. Any eligible resort. |
| **Opening time** | 8:00 AM Eastern, online. 9:00 AM Eastern by phone. |
| **Night limit** | Max 7 consecutive nights at window opening. Additional nights via modification, one at a time. |
| **End-of-month edge case** | When the booking month has fewer days (e.g., check-in Jan 31 maps to Feb 28/29), multiple check-in dates compress. `dateutil.relativedelta` (already in deps) handles this correctly. |
| **Resale restriction interaction** | Restricted resort resale (Riviera, DLH, Cabins FW): home resort only, so 7-month is irrelevant. Original 14 resale: 11-month at home, 7-month at other original 13. Direct: 11-month at home, 7-month everywhere. |

### Table Stakes

| Feature | Why Expected | Complexity | Existing Code Dependency |
|---------|--------------|------------|--------------------------|
| Show booking window date for a trip | "When can I book this?" | Low | `relativedelta(months=-11)` and `relativedelta(months=-7)` from check_in. `python-dateutil` already in backend requirements. |
| Distinguish home vs non-home windows | Different windows depending on contract + target resort | Low | `get_eligible_resorts()` + `contract.home_resort` field |
| Days-until-window countdown | "Your booking window opens in 12 days" | Low | Simple date arithmetic |
| Dashboard integration | Show upcoming booking windows in existing alert area | Med | Extend `UrgentAlerts.tsx` (already shows 60-day banking, 90-day expiration alerts) |
| Color-coded urgency | Red = opens tomorrow, amber = opens this week, green = opens this month | Low | Frontend Tailwind styling only |

### Differentiators

| Feature | Value Proposition | Complexity | Existing Code Dependency |
|---------|-------------------|------------|--------------------------|
| Booking window on Trip Explorer results | From Trip Explorer, show "window opens [date]" for each affordable option | Low | Add window date to `TripExplorerOption` response |
| Window status on reservation form | When creating a reservation, show whether the booking window is already open | Low | Same date calculation in the preview dialog |
| Waitlist timing guidance | For popular resorts (Poly, Beach Club), note 11-month is critical | Low | Static domain knowledge in UI tooltip |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Email/SMS notifications | No auth, no email infrastructure, personal local tool | In-app dashboard alerts; optionally browser Notification API |
| DVC booking automation | Violates Disney ToS; risks account suspension | Show exact date/time; user books on Disney's site |
| Calendar export (iCal) | Over-engineering for v1.1 | Defer to v2; dashboard display covers 95% of the use case |

### Implementation Notes

**Data source for "desired trips":** Alerts need to know what trips the user wants to book. Two options:

1. **Add `planned` status to existing reservation model** -- Join existing `confirmed/pending/cancelled` statuses. A planned reservation has dates and resort but zero point deduction. Pro: single data model, dashboard queries already fetch reservations. Con: slightly overloads the reservation concept.

2. **Compute from Trip Explorer on-the-fly** -- When user searches dates, append booking window dates to results. No persistence. Pro: zero data model changes. Con: no persistent dashboard alerts.

**Recommendation:** Use both. Option 2 is the quick win (add window dates to Trip Explorer results, no schema change). Option 1 adds persistent dashboard alerts for trips the user is actively planning. The `planned` status on the existing `ReservationStatus` enum is a one-line schema addition.

**Backend function (trivial):**
```python
from dateutil.relativedelta import relativedelta

def get_booking_windows(check_in: date, is_home_resort: bool) -> dict:
    return {
        "home_resort_window": (check_in - relativedelta(months=11)).isoformat(),
        "non_home_window": (check_in - relativedelta(months=7)).isoformat() if not is_home_resort else None,
        "home_window_open": date.today() >= check_in - relativedelta(months=11),
        "non_home_window_open": date.today() >= check_in - relativedelta(months=7) if not is_home_resort else None,
    }
```

---

## Feature Area 4: Seasonal Cost Heatmap

**Purpose:** Visualize a full year's point costs as a color-coded calendar so users can spot the cheapest and most expensive dates at a glance.

### Season Structure in Existing Data (HIGH confidence -- verified from `polynesian_2026.json` in codebase)

Using Polynesian 2026 `deluxe_studio_standard` as reference:

| Season | Example Dates | Weekday pts | Weekend pts | Relative Cost |
|--------|---------------|-------------|-------------|---------------|
| Adventure | Jan, Sep | 14 | 19 | Cheapest |
| Choice | Early Feb | 16 | 22 | |
| Select | Apr-mid Jun, late Aug, Oct-late Nov | 17 | 23 | |
| Dream | Mid Feb-early Mar, mid Jun-mid Aug | 20 | 26 | |
| Magic | Mar-mid Apr, late Nov-late Dec | 22 | 29 | |
| Premier | Dec 24-31 | 28 | 36 | Most Expensive |

Six named seasons for Polynesian. Season names and boundaries vary by resort. The point chart schema supports arbitrary season counts per resort.

### Table Stakes

| Feature | Why Expected | Complexity | Existing Code Dependency |
|---------|--------------|------------|--------------------------|
| Calendar-year grid with color-coded days | Core visualization -- see 365 days at a glance | Med | Point chart data from `/api/point-charts/{resort}/{year}` |
| Resort selector dropdown | Different resorts have different season boundaries and costs | Low | Resort list from `/api/resorts` (17 resorts) |
| Room type selector dropdown | Costs vary dramatically (studio 14 pts vs bungalow 79 pts) | Low | Room keys in point chart JSON `seasons[].rooms` |
| Color legend with point values | Map color to cost: green=cheap, red=expensive | Low | Frontend styling |
| Weekday vs weekend visual distinction | Fri/Sat cost more; must be visible in the grid | Med | Chart schema already has `weekday`/`weekend` fields |
| Hover tooltip with details | "Jan 15 (Thu): Adventure, 14 pts/night" | Low | Combine season name + point cost from chart data |
| Season name labels | Show season boundaries/names in the calendar | Low | Season names already in chart data |

### Differentiators

| Feature | Value Proposition | Complexity | Existing Code Dependency |
|---------|-------------------|------------|--------------------------|
| "Affordable dates" overlay | Highlight dates where N-night stay is within point balance | Med | Availability engine + sliding-window cost sum |
| Multi-resort side-by-side | Compare 2 resorts' season patterns | Med | Same rendering, multiple data sets |
| Stay-length mode | Color = total cost for N nights starting on that date, not just per-night | Med | Sliding window sum across consecutive days |
| Year-over-year comparison | Compare 2026 vs 2027 season boundary shifts | Low | Load two chart files (only if both exist) |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Real-time room availability overlay | No DVC API; this shows COST not AVAILABILITY | Label: "Point Cost by Date" |
| All-resort aggregate heatmap | Meaningless to average costs across resorts with different seasons | One resort at a time, fast dropdown switching |
| All room types simultaneously | Visual noise; overlapping color scales | Single room type selected via dropdown |

### Implementation Notes

**Build custom component vs. library?** Recommendation: **build a custom component.** Rationale:
- Libraries (`react-calendar-heatmap`, `@uiw/react-heat-map`) use GitHub-contribution-style layout (52 columns x 7 rows), which does NOT match how DVC members read point charts (month-by-month calendars with labeled seasons)
- A 12-month grid (7 cols for days of week, ~5 rows per month) with Tailwind-styled cells is straightforward
- No new dependency for a domain-specific visualization
- Full control over DVC-specific UX: season name labels, weekday/weekend patterns, custom tooltips
- The existing codebase already uses Tailwind extensively and has shadcn/ui primitives

Using `@nivo/heatmap` (mentioned in previous version of this file) is **not recommended** because nivo adds ~150KB+ to the bundle for a single chart type, and its heatmap layout (rows x columns matrix) does not naturally render as a 12-month calendar grid.

**Color scale (6 stops mapping to season cost tiers):**
- Deep green: Adventure (cheapest)
- Medium green: Choice
- Yellow-green: Select
- Yellow: Dream
- Orange: Magic
- Red: Premier (most expensive)

Maps to existing season names. DVC members already associate these names with cost tiers.

**Backend:** Existing `/api/point-charts/{resort}/{year}` returns all data needed. A convenience endpoint `GET /api/point-charts/{resort}/{year}/daily-costs?room_key=X` returning pre-computed `{date, cost, season_name, is_weekend}` for all 365 days would simplify frontend and keep computation server-side. Uses existing `get_point_cost()` + `get_season_for_date()` in a loop.

**Frontend:** New `SeasonalHeatmap.tsx` component. Complements existing `SeasonCalendar.tsx` (which shows season date ranges as a list, not a visual calendar). New page `HeatmapPage.tsx` or embedded in existing `PointChartsPage.tsx`.

---

## Feature Area 5: Docker Packaging

**Purpose:** Package the app as a single Docker image so other DVC members can self-host with `docker compose up`.

### Table Stakes

| Feature | Why Expected | Complexity | Existing Code Dependency |
|---------|--------------|------------|--------------------------|
| Single `docker compose up` starts everything | Standard for self-hosted tools | Med | New: Dockerfile, docker-compose.yml, .dockerignore |
| SQLite data persisted via volume | Data survives container restarts/rebuilds | Low | Mount `/app/data` (contains `dvc.db` + point chart JSONs) |
| `.env.example` with documented variables | Users need to know what's configurable | Low | Template file with comments |
| Multi-stage build (small image) | Build deps not shipped to production | Med | Stage 1: node:22-slim for Vite. Stage 2: python:3.12-slim for runtime |
| Health check in compose | Container monitoring | Low | Existing `GET /api/health` returns `{"status": "ok"}` |
| Backend serves frontend static files | Single container, single port, no Nginx | Med | FastAPI `StaticFiles` mount for Vite `dist/` output |
| Auto DB migration on startup | User never runs manual migration commands | Low | Entrypoint: `alembic upgrade head && uvicorn ...` |
| Configurable CORS via env var | Currently hardcoded to `localhost:5173` in `main.py` | Low | Read `CORS_ORIGINS` from `os.environ` with sensible default |

### Differentiators

| Feature | Value Proposition | Complexity | Existing Code Dependency |
|---------|-------------------|------------|--------------------------|
| Docker quickstart in README | First thing GitHub visitors see; lowers try-it friction | Low | Documentation only |
| Pre-seeded point chart data in image | Works out of the box with 2026 charts | Low | Already in `data/point_charts/` |
| Volume for custom point charts | Users add their own resort/year JSON files | Low | Same volume mount covers both DB and charts |
| ARM64 + AMD64 multi-arch | Works on Raspberry Pi, Apple Silicon, x86 servers | Med | `docker buildx --platform` in CI |

### Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Separate frontend/backend containers | Over-engineered for single-user SQLite tool | Single container: FastAPI serves API + static frontend |
| Nginx/Caddy in compose | Unnecessary for personal tool; users add their own reverse proxy | Uvicorn serves directly; document reverse proxy setup |
| Built-in HTTPS/TLS | Users deploy behind their own proxy | Document: "put behind Caddy/Traefik for HTTPS" |
| Postgres/MySQL option | SQLite is correct for single-user tool | SQLite only; document as deliberate design choice |
| Built-in authentication | Single-user, runs on local network | Document: "do not expose to public internet without auth proxy" |

### Implementation Notes

**Dockerfile (multi-stage):**

```
Stage 1: node:22-slim (frontend build)
  - COPY frontend/package*.json, npm ci, COPY frontend/, npm run build
  - Output: /app/frontend/dist/

Stage 2: python:3.12-slim (runtime)
  - pip install --no-cache-dir -r requirements.txt
  - COPY backend/, data/, alembic.ini, migrations
  - COPY --from=stage1 /app/frontend/dist ./static/
  - CMD: alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**FastAPI static file serving (change to `main.py`):**
```python
from fastapi.staticfiles import StaticFiles
# IMPORTANT: mount AFTER all API routers so /api/* routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```
The `html=True` parameter enables SPA fallback: requests for `/trips`, `/dashboard`, etc. serve `index.html`, letting React Router handle client-side routing.

**Critical SQLite + Docker volume behavior:** The DB file and point chart JSONs both live in `/app/data/`. Mounting as a named Docker volume means:
1. **First run:** Docker copies pre-seeded data (charts) from image into volume
2. **Subsequent runs:** Volume persists DB and any user-added chart files
3. **Image update:** New files in image do NOT overwrite existing volume data (Docker named volume behavior). This is correct for user data, but means new chart releases need a startup check-and-copy script.

**Point chart update strategy:** On container start, before running the app, check if expected chart files exist in the volume. If missing, copy from a bundled location. This handles "user upgrades image, new 2027 charts are available but volume already has 2026 only."

**CORS fix (required):** Current `main.py` line 24 hardcodes `allow_origins=["http://localhost:5173"]`. In Docker, frontend is served from same origin (port 8000), so CORS must either be `["*"]` or dynamically configured:
```python
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
```

**Environment variables for `.env.example`:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/dvc.db` | SQLite database path |
| `PORT` | `8000` | HTTP listen port |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins (`*` for Docker) |

---

## Feature Dependencies (v1.1)

```
Docker Packaging ---------> (independent, infrastructure)

Seasonal Cost Heatmap ----> (independent, reads existing point chart data)

Booking Impact Preview ---> (wraps existing availability + trip explorer engines)
       |
       v
What-If Scenarios --------> (extends preview to multiple hypotheticals + Zustand workspace)
       |
       v
Booking Window Alerts ----> (needs "planned trip" concept; quick-win variant needs only Trip Explorer)
```

### Ordering Rationale

1. **Docker** first: infrastructure-only, no feature interaction, unblocks sharing
2. **Heatmap** early: read-only visualization, no new data models, high visual impact for planning
3. **Impact Preview** before Scenarios: establishes the "hypothetical availability diff" pattern that Scenarios extend
4. **Scenarios** after Preview: adds multi-hypothetical workspace UI on the proven preview foundation
5. **Booking Window Alerts** last or parallel: the quick-win (Trip Explorer enhancement) can ship early, but full dashboard alerts need the `planned` reservation status decision, which benefits from having preview/scenario patterns established

---

## MVP Scope Per Feature

**Booking Impact Preview MVP:** Before/after point balance per contract. Nightly breakdown. Banking deadline warning if applicable. NO alternative room suggestions, NO undo/cancel preview.

**What-If Scenario MVP:** Add/remove hypothetical reservations, see cumulative point impact. Scenarios are ephemeral (Zustand, lost on reload). NO banking simulation, NO saved scenarios, NO timeline chart.

**Booking Window Alerts MVP:** Show 11-month and 7-month window open dates on Dashboard for confirmed + pending reservations. Add window dates to Trip Explorer results. NO browser notifications, NO calendar export.

**Seasonal Cost Heatmap MVP:** Single resort, single room type, full year calendar grid with color-coded days. Weekday costs. Hover tooltips. Resort and room type dropdowns. NO affordable-dates overlay, NO multi-resort comparison, NO stay-length mode.

**Docker MVP:** `docker compose up` starts on port 8000 with persisted SQLite. `.env.example` with three variables. Multi-stage Dockerfile. Pre-seeded 2026 charts. NO multi-arch, NO auto-update, NO backup scripts.

---

## Sources

- DVC Booking Window Rules: [DVC Shop - Booking Windows Explained](https://dvcshop.com/the-7-and-11-month-booking-windows-explained/), [Official DVC FAQ](https://disneyvacationclub.disney.go.com/faq/resort-reservations/booking-window/), [DVC Field Guide - Key Dates Calculator](https://dvcfieldguide.com/blog/key-membership-dateshow-to-calculate), [planDisney - Booking Window Q&A](https://plandisney.disney.go.com/question/calculator-help-determine-date-upon-booking-book-home-546096/), [DVC Help - Use Year & Booking Window](https://www.dvchelp.com/page/use-year-booking-window)
- DVC Season Structure: [DVCNews - 2026 Charts Released](https://dvcnews.com/dvc-program-menu/policies-a-procedures/dvc-policy-news/6068-disney-vacation-club-points-charts-released-for-2026), [DVC Fan - 2026 Charts](https://dvcfan.com/general-dvc/2026-disney-vacation-club-points-charts/), [DVCNews - 7 Seasons Introduced 2021](https://dvcnews.com/index.php/dvc-program/policies-a-procedures/news-70636/4648-dvc-releases-point-charts-for-2021-increases-calendar-to-7-seasons), [DVC Help - Point Charts by Date](https://www.dvchelp.com/point-charts/all-resorts-by-date)
- React Heatmap Libraries Evaluated: [react-calendar-heatmap (npm)](https://www.npmjs.com/package/react-calendar-heatmap), [@uiw/react-heat-map](https://github.com/uiwjs/react-heat-map), [Shadcn Calendar Heatmap](https://www.shadcn.io/template/gurbaaz27-shadcn-calendar-heatmap), [Syncfusion React HeatMap](https://www.syncfusion.com/react-components/react-heatmap-chart)
- Docker Multi-Stage Builds: [Docker Official Docs](https://docs.docker.com/build/building/multi-stage/), [FastAPI Docker Docs](https://fastapi.tiangolo.com/deployment/docker/), [FastAPI+React Single Container](https://dakdeniz.medium.com/fastapi-react-dockerize-in-single-container-e546e80b4e4d), [Serving React with FastAPI](https://davidmuraya.com/blog/serving-a-react-frontend-application-with-fastapi/)
- Docker SQLite Volumes: [Docker Volumes Docs](https://docs.docker.com/engine/storage/volumes/), [SQLite with Docker Compose](https://www.hibit.dev/posts/215/setting-up-sqlite-with-docker-compose), [SQLite in Docker (2026)](https://github.com/oneuptime/blog/tree/master/posts/2026-02-08-how-to-run-sqlite-in-docker-when-and-how)
- Docker Env Configuration: [Docker Env Files Best Practices (2026)](https://oneuptime.com/blog/post/2026-01-16-docker-env-files/view)
- Points Management Tool Patterns: [The Points Guy Calculator](https://thepointsguy.com/news/awards-calculator/), [NerdWallet Points Calculator](https://www.nerdwallet.com/article/travel/calculator-should-you-book-a-flight-with-cash-or-miles), [Upgraded Points Transfer Tool](https://upgradedpoints.com/travel/transfer-partner-tool-calculator/)
- Codebase: `backend/engine/availability.py`, `backend/engine/trip_explorer.py`, `backend/data/point_charts.py`, `backend/engine/eligibility.py`, `backend/engine/use_year.py`, `backend/models/reservation.py`, `backend/models/contract.py`, `backend/main.py`, `backend/db/database.py`, `frontend/src/components/UrgentAlerts.tsx`, `frontend/src/pages/TripExplorerPage.tsx`, `frontend/src/pages/DashboardPage.tsx`, `data/point_charts/polynesian_2026.json`

---
*Feature research for: DVC Dashboard v1.1 Planning Tools & Docker Packaging*
*Researched: 2026-02-10*
