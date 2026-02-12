# Phase 7: Seasonal Cost Heatmap - Research

**Researched:** 2026-02-11
**Domain:** Calendar heatmap visualization, DVC point chart data model, FastAPI endpoint design
**Confidence:** HIGH

## Summary

Phase 7 adds a full-year calendar heatmap where each day is color-coded by point cost, allowing users to visually compare pricing across seasons for any resort/room type combination. The existing codebase already contains **most of the building blocks**: a `SeasonCalendar` component with a 12-month grid (color-coded by season name), a `PointChartTable` with a `heatColor()` function mapping values to Tailwind classes, backend `get_point_cost()` and `get_season_for_date()` functions, and API endpoints serving full point charts and room lists. The heatmap can be built as a new tab on the existing Point Charts page or as a standalone page -- both patterns exist in the codebase.

The key architectural decision is where computation happens. The backend already has `get_point_cost(chart, room_key, date)` which resolves season + weekday/weekend for a single date. Rather than calling this 365 times from the frontend, a new backend endpoint should return a pre-computed array of daily costs for a full year, enabling a single API call. Alternatively, since the frontend already receives the full point chart via `GET /api/point-charts/{resort}/{year}`, the computation could happen entirely client-side -- the data is small (6 seasons, ~10 rooms each) and the algorithm is simple. **The client-side approach is recommended** because: (1) the full chart is already fetched, (2) the logic is trivially a ~30-line function, (3) it avoids a new endpoint, and (4) caching via React Query already works.

**Primary recommendation:** Build a `CostHeatmap` component that reuses the `SeasonCalendar` grid pattern but replaces season-based coloring with cost-based coloring, computes daily costs from the already-fetched `PointChart` data client-side, adds interactive hover tooltips, and integrates as a new tab ("Cost Heatmap") on the existing `PointChartsPage`. No new backend endpoint needed.

## Standard Stack

### Core (already installed -- no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | ^19.2.4 | UI framework | Already in use |
| Tailwind CSS | ^4.1.18 | Styling + heatmap colors | Already in use, color utility classes perfect for heatmaps |
| @tanstack/react-query | ^5.90.20 | Data fetching + caching | Already used for all API calls |
| date-fns | ^4.1.0 | Date formatting in tooltips | Already used in 4 components |
| shadcn/ui (new-york) | ^3.8.4 | UI primitives (Select, Card) | Already the design system |
| lucide-react | ^0.563.0 | Icons | Already used for icons |

### Supporting (already available)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| clsx + tailwind-merge | ^2.1.1 / ^3.4.0 | Conditional class merging | Used in `cn()` utility throughout |
| zustand | ^5.0.11 | State management | Not needed for this feature (no cross-page state) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pure Tailwind heatmap | D3.js or recharts | Heavy dependency for a simple calendar grid; the existing `SeasonCalendar` proves pure Tailwind works perfectly |
| Client-side cost computation | New backend `/api/point-charts/{resort}/{year}/heatmap/{room_key}` endpoint | Adds backend work for no real benefit; full chart data is already available client-side |
| Shadcn Tooltip component | Native `title` attribute | Shadcn Tooltip provides richer hover UX; worth adding via `npx shadcn@latest add tooltip` |

**Installation:**
```bash
# Only if tooltip component is needed (optional but recommended for HEAT-04):
cd frontend && npx shadcn@latest add tooltip
```

## Architecture Patterns

### Recommended Project Structure (new/modified files only)

```
frontend/src/
  components/
    CostHeatmap.tsx          # NEW: 12-month grid with cost-based coloring + tooltips
  pages/
    PointChartsPage.tsx      # MODIFIED: add "Cost Heatmap" tab
  lib/
    utils.ts                 # MODIFIED: add buildDailyCosts() helper (or keep in CostHeatmap)
```

### Pattern 1: Tab Extension on Existing Page

**What:** The `PointChartsPage` already uses a tab pattern (Point Chart / Season Calendar / Cost Calculator). Add a 4th tab "Cost Heatmap".
**When to use:** When new visualization shares the same resort/year/room selection context.
**Why this over a new page:** Avoids duplicating the resort/year selector, reuses existing data fetching hooks (`usePointChart`, `useChartRooms`).

