# Feature Research

**Domain:** DVC (Disney Vacation Club) Point Management & Vacation Planning Tool
**Researched:** 2026-02-09
**Confidence:** MEDIUM-HIGH (based on comprehensive competitor analysis and DVC community research; DVC domain rules well-documented)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Point balance tracking per contract** | Every DVC tool does this. Owners with 2-3 contracts need to see points across all contracts at a glance. The DVC website itself shows this but poorly for multi-contract owners. | LOW | Core data model: contracts have points, use years, home resorts. Must track current year allocation, banked points, borrowed points, and used points per contract. |
| **Use year timeline with banking/borrowing** | Banking deadlines are the #1 thing DVC owners forget and lose points over. DVCHelp, DVC Planner, DVC Toolkit all track this. Community spreadsheets (DISboards) exist specifically for this. | MEDIUM | Must model: UY start date, 8-month banking deadline, points expiring if not banked, banked points can't be re-banked. Borrowing up to current limit from next UY. Banking/borrowing are final/irreversible transactions. |
| **Point cost calculator (dates + resort + room type)** | Every competitor has this. DVC Fan, DVCRequest, DVC Trip Planner, DVC Toolkit all provide point charts lookup. This is the most basic planning feature. | MEDIUM | Requires ingesting annual point charts (released by Disney each year). 7 seasons, weekday/weekend rates, per-resort per-room-type per-view pricing. Charts change yearly with minor adjustments. |
| **Reservation tracking** | DVC Planner, DVCHelp, and DVC Toolkit all track current/upcoming reservations with point costs, check-in dates, and important associated dates. | LOW | Store resort, room type, dates, points used, which contract points came from. |
| **Key date reminders** | DVCHelp provides calendar integration. DVC Toolkit has reminders. DVC Planner calculates 11-month, 7-month, and dining reservation dates. Owners forget these constantly. | MEDIUM | Banking deadline (8 months from UY start), 11-month home resort booking window, 7-month non-home booking window, 60-day dining reservations, 30-day holding account threshold. All dates are relative to check-in or UY. |
| **Resale contract restriction awareness** | Critical for resale owners (the target user). Resale contracts purchased after Jan 19, 2019 at original 14 resorts can only book those 14 resorts. Riviera/Disneyland Hotel/Fort Wilderness resale = home resort only. | LOW | Simple rules engine: based on contract purchase date and home resort, filter available booking resorts. Must be correct -- booking a restricted resort wastes the user's time. |
| **"What can I afford?" query** | Given my available points for a date range, what resort/room combos can I book? Every point calculator implicitly supports this by showing costs. DVC Toolkit lets you set a max points limit to filter. | MEDIUM | Reverse lookup: instead of "how much does X cost?", answer "what can I get for N points?" across all eligible resorts. Requires point charts + resale restriction filtering. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **DVC website scraping for live data** | No existing tool does this. DVCHelp, DVC Planner, DVC Toolkit all require manual entry of contract info, point balances, and reservations. Automatic sync from the DVC member portal eliminates data entry and ensures accuracy. This is the killer feature. | HIGH | Must authenticate with Disney's member portal, scrape point balances, reservation details, contract info. Fragile (Disney can change their site). Needs session management, error handling, change detection. Single-user app mitigates scale concerns but not fragility. |
| **Point timeline calculator ("pick a future date, see available points")** | Multi-contract owners struggle to mentally combine points across use years, banking windows, and borrowing limits. No existing tool provides a forward-looking "what will I have available on date X?" view that accounts for upcoming expirations, pending reservations, and banking/borrowing possibilities. | HIGH | Must model point lifecycle: current balance, banked points (expire end of banked-into UY), borrowing eligibility, existing reservation holds, holding account points. Project forward to any future date showing available, expiring-soon, and borrowable points per contract and combined. |
| **Trip explorer with constraint awareness** | "Show me everywhere I can go in October for 5 nights with my available points" -- filtered by resale restrictions, point availability (including banking/borrowing needed), and room occupancy. Existing tools require you to check one resort at a time. | HIGH | Combines point timeline calculator + point charts + resale restrictions + room capacity data into a single query. Must handle multi-contract point pooling scenarios. |
| **Point optimization suggestions** | D Point app has a "Point Maximizer" feature. But a tool aware of your actual contracts and point balances could suggest: "Bank 50 points from Contract A before March 31 deadline" or "You can save 12 points by shifting check-in one day later." | HIGH | Requires all underlying data models to be solid. Optimization across banking decisions, date flexibility, and resort alternatives. Could start simple (banking deadline warnings) and grow. |
| **"What-if" scenario planning** | "If I bank points from Contract A and borrow from Contract B, can I book a 1BR at Poly in December?" No existing tool lets you model hypothetical banking/borrowing decisions before committing them (they're irreversible on the DVC site). | MEDIUM | Build on point timeline calculator. Let user toggle banking/borrowing decisions and see impact on future availability. Critical because banking/borrowing are final -- modeling before committing is hugely valuable. |
| **Multi-contract point pooling visualization** | DVCHelp mentions tracking point usage across multiple contracts for a single stay. DVC pulls points from contracts in a specific order. Visualizing which contracts fund which reservations helps owners plan. | MEDIUM | DVC pulls points in a specific order (current UY points before banked, home resort before non-home). Visualizing this helps owners understand point flow and plan banking strategically. |
| **Seasonal cost heatmap** | Show point costs as a calendar heatmap across an entire year for a given resort/room type. Makes it visually obvious when the cheap vs expensive seasons are. Existing tools show point charts as tables; a visual calendar is more intuitive. | LOW | Straightforward data visualization once point charts are loaded. Low effort, high impact for planning. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Multi-user / family sharing** | Families want to collaborate on trip planning | Adds authentication, authorization, data isolation complexity. This is a personal tool for a single owner. Multi-user = 10x complexity for zero benefit in this use case. | Single-user app. Share via screen or export if needed. |
| **Real-time DVC availability checking** | Knowing if a room is actually bookable is the ultimate feature | DVC availability requires scraping Disney's booking system in real-time, which is technically fragile, legally gray, and rate-limited. DVCapp.com does this as their entire business. Competing here is unnecessary. | Link out to DVCapp.com or DVC member portal for live availability. Focus on "what could I book?" (point math) not "what's available right now?" (live inventory). |
| **Automated booking** | "Just book it for me when it opens at 8am" | Automating bookings on Disney's platform violates ToS, risks account suspension, and is technically unreliable. | Provide exact booking window dates/times and reminders so the user can book manually at the right moment. |
| **Point rental marketplace** | DVC owners frequently rent excess points (DVCRequest, DVC Rental Store) | Building a marketplace is a massive product in itself. Legal, payment processing, trust/safety concerns. David's Vacation Club Rentals is a whole company doing just this. | If user wants to rent points, link to existing services. Track "excess points available to rent" as a balance indicator, not a marketplace feature. |
| **Dining / park reservation planning** | Disney trip planning extends well beyond DVC resort booking | Scope creep into general Disney trip planning (dining at 60 days, park reservations, Genie+, etc.). Hundreds of apps do this. Focus on the DVC points niche. | Track the 60-day dining reservation date as a reminder tied to check-in. Don't build a dining planner. |
| **Mobile native app** | "I want it on my phone" | Building and maintaining iOS/Android native apps doubles development effort. Single user, personal tool. | Build as a responsive web app (PWA-capable). Works on phone browser. No App Store overhead. |
| **Annual dues tracking / financial analysis** | Some owners track cost-per-point, ROI, total investment | Financial tracking is a nice-to-have that adds complexity without improving the core "plan my vacation with my points" workflow. | Show dues amount per contract (from point charts data). Don't build a full financial tracker. |
| **Community features (forums, reviews, tips)** | Social features increase engagement | This is a personal tool, not a community platform. DVCinfo, DISboards, DVC Fan already serve this need. | Link to community resources. Don't build social features. |

## Feature Dependencies

```
[DVC Website Scraping]
    |
    |--populates--> [Point Balance Tracking Per Contract]
    |                   |
    |                   |--requires--> [Use Year Timeline with Banking/Borrowing]
    |                   |                   |
    |                   |                   |--enables--> [Point Timeline Calculator]
    |                   |                   |                 |
    |                   |                   |                 |--enables--> [Trip Explorer]
    |                   |                   |                 |                 |
    |                   |                   |                 |                 |--enhances--> [Point Optimization Suggestions]
    |                   |                   |                 |
    |                   |                   |                 |--enables--> [What-If Scenario Planning]
    |                   |                   |
    |                   |                   |--enables--> [Multi-Contract Point Pooling Visualization]
    |                   |
    |                   |--combined-with--> [Point Cost Calculator] --enables--> [Trip Explorer]
    |
    |--populates--> [Reservation Tracking]
    |                   |
    |                   |--feeds--> [Key Date Reminders]
    |                   |--feeds--> [Point Timeline Calculator]
    |
    |--populates--> [Contract Details] --enables--> [Resale Restriction Awareness]
    |                                                     |
    |                                                     |--filters--> [Trip Explorer]
    |                                                     |--filters--> ["What Can I Afford?" Query]

[Point Charts Data (Static/Annual)]
    |
    |--required-by--> [Point Cost Calculator]
    |                     |
    |                     |--enables--> ["What Can I Afford?" Query]
    |                     |--enables--> [Trip Explorer]
    |                     |--enables--> [Seasonal Cost Heatmap]
    |                     |--enables--> [Point Optimization Suggestions]
```

### Dependency Notes

- **DVC Website Scraping enables everything:** Without scraping, the user must manually enter all contract info, point balances, and reservations. Scraping is the foundation that eliminates data entry. However, the app must also work with manual entry as a fallback (scraping will break).
- **Point Charts Data is independently loaded:** Annual point charts are published publicly by Disney. This data can be loaded independently of scraping -- it's static reference data that changes once per year.
- **Point Timeline Calculator is the core differentiator:** It depends on point balance tracking AND use year timeline modeling. Once built, it enables the trip explorer and what-if planning -- the features that make this tool uniquely valuable.
- **Resale Restriction Awareness is low-complexity but high-impact:** Simple rules, but filtering all queries through these rules is critical for resale contract owners. Must be applied consistently across trip explorer, "what can I afford?", and point cost calculator.
- **Trip Explorer combines everything:** It's the culmination feature requiring point timeline, point charts, resale restrictions, and room data all working together.

## MVP Definition

### Launch With (v1)

Minimum viable product -- what's needed to validate the concept.

- [ ] **Contract and point balance data model** -- Store contracts with use years, home resorts, point allocations, resale purchase dates
- [ ] **Manual data entry** -- Allow entering contract info and point balances by hand (fallback for when scraping isn't ready or breaks)
- [ ] **Point charts ingestion** -- Load current/upcoming year point charts for all DVC resorts
- [ ] **Point cost calculator** -- Select dates + resort + room type, see point cost
- [ ] **Use year timeline** -- Show point allocations, banking deadlines, expiration dates per contract
- [ ] **Resale restriction filtering** -- Know which resorts each contract can book at
- [ ] **"What can I afford?" basic query** -- Given a date range and available points, show bookable resort/room options

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] **DVC website scraping** -- Automate point balance and reservation data import (trigger: manual data entry proves tedious and error-prone)
- [ ] **Point timeline calculator** -- "Pick a future date, see available points" with banking/borrowing projections (trigger: core data model is solid and tested)
- [ ] **Reservation tracking with key date reminders** -- Track bookings and surface important dates like banking deadlines, booking windows (trigger: scraping provides reservation data or user enters reservations)
- [ ] **What-if scenario planning** -- Model banking/borrowing decisions before committing (trigger: point timeline calculator is working)
- [ ] **Seasonal cost heatmap** -- Visual calendar showing point costs across a year (trigger: point charts are loaded; low effort, high visual impact)

### Future Consideration (v2+)

Features to defer until core product is proven.

- [ ] **Full trip explorer** -- "Show me everywhere I can go" with all constraints applied (defer: requires all underlying systems to be robust)
- [ ] **Point optimization suggestions** -- "Bank these points before deadline" or "shift dates to save points" (defer: requires mature data models and reliable scraping)
- [ ] **Multi-contract point pooling visualization** -- Show which contracts fund which reservations (defer: nice-to-have visualization, not core planning)
- [ ] **Calendar integration (CalDAV/iCal export)** -- Export key dates to phone calendar (defer: reminders in-app are sufficient initially)

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Point balance tracking per contract | HIGH | LOW | P1 |
| Use year timeline with banking/borrowing | HIGH | MEDIUM | P1 |
| Point cost calculator | HIGH | MEDIUM | P1 |
| Resale restriction filtering | HIGH | LOW | P1 |
| "What can I afford?" query | HIGH | MEDIUM | P1 |
| Point charts data ingestion | HIGH | MEDIUM | P1 |
| Reservation tracking | MEDIUM | LOW | P1 |
| Key date reminders | HIGH | MEDIUM | P2 |
| DVC website scraping | HIGH | HIGH | P2 |
| Point timeline calculator | HIGH | HIGH | P2 |
| What-if scenario planning | HIGH | MEDIUM | P2 |
| Seasonal cost heatmap | MEDIUM | LOW | P2 |
| Trip explorer (full) | HIGH | HIGH | P3 |
| Point optimization suggestions | MEDIUM | HIGH | P3 |
| Multi-contract pooling visualization | LOW | MEDIUM | P3 |
| Calendar export (iCal/CalDAV) | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for launch -- core point tracking and basic planning
- P2: Should have, add when possible -- differentiating features that make this tool unique
- P3: Nice to have, future consideration -- polish and advanced features

## Competitor Feature Analysis

| Feature | DVCHelp.com | DVC Toolkit (iOS) | DVC Planner (iOS) | D Point (iOS) | DVC Trip Planner (Web) | Community Spreadsheets | Our Approach |
|---------|-------------|-------------------|-------------------|---------------|------------------------|------------------------|--------------|
| Point balance tracking | Yes (manual entry) | Yes (manual entry) | Yes (manual entry) | Yes (manual entry) | No | Yes (manual entry) | **Auto-populated via scraping** + manual fallback |
| Multi-contract support | Yes | Yes | Yes | Yes | No | Yes | Yes, first-class multi-contract with pooling |
| Point cost calculator | Yes | Yes | Yes | Yes | Yes | No | Yes, with resale restriction awareness |
| Use year / banking tracking | Yes | Yes (banking deadlines) | Yes | Yes (bank/borrow tracking) | No | Yes | Yes, with forward-looking timeline projections |
| Reservation tracking | Yes | Yes (trip mgmt) | Yes | No | Yes (itinerary) | No | Yes, auto-populated from scraping |
| Date reminders | Yes (email + calendar) | Yes (push notifications) | Yes (calculates dates) | Yes (reminders) | Yes (booking reminders) | No | Yes, in-app + potential calendar export |
| Availability alerts | No | Yes (paid Plus tier) | No | No | No | No | **Not building** -- link to DVCapp.com |
| Resale restriction awareness | No | No | No | No | No | No | **Yes -- unique differentiator** for resale owners |
| Forward-looking point projection | No | No | No | No | No | No | **Yes -- core differentiator** |
| What-if scenario planning | No | No | No | No | No | No | **Yes -- unique differentiator** |
| Point optimization | No | No | No | Yes ("Point Maximizer") | No | No | Yes, but deferred to v2+ |
| Seasonal heatmap | No | No | No | No | No | No | **Yes -- easy visual win** |
| Auto data sync (scraping) | No | No | No | No | No | No | **Yes -- killer feature** |
| Platform | Web | iOS only | iOS only | iOS only | Web | Google Sheets | Web (responsive/PWA) |

### Key Competitive Gaps We Fill

1. **No tool auto-syncs with the DVC member portal.** Every existing tool requires manual data entry. Scraping is our highest-risk, highest-reward differentiator.
2. **No tool projects point availability into the future.** Owners must do mental math combining use years, banking, borrowing, and existing reservations across multiple contracts. Our point timeline calculator solves this.
3. **No tool accounts for resale restrictions.** Resale owners (our target user) must mentally filter which resorts their contracts can access. We bake this into every query.
4. **No tool provides what-if scenario planning.** Banking and borrowing are irreversible. Letting users model these decisions before committing is uniquely valuable.
5. **Most tools are iOS-only.** Web-based approach is more accessible and avoids App Store friction.

## DVC Domain Concepts (Reference for Implementation)

Understanding these is critical for correct feature implementation:

| Concept | Rule | Impact on Features |
|---------|------|-------------------|
| **Use Year (UY)** | 8 possible start months (Feb, Mar, Apr, Jun, Aug, Sep, Oct, Dec). Points allocated at UY start. | Core date math for all point tracking. |
| **Banking** | Must bank within first 8 months of UY. Points move to next UY. Irreversible. Banked points can't be re-banked. | Banking deadline is the most critical reminder. Missed deadline = lost points. |
| **Borrowing** | Can borrow from next UY into current UY. Currently up to 100% (was 50% pre-pandemic, may revert). Irreversible. | Affects future-year point availability. Must track policy changes. |
| **Holding Account** | Cancel within 30 days of check-in: points go to holding account. Can only be used for reservations within 60 days. Can't bank or borrow. Expire at UY end. | Must track holding account points separately. Affects available point calculations. |
| **Booking Windows** | Home resort: 11 months before check-in. Non-home: 7 months. Max 7 consecutive nights per booking. | Key date calculations for reminders. |
| **Resale Restrictions** | Pre-Jan 2019: all 14 original resorts accessible. Post-Jan 2019 original 14: only those 14 (no Riviera, Disneyland Hotel, Fort Wilderness). Riviera/DLH/FW resale: home resort only. | Must filter resort availability per contract. |
| **Point Charts** | Published annually by Disney. 7 seasons, weekday/weekend rates, per resort/room/view. Minor yearly adjustments. | Static reference data, updated once per year. Need a reliable ingestion process. |
| **Annual Dues** | Per-point cost, varies by resort, changes annually. | Display only. Not core to point planning. |

## Sources

- [DVCHelp.com - DVC Tools & Trip Planner](https://www.dvchelp.com/page/dvc-tools) -- Most feature-complete web-based competitor
- [DVC Toolkit - App Store](https://apps.apple.com/us/app/dvc-toolkit/id1558277298) -- Best-reviewed iOS app with availability alerts
- [DVC Planner - App Store](https://apps.apple.com/us/app/dvc-planner/id330703403) -- iOS app with vacation planning and point management
- [DVC by D Point - App Store](https://apps.apple.com/us/app/dvc-by-d-point/id335895986) -- iOS app with Point Maximizer feature
- [DVC Trip Planner](https://dvctripplanner.com/) -- Web-based point comparison tool
- [DVCapp.com](https://www.dvcapp.com/) -- Availability monitoring with email/SMS alerts
- [DVC Fan - Point Charts](https://dvcfan.com/point-charts/) -- Point chart analysis and comparison
- [DVCRequest/David's Vacation Club - Cost Calculator](https://dvcrequest.com/dvc-guests/cost-calculator) -- Point-to-dollar cost calculator
- [DISboards - Point Tracker Spreadsheet threads](https://www.disboards.com/threads/my-points-tracker-spreadsheet.3948887/) -- Community spreadsheets showing what owners build themselves
- [DVC Field Guide - Banking Deadlines](https://dvcfieldguide.com/banking-deadlines) -- Comprehensive DVC deadline reference
- [DVC Resale Market - Resale Restrictions](https://www.dvcresalemarket.com/blog/new-dvc-resale-restrictions-and-who-is-most-impacted/) -- Resale restriction rules
- [Disney Vacation Club Official - Points Charts](https://disneyvacationclub.disney.go.com/vacation-planning/points-charts/) -- Official point chart source
- [Disney Vacation Club Official - Banking/Borrowing](https://disneyvacationclub.disney.go.com/points/bank-borrow/) -- Official banking/borrowing rules

---
*Feature research for: DVC Point Management & Vacation Planning Tool*
*Researched: 2026-02-09*
