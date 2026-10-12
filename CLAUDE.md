# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo — Vue 3 frontend, Python FastAPI backend, in-memory mock data (no database).

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored — leave both in place.

## Critical Tool Usage Rules

### Subagents
- **vue-expert**: **MANDATORY** for ANY creation or significant modification of `.vue` files
- **code-reviewer**: Use after writing significant code
- **Explore**: Use for codebase exploration and pattern searches
- **general-purpose**: Use for complex multi-step tasks

### Skills
- **backend-api-test**: Use when writing or modifying tests in `tests/backend/`

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches — use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Frontend: `http://localhost:3000` — Backend: `http://localhost:8001`

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded at startup via `server/mock_data.py`

## Commands

```bash
# Start/stop both servers
./scripts/start.sh
./scripts/stop.sh

# Backend only
cd server && uv run python main.py

# Frontend only
cd client && npm install && npm run dev
cd client && npm run build
```

### Tests (backend only — no frontend test suite)
```bash
cd tests && uv run pytest -v                                                                              # all tests
cd tests && uv run pytest backend/test_inventory.py -v                                                   # single file
cd tests && uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v   # single test
```

## Architecture

### Data Flow
Vue filter state → `client/src/api.js` (axios + URLSearchParams) → FastAPI query params → in-memory Python filtering → Pydantic validation → JSON response → Vue computed properties

### Filter System
`useFilters.js` holds **module-level refs** (singleton) so all components share the same four values: `selectedPeriod`, `selectedLocation`, `selectedCategory`, `selectedStatus`. `getCurrentFilters()` maps them to API param names (`selectedLocation` → `warehouse`, `selectedPeriod` → `month`). The backend ignores a filter when its value is `'all'`. Month values are `YYYY-MM`; quarter values are `Q1-2025`.

### Backend (`server/`)
- `main.py` — all endpoints; `apply_filters()` and `filter_by_month()` are shared filter utilities; filtering is case-insensitive
- `mock_data.py` — loads JSON into module-level variables at startup; changes are lost on restart
- Adding data: update JSON file → update Pydantic model if structure changed → restart server

### Frontend (`client/src/`)
- `api.js` — centralized axios client; omits `'all'` values from query params
- `composables/useFilters.js` — singleton filter state (see above)
- `composables/useI18n.js` — i18n; locale persisted in `localStorage`; currency follows locale (USD for `en`, JPY for `ja`); locales in `locales/en.js` and `locales/ja.js`
- Views store raw API data in refs (`allOrders`, `inventoryItems`) and derive display data via computed properties
- Charts are custom SVG — no third-party charting library

## API Endpoints
- `GET /api/inventory` — Filters: `warehouse`, `category`
- `GET /api/orders` — Filters: `warehouse`, `category`, `status`, `month`
- `GET /api/dashboard/summary` — All filters
- `GET /api/demand`, `GET /api/backlog` — No filters
- `GET /api/spending/summary`, `/monthly`, `/categories`, `/transactions`
- `GET /api/reports/quarterly`, `/reports/monthly-trends`

## Common Issues
1. Use unique keys in `v-for` (not `index`) — use `sku`, `month`, order ID, etc.
2. Validate dates before calling `.getMonth()` — check `!isNaN(date.getTime())`
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support `month` (inventory has no time dimension)
5. Revenue goals: $800K/month single warehouse, $9.6M YTD across all warehouses

## File Locations
- Views: `client/src/views/*.vue`
- Reusable components: `client/src/components/*.vue`
- Composables: `client/src/composables/` (`useFilters`, `useI18n`, `useAuth`)
- API client: `client/src/api.js`
- Router: `client/src/main.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data files: `server/data/*.json`
- Tests: `tests/backend/`
- Global styles: `client/src/App.vue`

## Design System
- Colors: Slate/gray (`#0f172a`, `#64748b`, `#e2e8f0`)
- Status badges: green / blue / yellow / red
- Layouts: CSS Grid; Flexbox for component internals
- Charts: Custom SVG
- No emojis in UI