**Example (existing pattern from PointChartsPage.tsx):**
```typescript
// Source: frontend/src/pages/PointChartsPage.tsx lines 20-26
type TabId = "chart" | "calendar" | "calculator" | "heatmap";  // add "heatmap"

const TABS: { id: TabId; label: string }[] = [
  { id: "chart", label: "Point Chart" },
  { id: "calendar", label: "Season Calendar" },
  { id: "calculator", label: "Cost Calculator" },
  { id: "heatmap", label: "Cost Heatmap" },  // NEW
];
```

### Pattern 2: Client-Side Daily Cost Computation

**What:** Transform the season-based point chart into a 365-day array with per-day cost, season name, and weekend flag.
**When to use:** When building the heatmap data from the already-fetched `PointChart`.
**Why not server-side:** The full chart JSON is ~5KB, already fetched by `usePointChart()`. The date-range-to-daily expansion is O(365) -- trivial.

**Algorithm:**
```typescript
interface DayCost {
  date: string;       // "2026-01-01"
  points: number;     // e.g. 14
  season: string;     // "Adventure"
  isWeekend: boolean;  // true for Fri/Sat (DVC definition)
  dayOfWeek: number;   // 0-6
}

function buildDailyCosts(chart: PointChart, roomKey: string): DayCost[] {
  const result: DayCost[] = [];
  const year = chart.year;

  // Build a date-to-season lookup (same pattern as SeasonCalendar)
  const seasonLookup: Map<string, { name: string; rooms: Record<string, { weekday: number; weekend: number }> }> = new Map();
  for (const season of chart.seasons) {
    for (const [startStr, endStr] of season.date_ranges) {
      const start = new Date(startStr + "T12:00:00");
      const end = new Date(endStr + "T12:00:00");
      const current = new Date(start);
      while (current <= end) {
        const key = current.toISOString().slice(0, 10);
        seasonLookup.set(key, season);
        current.setDate(current.getDate() + 1);
      }
    }
  }

  // Walk every day of the year
  const start = new Date(year, 0, 1);  // Jan 1
  const end = new Date(year, 11, 31);  // Dec 31
  const current = new Date(start);
  while (current <= end) {
    const dateStr = current.toISOString().slice(0, 10);
    const dayOfWeek = current.getDay();
    const isWeekend = dayOfWeek === 5 || dayOfWeek === 6; // Fri=5, Sat=6
    const season = seasonLookup.get(dateStr);
    const room = season?.rooms[roomKey];
    const points = room ? (isWeekend ? room.weekend : room.weekday) : 0;

    result.push({
      date: dateStr,
      points,
      season: season?.name ?? "Unknown",
      isWeekend,
      dayOfWeek,
    });
    current.setDate(current.getDate() + 1);
  }

  return result;
}
```

### Pattern 3: Quantile-Based Color Scale

**What:** Map point costs to a 5-tier color scale using the data's actual min/max range.
**When to use:** For the heatmap cell background colors.
**Why quantile, not absolute:** Different room types have vastly different ranges (Studio Standard: 14-36 pts, Bungalow Theme Park: 88-206 pts). A relative scale ensures each heatmap uses the full color gradient.

**Existing pattern (from PointChartTable.tsx):**
```typescript
// Source: frontend/src/components/PointChartTable.tsx lines 17-25
function heatColor(value: number, min: number, max: number): string {
  if (max === min) return "bg-green-100 dark:bg-green-900/30";
  const ratio = (value - min) / (max - min);
  if (ratio < 0.2) return "bg-green-100 dark:bg-green-900/30";
  if (ratio < 0.4) return "bg-lime-100 dark:bg-lime-900/30";
  if (ratio < 0.6) return "bg-yellow-100 dark:bg-yellow-900/30";
  if (ratio < 0.8) return "bg-orange-100 dark:bg-orange-900/30";
  return "bg-red-100 dark:bg-red-900/30";
}
```

**Recommendation:** Reuse exactly this `heatColor()` function. Extract it to `lib/utils.ts` so both `PointChartTable` and `CostHeatmap` can share it. The green-to-red gradient is intuitive (green = cheap, red = expensive) and already established in the app.

