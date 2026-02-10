# Project Research Summary

**Project:** DVC Dashboard v1.1 "Share & Plan"
**Domain:** Disney Vacation Club points management — planning tools and self-hosting
**Researched:** 2026-02-10
**Confidence:** HIGH

## Executive Summary

DVC Dashboard v1.1 adds Docker packaging and planning features to an existing FastAPI + React app that helps Disney Vacation Club members manage their points, contracts, and trip planning. The research confirms this is a straightforward extension of proven v1.0 patterns: pure-function calculation engines on the backend, TanStack Query-driven React components on the frontend, and SQLite for single-user data persistence.

The recommended approach is conservative and low-dependency. Docker packaging uses a single-container pattern (FastAPI serves both API and built React assets) to maximize simplicity for self-hosting. All five new features reuse existing stack components: the booking impact preview and what-if scenarios extend the proven availability engine with Zustand for ephemeral client state; booking window alerts are pure date math using already-installed python-dateutil; the seasonal cost heatmap clones the existing SeasonCalendar.tsx pattern with value-based colors instead of categorical; and configurable borrowing policy adds a single settings table. Zero new npm packages required for the MVP scope.

The key risks are Docker-specific: SQLite data loss due to missing volume mounts (the most common Docker+SQLite failure mode), and StaticFiles mount ordering breaking API routes. Both have well-documented prevention strategies. Feature risks are minimal because all new computation reuses the tested v1.0 engine architecture.

## Key Findings

### Recommended Stack

**All five v1.1 features are achievable with the existing stack plus Docker.** No new npm packages required for MVP scope. The existing toolkit (FastAPI, React 19, Vite, Tailwind, shadcn/ui, TanStack Query, SQLAlchemy, python-dateutil, date-fns, Zustand) covers all requirements.

**Core additions:**
- **Docker (multi-stage)**: Single container packages entire app — Node stage builds frontend, Python stage serves everything. `python:3.12-slim` base image keeps final image ~200MB instead of ~1GB.
- **FastAPI StaticFiles mount**: Eliminates need for nginx by serving React build output directly via `app.mount("/", StaticFiles(directory="frontend/dist", html=True))`. The `html=True` parameter enables SPA catch-all routing for React Router deep links.
- **Docker Compose with named volume**: `docker compose up` provides one-command startup. Named volume for `/app/data` ensures SQLite database persists across container rebuilds.
- **Zustand (already installed)**: Currently in package.json but unused. Perfect for what-if scenario state — lightweight (1.1kB), subscription-based re-rendering, no prop drilling.

**Optional addition (defer to later phase):**
- **@nivo/heatmap + @nivo/core**: For a room-comparison matrix heatmap (rows = room types, columns = seasons). Only needed if the calendar-style heatmap (Option A: extend SeasonCalendar.tsx with zero dependencies) proves insufficient for cross-room comparison.

### Expected Features

**Must have (table stakes):**
- **Docker packaging**: Single `docker compose up` starts everything with persistent SQLite — infrastructure requirement for sharing
- **Booking impact preview**: Before/after point balance per contract with nightly breakdown — core value of "what happens to my points if I book this?"
- **Seasonal cost heatmap**: Calendar-year grid with color-coded days showing when to visit for lowest point costs — highest visual impact for planning
- **Booking window alerts**: Show 11-month (home) and 7-month (all resorts) window open dates — DVC-specific domain knowledge automation

**Should have (competitive):**
- **What-if scenario playground**: Add multiple hypothetical bookings, see cumulative impact — extends booking preview to multi-trip planning
- **Configurable borrowing policy**: Toggle 100% vs 50% borrowing limits — reflects DVC policy changes (was 50% during COVID, returned to 100% in 2022)
- **Booking window on Trip Explorer results**: Show "window opens [date]" for each affordable option — inline context where users need it

**Defer (v2+):**
- Banking simulation in scenarios (high complexity, requires modeling UY boundary rules)
- Saved/named scenarios (MVP uses ephemeral Zustand state)
- Multi-resort side-by-side heatmap comparison (MVP: one resort at a time)
- Timeline visualization for scenarios (complexity vs value ratio)
- Browser notifications for booking windows (no auth, local-only tool)

### Architecture Approach

