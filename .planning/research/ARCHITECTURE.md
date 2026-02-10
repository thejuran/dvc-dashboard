# Architecture Research

**Domain:** Personal DVC (Disney Vacation Club) dashboard with web scraping, time-based point calculations, and data visualization
**Researched:** 2026-02-09
**Confidence:** MEDIUM -- domain rules well-understood; scraping layer carries uncertainty due to Disney authentication and ToS

## Standard Architecture

### System Overview

```
                         ┌──────────────────────────────────────────────────┐
                         │              PRESENTATION LAYER                 │
                         │  ┌────────────┐ ┌──────────┐ ┌──────────────┐   │
                         │  │ Dashboard  │ │   Trip   │ │ Reservation  │   │
                         │  │  (Home)    │ │ Explorer │ │   Tracker    │   │
                         │  └─────┬──────┘ └────┬─────┘ └──────┬───────┘   │
                         │        │             │              │           │
                         ├────────┴─────────────┴──────────────┴───────────┤
                         │              CALCULATION ENGINE                 │
                         │  ┌─────────────────┐ ┌────────────────────────┐ │
                         │  │ Point Availability│ │   Booking Eligibility │ │
                         │  │   Calculator     │ │   Resolver            │ │
                         │  └────────┬─────────┘ └───────────┬───────────┘ │
                         │           │                       │             │
                         ├───────────┴───────────────────────┴─────────────┤
                         │                DATA LAYER                       │
                         │  ┌───────────┐ ┌────────────┐ ┌─────────────┐  │
                         │  │ Contracts │ │   Point    │ │Reservations │  │
                         │  │  Store    │ │   Charts   │ │   Store     │  │
                         │  └───────────┘ └────────────┘ └─────────────┘  │
                         ├─────────────────────────────────────────────────┤
                         │              SCRAPING LAYER                     │
                         │  ┌──────────────────┐  ┌──────────────────────┐ │
                         │  │  DVC Site Scraper │  │  Sync Scheduler     │ │
                         │  │  (Playwright)     │  │  (cron/manual)      │ │
                         │  └──────────────────┘  └──────────────────────┘ │
                         └─────────────────────────────────────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │  disneyvacationclub     │
                              │  .disney.go.com         │
                              │  (member portal)        │
                              └────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| **DVC Site Scraper** | Authenticates with Disney member portal, extracts point balances, reservation data, and contract details | Disney member site (external), Data Layer (writes) |
| **Sync Scheduler** | Triggers scraping on schedule or manual request; manages session persistence | DVC Site Scraper |
| **Contracts Store** | Persists contract details: home resort, use year, annual points, purchase type (resale/direct), expiration | Calculation Engine (reads) |
| **Point Charts Store** | Stores points-per-night tables by resort, room type, season, day-of-week | Calculation Engine (reads), Trip Explorer (reads) |
| **Reservations Store** | Tracks current and past reservations with point costs and dates | Dashboard (reads), Calculation Engine (reads) |
| **Point Availability Calculator** | Given a target date, computes available points per contract factoring banking windows, borrowed points, use year boundaries, and existing reservations | Contracts Store (reads), Reservations Store (reads) |
| **Booking Eligibility Resolver** | Given a contract (resale vs direct, home resort), determines which resorts/room types are bookable | Contracts Store (reads), Point Charts (reads) |
| **Dashboard** | Homepage showing point balances, upcoming reservations, banking deadlines, key dates | Calculation Engine, Data Layer |
| **Trip Explorer** | "What can I book?" interface -- pick dates, see eligible resorts/rooms with point costs vs available points | Calculation Engine, Booking Eligibility, Point Charts |
| **Reservation Tracker** | View and manage current reservations, see point impact | Data Layer |

## Recommended Project Structure

```
dvc-dashboard/
├── backend/
│   ├── scraper/              # Web scraping layer
│   │   ├── auth.py           # Disney member site authentication
│   │   ├── session.py        # Session persistence (cookies/storage state)
│   │   ├── points_scraper.py # Extract point balances from member site
│   │   ├── reservations_scraper.py  # Extract reservation data
│   │   └── scheduler.py      # Sync scheduling logic
│   ├── models/               # Data models
│   │   ├── contract.py       # DVC contract model
│   │   ├── point_chart.py    # Point chart model (resort/room/season/day)
│   │   ├── reservation.py    # Reservation model
│   │   └── point_balance.py  # Point balance snapshot model
│   ├── engine/               # Calculation engine
│   │   ├── availability.py   # Point availability calculator
│   │   ├── eligibility.py    # Booking eligibility resolver (resale restrictions)
│   │   ├── use_year.py       # Use year date math (banking deadlines, expiry)
│   │   └── trip_calculator.py # "What can I book" logic
│   ├── api/                  # API routes
│   │   ├── dashboard.py      # Dashboard data endpoints
│   │   ├── trips.py          # Trip explorer endpoints
│   │   ├── reservations.py   # Reservation endpoints
│   │   └── sync.py           # Manual sync trigger endpoint
│   ├── db/                   # Database
│   │   ├── database.py       # Connection/session management
│   │   └── migrations/       # Schema migrations
│   └── main.py               # FastAPI app entry point
├── frontend/
│   ├── src/
│   │   ├── pages/            # Dashboard, TripExplorer, Reservations
│   │   ├── components/       # Shared UI components
│   │   ├── hooks/            # Data fetching hooks
│   │   └── utils/            # Date formatting, point display helpers
│   └── ...
├── data/                     # Static data (point charts, resort metadata)
│   ├── point_charts/         # Point chart CSVs or JSON by resort/year
│   └── resorts.json          # Resort metadata (names, room types, views)
└── tests/
    ├── engine/               # Calculation engine tests (critical)
    ├── scraper/              # Scraper tests with fixtures
    └── api/                  # API tests
