# Phase 8: Code Hardening - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Every API call returns structured errors, every input is validated, every failure is caught gracefully, and all code paths are tested. This phase hardens the existing codebase — no new features, no UX polish (that's Phase 9).

</domain>

<decisions>
## Implementation Decisions

### Error response shape
- Consistent JSON structure for ALL API errors: `{ "error": { "type": "VALIDATION_ERROR", "message": "Human-readable message", "fields": [...] } }`
- Error types are category-level: VALIDATION_ERROR, NOT_FOUND, SERVER_ERROR, CONFLICT (not granular codes like ERR_CONTRACT_OVERLAP)
- Validation errors include field-level detail: `{ "field": "start_date", "issue": "Must be after contract start date" }`
- Validation errors return ALL invalid fields at once (not fail-on-first)
- 500/unexpected errors return generic "Something went wrong" to the client — real detail only in server logs
- No stack traces or internal details exposed in any error response

### Error boundary UX
- Per-section error boundaries (dashboard, trip explorer, contract forms, etc.) — a crash in one section doesn't take down others
- No app-level boundary needed (per-section is sufficient)
- Fallback UI: styled card matching app design, shows "Something went wrong in [section]" with a retry button that remounts the component
- Error boundaries log the error + component stack to browser console for debugging

### Validation behavior
- Dual validation: frontend validates for instant UX feedback, backend re-validates as safety net
- Frontend form validation triggers on blur (when user leaves a field)
- Validation errors display as inline red text below each invalid field
- Date fields enforce full business logic at the form level: valid ranges, use year boundaries, overlap detection, expired use years
- All other fields validated for type, required, and format constraints

### Test coverage
- Mix of unit tests (engine/calculation layer) and integration tests (API endpoints)
- No numeric coverage target — cover critical paths from success criteria
- Backend + engine tests only — no React component tests (frontend is thin)
- Critical flows that MUST be tested:
  - Create contract
  - Make reservation
  - Check availability
  - What-if scenarios
  - Booking impact preview
- Edge cases that MUST be tested:
  - 0 contracts / 0 points
  - Expired use years
  - Boundary dates
  - Invalid inputs for all endpoints

### Lint & cleanup
- Zero lint warnings in both frontend and backend
- Remove all dead code (unused imports, unreachable branches, commented-out code)

### Claude's Discretion
- Exact error type taxonomy (beyond the core categories above)
- Which specific React sections get their own error boundary
- Test framework and assertion patterns
- Lint rule configuration
- Order of implementation (errors first vs validation first vs tests first)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Key principles:
- Belt-and-suspenders: validate in both layers, never trust client-side alone
- Open-source ready: no internal details leak through error responses
- Developer-friendly: console logging for debugging, clear error messages for users

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-code-hardening*
*Context gathered: 2026-02-11*
