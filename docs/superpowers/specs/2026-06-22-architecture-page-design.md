# Architecture Page Design

**Date:** 2026-06-22  
**Output:** `docs/architecture.html`

## Goal

A single self-contained HTML file that serves as a developer reference for the Factory Inventory Management System architecture — something to glance at while building.

## Audience

Developer (internal reference). Not a stakeholder presentation or demo artifact. Scannable over polished.

## Approach

Layered stack diagram: three horizontal bands (Frontend / Backend / Data) with a data flow arrow diagram and quick-reference endpoint table below.

## Layout

```
HEADER — title + port badges (3000 / 8001)
─────────────────────────────────────────
FRONTEND band — Vue 3 + Vite · port 3000
  6 Views, 8 Components, useFilters, useI18n, useAuth, api.js
─────────────────────────────────────────
BACKEND band — FastAPI + Pydantic · port 8001
  20+ endpoints, apply_filters(), mock_data.py
─────────────────────────────────────────
DATA band — 7 JSON files in server/data/
  inventory, orders, spending, backlog, demand, transactions, purchase_orders
─────────────────────────────────────────
DATA FLOW — left-to-right arrow diagram
  FilterBar (UI) → useFilters (shared state) → View calls getCurrentFilters()
  → api.js (Axios) → FastAPI → apply_filters() + filter_by_month()
  → JSON → Pydantic → JSON response → Vue ref() → re-render
─────────────────────────────────────────
QUICK REF TABLE — key endpoints + params
```

## Style

- Background: `#0f172a` (matches app design system)
- Font: monospace
- Band colors: slate gradient darkening top to bottom
- Badges: green=Frontend, blue=Backend, amber=Data
- No JavaScript — pure HTML/CSS
- No external dependencies — fully self-contained

## Key Content

### Tech Stack
| Layer | Tech | Version | Port |
|-------|------|---------|------|
| Frontend | Vue 3 + Composition API | 3.4.21 | 3000 |
| Build | Vite | 5.2.0 | — |
| HTTP | Axios | 1.6.7 | — |
| Backend | FastAPI + Pydantic | latest | 8001 |
| Server | Uvicorn (ASGI) | — | — |
| Data | JSON files (in-memory) | — | — |

### Data Flow
Filter UI → `useFilters` composable → `api.js` (Axios) → FastAPI endpoint → `apply_filters()` → JSON data → Pydantic model → JSON response → Vue `ref()` → re-render

### Key Endpoints Table Columns
`Endpoint | Method | Params | Notes`

| Endpoint | Method | Params | Notes |
|----------|--------|--------|-------|
| `/api/inventory` | GET | warehouse, category | No month filter |
| `/api/orders` | GET | warehouse, category, status, month | Supports quarter (Q1-2025) |
| `/api/dashboard/summary` | GET | warehouse, category, status, month | Aggregated KPIs |
| `/api/spending/summary` | GET | — | No filters |
| `/api/spending/monthly` | GET | — | Monthly breakdown |
| `/api/spending/categories` | GET | — | Category totals |
| `/api/spending/transactions` | GET | — | 60+ transaction records |
| `/api/demand` | GET | — | No filters |
| `/api/backlog` | GET | — | No filters |
| `/api/purchase-orders` | GET/POST | backlogItemId | Draft feature (empty data) |

## Out of Scope

- Interactive diagrams (static only)
- External CDN dependencies
- JavaScript behavior
- Mobile responsiveness (dev tool, viewed on desktop)