**v1.1 integrates cleanly with established v1.0 patterns.** The existing architecture is a clean three-layer design: React pages call TanStack Query hooks that call FastAPI API routes that call pure-function engines that return computed results. All new features slot into this without architectural changes. The booking impact and scenario engines are pure functions that accept contracts/balances/reservations as dicts and return computed impacts — they reuse the existing availability engine with augmented inputs. The heatmap backend iterates through 365 days calling the existing `get_point_cost()` function. Booking window calculations are pure date math with no database queries.

**Major components (new):**
1. **engine/booking_impact.py** — Pure function computing before/after point balance for a single hypothetical reservation
2. **engine/scenario.py** — Composes booking_impact for multiple hypotheticals sequentially (each builds on prior)
3. **engine/booking_windows.py** — Date arithmetic: check-in minus 11/7 months using python-dateutil
4. **Zustand scenario store** — Client-side ephemeral state for hypothetical booking list (disappears on reload)
5. **CostHeatmap.tsx** — Clones SeasonCalendar.tsx pattern with value-based color scale instead of categorical seasons
6. **Docker multi-stage build** — Stage 1: node:22-alpine builds frontend; Stage 2: python:3.12-slim serves API + static files

**Key architectural decision:** Server-side computation, client-side state. Scenarios are built in Zustand (frontend), sent to backend as payload, computed server-side using existing Python engine, results returned. This keeps all DVC business logic in Python (141 tests would need duplication if moved to TypeScript) while maintaining fast UX (round-trip <100ms for this payload size).

### Critical Pitfalls

1. **SQLite database loss in Docker due to missing volume mount** — The database file lives inside the container by default. On `docker compose up --build`, all data disappears. Prevention: Mount the **directory** (not just the file) as a named volume so WAL/SHM sidecar files are co-located. Set `DATABASE_URL` to point inside the volume path. Test with `docker compose down && up` before shipping.

2. **What-if scenario engine mutating real point balances** — If implementation inserts hypothetical reservations into the database (even with rollback), scenarios leak into real data or cause SQLite locking. Prevention: The existing engine is already pure — functions take `reservations: list[dict]` as input. Scenarios create `real_reservations + hypothetical` in memory, pass to engine, never touch DB.

3. **Booking window alert dates calculated wrong due to use year confusion** — Booking windows are computed from check-in date (check-in minus 11/7 months), NOT from use year start date. These are independent date systems. Prevention: New engine function that does zero use year logic. Test edge case: Jan 15 check-in has Feb 15 **previous year** window opening.

4. **FastAPI StaticFiles mount ordering breaks API routes** — If SPA mount registered before API routers, `/api/*` requests return React index.html instead of JSON. Prevention: Register all `app.include_router()` calls BEFORE `app.mount("/", StaticFiles(...))`. Verify with `curl http://localhost:8000/api/health | jq .status` in Docker build.

5. **Borrowing policy toggle not propagating to all calculation paths** — Policy toggle added only to API validation but not to scenario/trip-explorer/impact engines means different parts of app give contradictory answers. Prevention: Add borrowing limit as engine function parameter, not just API-layer validation. Scenarios must receive and enforce the policy setting.

## Implications for Roadmap

Based on research, suggested phase structure follows dependency chains and validation checkpoints:

### Phase 1: Docker Packaging + Settings Foundation
**Rationale:** Docker is infrastructure that enables sharing all subsequent work. Borrowing policy settings establish the pattern for system-level configuration used elsewhere.

**Delivers:**
- `docker compose up` starts app on port 8000 with persistent SQLite
- Multi-stage Dockerfile (node:22-alpine builds frontend, python:3.12-slim serves)
- FastAPI serves React build output via StaticFiles mount
- Settings model + API endpoint for borrowing policy toggle
- .dockerignore, docker-compose.yml, .env.example

**Addresses:**
- Docker packaging (table stakes from FEATURES.md)
- Configurable borrowing policy (affects all subsequent calculation features)

**Avoids:**
- Pitfall 1: SQLite data loss — volume mount tested immediately
- Pitfall 4: StaticFiles mount ordering — API routes registered first
- Pitfall 3: lru_cache path issues — Dockerfile preserves directory structure

**Stack elements:**
- Docker, Docker Compose (STACK.md: single container pattern)
- Settings table in SQLite (ARCHITECTURE.md: establishes config pattern)

**Research flag:** Standard Docker patterns. Skip `/gsd:research-phase` — well-documented.

---

### Phase 2: Booking Impact Preview + Booking Window Alerts
**Rationale:** These are the smallest engine features and enrich existing pages (Trip Explorer, Dashboard) rather than creating new ones. Booking impact is prerequisite for scenarios.

