# Architecture Page Design

**Date:** 2026-06-22  
**Status:** Approved  
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
  6 Views, 8 Components, useFilters, useI18n, api.js
─────────────────────────────────────────
BACKEND band — FastAPI + Pydantic · port 8001
  20+ endpoints, apply_filters(), mock_data.py
─────────────────────────────────────────
DATA band — 7 JSON files in server/data/
  inventory, orders, spending, backlog, demand, transactions
─────────────────────────────────────────
DATA FLOW — left-to-right arrow diagram
  Filter UI → useFilters → api.js → FastAPI
  → apply_filters() → JSON → Pydantic → Vue ref
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

### Key Endpoints
- `GET /api/inventory` — warehouse, category filters
- `GET /api/orders` — warehouse, category, status, month filters
- `GET /api/dashboard/summary` — all filters
- `GET /api/spending/*` — summary, monthly, categories, transactions
- `GET /api/demand`, `/api/backlog` — no filters

## Out of Scope

- Interactive diagrams (static only)
- External CDN dependencies
- JavaScript behavior
- Mobile responsiveness (dev tool, viewed on desktop)
