# Factory Inventory Management — Architecture

## System Overview

A full-stack demo application for factory inventory tracking. No database — all data lives in JSON files loaded into memory at server startup.

```
┌─────────────────┐     HTTP/JSON      ┌─────────────────┐     import      ┌─────────────┐
│  Vue 3 SPA      │ ─────────────────> │  FastAPI        │ ──────────────> │  JSON files │
│  (port 3000)    │ <───────────────── │  (port 8001)    │  at startup     │  server/data│
└─────────────────┘                    └─────────────────┘                 └─────────────┘
      │                                       │
      │                                       │
  Vite dev server                       In-memory lists
  Vue Router (7 views)                  Pydantic validation
  Axios client                          List-comprehension filters
```

## Tech Stack

| Layer      | Technology                          | Purpose                              |
|------------|-------------------------------------|--------------------------------------|
| Frontend   | Vue 3 (Composition API)             | Reactive UI                          |
| Router     | Vue Router 4                        | Client-side navigation               |
| HTTP       | Axios                               | API calls                            |
| Build      | Vite 5                              | Dev server + bundler                 |
| Backend    | FastAPI                             | REST API                             |
| Validation | Pydantic 2                          | Response model enforcement           |
| Server     | Uvicorn                             | ASGI runtime                         |
| Data       | JSON files (no DB)                  | Loaded once at import time           |
| Testing    | pytest + httpx + FastAPI TestClient | Backend only                         |

## Frontend Structure

```
client/src/
├── views/              7 route-level pages
│   ├── Dashboard.vue   KPI summary + charts
│   ├── Inventory.vue   Stock levels by SKU
│   ├── Orders.vue      Order list (250 records)
│   ├── Demand.vue      Forecasts
│   ├── Backlog.vue     Pending items
│   ├── Spending.vue    Cost breakdown
│   └── Reports.vue     Quarterly + monthly trends
├── components/         8 modals + FilterBar + ProfileMenu + LanguageSwitcher
├── composables/
│   ├── useFilters.js   Shared filter state (warehouse, category, status, month)
│   ├── useAuth.js      Auth state
│   └── useI18n.js      en/ja locale switching
├── api.js              Axios wrapper — builds query strings from filter state
└── App.vue             Shell + global styles
```

## Backend Structure

```
server/
├── main.py             FastAPI app, 14 routes, Pydantic models, filter helpers
├── mock_data.py        Loads all JSON → module-level lists at import time
├── generate_data.py    Seed-data generator (dev utility)
└── data/
    ├── inventory.json        32 items
    ├── orders.json           250 records
    ├── demand_forecasts.json 9 records
    ├── backlog_items.json    4 records
    ├── spending.json         summary + monthly + category
    ├── transactions.json     56 records
    └── purchase_orders.json  empty
```

## API Surface

| Endpoint                       | Filters                             | Returns           |
|--------------------------------|-------------------------------------|-------------------|
| `GET /api/inventory`           | warehouse, category                 | InventoryItem[]   |
| `GET /api/inventory/{id}`      | —                                   | InventoryItem     |
| `GET /api/orders`              | warehouse, category, status, month  | Order[]           |
| `GET /api/orders/{id}`         | —                                   | Order             |
| `GET /api/demand`              | —                                   | DemandForecast[]  |
| `GET /api/backlog`             | —                                   | BacklogItem[]     |
| `GET /api/dashboard/summary`   | warehouse, category, status, month  | aggregated dict   |
| `GET /api/spending/summary`    | —                                   | dict              |
| `GET /api/spending/monthly`    | —                                   | list              |
| `GET /api/spending/categories` | —                                   | list              |
| `GET /api/spending/transactions`| —                                  | list              |
| `GET /api/reports/quarterly`   | —                                   | dict              |
| `GET /api/reports/monthly-trends`| —                                 | dict              |

## Data Flow — Filter Pipeline

This is the core pattern. A single filter change propagates end-to-end:

```
1. User selects "Warehouse B" in FilterBar.vue
        │
        ▼
2. useFilters.js composable updates reactive ref
        │
        ▼
3. View component's watch() fires → calls api.getOrders(filters)
        │
        ▼
4. api.js builds query string: GET /api/orders?warehouse=Warehouse+B
        │
        ▼
5. main.py apply_filters() → [o for o in orders if o['warehouse'] == 'Warehouse B']
        │
        ▼
6. Pydantic validates each item against Order model
        │
        ▼
7. JSON response → Axios → ref update → Vue re-renders
```

**Key insight:** filters are stateless on the server — every request re-filters the full in-memory list. No caching, no pagination. Fine for 250 records; would not scale.

## Filtering Internals (`main.py`)

- `apply_filters(items, warehouse, category, status)` — chained list comprehensions, case-insensitive on category/status
- `filter_by_month(items, month)` — supports quarter tokens (`Q1-2025` → expands to 3 month prefixes) via `QUARTER_MAP`, matched by substring against `order_date`
- `'all'` sentinel = no filter (checked both client and server side)

## Data Loading

`mock_data.py` runs at **import time** — every JSON file is read once when the server process starts. The data lives as module-level Python lists for the lifetime of the process. Editing a JSON file requires a server restart to take effect.
