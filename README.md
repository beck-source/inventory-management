# Factory Inventory Management System

A full-stack demo application for a Claude Code workshop — inventory management, order tracking, demand forecasting, and analytics for factory operations.

![Dashboard](docs/dashboard-screenshot.png)

## Tech Stack

- **Frontend**: Vue 3 (Composition API) + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: In-memory mock data (no database)

## Features

- **Dashboard** — KPIs, order-health donut, inventory value, shortages, and top products, all filter-aware
- **Inventory** — stock-level tracking across multiple warehouses, with search
- **Orders** — order management with status tracking
- **Demand forecasting** — trend analysis (increasing / stable / decreasing)
- **Backlog** — inventory-shortage tracking by priority (at `/backlog`)
- **Performance reports** — quarterly metrics and month-over-month revenue trends (at `/reports`)
- **Restocking** — budget-based reorder recommendations driven by the demand forecast
- **Finance** — revenue, cost, and spending analytics
- **Global filter bar** — Time Period / Warehouse / Category / Order Status filters applied consistently across every page
- **Bilingual UI** — full English / 日本語 localization with locale-aware currency (USD/JPY) and date formatting
- **Dark theme** — a midnight-navy + orange design system built on CSS custom properties

## Quick Start

**One-command startup:**
```bash
./scripts/start.sh
# Starts both backend and frontend
# Backend: http://localhost:8001
# Frontend: http://localhost:3000
# API Docs: http://localhost:8001/docs
```

**Manual startup:**

Backend:
```bash
cd server
uv venv && uv sync
uv run python main.py
```

Frontend:
```bash
cd client
npm install
npm run dev
```

## API Endpoints

Most endpoints support optional filtering via query params: `warehouse`, `category`, `status`, `month`

- `GET /api/inventory` - Inventory items
- `GET /api/orders` - Orders
- `GET /api/demand` - Demand forecasts
- `GET /api/backlog` - Backlog items
- `GET /api/dashboard/summary` - Summary statistics
- `GET /api/reports/quarterly` - Quarterly performance (orders, revenue, fulfillment rate)
- `GET /api/reports/monthly-trends` - Month-over-month revenue trends
- `GET /api/spending/*` - Spending data

## Internationalization & Theming

- **Languages:** English and Japanese, switchable from the header. The choice persists (localStorage) and drives the currency symbol (USD → `$`, JPY → `¥`) and date formats. Translation strings live in `client/src/locales/{en,ja}.js`.
- **Theme:** a dark midnight-navy + orange palette defined as CSS design tokens in `client/src/App.vue` (`:root`). Every view and component references `var(--*)` tokens, so the entire look can be re-tuned by editing that one block — surfaces, accent, status colors, and chart colors included.

## Demo Data

Mock data includes:
- Inventory items (Circuit Boards, Sensors, Actuators, Controllers, Power Supplies)
- Orders spanning 12 months (Delivered, Shipped, Processing, Backordered)
- Demand forecasts with trends
- Backlog items
- Spending transactions

Data files: `server/data/*.json`

## Production Build

```bash
cd client
npm run build  # Output: client/dist/
```

## Platform Notes

**macOS/Linux:** The one-command startup script (`./scripts/start.sh`) and stop script (`./scripts/stop.sh`) work out of the box.

**Windows:** The shell scripts in `scripts/` are macOS/Linux only. Use the manual startup commands instead — run each in a separate terminal:

Backend:
```bash
cd server
uv venv && uv sync
uv run python main.py
```

Frontend:
```bash
cd client
npm install
npm run dev
```

To stop the servers, press Ctrl+C in each terminal window.

---

**Note:** Demo application with in-memory data. Not production-ready without database, authentication, and security implementation.
