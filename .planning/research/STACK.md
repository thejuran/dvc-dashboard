# Stack Research

**Domain:** Personal DVC (Disney Vacation Club) points tracking and trip planning web dashboard
**Researched:** 2026-02-09
**Confidence:** HIGH

## Recommended Stack

This is a single-user personal dashboard that scrapes authenticated external data, runs time-based financial calculations (point banking/borrowing across use years), and presents interactive visualizations. The architecture mirrors your NephSched monorepo pattern (FastAPI backend + React/Vite frontend) because it works and you already know it.

### Core Technologies

| Technology | Version | Purpose | Why Recommended | Confidence |
|------------|---------|---------|-----------------|------------|
| **Python** | 3.12+ | Backend runtime | Required by FastAPI 0.128.x. Python 3.9 is minimum; 3.12 gives best performance and type hint support. Do NOT use 3.14 yet (beta). | HIGH |
| **FastAPI** | 0.128.5 | Backend API framework | Native async/await for non-blocking scraping tasks. Built-in Pydantic validation. You already know it from NephSched. 38% Python developer adoption in 2025, up 40% YoY. | HIGH |
| **Pydantic** | 2.12.x | Data validation/models | Ships with FastAPI. Model DVC contracts, point allocations, and reservation data as typed Pydantic models. Rust-core v2 is 5-50x faster than v1. | HIGH |
| **React** | 19.2.x | Frontend UI framework | Stable, you know it from NephSched. React 19 brings `use()` hook, automatic memoization via React Compiler. No reason to switch. | HIGH |
| **TypeScript** | 5.9.x | Frontend type safety | Use 5.9 stable. TypeScript 7 (Go-native rewrite) is in preview but NOT production-ready -- JS emit pipeline incomplete. Avoid 6.0 (transitional). | HIGH |
| **Vite** | 7.x | Frontend build tool | Use Vite 7 stable. Vite 8 beta available but uses Rolldown (new bundler) -- wait for stable. You already use Vite in NephSched. | MEDIUM |
| **SQLite** | 3.x | Database | Single user, no concurrency needs, zero configuration, no server process. File-based means trivial backups (copy one file). Perfectly suited for personal dashboards. | HIGH |

### Backend Libraries

| Library | Version | Purpose | Why | Confidence |
|---------|---------|---------|-----|------------|
| **SQLAlchemy** | 2.0.46 | ORM / database toolkit | Industry standard Python ORM. Async support via `aiosqlite` driver. Type-safe query construction. You know it from NephSched. | HIGH |
| **aiosqlite** | 0.21.x | Async SQLite driver | Enables SQLAlchemy async engine with SQLite (`sqlite+aiosqlite:///`). Non-blocking DB access in FastAPI's async handlers. | HIGH |
| **Alembic** | 1.18.3 | Database migrations | Official SQLAlchemy migration tool. Auto-generates migration scripts from model changes. Essential even for personal projects -- schema WILL evolve. | HIGH |
| **Playwright** | 1.58.0 | Browser automation / scraping | DVC member website requires JavaScript rendering and authenticated sessions. Playwright handles login flows, session persistence, and JS-heavy pages. Headless Chromium. Superior to Selenium (faster, more reliable, better API). | HIGH |
| **httpx** | 0.28.x | HTTP client | Async-native HTTP client for API calls and lightweight requests. Drop-in replacement for `requests` with async support. Use for non-browser HTTP calls (point charts, public data). | MEDIUM |
| **BeautifulSoup4** | 4.12.x | HTML parsing | Parse HTML from Playwright page sources. Mature, handles malformed markup gracefully. Use for extracting structured data from scraped pages. | HIGH |
| **APScheduler** | 3.11.2 | Task scheduling | Periodic scraping jobs (daily point sync, availability checks). In-process scheduler -- no Redis/RabbitMQ needed. Perfect for single-user apps. Celery is massive overkill here. | HIGH |
| **python-dateutil** | 2.9.x | Date calculations | DVC use years, banking windows (expiration dates), and borrowing calculations require robust relative date arithmetic. `relativedelta` handles "11 months from use year start" cleanly. | HIGH |

### Frontend Libraries