```

### Structure Rationale

- **backend/scraper/:** Isolated from business logic. Scraping is fragile and will break when Disney changes their site. Keeping it separate means breakage in scraping does not cascade into the calculation or presentation layers.
- **backend/engine/:** The calculation engine is the core intellectual property of the app. It encodes complex DVC rules (banking windows, borrowing limits, use year math, resale restrictions). It must be independently testable with no dependency on scraping or the database -- pure functions that take data in and return calculations.
- **backend/models/:** Shared data shapes used across scraper, engine, and API. Single source of truth for what a "contract" or "reservation" looks like.
- **data/:** Point charts change annually but are publicly available. Storing them as static data files (not scraped) keeps the system simple. Can be manually updated once a year when Disney publishes new charts.
- **tests/engine/:** The calculation engine deserves the heaviest test coverage. Getting point availability wrong defeats the purpose of the entire app.

## Architectural Patterns

### Pattern 1: Scrape-Store-Calculate (Decoupled Pipeline)

**What:** The scraper writes raw data to the database. The calculation engine reads from the database and computes derived values on demand. The scraper never calls the calculation engine; the calculation engine never calls the scraper.
**When to use:** Always. This is the foundational pattern for the entire system.
**Trade-offs:** Adds a data staleness window (points shown may be minutes/hours old), but eliminates coupling between the most fragile layer (scraping) and the most critical layer (calculations).

```
Scraper → [writes] → Database ← [reads] ← Engine ← [calls] ← API ← [calls] ← Frontend
```

The scraper is a "data pump." It runs periodically (or on demand), pushes data into the database, and exits. The rest of the system operates purely on stored data.

### Pattern 2: Static Data for Point Charts

**What:** Point charts (points-per-night by resort/room/season/day-of-week) are stored as versioned static files (JSON or CSV), not scraped.
**When to use:** Always for point charts. They change once per year when Disney publishes new charts and are publicly available on fan sites and the official DVC site.
**Trade-offs:** Requires a manual annual update (small effort), but eliminates an entire scraping target and its failure modes.

Point charts have a specific structure:
- **7 seasons** per year (Adventure, Choice, Dream, Magic, Premier, etc.)
- **Date ranges** map calendar dates to seasons
- **Room types** vary by resort (Studio, 1BR, 2BR, Grand Villa, plus view categories)
- **Day-of-week** pricing: weekday (Sun-Thu) vs weekend (Fri-Sat)
- **Per-night values** in points

```json
{
  "resort": "Boulder Ridge Villas",
  "year": 2026,
  "seasons": [
    {
      "name": "Adventure",
      "date_ranges": [["2026-01-01", "2026-01-31"], ["2026-09-01", "2026-09-30"]],
      "rooms": {
        "studio_standard": { "weekday": 10, "weekend": 13 },
        "one_bedroom": { "weekday": 20, "weekend": 26 },
        "two_bedroom": { "weekday": 30, "weekend": 38 }
      }
    }
  ]
}
```

### Pattern 3: Pure Function Calculation Engine

**What:** The calculation engine is implemented as stateless, pure functions. Give it contract data, current date, and reservation data; it returns point availability, banking deadlines, and booking options. No database calls, no side effects.
**When to use:** For all point calculation logic.
**Trade-offs:** Requires the API layer to fetch data from the DB and pass it to the engine (slightly more code in the API layer), but the engine becomes trivially testable and completely decoupled from storage.

```python
# engine/availability.py -- pure function, no DB dependency

