# Project Research Summary

**Project:** DVC Points Management & Vacation Planning Dashboard
**Domain:** Personal web dashboard with authenticated scraping, time-based financial calculations, and data visualization
**Researched:** 2026-02-09
**Confidence:** MEDIUM-HIGH

## Executive Summary

This is a single-user personal dashboard for managing Disney Vacation Club (DVC) timeshare points across multiple contracts with complex time-based rules (banking, borrowing, use years, resale restrictions). The recommended approach mirrors the proven NephSched monorepo pattern (FastAPI backend + React/Vite frontend) because it works and you already know it. The killer feature is automated scraping of the DVC member portal to eliminate manual data entry—no existing competitor does this—but scraping Disney's authenticated site is inherently fragile and requires architecting the entire app to function gracefully with stale data.

The core technical challenge is not the stack (which is standard and well-supported) but rather encoding complex DVC domain rules into a calculation engine that projects point availability across multiple contracts, use years, banking windows, and resale restrictions. The point timeline calculator—"pick a future date, see available points accounting for banking/borrowing/expiration"—is the product's primary value proposition and requires getting the data model right from day one. Incorrect point calculations or missing resale restrictions would make the app worse than useless by creating false confidence in bad data.

Critical risks and mitigations: (1) Scraping fragility—mitigate by treating scraping as an import mechanism not a data source, always showing data age, and supporting manual entry as fallback; (2) Complex point lifecycle math—mitigate by building calculation engine as pure functions with exhaustive unit tests before adding UI; (3) DVC rule changes—mitigate by versioning point charts as data not code and designing schema for annual updates; (4) Disney legal action—mitigate by keeping scraping manual, low-frequency, and personal-use-only.

## Key Findings

### Recommended Stack

The stack leverages modern async Python for backend (FastAPI + Playwright for scraping + SQLite for storage) and React 19 + TypeScript for frontend. All technologies are stable, production-ready, and align with your existing NephSched expertise. Python 3.12+ with FastAPI 0.128.x provides native async/await for non-blocking scraping tasks. Playwright handles JavaScript-rendered authenticated sessions better than alternatives. SQLite is perfect for single-user with zero-configuration file-based storage enabling trivial backups. React 19 + Vite 7 + Tailwind 4 + shadcn/ui gives you a complete modern frontend stack with excellent DX.

**Core technologies:**
- **FastAPI 0.128.5:** Native async for scraping workloads, built-in Pydantic validation, you know it from NephSched
- **Playwright 1.58:** Browser automation for authenticated scraping; superior to Selenium for handling Disney's JS-heavy login flow
- **SQLite 3.x:** Single-user file-based DB, zero configuration, perfect for personal dashboards
- **React 19.2 + TypeScript 5.9:** Stable frontend stack you already use; React 19 brings automatic memoization
- **Recharts 3.7:** React-native SVG charts for point timelines and cost visualizations
- **TanStack Query 5.90:** Automatic caching and background refetching for server state
- **Tailwind CSS 4.x:** 5x faster builds than v3, first-party Vite plugin, pairs with shadcn/ui components
- **SQLAlchemy 2.0.46 + Alembic:** Industry-standard ORM with async support, essential for schema evolution

**Critical version notes:**
- Do NOT use TypeScript 7 (Go rewrite in preview, JS emit incomplete)
- Do NOT use Vite 8 beta (wait for Rolldown bundler stable)
- Do NOT use Python 3.14 beta (stick with 3.12 stable)

### Expected Features

Research identified a clear split between table stakes (what every DVC tool has), differentiators (what makes this tool unique), and anti-features (commonly requested but problematic).

**Must have (table stakes):**
- Point balance tracking per contract with use year awareness
- Use year timeline showing banking deadlines and expiration dates
- Point cost calculator (resort + room + dates → points)
- Resale restriction filtering (critical for target user)
- "What can I afford?" query (given points and dates, show bookable options)
- Reservation tracking with key date reminders