### Pattern 4: Room Type Selector with Existing Hook

**What:** Use `useChartRooms()` to get the room list, render a `<Select>` for room type selection.
**When to use:** The heatmap needs a room_key to look up costs. This pattern already exists in `StayCostCalculator`.

**Existing pattern (from StayCostCalculator.tsx):**
```typescript
// Source: frontend/src/components/StayCostCalculator.tsx lines 122-135
<Select value={roomKey} onValueChange={setRoomKey}>
  <SelectTrigger className="w-full">
    <SelectValue placeholder="Select room..." />
  </SelectTrigger>
  <SelectContent>
    {rooms.map((room) => (
      <SelectItem key={room.key} value={room.key}>
        {room.room_type} - {room.view}
      </SelectItem>
    ))}
  </SelectContent>
</Select>
```

### Pattern 5: Tooltip on Hover

**What:** Show date, season name, point cost, and weekday/weekend on hover over each calendar cell.
**Existing approach:** The `SeasonCalendar` uses native `title` attribute for basic hover info:
```typescript
title={`${dateKey}${seasonName ? ` - ${seasonName}` : ""}${isWeekend ? " (weekend)" : ""}`}
```
**Recommended upgrade:** Install shadcn `Tooltip` for richer display. Or use a custom positioned tooltip with Tailwind for more control without adding a dependency.

**Simple custom tooltip pattern (no new component):**
```typescript
// Tooltip state managed in parent component
const [tooltip, setTooltip] = useState<{ x: number; y: number; data: DayCost } | null>(null);

// On cell hover:
onMouseEnter={(e) => setTooltip({
  x: e.clientX, y: e.clientY,
  data: dayCost
})}
onMouseLeave={() => setTooltip(null)}

// Tooltip render:
{tooltip && (
  <div
    className="fixed z-50 bg-popover text-popover-foreground border rounded-lg shadow-lg px-3 py-2 text-sm pointer-events-none"
    style={{ left: tooltip.x + 12, top: tooltip.y + 12 }}
  >
    <div className="font-semibold">{format(parseISO(tooltip.data.date), "EEEE, MMM d, yyyy")}</div>
    <div>Season: {tooltip.data.season}</div>
    <div>Cost: {tooltip.data.points} points ({tooltip.data.isWeekend ? "Weekend" : "Weekday"})</div>
  </div>
)}
```

### Anti-Patterns to Avoid

- **365 individual API calls:** Do NOT call `/api/point-charts/calculate` for each day. Compute client-side from the already-fetched chart data.
- **New page with duplicated selectors:** Do NOT create a separate `/heatmap` page. The `PointChartsPage` already has resort/year selection; add a tab.
- **Canvas/SVG-based rendering:** Do NOT use canvas or SVG for the calendar grid. The existing `SeasonCalendar` proves that a CSS grid with Tailwind renders perfectly and is fully accessible.
- **Tooltip library dependency:** Do NOT add a heavy tooltip library (tippy.js, react-tooltip). Either use shadcn Tooltip (already in design system) or a simple positioned div.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Calendar grid layout | Custom calendar logic | Copy `SeasonCalendar` MonthGrid pattern | Already handles month padding, day-of-week alignment, weekend detection |
| Color scale | Custom color interpolation | Reuse `heatColor()` from PointChartTable | Already maps 5 tiers with dark mode support |
| Resort/room selectors | New selector components | Reuse `useAvailableCharts`, `useChartRooms`, Select pattern from PointChartsPage | Proven data flow, consistent UX |
| Date formatting | Manual date string manipulation | `date-fns` format/parseISO | Already imported in 4 components, handles timezone edge cases |
| Season-to-date mapping | New lookup algorithm | Copy `dateSeasonMap` useMemo from SeasonCalendar | Identical problem, proven implementation |

**Key insight:** This phase is primarily a frontend visualization task. Nearly every building block already exists in the codebase. The work is composing existing patterns into a new component, not building new infrastructure.

## Common Pitfalls

