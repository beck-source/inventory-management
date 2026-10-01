# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database). `client/CLAUDE.md` and `server/CLAUDE.md` hold area-specific conventions.

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored to prevent locally-configured registries from leaking into commits — leave both in place.

## Critical Tool Usage Rules

### Subagents
Use the Task tool with these specialized subagents (defined in `.claude/agents/`) for appropriate tasks:

- **vue-expert**: Use for Vue 3 frontend features, UI components, styling, and client-side functionality
  - Examples: Creating components, fixing reactivity issues, performance optimization, complex state management
  - **MANDATORY RULE: ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert**
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **security-auditor**: Fast security review of changed files
- **Explore**: Use for understanding codebase structure, searching for patterns, or answering questions about how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test** skill: Use when writing or modifying tests in `tests/backend` directory with pytest and FastAPI TestClient

### MCP Tools
MCP servers are configured in `.mcp.json` (GitHub server needs `GITHUB_PERSONAL_ACCESS_TOKEN`).
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Release Standards
- All changes need test evidence (e.g., passing test output or Playwright verification) before merging
- No direct commits to `main` — always work on a branch and open a PR
- Every PR must include a one-line business impact summary

## Stack
- **Frontend**: Vue 3 + Composition API + Vite + vue-router + axios (port 3000). Requires Node `^20.19.0 || >=22.12.0`.
- **Backend**: Python FastAPI (port 8001, API docs at `/docs`). Python >=3.11, managed with `uv`.
- **Data**: JSON files in `server/data/` loaded once at import time by `server/mock_data.py`

## Commands

```bash
# Start/stop both servers (macOS/Linux; installs deps if missing, logs to /tmp/inventory-*.log)
./scripts/start.sh
./scripts/stop.sh

# Backend
cd server && uv sync && uv run python main.py

# Frontend
cd client && npm install && npm run dev
cd client && npm run build          # output: client/dist/

# Backend tests (tests/ has no pyproject; deps come from server/'s dev-dependencies)
cd tests && uv run --project ../server pytest
cd tests && uv run --project ../server pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory
```

There is no linter, type checker, or frontend test suite configured.

## Architecture

**Backend is a single file.** All Pydantic models, filter helpers, and routes live in `server/main.py`. Two helpers do all filtering in memory:
- `apply_filters(items, warehouse, category, status)` — exact match on warehouse, case-insensitive on category/status; the value `'all'` means no filter.
- `filter_by_month(items, month)` — accepts `YYYY-MM` or a quarter key (`Q1-2025`…`Q4-2025` from the hardcoded `QUARTER_MAP`), substring-matched against `order_date`.

**Filter flow.** `client/src/composables/useFilters.js` holds module-level singleton refs (shared across all views) for Period, Location, Category, Status. `getCurrentFilters()` maps them to API params (Location → `warehouse`, Period → `month`), and `client/src/api.js` drops any param equal to `'all'` before calling the backend. Views keep raw API data in refs (`allOrders`, `inventoryItems`) and derive everything else with computed properties.

**i18n and currency.** All UI strings go through `useI18n().t('dot.path')` with dictionaries in `client/src/locales/en.js` and `ja.js`; add new keys to both. Locale persists in localStorage (`app-locale`) and drives currency: `ja` → JPY via a fixed 150x rate in `client/src/utils/currency.js`. Backend values are always USD; format them with `formatCurrency(amount, currentCurrency)`, never by hand.

**Auth is mocked.** `useAuth.js` returns a hardcoded, locale-aware user; there is no backend auth.

## API Endpoints
- `GET /api/inventory`, `/api/inventory/{id}` - Filters: warehouse, category
- `GET /api/orders`, `/api/orders/{id}` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters (but `total_backlog_items` is never filtered)
- `GET /api/demand`, `/api/backlog` - No filters (`/api/backlog` computes `has_purchase_order` from `purchase_orders.json`)
- `GET /api/spending/{summary,monthly,categories,transactions}` - No filters
- `GET /api/reports/{quarterly,monthly-trends}` - All filters; computed from orders. Quarters are derived from `order_date`, but the `month` filter only understands the 2025 quarter keys in `QUARTER_MAP`
- `GET /api/restocking/recommendations?budget=` - Required budget (0 < budget <= 10,000,000). Fills the budget from demand forecasts whose forecast exceeds on-hand + on-order stock, `increasing` trend first. Forecast `item_sku`/`item_name`/`unit_cost` must match `inventory.json`
- `GET/POST /api/restocking/orders` - In-memory restocking orders (reset on restart), newest first. Server prices lines from the forecast and rejects unknown/duplicate SKUs and totals over budget; submitted quantities count as on order in later recommendations
- `GET/POST /api/tasks`, `PATCH/DELETE /api/tasks/{id}` - In-memory tasks (reset on restart); PATCH toggles pending/completed. IDs are `task-N` strings so they never collide with the numeric mock tasks in `useAuth.js`

**Known gap:** `client/src/api.js` calls `/api/purchase-orders` (POST, GET by backlog item), which **does not exist in `server/main.py`**, so implement it before relying on that UI feature.

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months
6. Real data values: categories Actuators, Circuit Boards, Controllers, Power Supplies, Sensors; warehouses London, San Francisco, Tokyo; order statuses Delivered, Shipped, Processing, Backordered; orders span 2025-01 to 2025-12.
7. **Do not run `server/generate_data.py`.** It uses an outdated product catalog (Widgets/Bearings/etc.) and overwrites `server/data/orders.json`, which would break tests and the UI.
8. `tests/README.md` mentions `test_orders.py`, but that file doesn't exist. The test files are `test_inventory.py`, `test_dashboard.py`, `test_misc_endpoints.py`, `test_reports.py`, `test_restocking.py`, and `test_tasks.py`.

## File Locations
- Views (one per route in `client/src/main.js`): `client/src/views/*.vue`
- Modals and shared UI: `client/src/components/`
- Composables: `client/src/composables/` (`useFilters`, `useI18n`, `useAuth`)
- API Client: `client/src/api.js` (base URL hardcoded to `http://localhost:8001/api`)
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Global styles: `client/src/App.vue`
- Project slash commands: `.claude/commands/` (`/start`, `/stop`, `/test`, `/demo-branch`, `/reset-branch`, `/optimize`)

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
