# API Reference

Base URL: `http://localhost:8000`

All endpoints return JSON. Errors follow a consistent format:

```json
{
  "error": {
    "type": "VALIDATION_ERROR",
    "message": "Human readable message",
    "fields": [{"field": "field_name", "issue": "Field-specific error"}]
  }
}
```

Error types: `VALIDATION_ERROR` (422), `NOT_FOUND` (404), `CONFLICT` (409), `SERVER_ERROR` (500).

---

## Health

### `GET /api/health`

Returns server status.

**Response:**
```json
{"status": "ok", "version": "0.1.0"}
```

## Resorts

### `GET /api/resorts`

List all DVC resort metadata (loaded from `data/resorts.json`).

**Response:** Array of resort objects with slug, name, view categories, and other metadata.

---

## Contracts

### `GET /api/contracts`

List all contracts with point balances, eligible resorts, and use year timeline.

**Response:** Array of `ContractWithDetails` objects.

### `GET /api/contracts/{contract_id}`

Get a single contract with full details.

**Path params:** `contract_id` (int)

**Response:** `ContractWithDetails` object.

### `POST /api/contracts`

Create a new contract. Returns `201`.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | No | Friendly name (max 100 chars) |
| `home_resort` | string | Yes | Resort slug (must be valid from `/api/resorts`) |
| `use_year_month` | int | Yes | One of: 2, 3, 4, 6, 8, 9, 10, 12 |
| `annual_points` | int | Yes | 1--2000 |
| `purchase_type` | string | Yes | `"resale"` or `"direct"` |

**Example:**
```bash
curl -X POST http://localhost:8000/api/contracts \
  -H "Content-Type: application/json" \
  -d '{"home_resort": "polynesian", "use_year_month": 6, "annual_points": 200, "purchase_type": "direct"}'
```

**Response:**
```json
{
  "id": 1,
  "name": null,
  "home_resort": "polynesian",
  "use_year_month": 6,
  "annual_points": 200,
  "purchase_type": "direct",
  "created_at": "2026-01-15T10:30:00",
  "updated_at": "2026-01-15T10:30:00"
}
```

### `PUT /api/contracts/{contract_id}`

Partial update of a contract. Only send fields you want to change.

**Request body:** Same fields as POST, all optional.

### `DELETE /api/contracts/{contract_id}`

Delete a contract. Cascade-deletes associated point balances and reservations. Returns `204`.

---

## Point Balances

### `GET /api/contracts/{contract_id}/points`

List point balances for a contract, grouped by use year.

**Response:**
```json
{
  "contract_id": 1,
  "contract_name": "Our Poly contract",
  "annual_points": 200,
  "balances_by_year": {
    "2026": {"current": 200, "banked": 50, "borrowed": 0, "holding": 0, "total": 250}
  },
  "grand_total": 250
}
```

### `POST /api/contracts/{contract_id}/points`

Add a point balance entry. Returns `201`. Duplicate (same contract + use year + allocation type) returns `409`.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `use_year` | int | Yes | 2020--2035 |
| `allocation_type` | string | Yes | `"current"`, `"banked"`, `"borrowed"`, or `"holding"` |
| `points` | int | Yes | 0--4000 |

### `PUT /api/points/{balance_id}`

Update a point balance entry.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `points` | int | Yes | 0--4000 |

### `DELETE /api/points/{balance_id}`

Delete a point balance entry. Returns `204`.

### `GET /api/contracts/{contract_id}/timeline`

Get the use year timeline for a contract (current and next use year periods, deadlines).

**Response:**
```json
{
  "contract_id": 1,
  "use_year_month": 6,
  "timelines": [
    {"use_year": 2026, "start": "2026-06-01", "end": "2027-05-31", "banking_deadline": "2027-01-31", ...},
    {"use_year": 2027, "start": "2027-06-01", "end": "2028-05-31", ...}
  ]
}
```

---

## Reservations

### `GET /api/reservations`

List all reservations with optional filters.

**Query params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `contract_id` | int | -- | Filter by contract |
| `status` | string | -- | Filter by status (`confirmed`, `pending`, `cancelled`) |
| `upcoming` | bool | `false` | Only future check-in dates |