**Should have (competitive differentiators):**
- DVC website scraping for auto-populated data (killer feature—NO competitor does this)
- Point timeline calculator ("pick future date, see available points" with banking/borrowing projections)
- What-if scenario planning (model banking/borrowing decisions before committing)
- Trip explorer with full constraint awareness (resale restrictions + point availability + multi-contract pooling)
- Seasonal cost heatmap (calendar visualization of point costs)

**Defer (v2+):**
- Point optimization suggestions ("shift check-in to save 12 points")
- Multi-contract point pooling visualization
- Full trip explorer (requires all underlying systems mature)
- Calendar integration (iCal export)

**Anti-features (explicitly NOT building):**
- Multi-user/family sharing (10x complexity, zero benefit for personal tool)
- Real-time availability checking (competes with DVCapp.com, legally gray)
- Automated booking (violates Disney ToS, risks account suspension)
- Point rental marketplace (massive product in itself)
- Mobile native apps (responsive web PWA is sufficient)

### Architecture Approach

The architecture follows a strict scrape-store-calculate decoupled pipeline. The scraper writes raw data to the database and never calls business logic. The calculation engine reads from the database and computes derived values on demand using pure functions with no database dependencies. The frontend is a pure display layer calling the API. This isolation is critical because scraping is the most fragile component—when it breaks, the calculation engine and UI continue functioning with cached data.

**Major components:**
1. **Scraping Layer** (backend/scraper/) — Playwright-based authentication and extraction; isolated from business logic so breakage doesn't cascade
2. **Calculation Engine** (backend/engine/) — Pure functions encoding DVC rules (banking windows, use year math, resale restrictions); independently testable with no I/O dependencies
3. **Data Layer** (SQLite via SQLAlchemy) — Stores contracts, point allocations, reservations, and point charts as versioned data
4. **API Layer** (FastAPI routes) — Orchestrates DB reads + engine calculations + JSON serialization
5. **Presentation Layer** (React components) — Dashboard, trip explorer, reservation tracker; displays pre-computed results from API

**Key patterns:**
- Point charts stored as static JSON files (not scraped)—they change once per year and are publicly available
- Session persistence to minimize Disney logins (scraping runs on-demand or manually, not scheduled cron)
- Always show "last synced" timestamp; app works 100% with stale data
- Manual data entry fallback for when scraping breaks

### Critical Pitfalls

1. **Hardcoding DVC business rules that change annually** — Point charts, season names, and view categories change every year. Disney replaced 5 seasons with 7 travel periods in 2021; renamed "Standard View" to "Resort View" in 2026. Solution: Store charts as versioned data keyed by resort + year. Build staleness check for when new charts are released.

2. **Scraping Disney's authenticated site without resilience strategy** — Disney blocks automated access (May 2023 2FA rollout broke all scrapers, DMCA takedowns against dining scrapers). Login involves JS rendering, redirects, dynamic tokens, and bot detection. Solution: Accept fragility as architectural constraint. Use browser automation (Playwright), scrape-then-cache with timestamps, manual "refresh" not cron, scrape health monitoring, extremely low frequency.

3. **Incorrect point timeline calculations** — "Pick a future date, see points" involves 6+ buckets per contract (current year, banked, borrowed, each with different expiration dates). Multiple contracts on different use years create combinatorial complexity. Solution: Model each point allocation as first-class entity with status/expiration. Never aggregate without checking temporal constraints. Build as state machine with exhaustive edge-case testing.

4. **Ignoring resale contract restrictions in trip explorer** — Restrictions depend on when resort opened AND when contract was purchased. Original 14 resorts pre-2019: resale can book any of those 14. Post-2019 resorts (Riviera, Cabins, DLH): resale can ONLY book home resort. Solution: Build explicit can_book_at(contract, resort) function encoding all rules. Filter all trip results through this.