**Delivers:**
- `engine/booking_impact.py` — pure function computing before/after point balance
- Trip Explorer results enriched with expandable impact panels
- `engine/booking_windows.py` — date arithmetic for 11/7-month window calculation
- Dashboard alerts showing upcoming booking window openings
- Booking window dates on Trip Explorer results

**Addresses:**
- Booking impact preview (must-have from FEATURES.md)
- Booking window alerts (must-have from FEATURES.md)
- Booking window on Trip Explorer (should-have from FEATURES.md)

**Avoids:**
- Pitfall 3: Booking window date calculation — independent from use year logic
- Pitfall 11: Double-counting overlapping reservations — baseline diff approach

**Implements:**
- ARCHITECTURE.md: Pure-function engine pattern (booking_impact, booking_windows)
- Existing `get_contract_availability()` reused with augmented inputs

**Research flag:** Standard patterns. Skip `/gsd:research-phase` — reuses proven engine architecture.

---

### Phase 3: What-If Scenario Playground
**Rationale:** Most complex new feature. Depends on booking_impact engine from Phase 2. First use of Zustand store.

**Delivers:**
- `engine/scenario.py` — composes booking_impact for multiple hypotheticals sequentially
- `api/scenarios.py` + Pydantic schemas
- Zustand store for scenario state (`useScenarioStore`)
- ScenarioPage with builder form and cumulative impact display
- Cache invalidation on real mutations (prevent stale state)

**Addresses:**
- What-if scenario playground (should-have from FEATURES.md)

**Avoids:**
- Pitfall 2: Mutating real data — pure function approach, in-memory augmented reservations list
- Pitfall 5: Borrowing policy not enforced — engine accepts policy parameter
- Pitfall 9: Stale state — invalidate scenario cache on mutations

**Uses:**
- Zustand (STACK.md: already installed, first activation)
- Phase 2 booking_impact engine as composition foundation

**Implements:**
- ARCHITECTURE.md: Server-side computation, client-side state pattern

**Research flag:** Standard patterns. Skip `/gsd:research-phase` — extends Phase 2 engine work.

---

### Phase 4: Seasonal Cost Heatmap
**Rationale:** Standalone visualization with no dependencies on other v1.1 features. Can be built last since it's additive.

**Delivers:**
- `api/heatmap.py` — endpoint returning 365 days of {date, points, season, is_weekend}
- CostHeatmap.tsx — clones SeasonCalendar.tsx pattern with value-based colors
- HeatmapPage with resort/room selector
- Color legend and hover tooltips

**Addresses:**
- Seasonal cost heatmap (must-have from FEATURES.md)

**Avoids:**
- Pitfall 6: Performance issues — CSS Grid, not nested components; lazy-load per resort tab
- Pitfall 7: Date gaps — validate chart coverage; show "no data" indicator for gaps
- Pitfall 13: Weekday/weekend distinction — use per-date `get_point_cost()` function

**Implements:**
- ARCHITECTURE.md: Extend existing SeasonCalendar pattern (zero new dependencies)
- Reuses existing `get_point_cost()` from point_charts.py

**Research flag:** Standard patterns. Skip `/gsd:research-phase` — clones existing component pattern.

---

### Phase Ordering Rationale

```
Phase 1: Docker + Settings   Infrastructure foundation, enables sharing
         |
         v
Phase 2: Impact + Windows     Engine extensions, enrich existing pages
         |                    booking_impact prerequisite for scenarios
         v
Phase 3: Scenarios           Depends on Phase 2 engine, activates Zustand
         |
         v
Phase 4: Heatmap             Independent, additive, high visual impact
```

- **Docker first** because every subsequent feature should be testable in Docker environment. Volume mount and StaticFiles issues must be caught immediately.
- **Impact before Scenarios** because scenario engine composes the booking_impact engine. Sequential dependency.
- **Booking windows with impact** because both are small, read-only engine features that enrich existing pages without creating new data models.
- **Scenarios third** because it extends Phase 2 patterns and introduces Zustand (first client-state management need).
- **Heatmap last** because it's purely additive with zero feature interaction. Can ship independently if timeline pressure arises.

### Research Flags

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Docker):** Well-documented multi-stage build and StaticFiles patterns. FastAPI docs and community consensus.
- **Phase 2 (Impact/Windows):** Pure-function engine extensions reusing existing availability.py patterns.
- **Phase 3 (Scenarios):** Composes Phase 2 engine work; Zustand usage is straightforward.
- **Phase 4 (Heatmap):** Clones existing SeasonCalendar.tsx component pattern.

