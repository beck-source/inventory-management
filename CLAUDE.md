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
# One-command startup (both servers)
./scripts/start.sh

# Or manually:
# Backend
cd server && uv run python main.py

# Frontend
cd client && npm install && npm run dev
```

## Commands

```bash
# Backend tests (run from repo root)
cd tests && uv run pytest backend/ -v

# Single test file
cd tests && uv run pytest backend/test_inventory.py -v

# Single test method
cd tests && uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v

# With coverage
cd tests && uv run pytest backend/ --cov=server --cov-report=html

# Frontend build
cd client && npm run build
```

## Architecture

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) managed by `client/src/composables/useFilters.js` and sent as query params to every API call.

**Data Flow**: `useFilters` composable → `client/src/api.js` (builds URLSearchParams, skips `'all'` values) → FastAPI `apply_filters()` helper → Pydantic-validated response → computed properties for display.

**Reactivity**: Raw data stored in refs (`allOrders`, `inventoryItems`), derived/filtered data in computed properties. Never mutate props directly.

**Composables**: `useFilters` (global filter state), `useAuth` (authentication), `useI18n` (translations via `client/src/locales/en.js` and `ja.js`).

**Mock data**: `server/mock_data.py` loads all JSON files at startup into module-level globals. Data covers 12 months across 4 product categories (Circuit Boards, Sensors, Actuators, Controllers) and multiple warehouses.

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions
- `GET /api/reports/*` - Quarterly and monthly trends

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months
6. `apply_filters()` in `server/main.py` handles warehouse/category; `filter_by_month()` handles time periods including quarters via `QUARTER_MAP`
7. Always document non-obvious logic changes with comments

## File Locations
- Views: `client/src/views/*.vue`
- Components: `client/src/components/*.vue`
- Composables: `client/src/composables/` (useFilters, useAuth, useI18n)
- API Client: `client/src/api.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Tests: `tests/backend/` (conftest.py, test_inventory.py, test_dashboard.py, test_misc_endpoints.py)
- Styles: `client/src/App.vue`

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