**Response:** Array of `ReservationResponse` objects.

### `GET /api/contracts/{contract_id}/reservations`

List reservations for a specific contract, ordered by check-in date.

### `GET /api/reservations/{reservation_id}`

Get a single reservation.

### `POST /api/contracts/{contract_id}/reservations`

Create a reservation for a contract. Returns `201`. Validates resort eligibility against the contract's purchase type.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `resort` | string | Yes | Resort slug (must be eligible for the contract) |
| `room_key` | string | Yes | Room type key, e.g. `"deluxe_studio_lake"` (max 100 chars) |
| `check_in` | date | Yes | ISO format `YYYY-MM-DD` |
| `check_out` | date | Yes | Must be after check_in, max 14 nights |
| `points_cost` | int | Yes | 1--4000 |
| `status` | string | No | `"confirmed"` (default), `"pending"`, or `"cancelled"` |
| `confirmation_number` | string | No | Max 50 chars |
| `notes` | string | No | Max 500 chars |

### `POST /api/reservations/preview`

Preview the impact of a proposed reservation on point balances before creating it. Returns before/after availability snapshots, nightly cost breakdown, booking window status, and banking warnings.

**Request body:**

| Field | Type | Required |
|---|---|---|
| `contract_id` | int | Yes |
| `resort` | string | Yes |
| `room_key` | string | Yes |
| `check_in` | date | Yes |
| `check_out` | date | Yes |

**Example response:**
```json
{
  "before": {"total_points": 250, "committed_points": 80, "available_points": 170, "balances": {}},
  "after": {"total_points": 250, "committed_points": 192, "available_points": 58, "balances": {}},
  "points_delta": -112,
  "total_points": 112,
  "num_nights": 7,
  "nightly_breakdown": [{"date": "2026-06-15", "day_of_week": "Monday", "season": "Premier", "is_weekend": false, "points": 16}],
  "booking_windows": {"home_resort_window": "2025-07-15", "home_resort_window_open": true, ...},
  "banking_warning": null
}
```

### `PUT /api/reservations/{reservation_id}`

Partial update of a reservation. Same fields as create, all optional.

### `DELETE /api/reservations/{reservation_id}`

Delete a reservation. Returns `204`.

---

## Point Charts

### `GET /api/point-charts`

List available point charts (resort + year summaries).

**Response:**
```json
[{"resort": "polynesian", "year": 2025, "file": "polynesian_2025.json"}]
```

### `GET /api/point-charts/{resort}/{year}`

Get the full point chart for a resort and year, including all seasons, room types, and weekday/weekend costs.

### `GET /api/point-charts/{resort}/{year}/rooms`

List parsed room types for a chart, with room type name and view category.

**Response:**
```json
{"resort": "polynesian", "year": 2025, "rooms": [{"key": "deluxe_studio_lake", "room_type": "Deluxe Studio", "view": "Lake"}]}
```

### `GET /api/point-charts/{resort}/{year}/seasons`

List season names and date ranges for a chart (without room costs).

### `POST /api/point-charts/calculate`

Calculate total stay cost for a given resort, room, and date range. Returns nightly breakdown with per-night season and points.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `resort` | string | Yes | Resort slug (max 50 chars) |
| `room_key` | string | Yes | Room type key (max 100 chars) |
| `check_in` | string | Yes | ISO date `YYYY-MM-DD` |
| `check_out` | string | Yes | ISO date `YYYY-MM-DD`, max 14 nights |

**Response:**
```json
{
  "resort": "polynesian",
  "room": "deluxe_studio_lake",
  "check_in": "2026-06-15",
  "check_out": "2026-06-22",
  "num_nights": 7,
  "total_points": 112,
  "nightly_breakdown": [{"date": "2026-06-15", "day_of_week": "Monday", "season": "Premier", "is_weekend": false, "points": 16}]
}
```

---

## Availability

### `GET /api/availability`

Calculate point availability across all contracts for a target date.

**Query params:**