def calculate_available_points(
    contracts: list[Contract],
    reservations: list[Reservation],
    target_date: date,
    today: date = date.today()
) -> list[ContractPointSummary]:
    """For each contract, compute points available on target_date."""
    results = []
    for contract in contracts:
        current_uy = get_use_year_window(contract.use_year_month, target_date)
        banking_deadline = current_uy.start + relativedelta(months=8)

        # Current year points: annual allotment minus used/reserved
        current_year_used = sum(
            r.points for r in reservations
            if r.contract_id == contract.id
            and current_uy.start <= r.check_in < current_uy.end
        )
        current_available = contract.annual_points - current_year_used

        # Banked points: carried from prior year (if any, already in DB)
        # Borrowable: up to 50% of next year's allotment
        borrowable = contract.annual_points // 2

        results.append(ContractPointSummary(
            contract=contract,
            current_year_available=current_available,
            banked_points=contract.banked_points,
            borrowable_points=borrowable,
            banking_deadline=banking_deadline,
            use_year_end=current_uy.end,
        ))
    return results
```

## Data Flow

### Scraping Flow (Data Ingestion)

```
[Manual Trigger or Cron]
    │
    ▼
[Scheduler] ─── loads saved session ──→ [Playwright Browser]
    │                                         │
    │                                    Login to DVC site
    │                                    (or reuse session)
    │                                         │
    │                               ┌─────────┴──────────┐
    │                               ▼                    ▼
    │                      [Points Scraper]     [Reservations Scraper]
    │                               │                    │
    │                         Extract point        Extract reservation
    │                         balances, banked      data, dates, costs
    │                         amounts, contract
    │                         details
    │                               │                    │
    │                               ▼                    ▼
    │                          [Data Layer — SQLite Database]
    │                                         │
    ▼                                    Save session
[Save session state]                    for next run
```

### Dashboard Request Flow

```
[User opens Dashboard]
    │
    ▼
[Frontend] ─── GET /api/dashboard ──→ [API Layer]
                                          │
                                    ┌─────┴──────┐
                                    ▼            ▼
                              [DB: Contracts] [DB: Reservations]
                                    │            │
                                    ▼            ▼
                              [Engine: calculate_available_points()]
                                    │
                                    ▼
                              [Engine: get_banking_deadlines()]
                                    │
                                    ▼
                              JSON response:
                              - Points per contract
                              - Banking deadlines
                              - Upcoming reservations
                              - Warnings (expiring points, etc.)
```

### Trip Explorer Flow

```
[User picks dates + party size]
    │
    ▼
