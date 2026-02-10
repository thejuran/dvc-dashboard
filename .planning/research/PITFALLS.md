# Pitfalls Research

**Domain:** DVC Points Management Dashboard with Web Scraping
**Researched:** 2026-02-09
**Confidence:** MEDIUM-HIGH (DVC domain rules are well-documented; scraping fragility is inherently unpredictable)

## Critical Pitfalls

### Pitfall 1: Hardcoding DVC Business Rules That Change Annually

**What goes wrong:**
Point charts, season/travel period dates, view category names, and room type classifications change every year. In 2021, Disney replaced the 5 named seasons (Adventure, Choice, Dream, Magic, Premier) with 7 unnamed "Travel Periods." In 2026, "Standard View" was renamed to "Resort View" and several higher-tier views became "Preferred View" across most resorts. Any system that hardcodes these values will silently produce wrong results after the next annual chart release.

**Why it happens:**
Developers model DVC point charts as static lookup tables. The annual changes are small enough (Disney limits how much a single night can change year-to-year) that tests still pass, but calculations drift. The renaming of categories (Standard -> Resort, Lake View -> Preferred) breaks string-matching logic.

**How to avoid:**
- Store point charts as versioned data, not code. Each chart is keyed by resort + year + effective date range.
- Treat season/travel period date ranges as data that gets refreshed annually, not constants.
- Use the scraped DVC website as the source of truth for current point values rather than a local copy.
- Build a "chart staleness" check: if the current date is past when new charts are typically released (late November/early December) and you haven't ingested the new year's data, surface a warning.

**Warning signs:**
- Point cost calculations don't match what the DVC website shows.
- View/room type names in your system don't match the DVC website dropdowns.
- Users see "unknown season" or unmapped travel periods after January.

**Phase to address:**
Data modeling phase. The schema for point charts must be designed for annual versioning from day one. Retrofitting versioned charts onto a hardcoded model is a rewrite.

---

### Pitfall 2: Scraping Disney's Authenticated Member Site Without a Resilience Strategy

**What goes wrong:**
Disney's DVC member website sits behind their unified "My Disney" login with two-factor authentication, Secure/SameSite cookies, and aggressive bot detection. Disney has a documented history of actively pursuing legal action against scrapers (they sued dining reservation scrapers, sent DMCA takedowns, and shut down multiple automated services). The site undergoes periodic security updates (e.g., the May 2023 2FA rollout that broke all existing automated logins). A scraper built against today's login flow will break when Disney next updates their auth system, and you may not know it broke until you're acting on stale data.

**Why it happens:**
Developers build scrapers against the current site structure and assume stability. Disney's unified login spans WDW, DVC, My Disney Experience, and Disney+ -- changes to any of these properties can cascade to break DVC authentication. Disney also explicitly prohibits automated access in their Terms of Service.

**How to avoid:**
- Accept scraping fragility as a core architectural constraint. Design the entire app to function gracefully with stale data.
- Implement scrape-then-cache: scrape on-demand or on a manual trigger (not automated cron jobs), store results locally with timestamps, and always show data age to the user.
- Use browser automation (Playwright/Puppeteer) rather than raw HTTP requests, since Disney's login involves JavaScript rendering, redirects across subdomains, and dynamic tokens.
- Build scrape health monitoring: detect when a scrape fails (auth rejection, CAPTCHA, changed DOM structure) and surface it immediately rather than silently serving old data.
- Keep scraping frequency extremely low. This is a personal tool for 2-3 contracts -- you only need fresh data when you're actively planning. A manual "refresh now" button is better than scheduled scraping.
- Consider the legal dimension: this is personal use of your own member account data, which is a much lower risk profile than commercial scraping, but avoid building features that look like the dining reservation scrapers Disney shut down.

**Warning signs:**
- Scraper returns HTTP 403 or redirects to a CAPTCHA page.
- Login flow adds new steps (SMS verification, email confirmation, new consent screens).
- Scraped HTML structure changes (new class names, different element hierarchy).
- Data timestamps show the last successful scrape was days/weeks ago.

**Phase to address:**
Phase 1 (scraping infrastructure). This is the foundation everything else depends on. Build scraping with failure as the expected case, not the exception.

---

### Pitfall 3: Incorrect Point Timeline Calculations Due to Use Year and Banking Complexity