| Param | Type | Required | Description |
|---|---|---|---|
| `target_date` | date | Yes | ISO format `YYYY-MM-DD` (year 2020--2040) |

**Response:** Per-contract breakdown with use year status, point balances by allocation type, committed points from reservations, available points, banking deadline status. Plus a summary with grand totals.

---

## Trip Explorer

### `GET /api/trip-explorer`

Search for affordable resort/room options across all contracts for given dates. Composes availability, eligibility, and cost calculation to answer "what can I afford?"

**Query params:**

| Param | Type | Required | Description |
|---|---|---|---|
| `check_in` | date | Yes | ISO format `YYYY-MM-DD` |
| `check_out` | date | Yes | ISO format `YYYY-MM-DD`, max 14 nights |

**Example:**
```bash
curl "http://localhost:8000/api/trip-explorer?check_in=2026-06-15&check_out=2026-06-22"
```

**Response:**
```json
{
  "check_in": "2026-06-15",
  "check_out": "2026-06-22",
  "num_nights": 7,
  "options": [
    {"contract_id": 1, "contract_name": "Poly", "available_points": 170, "resort": "polynesian", "resort_name": "Disney's Polynesian Village", "room_key": "deluxe_studio_lake", "total_points": 112, "num_nights": 7, "points_remaining": 58, "nightly_avg": 16}
  ],
  "resorts_checked": ["polynesian", "grand_floridian"],
  "resorts_skipped": [],
  "total_options": 1
}
```

---

## Booking Windows

### `GET /api/booking-windows/upcoming`

Get upcoming booking window openings for existing reservations (11-month home resort and 7-month any-resort windows).

**Query params:**

| Param | Type | Default | Description |
|---|---|---|---|
| `days` | int | `30` | Look-ahead window in days (1--90) |

**Response:** Array of up to 5 alerts sorted by soonest opening, each with contract name, resort, check-in date, window type, window open date, and days until open.

---

## Scenarios

### `POST /api/scenarios/evaluate`

Evaluate a what-if scenario with multiple hypothetical bookings. Returns baseline vs scenario availability per contract, resolved booking costs, and any errors.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `hypothetical_bookings` | array | Yes | Max 10 bookings |

Each booking:

| Field | Type | Required |
|---|---|---|
| `contract_id` | int | Yes |
| `resort` | string | Yes |
| `room_key` | string | Yes |
| `check_in` | date | Yes |
| `check_out` | date | Yes |

**Example:**
```bash
curl -X POST http://localhost:8000/api/scenarios/evaluate \
  -H "Content-Type: application/json" \
  -d '{"hypothetical_bookings": [{"contract_id": 1, "resort": "polynesian", "room_key": "deluxe_studio_lake", "check_in": "2026-06-15", "check_out": "2026-06-22"}]}'
```

**Response:**
```json
{
  "contracts": [
    {"contract_id": 1, "contract_name": "Poly", "home_resort": "polynesian", "baseline_available": 170, "baseline_total": 250, "baseline_committed": 80, "scenario_available": 58, "scenario_total": 250, "scenario_committed": 192, "impact": 112}
  ],
  "summary": {"baseline_available": 170, "scenario_available": 58, "total_impact": 112, "num_hypothetical_bookings": 1},
  "resolved_bookings": [{"contract_id": 1, "resort": "polynesian", "room_key": "deluxe_studio_lake", "check_in": "2026-06-15", "check_out": "2026-06-22", "points_cost": 112, "num_nights": 7}],
  "errors": []
}
```

---

## Settings

### `GET /api/settings`

List all app settings.

**Response:**
```json
[{"key": "borrowing_limit_pct", "value": "100"}]
```

### `GET /api/settings/{key}`

Get a single setting by key.

### `PUT /api/settings/{key}`

Update a setting value. Only known keys with valid values are accepted.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `value` | string | Yes | Max 50 chars. Allowed values depend on the key. |

Currently supported settings:

| Key | Allowed Values | Default | Description |
|---|---|---|---|
| `borrowing_limit_pct` | `"50"`, `"100"` | `"100"` | Maximum percentage of annual points that can be borrowed from the next use year |
