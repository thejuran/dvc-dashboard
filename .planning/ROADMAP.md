# Roadmap: DVC Dashboard

## Shipped Milestones

- [x] **v1.0** -- Data foundation, calculations & reservations, dashboard & trip explorer (3 phases, 9 plans, 18 requirements) -- [archive](milestones/v1.0-ROADMAP.md)
- [x] **v1.1** -- Docker self-hosting, booking impact preview, what-if scenarios, booking window alerts, cost heatmap (4 phases, 9 plans, 23 requirements) -- [archive](milestones/v1.1-ROADMAP.md)

## v1.2 Harden & Open Source

**Milestone Goal:** Harden code quality, security, and UX polish across the existing app, then publish as a GPL v3 open-source project with full documentation and CI/CD.

**Phases:** 3 (phases 8-10)
**Requirements:** 21

### Phases

- [x] **Phase 8: Code Hardening** - Structured errors, input validation, error boundaries, test coverage, cleanup
- [x] **Phase 9: UX & Security Polish** - Loading states, error messages, mobile responsiveness, secrets audit, dependency audit
- [ ] **Phase 10: Open Source & Documentation** - Public repo, LICENSE, README, CI/CD, setup guide, architecture docs, API reference

### Phase Details

#### Phase 8: Code Hardening
**Goal**: Every API call returns structured errors, every input is validated, every failure is caught gracefully, and all code paths are tested
**Depends on**: Nothing (first phase of v1.2)
**Requirements**: QUAL-01, QUAL-02, QUAL-03, QUAL-04, QUAL-05, QUAL-06, SEC-02
**Success Criteria** (what must be TRUE):
  1. Every API endpoint returns errors in a consistent JSON structure with status code, error type, and human-readable message
  2. Submitting invalid data to any form or API endpoint produces a clear validation error (not a 500 or unhandled exception)
  3. A React component throwing an error does not crash the entire app -- the error boundary catches it and shows a recovery message
  4. Tests pass for edge cases: 0 contracts, 0 points, expired use years, boundary dates, and key user flows (create contract, make reservation, check availability)
  5. No lint warnings or dead code remain in either frontend or backend
**Plans**: 5 plans

Plans:
- [x] 08-01-PLAN.md -- Backend structured error infrastructure + frontend API layer update
- [x] 08-02-PLAN.md -- Backend input validation hardening across all endpoints
- [x] 08-03-PLAN.md -- Frontend error boundaries + form validation with inline errors
- [x] 08-04-PLAN.md -- Test coverage expansion: edge cases + integration tests
- [x] 08-05-PLAN.md -- Lint cleanup + dead code removal (ruff + eslint)

#### Phase 9: UX & Security Polish
**Goal**: The app feels polished on any device and contains no security liabilities that would embarrass an open-source release
**Depends on**: Phase 8 (error handling must exist before UX can surface it properly)
**Requirements**: UX-01, UX-02, UX-03, UX-04, SEC-01, SEC-03
**Success Criteria** (what must be TRUE):
  1. Every page that loads data shows a skeleton or spinner until data arrives -- no blank flashes or layout shifts
  2. All error conditions show user-friendly messages (not raw stack traces, JSON blobs, or "undefined")
  3. All pages render correctly and are usable on a 375px mobile viewport and tablet
  4. Pages with no data (no contracts, no reservations, no point charts) show helpful empty states with guidance on what to do
  5. No credentials, secrets, or API keys exist anywhere in committed code, and all dependencies are pinned with no known vulnerabilities
**Plans**: 3 plans

Plans:
- [x] 09-01-PLAN.md -- Loading skeletons, error alerts with retry, and empty states across all pages
- [x] 09-02-PLAN.md -- Mobile responsive layout with hamburger sidebar and viewport fixes
- [x] 09-03-PLAN.md -- Secrets audit, .gitignore hardening, dependency pinning and vulnerability audit

#### Phase 10: Open Source & Documentation
**Goal**: A stranger can discover the project on GitHub, understand what it does, clone it, run it, and contribute back -- all from the repo alone
**Depends on**: Phase 9 (code must be hardened and polished before public release)
**Requirements**: OSS-01, OSS-02, OSS-03, OSS-04, OSS-05, DOCS-01, DOCS-02, DOCS-03
**Success Criteria** (what must be TRUE):
  1. Public GitHub repo exists at `dvc-dashboard` with GPL v3 LICENSE and a README that includes project description, screenshots, feature list, and quickstart instructions
  2. A new developer can clone the repo, copy `.env.example`, run `docker compose up`, and have the app working -- following only the setup guide
  3. CONTRIBUTING.md documents dev setup, code style, and PR process so a contributor knows how to submit changes
  4. GitHub Actions CI runs tests, lint, and Docker build on every PR -- and it passes on the current codebase
  5. Architecture document and API reference exist so a developer can understand the system structure and all REST endpoints without reading source code
**Plans**: 3 plans

Plans:
- [ ] 10-01-PLAN.md -- GPL v3 LICENSE, README with features/quickstart, CONTRIBUTING.md
- [ ] 10-02-PLAN.md -- GitHub Actions CI pipeline (tests, lint, Docker build)
- [ ] 10-03-PLAN.md -- Technical documentation (setup guide, architecture, API reference)

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 8. Code Hardening | v1.2 | 5/5 | ✓ Complete | 2026-02-12 |
| 9. UX & Security Polish | v1.2 | 3/3 | ✓ Complete | 2026-02-12 |
| 10. Open Source & Documentation | v1.2 | 0/3 | Not started | - |

---
*Roadmap created: 2026-02-11*
*Last updated: 2026-02-12*