**What goes wrong:**
The "pick a future date, see available points" feature is the core value proposition but involves a combinatorial explosion of rules across multiple contracts. Each contract has: a Use Year (Feb, Mar, Apr, Jun, Aug, Sep, Oct, or Dec), a banking deadline (8 months into the Use Year), a borrowing allowance (100% of next year's points), and the constraint that banked points cannot be re-banked or returned. With 2-3 contracts potentially on different Use Years, calculating "what points are available on date X" requires tracking 6+ separate point buckets (current year per contract, banked points per contract, borrowed points per contract), each with different expiration dates.

**Why it happens:**
Developers model points as a single pool ("you have 400 points") instead of modeling the actual lifecycle of each point bucket. The banking deadline creates a cliff where points go from "bankable" to "use-or-lose" status. Borrowed points are irreversible, creating a commitment that constrains future years. When multiple contracts have different Use Years, the interaction between banking windows, borrowing, and expiration creates scenarios that are extremely hard to reason about.

**How to avoid:**
- Model each "point allocation" as a first-class entity with properties: contract_id, use_year, allocation_year, quantity, status (available/banked/borrowed/used/expired), bank_deadline, expiration_date.
- Never aggregate points into a single number without first checking temporal constraints. The question "how many points do I have?" is always relative to a date and a set of decisions about banking/borrowing.
- Build the timeline calculator as a state machine: for any target date, walk forward from today and compute the state of each allocation, respecting banking deadlines and expirations.
- Test with edge cases: what happens when the target date falls between two contracts' banking deadlines? What if you bank on Contract A but not Contract B? What if you've already borrowed from next year on one contract?

**Warning signs:**
- Point totals don't match what the DVC website shows for your account.
- The system shows points as "available" that have already passed their banking deadline and are about to expire.
- Borrowed points aren't being subtracted from next year's balance.
- Timeline shows different totals for the same date depending on the path you take through the UI.

**Phase to address:**
Core calculation engine phase. This must be right before building any UI on top of it. Write exhaustive unit tests with known scenarios before building the timeline feature.

---

### Pitfall 4: Ignoring Resale Contract Restrictions in Trip Explorer

**What goes wrong:**
The trip explorer ("what can I book with my points?") shows resorts that are actually unavailable to resale contract holders. Resale restrictions are complex and depend on when the resort opened AND when the contract was purchased. A user sees "You can stay at Riviera Resort for 150 points!" but their resale contract for Bay Lake Tower cannot be used at Riviera. This produces the worst kind of UX failure: the app confidently tells you something you can't actually do.

**Why it happens:**
The restriction rules have multiple tiers:
1. Original 14 resorts (pre-2019): Resale contracts can book at any of these 14, but NOT at Riviera, Cabins at Fort Wilderness, or Villas at Disneyland Hotel.
2. Post-2019 resorts (Riviera, Cabins at Fort Wilderness, Villas at Disneyland Hotel): Resale contracts can ONLY book at their home resort.
3. Resale contracts cannot access Concierge Collection, Disney Collection, or Adventurer Collection regardless of home resort.
4. Direct purchase contracts have no resort restrictions.

Developers often model this as a simple boolean (resale: yes/no) rather than encoding the full restriction matrix.

**How to avoid:**
- Model each contract with: home_resort, purchase_type (direct/resale), purchase_date, and resort_open_date.
- Build an explicit "can_book_at(contract, target_resort) -> bool" function that encodes all restriction rules.
- The trip explorer must filter results through this function before displaying options.
- Include a data source for when each resort opened (and when Disney might add new restricted resorts in the future).
- Surface the restriction reason in the UI: "Riviera Resort is not available with your Bay Lake Tower resale contract" rather than silently hiding it.

**Warning signs:**
- Trip explorer shows the same results regardless of which contract's points are being used.
- No distinction between direct and resale contracts in the data model.
- New DVC resorts are added without updating restriction rules.

**Phase to address:**
Data modeling phase (contract model) and Trip Explorer feature phase. The contract model must capture purchase type from the start; the trip explorer must enforce restrictions before showing results.

---

### Pitfall 5: Building the App Around Scraping Instead of Around Local Data

**What goes wrong:**
The app treats the DVC website as a live data source, making scraping requests as part of normal user flows (e.g., scraping on every page load, scraping to check availability in real-time). When the scraper breaks -- and it will break -- the entire app becomes unusable. This also increases the risk of Disney detecting automated access and potentially flagging the member account.

**Why it happens:**
It's architecturally simpler to treat the DVC website as an API. Developers reason: "I'll just fetch the data when I need it." This works during development but creates a brittle dependency in production.

**How to avoid:**
- Architecture: Scraping is an import mechanism, not a data source. The app reads from a local database. Scraping populates that database.
- The app must be 100% functional with zero scraping connectivity. If the DVC website is down, redesigned, or blocking you, the app still works with its last-known data.
- Show a clear "last synced" timestamp on every screen. Let the user manually trigger a sync.
- Allow manual data entry as a fallback. If scraping breaks for weeks, the user can still type in their point balances from the DVC website.

**Warning signs:**
- Page load times depend on scraper response times.
- App shows spinners or errors when the DVC website is slow or unreachable.
- No local database -- data lives only in scraper responses.
- No manual data entry capability.

**Phase to address:**
Architecture phase. This is the most important architectural decision in the project. "Scraping is import, local data is truth" must be the guiding principle from day one.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Storing point charts as JSON files instead of a database | Fast to implement, easy to version in git | Hard to query across years, no relational integrity, manual updates | MVP only -- migrate to DB before building timeline calculator |
| Scraping with raw HTTP instead of browser automation | Faster, simpler, fewer dependencies | Disney's login uses JS rendering and dynamic tokens; raw HTTP will break first | Never -- Disney's auth requires browser automation from the start |
| Single "points" integer per contract instead of bucketed allocations | Simple data model, easy to display | Cannot compute banking deadlines, expiration, or multi-year scenarios | Never -- this is the core domain model, get it right first |
| Skipping manual data entry fallback | Faster to ship | When scraper breaks, app is useless until fixed | Acceptable in Phase 1, must add in Phase 2 |
| Hardcoding the list of DVC resorts | Quick, list doesn't change often | New resorts (like Cabins at Fort Wilderness) break the app | MVP only -- pull from a config file at minimum |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Disney unified login | Treating it as a simple username/password POST request | Use full browser automation (Playwright); handle redirects across disney.go.com subdomains, 2FA prompts, cookie consent, and session tokens |
| DVC point chart pages | Scraping HTML tables with fixed CSS selectors | Use data attributes or structural patterns rather than class names; Disney changes class names during redesigns. Better yet, check if the point data is available in embedded JSON/API responses in the page source |
| DVC member dashboard | Assuming the logged-in session persists indefinitely | Sessions expire; implement session health checks and re-authentication. Store credentials securely (OS keychain, not plaintext config) |
| Disney CDN/caching | Assuming the page you get is the latest version | Disney uses CDN edge caching; scraped content may be minutes to hours stale. Check response headers for cache age |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Computing point availability by brute-forcing all date combinations | Timeline calculator takes seconds instead of milliseconds | Pre-compute point bucket states at key boundary dates (banking deadlines, expiration dates, use year starts); interpolate for dates between boundaries | With 3 contracts, you have ~15 point buckets with ~30 boundary dates per year; the combinatorics are manageable with pre-computation but not with brute force |
| Storing full HTML scrape responses | Database grows rapidly; queries slow down | Parse and extract only the structured data you need; discard raw HTML after extraction (or archive separately for debugging) | After a few months of regular scraping |
| Re-scraping the entire DVC site on every sync | Slow syncs, increased detection risk | Scrape only what changed: check point balances first (quick), then only scrape detailed charts if balances differ from stored values | Immediately -- full scrapes are unnecessary and risky |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing Disney login credentials in plaintext config files | Credentials leaked via git, backups, or file access; account compromise | Use OS keychain (macOS Keychain, etc.) or encrypted environment variables. Never commit credentials to version control |
| Logging full HTTP responses including auth tokens | Session tokens in log files can be used to hijack the Disney session | Sanitize logs to strip Authorization headers, cookies, and tokens |
| Running the scraper on a public server without access controls | Anyone with the URL can trigger scrapes against your Disney account | If deployed, add authentication to the web app itself. Consider running locally-only for a single-user tool |
| Not handling 2FA codes securely | If the app stores or caches 2FA codes, they could be intercepted | Let 2FA be a manual step in the sync flow; don't try to automate it |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing point totals without date context | User thinks they have 400 points but 150 expire next month | Always show points with temporal qualifiers: "400 points available today (150 expire Oct 1)" |
| Not distinguishing point sources in trip explorer | User plans a trip at Riviera using resale-restricted points | Color-code or label points by contract and show which contracts can book which resorts |
| Hiding data staleness | User makes decisions based on data that was scraped 3 weeks ago | Show "Last synced: [date]" prominently; use visual warnings (yellow/red) when data is older than 1 day / 1 week |
| Overwhelming the timeline with all contracts merged | User can't understand which points come from which contract or when deadlines apply | Default to per-contract timeline view; offer a merged view as an advanced option with clear contract attribution |
| Not showing banking deadline urgency | User misses a banking deadline and loses points | Show countdown timers for upcoming banking deadlines; push these to the dashboard home screen |

## "Looks Done But Isn't" Checklist

- [ ] **Point timeline calculator:** Often missing the "banked points can't be re-banked" rule -- verify that banked points are marked as single-use and expire at the end of the banked-into year
- [ ] **Trip explorer:** Often missing resale restrictions -- verify that results are filtered by the contract's booking eligibility, not just point balance
- [ ] **Point availability:** Often missing the banking deadline cliff -- verify that points past the 8-month banking deadline show as "use-or-lose" rather than "available"
- [ ] **Reservation tracking:** Often missing the point-type attribution -- verify that reservations show which contract's points (and which year's allocation) are being consumed
- [ ] **Scraper health:** Often missing failure detection -- verify that a scraper failure produces an alert/notification, not silent stale data
- [ ] **Date calculations:** Often missing weekday/weekend distinction -- verify that point cost calculations account for the different per-night costs for weekdays vs. weekends (Fri/Sat cost more)
- [ ] **Multi-contract booking:** Often missing the cross-contract limitation -- verify that the app correctly models that you cannot combine points from contracts with different Use Years without a transfer (which requires calling Member Services)

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Hardcoded point charts become stale | LOW | Update the chart data; if schema supports versioning, just add a new version. If not, refactor schema first (MEDIUM cost) |
| Scraper breaks due to Disney site change | MEDIUM | Inspect the new site structure, update selectors/flow. If login flow changed fundamentally, may need to rearchitect the scraping layer. App remains usable with cached data during recovery |
| Point calculations are wrong due to bad domain model | HIGH | Requires schema migration + recalculation of all stored point states. This is why getting the data model right in Phase 1 matters |
| Resale restrictions not enforced in trip explorer | LOW | Add filtering function and re-render results. Data model change is small (adding purchase_type to contracts) if not already present |
| Disney flags/blocks your member account for scraping | HIGH | No technical recovery -- must contact Disney Member Services. Mitigate by keeping scraping manual, low-frequency, and indistinguishable from normal browser usage |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Hardcoded point charts | Data Modeling | Schema review: are charts versioned by year with effective date ranges? |
| Fragile scraping with no fallback | Architecture / Scraping Infrastructure | Can the app function for a week with zero successful scrapes? Is there manual data entry? |
| Incorrect point timeline math | Core Calculation Engine | Unit tests covering: multi-contract different Use Years, banking deadline edge, borrowed points subtraction, banked points non-re-bankable |
| Missing resale restrictions | Data Modeling + Trip Explorer | Test: does trip explorer show different results for a Bay Lake Tower resale contract vs. a direct contract? |
| App depends on live scraping | Architecture | Code review: does any user-facing page make a scraping call? (Answer should be: never) |
| Stale data shown without warning | UI/Dashboard | Every screen shows "last synced" timestamp; visual warning when data age exceeds threshold |
| Banking deadline missed | Dashboard / Notifications | Dashboard home screen shows countdown to next banking deadline across all contracts |
| Credential exposure | Security Review | Grep codebase for plaintext passwords, API keys, or tokens in config files or logs |
| Point cost weekday/weekend confusion | Calculation Engine | Unit tests: same room, same season, Friday vs. Monday should show different point costs |