| Library | Version | Purpose | Why | Confidence |
|---------|---------|---------|-----|------------|
| **Recharts** | 3.7.0 | Data visualization | React-native component API (not a wrapper). SVG-based charts with smooth animations. Point timeline charts, availability heatmaps, cost comparisons. Simpler API than Nivo, adequate for dashboard-scale data (not big data). | HIGH |
| **TanStack Query** | 5.90.x | Server state / data fetching | Automatic caching, background refetching, loading/error states. Eliminates manual fetch/loading/error boilerplate. Pairs perfectly with FastAPI endpoints. | HIGH |
| **React Router** | 7.x | Client-side routing | Stable, battle-tested, you know it. TanStack Router has better type safety but steeper learning curve and rapidly evolving API (v1.158 with frequent releases = churn). For a personal dashboard with 4-5 routes, React Router is sufficient. | MEDIUM |
| **Tailwind CSS** | 4.x | Utility-first styling | v4.0 rewrote the engine: 5x faster builds, CSS-first config (no `tailwind.config.js`), automatic content detection. First-party Vite plugin. | HIGH |
| **shadcn/ui** | latest | UI components | Copy-paste components (you own the code, no dependency). Built on Radix UI + Tailwind. Tables, cards, dialogs, date pickers -- everything a dashboard needs without building from scratch. | HIGH |
| **date-fns** | 4.1.0 | Date manipulation | Tree-shakable (import only what you use). 100% TypeScript. 200+ functions. Use for displaying dates, formatting use year ranges, calculating days until banking deadlines. | HIGH |
| **Zustand** | 5.0.11 | Client state management | Minimal boilerplate, tiny bundle (1.1kB). For UI state only: selected filters, sidebar state, active contract selection. TanStack Query handles all server state -- Zustand fills the small gap for client-only state. | MEDIUM |

### Development Tools

| Tool | Purpose | Notes | Confidence |
|------|---------|-------|------------|
| **pytest** | Backend testing | You already use it in NephSched. pytest-asyncio for async test support. | HIGH |
| **Ruff** | Python linting + formatting | Replaces flake8 + black + isort. Single tool, Rust-based, 10-100x faster. Industry standard for new Python projects in 2025+. | HIGH |
| **ESLint** | Frontend linting | Use flat config (eslint.config.js). Pairs with TypeScript ESLint for type-aware rules. | HIGH |
| **Prettier** | Frontend formatting | Code formatting for JS/TS/CSS/JSON. Opinionated = no debates. | HIGH |

## Installation

```bash
# Backend (Python)
pip install "fastapi[standard]>=0.128.0" \
  sqlalchemy>=2.0.46 \
  aiosqlite>=0.21.0 \
  alembic>=1.18.0 \
  playwright>=1.58.0 \
  httpx>=0.28.0 \
  beautifulsoup4>=4.12.0 \
  apscheduler>=3.11.0 \
  python-dateutil>=2.9.0 \
  pydantic>=2.12.0

# Install Playwright browsers
playwright install chromium

# Backend dev dependencies
pip install pytest pytest-asyncio ruff

# Frontend
npm create vite@latest frontend -- --template react-ts

# Frontend core
npm install react@^19.2.0 react-dom@^19.2.0 \
  recharts@^3.7.0 \
  @tanstack/react-query@^5.90.0 \
  react-router-dom@^7.0.0 \
  date-fns@^4.1.0 \
  zustand@^5.0.0

# Frontend UI
npm install tailwindcss@^4.0.0 \
  @tailwindcss/vite

# shadcn/ui (init then add components as needed)
npx shadcn@latest init
npx shadcn@latest add table card button dialog calendar

# Frontend dev dependencies
npm install -D typescript@^5.9.0 \
  eslint @eslint/js \
  typescript-eslint \
  prettier
```

## Alternatives Considered