### Pitfall 1: Weekend Definition Mismatch
**What goes wrong:** Using JavaScript's `getDay()` (0=Sun, 6=Sat) but DVC defines weekend as Friday (day 5) + Saturday (day 6), not Saturday + Sunday.
**Why it happens:** Common assumption that "weekend" means Sat-Sun.
**How to avoid:** DVC weekend = Friday + Saturday. This is already correctly implemented in both the backend (`target_date.weekday() in (4, 5)` -- Python weekday where Mon=0, Fri=4, Sat=5) and the existing `SeasonCalendar` component (`dow === 5 || dow === 6` -- JS getDay where Sun=0, Fri=5, Sat=6). Copy the existing check exactly.
**Warning signs:** Weekend dots appearing on wrong days; cost values not matching the point chart table.

### Pitfall 2: Timezone Date Shift
**What goes wrong:** `new Date("2026-01-01")` may create Dec 31 2025 23:00 in some timezones, shifting all date calculations by one day.
**Why it happens:** ISO date strings without time component are parsed as UTC midnight, which shifts backwards in negative-UTC timezones.
**How to avoid:** The existing code uses `new Date(dateStr + "T00:00:00")` (local midnight) or `new Date(year, month, day)` (explicit components). Follow this pattern. The `SeasonCalendar` uses `new Date(startStr + "T00:00:00")` -- copy this approach.
**Warning signs:** First/last day of month appearing in wrong month; season boundaries off by one day.

### Pitfall 3: Missing Room Key After Resort Switch
**What goes wrong:** User selects resort A, picks a room, then switches to resort B. The old room_key doesn't exist in resort B's chart, causing the heatmap to show all zeros or crash.
**Why it happens:** Room keys are resort-specific (Polynesian has `bungalow_lake`, Riviera has `tower_studio_standard`).
**How to avoid:** Reset room_key selection when resort changes (pattern already exists in PointChartsPage via useEffect). Auto-select first available room when room list changes.
**Warning signs:** Empty heatmap after switching resorts; console errors about undefined room data.

### Pitfall 4: Dark Mode Color Contrast
**What goes wrong:** Heatmap colors are unreadable in dark mode because only light-mode Tailwind classes were used.
**Why it happens:** Forgetting to add `dark:` variants for background colors.
**How to avoid:** The existing `heatColor()` function already includes dark mode variants (e.g., `bg-green-100 dark:bg-green-900/30`). Reuse it as-is.
**Warning signs:** Colors invisible or washed out when system dark mode is active.

### Pitfall 5: Performance with useMemo
**What goes wrong:** Heatmap recomputes 365-day array on every render, causing visible lag when hovering.
**Why it happens:** `buildDailyCosts()` inside render without memoization.
**How to avoid:** Wrap in `useMemo` with `[chart, roomKey]` dependencies. The existing `SeasonCalendar` demonstrates this pattern with its `dateSeasonMap` memo.
**Warning signs:** Tooltip hover feels sluggish; React DevTools shows excessive re-renders.

## Code Examples

### Full CostHeatmap Component Structure (verified patterns from codebase)

```typescript
// Source: Composed from SeasonCalendar.tsx + PointChartTable.tsx patterns
import { useMemo, useState } from "react";
import { format, parseISO } from "date-fns";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PointChart, RoomInfo } from "../types";

interface CostHeatmapProps {
  chart: PointChart;
  rooms: RoomInfo[];
}

// Reusable from PointChartTable -- extract to lib/utils.ts
function heatColor(value: number, min: number, max: number): string {
  if (max === min) return "bg-green-100 dark:bg-green-900/30";
  const ratio = (value - min) / (max - min);
  if (ratio < 0.2) return "bg-green-100 dark:bg-green-900/30";
  if (ratio < 0.4) return "bg-lime-100 dark:bg-lime-900/30";
  if (ratio < 0.6) return "bg-yellow-100 dark:bg-yellow-900/30";
  if (ratio < 0.8) return "bg-orange-100 dark:bg-orange-900/30";
  return "bg-red-100 dark:bg-red-900/30";
}
```

### Backend Data Shape Already Available

The existing `GET /api/point-charts/{resort}/{year}` endpoint returns:
```json
{
  "resort": "polynesian",
  "year": 2026,
  "seasons": [
    {
      "name": "Adventure",
      "date_ranges": [["2026-01-01", "2026-01-31"], ["2026-09-01", "2026-09-30"]],
      "rooms": {
        "deluxe_studio_standard": { "weekday": 14, "weekend": 19 },
        "deluxe_studio_lake": { "weekday": 22, "weekend": 28 }
      }
    }
  ]
}
```

