# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored to prevent locally-configured registries from leaking into commits — leave both in place.

## Critical Tool Usage Rules

### Subagents
Use the Task tool with these specialized subagents for appropriate tasks:

- **vue-expert**: Use for Vue 3 frontend features, UI components, styling, and client-side functionality
  - Examples: Creating components, fixing reactivity issues, performance optimization, complex state management
  - **MANDATORY RULE: ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert**
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **Explore**: Use for understanding codebase structure, searching for patterns, or answering questions about how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test** skill: Use when writing or modifying tests in `tests/backend` directory with pytest and FastAPI TestClient

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API (Options-style `setup()`) + Vue Router + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded via `server/mock_data.py`

## Quick Start

```bash
# Backend
cd server
uv run python main.py

# Frontend
cd client
npm install && npm run dev
```

## Running Tests

```bash
cd tests
uv run pytest -v                                              # all tests
uv run pytest backend/test_inventory.py -v                    # one file
uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v  # one test
```

## Architecture

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) live in the `useFilters` composable (`client/src/composables/useFilters.js`) as module-level refs — a singleton shared across every view. `getCurrentFilters()` maps this state to API query params.

**Data Flow**: Vue filters (`useFilters`) → `client/src/api.js` → FastAPI query params → `apply_filters`/`filter_by_month` in `server/main.py` → Pydantic response models → Vue computed properties.

**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties.

**i18n**: `useI18n` composable (`client/src/composables/useI18n.js`) drives translations from `client/src/locales/{en,ja}.js`. Locale also determines currency (`en` → USD, `ja` → JPY); use `formatCurrency`/`convertAmount` from `client/src/utils/currency.js` rather than formatting amounts inline. Locale persists to `localStorage` under `app-locale`.

**Auth**: `useAuth` composable (`client/src/composables/useAuth.js`) is fully mocked — a hardcoded current user, `isAuthenticated` always `true`, `logout()` just alerts. Task list in `App.vue` merges this mock user's tasks with real ones fetched via the API.

**Mock data lifecycle**: JSON in `server/data/*.json` is loaded once into module-level Python lists in `server/mock_data.py` at import time. All mutations during a server run are in-memory only; restarting the server reloads from disk.

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/inventory/{item_id}`
- `GET /api/orders` - Filters: warehouse, category, status, month (accepts `YYYY-MM` or `QN-YYYY` quarters)
- `GET /api/orders/{order_id}`
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions
- `GET /api/reports/quarterly`, `/api/reports/monthly-trends` - Computed on the fly from `orders`, not filterable

**Known gap**: `client/src/api.js` also calls `/api/tasks` (GET/POST/PATCH/DELETE) and `/api/purchase-orders` (GET/POST) — these have no matching routes in `server/main.py`. Calls to them will 404 until implemented.

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models in `server/main.py` when changing JSON data structure in `server/data/`
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months
6. `Backlog.vue` exists under `client/src/views/` but is not registered in `client/src/main.js` router

## File Locations
- Views: `client/src/views/*.vue`
- Composables: `client/src/composables/*.js` (`useFilters`, `useAuth`, `useI18n`)
- API Client: `client/src/api.js`
- Router: `client/src/main.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Styles: `client/src/App.vue`

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
