# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

> Nested guidance: `client/CLAUDE.md` (Vue 3 patterns) and `server/CLAUDE.md` (FastAPI patterns) are auto-loaded when you work in those directories — consult them for subsystem detail.

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
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
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

# Tests (backend, 51 tests via pytest + FastAPI TestClient)
cd tests
uv run pytest -v
uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v  # single test
```

On macOS/Linux, `./scripts/start.sh` and `./scripts/stop.sh` start/stop both servers. On Windows, run the manual commands above in separate terminals.

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties
**Routing**: `client/src/main.js` defines vue-router routes — `/` Dashboard, `/inventory`, `/orders`, `/demand`, `/spending`, `/reports`
**Shared state (composables)**: `useFilters` (global filters), `useAuth` (auth/profile), `useI18n` (locale)
**i18n**: English/Japanese locales in `client/src/locales/{en,ja}.js`, toggled via `LanguageSwitcher.vue`
**Currency**: Format via `client/src/utils/currency.js` (don't hand-roll `toLocaleString` per component)

## API Endpoints
All routes are defined in `server/main.py`. Shared helpers: `apply_filters()` (warehouse/category/status) and `filter_by_month()` (month `2025-01` or quarter `Q1-2025` via `QUARTER_MAP`).
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/inventory/{item_id}` - Single item (404 if missing)
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/orders/{order_id}` - Single order (404 if missing)
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters (backlog injects `has_purchase_order` flag)
- `GET /api/spending/*` - summary, monthly, categories, transactions
- `GET /api/reports/quarterly`, `/api/reports/monthly-trends` - Computed from orders

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months
6. `client/src/api.js` calls `/api/tasks` (CRUD) and `/api/purchase-orders` (POST/GET) endpoints that are **not implemented** in `server/main.py` — add the backend routes before wiring up those features

## Conventions
- Always document non-obvious logic changes with comments

## File Locations
- Views: `client/src/views/*.vue`
- API Client: `client/src/api.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Styles: `client/src/App.vue`

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