5. **Building app around scraping instead of local data** — Treating DVC website as live API creates brittle dependency. When scraper breaks, app becomes unusable. Solution: Scraping is import mechanism, not data source. App reads from local DB. 100% functional with zero scraping. Allow manual data entry as fallback.

## Implications for Roadmap

Based on research, suggested phase structure emphasizes building from data model → calculation engine → UI, deferring scraping until core is solid.

### Phase 1: Foundation - Data Models & Static Data
**Rationale:** Everything depends on correct data shapes. The contract/point allocation model is the foundation. Get this wrong and recovery cost is HIGH (schema migration + recalculation). Point charts are static data published annually—load them first before building anything that needs them.

**Delivers:**
- Contract, reservation, point balance, and point chart data models
- SQLite database with schema and migrations (Alembic)
- Point chart data for current/upcoming year (manual entry of JSON files)
- Seed database with actual contract data (manual entry)
- Database able to describe DVC ownership in structured form

**Addresses features:**
- Point balance tracking per contract (data model only)
- Use year timeline (data model only)
- Point charts ingestion (static data)

**Avoids pitfalls:**
- Pitfall 1 (hardcoded rules) — charts versioned from day one
- Pitfall 3 (bad point math) — model allocations as first-class entities with temporal properties
- Pitfall 4 (resale restrictions) — contract model includes purchase_type, purchase_date, home_resort

**Research flag:** Standard data modeling patterns. Skip research-phase; proceed with implementation.

---

### Phase 2: Calculation Engine
**Rationale:** Core business logic must be correct before building UI. Pure functions with no I/O means you can test exhaustively with seed data from Phase 1. This is the intellectual property of the app—DVC domain rules encoded in software. Build it second because it can be validated independently before adding complexity.

**Delivers:**
- Point availability calculator (given contracts + date, compute available points per contract)
- Use year date math (banking deadlines, expiration dates, use year windows)
- Booking eligibility resolver (resale restriction filtering)
- Trip cost calculator (given resort + room + dates, compute point cost)
- Comprehensive unit test suite with edge cases

**Addresses features:**
- Use year timeline with banking/borrowing (calculation only)
- Point cost calculator (core math)
- Resale restriction filtering (core logic)
- "What can I afford?" query (calculation support)

**Avoids pitfalls:**
- Pitfall 3 (incorrect timeline math) — pure functions with exhaustive tests before UI
- Pitfall 4 (missing resale restrictions) — explicit can_book_at() function
- Pitfall 2 (embedding rules in frontend) — all DVC logic server-side

**Research flag:** Standard calculation patterns. Skip research-phase; TDD approach with known test cases.

---

### Phase 3: API & Manual Data Entry
**Rationale:** API wraps calculation engine for frontend consumption. Manual data entry enables testing the entire stack without scraping and provides critical fallback when scraping breaks. Build this before frontend so you can test API with curl/Postman.

**Delivers:**
- FastAPI routes for dashboard, trip explorer, reservations
- Manual data entry endpoints (contracts, point balances, reservations)
- Data validation with Pydantic models
- API documentation (FastAPI auto-generates)

**Addresses features:**
- Point balance tracking (with manual entry)
- Reservation tracking (CRUD)
- Manual data entry fallback (critical for scraper failures)

**Avoids pitfalls:**
- Pitfall 5 (scraping dependency) — app works 100% with manual entry before scraper exists

**Research flag:** Standard REST API patterns. Skip research-phase; proceed with FastAPI conventions.

---

### Phase 4: Frontend Dashboard & Trip Explorer
**Rationale:** Display layer comes after API is validated. Building frontend on top of tested calculations means you're rendering real results, not mock data. Dashboard and trip explorer are the two primary user workflows.

**Delivers:**
- Dashboard page (point balances, upcoming reservations, banking deadlines, warnings)
- Trip Explorer page (date picker, results grid showing eligible resorts with costs)
- Reservation tracker page
- Responsive layout (Tailwind + shadcn/ui)
- Date formatting and point display utilities