## Sources

- [DVC Point Charts 2026 - WDWInfo](https://www.wdwinfo.com/disney-vacation-club/dvc-point-charts.htm)
- [DVC Resale Restrictions - DVC Resale Market](https://www.dvcresalemarket.com/blog/new-dvc-resale-restrictions-and-who-is-most-impacted/)
- [DVC Resale Restrictions: Eligible Resorts - DVC Shop](https://dvcshop.com/resale-restrictions-eligible-resorts/)
- [DVC Banking and Borrowing - DVC Field Guide](https://dvcfieldguide.com/blog/how-to-bank-and-borrow-dvc-points)
- [Banking Deadlines - Disney Vacation Club Official](https://disneyvacationclub.disney.go.com/faq/bank-points/deadlines/)
- [DVC Use Year Explained - DVCinfo](https://dvcinfo.com/dvc-information/buying-dvc/understanding-use-year/)
- [Multiple Contracts Booking - DVC Resale Market](https://www.dvcresalemarket.com/blog/how-does-booking-work-with-multiple-dvc-contracts/)
- [Disney Scraping Legal Risks - Orlando Sentinel](https://www.orlandosentinel.com/business/os-disney-dining-web-scraping-20151010-story.html)
- [DVC Website Security Updates - DVC Shop](https://dvcshop.com/dvc-website-security-updates-5-24-23/)
- [DVC Point Chart Seasons to Travel Periods - Fidelity Real Estate](https://www.fidelityrealestate.com/blog/dvc-point-chart-seasons-change/)
- [2026 DVC Point Charts Analysis - DVC Fan](https://dvcfan.com/general-dvc/a-closer-look-at-the-2026-dvc-points-charts/)
- [Web Scraping Data Freshness - ShoppingScraper](https://shoppingscraper.com/blog/how-to-ensure-data-freshness-in-web-scraping)
- [Bypass Bot Detection 2026 - ZenRows](https://www.zenrows.com/blog/bypass-bot-detection)
- [Authenticated Session Scraping - DataFuel](https://www.datafuel.dev/blog/handling_session_management_for_authenticated_scraping_cookies_tokens_and_headers)

---
*Pitfalls research for: DVC Points Management Dashboard*
*Researched: 2026-02-09*