| Recommended | Alternative | Why Not the Alternative |
|-------------|-------------|------------------------|
| **FastAPI** | Django | Django's ORM, admin, and auth are overkill for single-user. FastAPI's async-native design is better for scraping + API workloads. You already know FastAPI. |
| **FastAPI** | Flask | Flask lacks native async, auto-docs, and Pydantic validation. FastAPI is Flask's modern successor for API-first projects. |
| **SQLite** | PostgreSQL | PostgreSQL requires a server process, adds deployment complexity (Docker/Railway addon). Single-user app with modest data volumes gains nothing from Postgres. SQLite file = trivial backup/restore. |
| **Recharts** | Nivo | Nivo is more feature-rich (Canvas + SVG + HTML rendering) but has a steeper learning curve and heavier bundle. Recharts' simpler component API is sufficient for dashboard charts. |
| **Recharts** | Chart.js (react-chartjs-2) | Canvas-based rendering makes individual element customization harder. React integration is a wrapper, not native components. Recharts' declarative JSX API is more React-idiomatic. |
| **React Router** | TanStack Router | TanStack Router has superior type safety but 158 releases in v1 = rapid churn. For a 4-5 route personal dashboard, React Router's stability wins. Revisit if building something larger. |
| **Tailwind CSS** | CSS Modules / Styled Components | Tailwind v4 with shadcn/ui provides a complete design system. CSS Modules require building everything from scratch. Styled Components adds runtime overhead and is declining in adoption. |
| **APScheduler** | Celery | Celery requires Redis/RabbitMQ broker, worker processes, and significant configuration. APScheduler runs in-process with zero external dependencies. Celery is for distributed systems, not personal dashboards. |
| **httpx** | requests | requests is sync-only. httpx provides the same familiar API with async support, HTTP/2, and 7x better performance for concurrent requests. |
| **Zustand** | Redux / Redux Toolkit | Redux is overengineered for a personal dashboard. 90%+ of state is server state (handled by TanStack Query). Zustand covers the remaining UI state with 5 lines of code. |
| **BeautifulSoup4** | selectolax | selectolax is faster but less mature, smaller community, and less tolerant of malformed HTML. BS4 is battle-tested for scraping. Performance difference irrelevant at this scale (parsing a few pages, not millions). |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Selenium** | Slower, heavier, worse API than Playwright. Legacy tool. Playwright is its modern replacement with auto-wait, better selectors, and native async. | Playwright |
| **Scrapy** | Framework designed for large-scale crawling with spiders, pipelines, middleware. Massive overkill for scraping one authenticated website. Doesn't handle JS rendering without plugins. | Playwright + BeautifulSoup4 |
| **Next.js** | Server-side rendering adds complexity with zero benefit for a single-user dashboard. No SEO needed. Deployment is more complex. Vite + React SPA is simpler and faster to develop. | Vite + React SPA |
| **MongoDB** | NoSQL is wrong for relational DVC data (contracts have points, points have use years, reservations reference rooms at resorts). Relational queries are natural here. | SQLite via SQLAlchemy |
| **Moment.js** | Deprecated by its own maintainers. Mutable API causes bugs. 67kB bundle (not tree-shakable). | date-fns |
| **Redux** | Boilerplate-heavy, steep learning curve, unnecessary for this app size. TanStack Query handles server state; Zustand handles the rest. | TanStack Query + Zustand |
| **Create React App (CRA)** | Officially deprecated. Unmaintained. Slow builds. | Vite |
| **Streamlit / Dash** | Python-only dashboards with limited interactivity and customization. No real component model. Good for data science prototypes, wrong for a real web app with custom UI. | React + FastAPI |
| **TypeScript 7** | Native Go-based compiler is in preview but JS emit is incomplete. Not a drop-in replacement yet. | TypeScript 5.9 |

## Stack Patterns by Variant

**If DVC website blocks automated login (bot detection):**
- Add `playwright-stealth` plugin to mask automation fingerprints
- Consider storing session cookies and refreshing them manually if detection is aggressive
- Fallback: manual data entry with CSV import as a backup data pipeline

**If you want mobile access later:**
- Keep the React SPA responsive (Tailwind handles this well)
- No need for React Native -- a responsive web dashboard accessed via mobile browser is sufficient for checking points
- Because Tailwind v4 is mobile-first by default

