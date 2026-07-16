# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

There are additional `CLAUDE.md` files with deeper patterns: `client/CLAUDE.md` (Vue 3 conventions, composables, styling) and `server/CLAUDE.md` (FastAPI/Pydantic conventions, filtering, error handling).

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
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded via `server/mock_data.py`

## Quick Start

```bash
# One-command startup (macOS/Linux): ./scripts/start.sh — stop with ./scripts/stop.sh

# Backend
cd server
uv venv && uv sync
uv run python main.py

# Frontend
cd client
npm install && npm run dev
```

## Testing

Backend tests live in `tests/backend/` (pytest + FastAPI `TestClient`, see `tests/pytest.ini` and the `backend-api-test` skill). Run from the `tests/` directory:

```bash
cd tests
uv run pytest -v                                              # all tests
uv run pytest backend/test_inventory.py -v                    # one file
uv run pytest backend/test_inventory.py::TestInventoryEndpoints -v                        # one class
uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v # one test
uv run pytest --cov=../server --cov-report=html               # with coverage
```

There is no frontend test runner configured in `client/package.json` (no `test` script, no test framework installed) — verify frontend changes with Playwright MCP against `http://localhost:3000` instead.

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties
**Filter state is a module-level singleton**: `client/src/composables/useFilters.js` defines its refs *outside* `useFilters()`, so every component calling the composable shares one global filter state rather than getting its own instance — intentional, but easy to break if refactored to look like a typical per-instance composable
**Routing**: `client/src/main.js` maps one view per top-level route (`/`, `/inventory`, `/orders`, `/demand`, `/spending`, `/reports`); `App.vue` owns the persistent nav shell and filter bar around the routed view

## API Endpoints
- `GET /api/inventory`, `GET /api/inventory/{id}` - Filters: warehouse, category
- `GET /api/orders`, `GET /api/orders/{id}` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/summary`, `/monthly`, `/categories`, `/transactions`
- `GET /api/reports/quarterly`, `/api/reports/monthly-trends`

**Known gap**: `client/src/api.js` has methods for `/api/tasks` (get/create/delete/toggle) and `/api/purchase-orders` (create/get by backlog item), but `server/main.py` implements neither — these calls will 404 until the backend endpoints are added.

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

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
