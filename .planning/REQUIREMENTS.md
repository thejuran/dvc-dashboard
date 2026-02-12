# Requirements: DVC Dashboard

**Defined:** 2026-02-11
**Core Value:** For any future date, clearly show available points across all contracts and what resorts/rooms those points can actually book.

## v1.2 Requirements

Requirements for v1.2 Harden & Open Source. Each maps to roadmap phases.

### Code Quality

- [ ] **QUAL-01**: User sees consistent error responses from all API endpoints (structured error format)
- [ ] **QUAL-02**: All backend API endpoints have input validation with clear error messages
- [ ] **QUAL-03**: Frontend components use error boundaries to catch and display failures gracefully
- [ ] **QUAL-04**: Test coverage expanded to cover edge cases (0 contracts, 0 points, expired use years, boundary dates)
- [ ] **QUAL-05**: Dead code removed and lint warnings resolved across both frontend and backend
- [ ] **QUAL-06**: Integration tests verify key user flows end-to-end (create contract, make reservation, check availability)

### Security

- [ ] **SEC-01**: No credentials, secrets, or API keys exist in committed code (`.env.example` provided instead)
- [ ] **SEC-02**: All API inputs validated and sanitized server-side before processing
- [ ] **SEC-03**: Dependencies audited for known vulnerabilities and pinned to specific versions

### UX Polish

- [ ] **UX-01**: All data-loading views show skeleton or spinner states while fetching
- [ ] **UX-02**: All error conditions display user-friendly messages (not raw stack traces)
- [ ] **UX-03**: All pages render correctly on mobile viewport (375px+) and tablet
- [ ] **UX-04**: Empty states handled gracefully (no contracts, no reservations, no point charts)

### Open Source

- [ ] **OSS-01**: New public GitHub repo `dvc-dashboard` created with GPL v3 LICENSE file
- [ ] **OSS-02**: README includes project description, screenshots, feature list, and quickstart instructions
- [ ] **OSS-03**: CONTRIBUTING.md documents dev setup, code style, and PR process
- [ ] **OSS-04**: `.env.example` with all configurable values documented
- [ ] **OSS-05**: GitHub Actions CI pipeline runs tests, lint, and Docker build on PRs

### Documentation

- [ ] **DOCS-01**: Setup guide covers Docker deployment, local dev environment, and configuration options
- [ ] **DOCS-02**: Architecture document describes system overview, component structure, data model, and key patterns
- [ ] **DOCS-03**: API reference documents all REST endpoints with request/response examples

## Future Requirements

Deferred from PROJECT.md — not in v1.2 scope.

### Data Import

- **IMP-01**: DVC account scraping to import contracts, point balances, and reservations
- **IMP-02**: DVC point chart scraping to get current room costs by resort/season

### Enhanced Scenarios

- **SCEN-01**: Save/name scenarios for later comparison
- **SCEN-02**: Simulate banking points from current use year
- **SCEN-03**: Model adding a hypothetical new contract

### Enhanced Heatmap

- **HEAT-01**: Overlay "affordable dates" on heatmap based on current point balance
- **HEAT-02**: Compare two resorts side-by-side on heatmap

### Notifications

- **NOTIF-01**: Browser notifications for upcoming booking windows
- **NOTIF-02**: Export booking window dates to calendar (iCal)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-user / authentication | Personal tool, single user only |
| Real-time availability checking | Fragile scraping, legally gray |
| Automated booking | Violates Disney ToS |
| Mobile native app | Web-first, responsive web sufficient |
| Cloud deployment (Railway etc.) | Docker for self-hosting; users deploy wherever |
| Email/SMS notifications | No auth infrastructure; in-app alerts sufficient |
| New features in this milestone | v1.2 is hardening only; features deferred to v2 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| QUAL-01 | Phase 8 | Pending |
| QUAL-02 | Phase 8 | Pending |
| QUAL-03 | Phase 8 | Pending |
| QUAL-04 | Phase 8 | Pending |
| QUAL-05 | Phase 8 | Pending |
| QUAL-06 | Phase 8 | Pending |
| SEC-01 | Phase 9 | Pending |
| SEC-02 | Phase 8 | Pending |
| SEC-03 | Phase 9 | Pending |
| UX-01 | Phase 9 | Pending |
| UX-02 | Phase 9 | Pending |
| UX-03 | Phase 9 | Pending |
| UX-04 | Phase 9 | Pending |
| OSS-01 | Phase 10 | Pending |
| OSS-02 | Phase 10 | Pending |
| OSS-03 | Phase 10 | Pending |
| OSS-04 | Phase 10 | Pending |
| OSS-05 | Phase 10 | Pending |
| DOCS-01 | Phase 10 | Pending |
| DOCS-02 | Phase 10 | Pending |
| DOCS-03 | Phase 10 | Pending |

**Coverage:**
- v1.2 requirements: 21 total
- Mapped to phases: 21
- Unmapped: 0

---
*Requirements defined: 2026-02-11*
*Last updated: 2026-02-11 after roadmap creation*