This is all the data needed. No new backend endpoint required.

### Room List Already Available

The existing `GET /api/point-charts/{resort}/{year}/rooms` returns:
```json
{
  "resort": "polynesian",
  "year": 2026,
  "rooms": [
    { "key": "deluxe_studio_standard", "room_type": "Deluxe Studio", "view": "Standard" },
    { "key": "deluxe_studio_lake", "room_type": "Deluxe Studio", "view": "Lake" }
  ]
}
```

Both are already fetched on the `PointChartsPage`.

### Existing SeasonCalendar MonthGrid (template for heatmap grid)

```typescript
// Source: frontend/src/components/SeasonCalendar.tsx lines 114-163
// This MonthGrid handles:
// - First-day-of-month offset (padding empty cells)
// - 7-column CSS grid
// - Day-of-week headers (S M T W T F S)
// - Weekend dot indicator
// - Season-based cell coloring with title tooltip
// The CostHeatmap MonthGrid will be nearly identical but replace:
//   - Season-color lookup -> heatColor(cost, min, max)
//   - title text -> richer tooltip with cost
//   - Optional: point value number inside cell (space permitting)
```

### Color Legend for Heatmap

```typescript
// 5-tier legend matching heatColor() thresholds
const COST_TIERS = [
  { label: "Low", bg: "bg-green-100 dark:bg-green-900/30", legend: "bg-green-400" },
  { label: "Below Avg", bg: "bg-lime-100 dark:bg-lime-900/30", legend: "bg-lime-400" },
  { label: "Average", bg: "bg-yellow-100 dark:bg-yellow-900/30", legend: "bg-yellow-400" },
  { label: "Above Avg", bg: "bg-orange-100 dark:bg-orange-900/30", legend: "bg-orange-400" },
  { label: "High", bg: "bg-red-100 dark:bg-red-900/30", legend: "bg-red-400" },
];
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| D3.js calendar heatmaps | CSS Grid + Tailwind utility classes | Tailwind v3+ (2022+) | No JS library needed for layout; Tailwind handles responsive grid + colors |
| react-tooltip for tooltips | CSS-only or shadcn Tooltip (Radix) | 2024+ | Less bundle size, better accessibility |
| Server-computed heatmap data | Client-side computation from cached data | React Query era | Simpler API, instant re-render on room change |

**No deprecated patterns in this phase.** All technologies in use are current.

## Data Model Details

### DVC Point Chart Structure (HIGH confidence -- verified from actual data files)

**Seasons per resort:** 6 named seasons (Adventure, Choice, Dream, Magic, Premier, Select)
**Date coverage:** Every day of the year belongs to exactly one season (no gaps, no overlaps)
**Non-contiguous seasons:** A season can have multiple date ranges (e.g., Adventure covers both January and September)
**Room keys:** Composite `{room_type}_{view_category}` (e.g., `deluxe_studio_standard`)
**Pricing:** Each room in each season has `weekday` and `weekend` integer point costs
**Weekend definition:** Friday + Saturday (NOT Saturday + Sunday)

### Point Cost Ranges (from actual data)

**Polynesian 2026:**
- Cheapest: 14 pts/night (Deluxe Studio Standard, Adventure weekday)
- Most expensive: 206 pts/night (Bungalow Theme Park, Premier weekend)
- Range factor: ~15x between cheapest and most expensive

**Riviera 2026:**
- Cheapest: 10 pts/night (Tower Studio Standard, Adventure weekday)
- Most expensive: 174 pts/night (Grand Villa Preferred, Premier weekend)
- Range factor: ~17x

### Rooms per Resort (from actual data)
- Polynesian: 11 room/view combos
- Riviera: 10 room/view combos
- Other resorts: typically 4-12 depending on room types and view categories

### Available Charts
- Currently: 2 charts (polynesian_2026, riviera_2026)
- More will be added over time via JSON files in `data/point_charts/`

## Implementation Approach: No New Backend Endpoint Needed

**Why no new endpoint is needed:**

1. `GET /api/point-charts/{resort}/{year}` already returns the full chart with all seasons, date ranges, and room costs
2. `GET /api/point-charts/{resort}/{year}/rooms` already returns parsed room types
3. Both are already fetched by `PointChartsPage` using `usePointChart()` and `useChartRooms()`
4. The daily cost computation from chart data is ~30 lines of TypeScript (see Pattern 2 above)
5. React Query caches the data (5-min staleTime configured), so switching rooms is instant
6. The data is static (point charts don't change mid-year), so no freshness concerns

**If a backend endpoint were later desired** (e.g., for HEAT-05 "affordable dates overlay" in v2+), the backend already has `get_point_cost(chart, room_key, date)` and `get_season_for_date(chart, date)` in `backend/data/point_charts.py` that could be composed into a `/heatmap` endpoint.

## Open Questions

1. **Should the heatmap show point values inside cells?**
   - What we know: Calendar cells are 28px tall (h-7 in SeasonCalendar). Point values are 2-3 digits. Fitting both the day number and point cost is tight.
   - What's unclear: Whether users want to see numbers or just colors.
   - Recommendation: Show day number only (like SeasonCalendar), rely on color + hover for cost. Optionally show cost instead of day number as a toggle.

2. **Should room selector be inside the heatmap or shared with the page?**
   - What we know: PointChartsPage has resort/year selectors shared across tabs. The Cost Calculator tab has its own room selector.
   - What's unclear: UX preference.
   - Recommendation: Follow StayCostCalculator pattern -- room selector lives inside the CostHeatmap component, scoped to the heatmap tab. This matches existing patterns and avoids overloading the page-level selectors.

3. **Tab placement: 4th tab or replace Season Calendar?**
   - What we know: Season Calendar shows season names color-coded. Cost Heatmap shows costs color-coded. They're related but distinct views.
   - What's unclear: Whether having both is confusing.
   - Recommendation: Keep both. Season Calendar answers "what season is this date?" while Cost Heatmap answers "how expensive is this date for my room?" They complement each other.

## Sources

### Primary (HIGH confidence)
- **Codebase inspection** -- All file paths, function signatures, data shapes, and patterns verified by reading actual source files
  - `data/point_charts/schema.json` -- Point chart JSON schema
  - `data/point_charts/polynesian_2026.json` -- Example point chart data (125 lines)
  - `data/point_charts/riviera_2026.json` -- Example point chart data (119 lines)
  - `data/resorts.json` -- All 16 DVC resorts with room types and view categories
  - `backend/data/point_charts.py` -- `load_point_chart()`, `get_season_for_date()`, `get_point_cost()`, `calculate_stay_cost()`
  - `backend/api/point_charts.py` -- Existing API endpoints (GET chart, GET rooms, GET seasons, POST calculate)
  - `frontend/src/components/SeasonCalendar.tsx` -- 12-month calendar grid with season coloring (164 lines)
  - `frontend/src/components/PointChartTable.tsx` -- `heatColor()` function, table rendering (112 lines)
  - `frontend/src/pages/PointChartsPage.tsx` -- Tab pattern, resort/year selectors (192 lines)
  - `frontend/src/components/StayCostCalculator.tsx` -- Room selector pattern (208 lines)
  - `frontend/src/hooks/usePointCharts.ts` -- `usePointChart()`, `useChartRooms()`, `useChartSeasons()`
  - `frontend/src/types/index.ts` -- TypeScript interfaces for PointChart, Season, RoomInfo
  - `frontend/src/lib/api.ts` -- API client wrapper
  - `frontend/package.json` -- All dependencies verified

### Secondary (MEDIUM confidence)
- Tailwind CSS color utilities -- verified via existing usage patterns in codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already installed and in active use
- Architecture: HIGH - All patterns verified from existing codebase; this is pattern composition, not new architecture
- Pitfalls: HIGH - Weekend definition, timezone issues, and room key reset all verified from existing code patterns
- Data model: HIGH - Verified from actual JSON data files and backend code

**Research date:** 2026-02-11
**Valid until:** Indefinite (data model and codebase patterns are stable; no external dependencies to go stale)