**Addresses features:**
- Dashboard visualization (timeline, warnings)
- Trip explorer interface
- "What can I afford?" query (UI)
- Seasonal cost heatmap (stretch goal for this phase)

**Avoids pitfalls:**
- UX pitfall: showing points without temporal context — always display with date qualifiers
- UX pitfall: hiding data staleness — show "last synced" (manual entry timestamp)

**Research flag:** Standard React patterns. Skip research-phase; use NephSched patterns.

---

### Phase 5: Web Scraping Integration
**Rationale:** Most fragile component built last. All other layers work with manual data until scraper is ready. This means even if scraping never works perfectly, you still have a useful tool. Scraping depends on Disney's site which you don't control—deferring reduces project risk.

**Delivers:**
- Playwright authentication with Disney member portal
- Point balance extraction from member dashboard
- Reservation data extraction
- Session persistence (save cookies, minimize re-login)
- Scrape scheduler (manual trigger + optional scheduled)
- Scrape health monitoring and failure detection
- UI integration: "sync now" button, "last synced" display with data age warnings

**Addresses features:**
- DVC website scraping (killer feature)
- Automated point balance updates
- Automated reservation tracking

**Avoids pitfalls:**
- Pitfall 2 (fragile scraping) — built as isolated layer with health checks
- Pitfall 5 (scraping dependency) — app already works without it
- Security: credentials in OS keychain, not plaintext; sanitized logs

**Research flag:** HIGH — scraping authenticated Disney site is complex. Needs research-phase for:
- Current Disney login flow (2FA handling, session tokens)
- Member portal DOM structure (point balance selectors, reservation data)
- Anti-bot detection techniques
- Session persistence patterns

---

### Phase 6: Advanced Features (Point Timeline Calculator)
**Rationale:** Differentiating feature requiring all underlying systems to be mature. Forward-looking point projection with banking/borrowing is complex—build only when calculation engine is proven solid.

**Delivers:**
- Point timeline calculator ("pick future date, see points available")
- What-if scenario planning (model banking/borrowing before committing)
- Multi-contract point pooling visualization
- Enhanced dashboard with timeline projections

**Addresses features:**
- Point timeline calculator (core differentiator)
- What-if scenario planning
- Multi-contract pooling visualization

**Avoids pitfalls:**
- Pitfall 3 (timeline math errors) — built on battle-tested calculation engine

**Research flag:** Standard visualization patterns. Skip research-phase; build on Phase 2 engine.

---

### Phase Ordering Rationale

- **Data model first:** Schema changes are expensive. Getting contract/point allocation structure right from day one avoids HIGH-cost recovery later.
- **Engine before UI:** Pure functions can be exhaustively tested with seed data. Building correct calculations before adding UI complexity de-risks the core value proposition.
- **API before frontend:** Testable with curl; validates calculations in isolation.
- **Manual entry before scraping:** De-risks the project. Even if scraping fails completely, you have a working tool.
- **Scraping last:** Most fragile, least controllable component. All other layers already work without it. Disney can change their site; your data model won't.
- **Advanced features deferred:** Point timeline calculator requires mature calculation engine. Build it after core features are validated.

This ordering follows ARCHITECTURE.md's build order suggestion and addresses all critical pitfalls identified in research.

### Research Flags

**Phases likely needing deeper research during planning:**

- **Phase 5 (Scraping):** HIGH priority for research-phase
  - Disney member portal structure changes frequently
  - Need to map current login flow, DOM structure, session handling
  - Anti-bot detection may require playwright-stealth
  - 2FA handling needs investigation

**Phases with standard patterns (skip research-phase):**

