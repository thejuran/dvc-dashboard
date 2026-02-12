# DVC Dashboard

**A self-hosted web app for managing Disney Vacation Club points across multiple contracts.**

![CI](https://github.com/thejuran/dvc-dashboard/actions/workflows/ci.yml/badge.svg)
![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)

<!-- TODO: Add screenshot of dashboard -->
*(Screenshot coming soon)*

## What It Does

DVC Dashboard gives you a unified view of your Disney Vacation Club ownership. For any future date, it shows available points across all your contracts and what resorts and rooms those points can actually book -- accounting for banking, borrowing, existing reservations, and resale restrictions.

The official DVC website doesn't provide cross-contract planning views. DVC Dashboard fills that gap with a self-hosted web app that runs entirely on your machine -- no cloud services, no accounts, no data leaving your network.

## Features

**Point Management**

- Track multiple contracts with home resort, points per year, and use year
- Point balances with banking from prior year and borrowing from next year
- Use year timelines showing availability by period with expiration tracking
- Resale vs. direct contract distinction with automatic resort eligibility filtering

**Trip Planning**

- Trip Explorer: search bookable resort/room options for your dates and point budget
- Booking impact preview: see before/after point balances before committing
- Booking window alerts: 11-month home resort and 7-month any-resort opening dates
- Reservation tracking with automatic point deductions

**Analysis**

- What-if scenario playground: model up to 10 hypothetical bookings and see cumulative impact
- Seasonal cost heatmap: full-year calendar with per-day cost coloring and room comparison
- Availability calendar across all contracts
- Dashboard with summary cards, urgent alerts, and upcoming reservations

**Technical**

- Docker self-hosting with `docker compose up`
- SQLite database (zero config, easy backups)
- Mobile responsive design
- Structured error handling with field-level validation
- Pre-seeded point chart data (Polynesian and Riviera 2026)

## Quickstart

```bash
git clone https://github.com/thejuran/dvc-dashboard.git
cd dvc-dashboard
cp .env.example .env
docker compose up
```

Visit **http://localhost:8000**. The app starts with pre-seeded point charts (Polynesian and Riviera 2026) -- just add your contracts to get started.

To stop: `docker compose down` (data persists in a Docker volume).
To reset: `docker compose down -v` (deletes the database).
To update: `git pull && docker compose up -d --build`

See the [Setup Guide](docs/setup.md) for local development setup and configuration options.

## Documentation

- [Setup Guide](docs/setup.md) -- Docker deployment, local dev, configuration
- [Architecture](docs/architecture.md) -- System design, components, data model
- [API Reference](docs/api-reference.md) -- REST endpoints
- [Contributing](CONTRIBUTING.md) -- How to contribute

## Tech Stack

FastAPI | SQLAlchemy | React 19 | Vite | TypeScript | Tailwind CSS 4 | shadcn/ui | SQLite | Docker

## License

This project is licensed under the GNU General Public License v3.0 -- see the [LICENSE](LICENSE) file for details.