[Frontend] ─── GET /api/trips?check_in=X&check_out=Y&guests=N ──→ [API Layer]
                                                                       │
                                                         ┌─────────────┼──────────────┐
                                                         ▼             ▼              ▼
                                                   [DB: Contracts] [DB: Reservations] [Point Charts]
                                                         │             │              │
                                                         ▼             ▼              │
                                                   [Engine: calculate_available_points()]
                                                         │                            │
                                                         ▼                            ▼
                                                   [Engine: resolve_eligible_resorts()]
                                                         │
                                                         ▼
                                                   [Engine: calculate_trip_cost()]
                                                   For each eligible resort/room:
                                                   - Sum points per night across date range
                                                   - Compare to available points
                                                         │
                                                         ▼
                                                   JSON response:
                                                   - List of bookable resort/room combos
                                                   - Points cost per option
                                                   - Available points (can you afford it?)
                                                   - Which contract(s) to use
```

### Key Data Flows

1. **Scrape-to-Store:** Playwright authenticates with Disney member portal, extracts current point balances and reservation data, writes snapshots to SQLite. Runs on demand or scheduled (e.g., daily). Session state persisted to avoid repeated logins.

2. **Store-to-Calculate:** API endpoints read contracts + reservations from DB, pass them to pure-function calculation engine. Engine computes derived values (available points, banking deadlines, borrowable amounts) without touching the DB.

3. **Calculate-to-Present:** API serializes engine output to JSON. Frontend renders dashboards, timelines, and trip options. All computation happens server-side; frontend is a display layer.

4. **Point Chart Lookup:** Trip Explorer reads point charts from static JSON files. No scraping needed -- charts are published annually and entered manually.

## DVC Domain Rules (Critical for Calculation Engine)

These rules drive the architecture of the calculation engine. Getting them wrong breaks the app's core value.

### Use Year System

- Each contract has a **use year month** (e.g., June). Points for a use year are available from the 1st of that month through the last day of the month before the next use year.
- Example: June use year = June 1, 2026 through May 31, 2027.

### Banking Rules

- **100% of current year points** can be banked into the next use year.
- **Banking deadline:** 8 months into the use year (e.g., June use year = bank by January 31).
- **After the deadline (months 9-12):** Cannot bank. Use them or lose them.
- **Banked points can only be banked once.** They cannot be re-banked into a third year.

### Borrowing Rules

- **Up to 50% of next year's allotment** can be borrowed into the current use year.
- Borrowed points reduce next year's available balance.

### Resale Contract Restrictions

- **Original 14 DVC resorts (pre-January 2019):** Resale contracts can book at any of the original 14 resorts.
- **Post-January 2019 resorts** (Riviera, Villas at Disneyland Hotel, Cabins at Fort Wilderness, future resorts): Resale contracts can ONLY book at their home resort.
- **Direct purchase contracts:** No restrictions, can book anywhere.
- **Resale contracts additionally cannot access:** Concierge Collection, Disney Collection, Adventurer Collection.

### Point Chart Structure

- **Per resort:** Each resort has its own chart.
- **7 seasons per year:** Season names and date ranges vary by resort.
- **Room types per resort:** Studio, 1BR, 2BR, Grand Villa (plus view categories like Standard, Lake, Theme Park, etc.).
- **Day-of-week pricing:** Sunday-Thursday (weekday) vs Friday-Saturday (weekend).
- **Values expressed as points per night.**
- **Charts published annually** and can change year to year (but total resort-wide points are fixed).

### The "Up To 4 Years" Rule

At any given time, a member can theoretically access points spanning up to 4 use years:
1. Banked points from the prior use year
2. Current use year points
3. Borrowed points from the next use year
4. (Edge case) Points in a use year that hasn't started yet but are committed via reservation

The calculation engine must track points across these windows per contract.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Disney member portal (disneyvacationclub.disney.go.com) | Playwright browser automation with session persistence | Disney actively discourages scraping (ToS). Use for personal data only. Respect rate limits. Session cookies can be saved/reused to minimize logins. Two-factor auth may be required -- handle interactively on first login, then persist session. |
| DVC point chart data (public) | Static JSON files, manually updated annually | Available on official site and fan sites (dvcfan.com, dvcnews.com, wdwinfo.com). No scraping needed. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Scraper -> Data Layer | Direct DB writes (SQLAlchemy models) | Scraper writes raw snapshots; never reads calculation results |
| API -> Engine | Function calls (engine is a library, not a service) | API fetches data from DB, passes to engine functions, returns results |
| API -> Data Layer | SQLAlchemy ORM queries | Standard CRUD operations |
| Frontend -> API | HTTP REST (JSON) | Frontend is a pure display layer; no business logic |
| Engine -> Point Charts | File reads (JSON) | Engine loads point chart data from static files at startup or on demand |

## Anti-Patterns

### Anti-Pattern 1: Scraping Inside Request Handlers

**What people do:** Call the scraper from an API endpoint when the user requests fresh data.
**Why it's wrong:** Scraping takes 10-30+ seconds, involves browser automation, and can fail due to Disney site changes. This blocks the API response and creates a terrible user experience. If the scrape fails, the dashboard shows an error instead of stale-but-usable data.
**Do this instead:** Scrape on a schedule or via a manual "sync now" button that runs asynchronously. Dashboard always reads from the database. Show "last synced: 2 hours ago" instead of blocking on a live scrape.

### Anti-Pattern 2: Embedding DVC Rules in the Frontend

**What people do:** Put banking deadline calculations, borrowing limit logic, or resale restriction checks in JavaScript/React components.
**Why it's wrong:** DVC rules are complex and interconnected. Splitting them across frontend and backend creates inconsistency, makes testing harder, and means changes to rules require updating two codebases.
**Do this instead:** All DVC business logic lives in the backend calculation engine. The frontend displays pre-computed results from the API. The frontend's job is layout and interaction, not point math.

### Anti-Pattern 3: Scraping Point Charts

**What people do:** Build a scraper to extract point charts from the DVC website or fan sites.
**Why it's wrong:** Point charts change once per year. Building and maintaining a scraper for data that changes annually is massive over-engineering. Charts are available in simple tabular format and can be entered manually in 30 minutes.
**Do this instead:** Store point charts as static JSON files. Update them once a year when Disney publishes new charts (usually in fall for the following year).

### Anti-Pattern 4: One Giant "Points" Table

**What people do:** Store all point information in a single database table with columns for every possible state.
**Why it's wrong:** Points have complex lifecycle states (allocated, banked, borrowed, reserved, used, expired) across multiple contracts and use years. A single table becomes an unqueryable mess.
**Do this instead:** Separate tables for contracts, point allocations (per use year), reservations (with point costs), and banking/borrowing transactions. The calculation engine derives current availability from these normalized records.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user (this project) | SQLite database, single FastAPI server, Playwright on same machine. No need for job queues, caching, or horizontal scaling. |
| 2-5 users (family sharing) | Same architecture works. Add basic auth to protect the dashboard. SQLite handles concurrent reads fine for this scale. |
| Beyond 5 users | Not a goal. This is a personal tool. Do not over-engineer for scale that will never materialize. |

### Scaling Priorities

1. **First bottleneck (and only one that matters):** Scraper fragility. When Disney changes their site, the scraper breaks. Mitigation: keep scraper isolated, well-logged, and make the rest of the app work fine with stale data. Show clear "last synced" timestamps.
2. **Second bottleneck:** Point chart accuracy. If charts are entered incorrectly, trip cost calculations are wrong. Mitigation: validate chart data (total points per resort should match known values), add unit tests against known booking costs.

## Build Order (Suggested)

Build order is driven by dependency chains and the ability to validate each layer independently.

### Phase 1: Data Models + Static Data

Build first because everything depends on the data shapes.
- Define contract, reservation, point balance, and point chart models
- Enter point chart data for your 2-3 home resorts (static JSON)
- Set up SQLite database with schema
- Seed with your actual contract data (manually entered)

**Validates:** You can describe your DVC ownership in structured data.

### Phase 2: Calculation Engine

Build second because it is the core value proposition and can be tested with seed data from Phase 1.
- Point availability calculator (given contracts + date, what points are available?)
- Use year date math (banking deadlines, use year windows, expiry dates)
- Booking eligibility resolver (resale restrictions per contract)
- Trip cost calculator (given resort + room + dates, how many points?)

**Validates:** Engine produces correct results against hand-calculated examples. Test-driven development is essential here.

### Phase 3: API Layer

Build third because it wraps the engine and data layer for the frontend.
- Dashboard endpoint (point summary, deadlines, warnings)
- Trip explorer endpoint (eligible resorts + costs for given dates)
- Reservation endpoints (CRUD)
- Manual sync trigger endpoint (placeholder -- scraper comes later)

**Validates:** API returns correct JSON. Can test with curl/Postman.

### Phase 4: Frontend (Dashboard + Trip Explorer)

Build fourth because it consumes the API.
- Dashboard page (point balances, timelines, banking deadlines)
- Trip Explorer page (date picker, results grid)
- Reservation tracker page

**Validates:** Visual confirmation that data flows correctly end-to-end.

### Phase 5: Scraper

Build last because it is the most fragile component and the hardest to test. All other layers work with manually-entered data until the scraper is ready.
- Playwright authentication with Disney member portal
- Point balance extraction
- Reservation data extraction
- Session persistence (avoid re-login on every run)
- Sync scheduler (cron or manual trigger)

**Validates:** Scraped data matches what you see on the DVC member site.

### Build Order Rationale

- **Engine before scraper:** The engine is the app's brain. Building it first with hand-entered test data means you can validate correctness before adding the complexity of scraping. If the scraper never works perfectly, you still have a useful tool with manual data entry.
- **Static data before dynamic scraping:** Point charts are static and publicly available. Contract details are known to the owner. Only current point balances and active reservations need scraping. Build the 90% that works without scraping first.
- **Frontend last (before scraper):** The frontend is pure display. Building it after the API means you are displaying real, tested calculations -- not mock data that might not match reality.
- **Scraper last:** It depends on an external site you don't control, involves browser automation complexity, and may require handling 2FA. It is the riskiest component. Deferring it means the rest of the app is solid when you tackle the hard part. Even without the scraper, the app is useful for manually-entered data and "what can I book" exploration.

## Sources

- [DVC Bank/Borrow Official Rules](https://disneyvacationclub.disney.go.com/points/bank-borrow/)
- [DVC Banking Deadlines FAQ](https://disneyvacationclub.disney.go.com/faq/bank-points/deadlines/)
- [Understanding the DVC Use Year - DVCinfo](https://dvcinfo.com/dvc-information/buying-dvc/understanding-use-year/)
- [How to Bank and Borrow Points - DVC Field Guide](https://dvcfieldguide.com/blog/how-to-bank-and-borrow-dvc-points)
- [DVC Resale Restrictions: Eligible Resorts - DVC Shop](https://dvcshop.com/resale-restrictions-eligible-resorts/)
- [DVC Resale Restrictions - Fidelity Real Estate](https://www.fidelityrealestate.com/blog/dvc-resale-restrictions/)
- [How DVC Point Charts Work - DVC Fan](https://dvcfan.com/general-dvc/how-dvc-point-charts-work-a-beginners-guide/)
- [2026 DVC Point Charts - wdwinfo.com](https://www.wdwinfo.com/disney-vacation-club/dvc-point-charts.htm)
- [DVC Availability Tools Discussion - DISboards](https://www.disboards.com/threads/dvc-availability-tools.3915367/)
- [How DVC Availability Charts Work - DVCHelp](https://www.dvchelp.com/page/how-do-the-charts-work)
- [Playwright Authentication Docs](https://playwright.dev/python/docs/auth)
- [DVC Points and Flexibility Official](https://disneyvacationclub.disney.go.com/points-and-flexibility/)

---
*Architecture research for: Personal DVC Dashboard*
*Researched: 2026-02-09*
