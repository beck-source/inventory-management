# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

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
- **vue-saas-redesign** skill: Use when redesigning the UI layout, adding a sidebar, or switching to vertical navigation

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded into memory at startup via `server/mock_data.py`

## Commands

```bash
# Start both servers together
./scripts/start.sh

# Stop both servers
./scripts/stop.sh

# Backend only
cd server && uv run python main.py

# Frontend only
cd client && npm install && npm run dev

# Backend tests (run from repo root)
cd tests && uv run pytest backend/ -v

# Single test file
cd tests && uv run pytest backend/test_inventory.py -v

# With coverage
cd tests && uv run pytest backend/ --cov=../server
```

API docs (Swagger UI) auto-generated at `http://localhost:8001/docs`.

## Architecture

**In-memory data model**: All JSON files in `server/data/` are loaded at startup via `server/mock_data.py`. Changes from POST requests persist only for the session — restart resets to file state. Run `server/generate_data.py` to regenerate the JSON files from scratch.

**Filter system**: 4 global filter refs (`selectedPeriod`, `selectedLocation`, `selectedCategory`, `selectedStatus`) live in `client/src/composables/useFilters.js` as a singleton. Every view calls `getCurrentFilters()` to build query params, watches those refs, and reloads when they change.

**Reactivity pattern**: Raw data in `ref()` (e.g. `allOrders`, `inventoryItems`), derived data in `computed()` (totals, filtered lists, chart data). Never mutate computed values directly.

**Data flow**: Vue filter change → `watch()` → `api.js` method with query params → FastAPI `apply_filters()` + `filter_by_month()` chaining → Pydantic-validated response → `ref` update → `computed` recalculation.

**Other composables**: `useI18n` (`client/src/composables/useI18n.js`) toggles EN/JP and exposes `t()` for translations. `useAuth` (`useAuth.js`) provides a mock logged-in user with a task list rendered in the active language — both are singletons like `useFilters`.

**i18n**: All UI strings keyed in `client/src/locales/en.js` and `ja.js`. Currency: USD default, JPY = USD × 150. Add keys to both locale files when adding new UI text.

**Restocking orders**: `POST /api/orders` creates orders with auto-generated `RST-2025-XXXX` order numbers and `Processing` status. These are identifiable in Orders view by the `RST-` prefix filter. In-memory only.

## API Endpoints

- `GET /api/inventory` — Filters: warehouse, category
- `GET /api/inventory/{id}` — Single item
- `GET /api/orders` — Filters: warehouse, category, status, month
- `GET /api/orders/{id}` — Single order
- `POST /api/orders` — Create restocking order (body: items, warehouse, category, customer)
- `GET /api/dashboard/summary` — All filters
- `GET /api/demand`, `/api/backlog` — No filters
- `GET /api/spending/*` — Summary, monthly, categories, transactions
- `GET /api/reports/quarterly`, `/api/reports/monthly-trends`

## Test Structure

`tests/backend/` — 51 pytest tests using FastAPI `TestClient` (via httpx):
- `conftest.py` — Client fixture + sample data fixtures
- `test_inventory.py` — Inventory filtering (10 tests)
- `test_orders.py` — Order endpoints and filtering
- `test_dashboard.py` — Dashboard summary with filter combinations (13 tests)
- `test_misc_endpoints.py` — Demand, backlog, spending, reports (13 tests)

## Common Issues

1. Use unique keys in `v-for` — use `sku`, `month`, `order_number`, not index
2. Validate dates before calling `.getMonth()` — order dates can be null
3. Update Pydantic models in `server/main.py` when changing JSON data structure
4. Inventory filters don't support `month` (inventory has no time dimension)
5. Revenue goals: $800K/month single warehouse, $9.6M YTD all months
6. Quarter filtering uses hardcoded `QUARTER_MAP` in `filter_by_month()` — format: `Q1-2025`

## Design System

- Colors: Slate/gray (`#0f172a`, `#64748b`, `#e2e8f0`)
- Status badges: green=Delivered, blue=Shipped, yellow=Processing, red=Backordered
- Charts: Custom SVG elements, CSS Grid for layouts
- No emojis in UI

## Code Style

- Always document non-obvious logic changes with comments