**Phases needing potential deeper research:** None. All features integrate with proven v1.0 patterns and use established libraries/techniques.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | Existing stack unchanged. Docker patterns well-documented. Zustand already installed. Heatmap needs zero new dependencies (extend SeasonCalendar pattern). Optional @nivo addition only if room-comparison matrix needed later. |
| Features | **HIGH** | DVC domain rules verified across official sources (11/7-month windows, booking policies, season structures). Feature MVP scopes clearly defined. Existing v1.0 code provides implementation patterns for all new features. |
| Architecture | **HIGH** | Clean integration with v1.0 three-layer pattern. Pure-function engine approach proven with 141 tests. Server-side computation, client-side state strategy is standard. Docker single-container pattern correct for single-user SQLite app. |
| Pitfalls | **MEDIUM-HIGH** | Docker+SQLite pitfalls well-documented with clear prevention strategies. DVC domain edge cases identified (borrowed points affect next year, banked points can't re-bank). Mount ordering and CORS config risks have established solutions. Frontend performance for 4K-cell heatmap manageable with CSS Grid. |

**Overall confidence:** **HIGH**

All features build on proven v1.0 foundation. No architectural changes. No experimental libraries. Docker risks are well-understood with documented mitigation.

### Gaps to Address

**Minor gaps requiring validation during implementation:**

- **Heatmap color scale usability**: Research shows 5-7 discrete color buckets, but optimal mapping of DVC season tiers to perceptually uniform colors needs user testing. Start with green-yellow-red sequential palette; iterate based on visual clarity.

- **Scenario cache invalidation strategy**: Need to determine exact queryKeys to invalidate on mutation (availability, reservations, scenarios) and whether to use optimistic updates or full refetch. TanStack Query docs + existing codebase patterns cover this, but specific keys need design during Phase 3.

- **Docker multi-arch builds**: Research identified ARM64 + AMD64 as "differentiator" feature. Decision needed: ship AMD64-only MVP (covers 95% of self-hosters) or add multi-arch in Phase 1. Defer to v1.2 if not immediately needed.

- **Point chart data validation**: Pitfall 7 requires validating 365-day coverage for each chart file. Add as test case during Phase 4 or proactively add to existing test suite. Low effort, high confidence gain.

**Handling strategy:** All gaps are implementation details within well-understood domains. Resolve during phase planning or first commit of affected phase. None block roadmap creation.

## Sources

### Primary (HIGH confidence)
- **STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md** — Four parallel research outputs (2026-02-10)
- [FastAPI Docker Deployment](https://fastapi.tiangolo.com/deployment/docker/) — Official Dockerfile pattern, slim image recommendation
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/) — StaticFiles mount pattern
- [Docker Volumes](https://docs.docker.com/engine/storage/volumes/) — Named volume best practices
- [DVC Official FAQ - Booking Windows](https://disneyvacationclub.disney.go.com/faq/resort-reservations/booking-window/) — 11/7-month window rules
- [DVC Shop - Booking Windows Explained](https://dvcshop.com/the-7-and-11-month-booking-windows-explained/) — Detailed window mechanics
- [Zustand GitHub](https://github.com/pmndrs/zustand) — v5 API, React 19 compatibility
- [Nivo React 19 Support Issue #2618](https://github.com/plouc/nivo/issues/2618) — Confirmed React 19 compatibility (if @nivo/heatmap added)

### Secondary (MEDIUM confidence)
- [SQLite in Docker (OneUptime 2026)](https://github.com/oneuptime/blog/tree/master/posts/2026-02-08-how-to-run-sqlite-in-docker-when-and-how) — Volume mount strategies
- [FastAPI + React Single Container (Medium)](https://dakdeniz.medium.com/fastapi-react-dockerize-in-single-container-e546e80b4e4d) — Monolith Docker pattern
- [DVC Banking FAQ](https://disneyvacationclub.disney.go.com/faq/bank-points/) — Banking restrictions
- [DVC Borrowing Restriction History](https://www.disneytouristblog.com/dvc-point-policy-updates/) — 50% restriction (2020) to 100% (2022) timeline
- [React Heatmap Performance](https://blog.logrocket.com/best-heatmap-libraries-react/) — Library comparison

### Tertiary (LOW confidence)
- Community tutorials and blog posts for Docker best practices (validated against official docs)

---
*Research completed: 2026-02-10*
*Ready for roadmap: yes*