- **Phase 1 (Data Models):** Standard SQLAlchemy patterns
- **Phase 2 (Calculation Engine):** Pure functions, TDD approach with known DVC rules
- **Phase 3 (API):** Standard FastAPI REST patterns
- **Phase 4 (Frontend):** React patterns proven in NephSched
- **Phase 6 (Timeline Calculator):** Builds on Phase 2 engine, standard visualization

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All recommended technologies verified at current versions; proven in similar projects (NephSched); extensive official documentation |
| Features | MEDIUM-HIGH | Table stakes validated via comprehensive competitor analysis (5+ existing tools); differentiators derived from identified gaps; DVC domain rules well-documented in official sources |
| Architecture | MEDIUM | Scrape-store-calculate pattern is standard for web scraping projects; calculation engine approach follows functional programming best practices; uncertainty lies in Disney site fragility (inherently unpredictable) |
| Pitfalls | MEDIUM-HIGH | DVC domain pitfalls (banking rules, resale restrictions) well-documented in community sources; scraping fragility validated by historical Disney anti-scraper actions; point math complexity identified via multi-contract edge cases |

**Overall confidence:** MEDIUM-HIGH

Research is strong on what to build (features), how to build it (stack + architecture), and what to avoid (pitfalls). Primary uncertainty is scraping layer fragility—this is inherent to the problem domain and cannot be eliminated, only mitigated through architecture.

### Gaps to Address

- **Disney member portal structure:** Research provides general scraping guidance but current DOM structure, selectors, and API endpoints need live investigation during Phase 5 planning. This is expected—Disney's site changes frequently.

- **DVC borrowing policy:** Currently 100% of next year's points, but was 50% pre-pandemic. Research notes this may revert. During Phase 2 implementation, make borrowing percentage configurable (not hardcoded) to handle future policy changes.

- **Point chart format variations by resort:** Research confirms 7 seasons, weekday/weekend pricing, but details of view categories vary per resort. During Phase 1, validate point chart JSON schema accommodates all resort-specific variations (some have 10+ view types, others have 3).

- **Holding account points:** Mentioned in PITFALLS (points from late cancellations with restricted use) but not fully modeled in recommended data structures. Address in Phase 1 schema: add point allocation type (normal/banked/borrowed/holding) with associated constraints.

- **Cross-contract point pooling limitations:** PITFALLS notes "you cannot combine points from contracts with different Use Years without a transfer (requires calling Member Services)." This restriction not fully modeled in calculation engine design. Verify during Phase 2: trip cost calculator should flag when a booking would require cross-UY pooling.

## Sources

### Primary (HIGH confidence)
- FastAPI Official Docs & PyPI (v0.128.5 confirmed)
- React Official Docs (v19.2 confirmed)
- Playwright Python Docs (v1.58.0 confirmed)
- Disney Vacation Club Official: Points Charts, Banking/Borrowing Rules, Use Year System
- DVC Field Guide: Banking Deadlines, Use Year Explanation, Banking/Borrowing How-To
- SQLAlchemy Official Docs (v2.0.46 confirmed)
- Tailwind CSS v4 Official Blog & Docs

### Secondary (MEDIUM confidence)
- DVCHelp.com: Competitor feature analysis, point calculator patterns
- DVC Toolkit / DVC Planner / D Point apps: Feature comparison via App Store listings
- DVCinfo & DISboards: Community consensus on DVC domain rules, user pain points
- DVC Resale Market / DVC Shop / Fidelity Real Estate: Resale restriction rules
- DVC Fan / wdwinfo.com: Point chart structure and historical changes
- JetBrains Python Survey 2025: FastAPI adoption data (38% developers)
- LogRocket / Better Stack: React library comparisons (Recharts, TanStack Router vs React Router)

### Tertiary (LOW confidence, needs validation)
- Orlando Sentinel: Disney scraping legal precedent (2015 dining scraper lawsuit)—demonstrates Disney's anti-scraping stance but details may be outdated
- ZenRows / ShoppingScraper: General scraping best practices for bot detection and data freshness—not DVC-specific, apply with caution

---
*Research completed: 2026-02-09*
*Ready for roadmap: yes*