**If data volume grows (multiple family members, historical data):**
- SQLite handles databases up to 281 TB. You will not hit its limits with DVC data.
- If concurrent access becomes needed (multiple users), migrate to PostgreSQL. SQLAlchemy makes this a connection string change.

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| FastAPI 0.128.x | Pydantic 2.12.x | FastAPI bundles Pydantic. Use v2 models (not v1 compatibility mode). |
| FastAPI 0.128.x | Python 3.9+ | Requires 3.9 minimum. Use 3.12 for best experience. |
| SQLAlchemy 2.0.46 | aiosqlite 0.21.x | Async SQLite via `sqlite+aiosqlite:///` connection string. |
| SQLAlchemy 2.0.46 | Python 3.10+ | v2.0.46 dropped Python 3.9. Aligns with Python 3.12 recommendation. |
| SQLAlchemy 2.0.46 | Alembic 1.18.x | Alembic is maintained by the same author. Always compatible with latest SQLAlchemy 2.0. |
| React 19.2.x | TypeScript 5.9 | Full support. React 19 types ship with `@types/react`. |
| Recharts 3.7.x | React 19.x | Recharts 3.x supports React 18+. Compatible with React 19. |
| TanStack Query 5.x | React 18+ | Requires React 18 minimum. Works with React 19. |
| Tailwind CSS 4.x | Vite 7.x | First-party `@tailwindcss/vite` plugin. Native integration. |
| shadcn/ui | Tailwind 4.x | shadcn/ui has explicit Tailwind v4 support and migration guide. |

## Sources

- [FastAPI PyPI](https://pypi.org/project/fastapi/) -- version 0.128.5 confirmed (HIGH)
- [FastAPI Official Docs](https://fastapi.tiangolo.com/) -- capabilities and features (HIGH)
- [React Versions](https://react.dev/versions) -- React 19.2 confirmed (HIGH)
- [TypeScript 5.9 Docs](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html) -- stable release confirmed (HIGH)
- [Vite Releases](https://vite.dev/releases) -- Vite 7.x, Vite 8 beta status (HIGH)
- [Recharts npm](https://www.npmjs.com/package/recharts) -- v3.7.0 confirmed (HIGH)
- [TanStack Query npm](https://www.npmjs.com/package/@tanstack/react-query) -- v5.90.x confirmed (HIGH)
- [Playwright PyPI](https://pypi.org/project/playwright/) -- v1.58.0 confirmed (HIGH)
- [SQLAlchemy Downloads](https://www.sqlalchemy.org/download.html) -- v2.0.46 confirmed (HIGH)
- [Alembic PyPI](https://pypi.org/project/alembic/) -- v1.18.3 confirmed (HIGH)
- [Pydantic Changelog](https://docs.pydantic.dev/latest/changelog/) -- v2.12.x confirmed (HIGH)
- [Tailwind CSS v4 Blog](https://tailwindcss.com/blog/tailwindcss-v4) -- v4.0 features confirmed (HIGH)
- [Zustand npm](https://www.npmjs.com/package/zustand) -- v5.0.11 confirmed (HIGH)
- [date-fns npm](https://www.npmjs.com/package/date-fns) -- v4.1.0 confirmed (HIGH)
- [APScheduler PyPI](https://pypi.org/project/APScheduler/) -- v3.11.2 confirmed (MEDIUM)
- [JetBrains Python Survey 2025](https://blog.jetbrains.com/pycharm/2025/09/the-most-popular-python-frameworks-and-libraries-in-2025-2/) -- FastAPI adoption data (MEDIUM)
- [LogRocket React Chart Libraries](https://blog.logrocket.com/best-react-chart-libraries-2025/) -- Recharts vs alternatives (MEDIUM)
- [Better Stack Router Comparison](https://betterstack.com/community/comparisons/tanstack-router-vs-react-router/) -- Router tradeoffs (MEDIUM)
- [Oxylabs httpx vs requests](https://oxylabs.io/blog/httpx-vs-requests-vs-aiohttp) -- HTTP client comparison (MEDIUM)
- [Leapcell APScheduler vs Celery](https://leapcell.io/blog/scheduling-tasks-in-python-apscheduler-vs-celery-beat) -- Scheduler comparison (MEDIUM)
- [DataCamp SQLite vs PostgreSQL](https://www.datacamp.com/blog/sqlite-vs-postgresql-detailed-comparison) -- Database comparison (MEDIUM)

---
*Stack research for: DVC Points Dashboard*
*Researched: 2026-02-09*
