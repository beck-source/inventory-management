# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

> **Nested guidance**: `client/CLAUDE.md` (detailed Vue 3 patterns) and `server/CLAUDE.md` (detailed FastAPI patterns) hold deeper, directory-specific best practices. Read them when doing substantial frontend or backend work.

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

# Frontend production build
cd client && npm run build   # output: client/dist/

# Backend tests (pytest + FastAPI TestClient; deps in server/pyproject.toml)
cd server && uv run pytest ../tests/backend -v
cd server && uv run pytest ../tests/backend/test_inventory.py::test_name -v   # single test
```

On macOS/Linux, `./scripts/start.sh` and `./scripts/stop.sh` run both servers. On Windows, use the manual commands above.

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties
**Composables** (`client/src/composables/`): `useFilters` (global filter state + `getCurrentFilters()`), `useI18n` (translations), `useAuth` (auth state)
**i18n**: English/Japanese via `useI18n` + `client/src/locales/{en,ja}.js`; `LanguageSwitcher` component. Add UI strings to both locale files
**Routing**: 6 views via vue-router (`client/src/main.js`): `/` Dashboard, `/inventory`, `/orders`, `/demand`, `/spending`, `/reports`

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions
- `GET /api/reports/quarterly`, `/api/reports/monthly-trends` - Reports view data
- `GET /api/inventory/{item_id}`, `/api/orders/{order_id}` - Single item (404 if missing)

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

## File Locations
- Views: `client/src/views/*.vue` (one per route)
- Components: `client/src/components/*.vue` (FilterBar, detail modals, ProfileMenu, LanguageSwitcher)
- Composables: `client/src/composables/*.js`
- Locales: `client/src/locales/{en,ja}.js`
- API Client: `client/src/api.js`
- Backend: `server/main.py` (endpoints), `server/mock_data.py` (JSON loader)
- Data: `server/data/*.json`
- Tests: `tests/backend/*.py`
- Styles: `client/src/App.vue` (global)

## Conventions
- Always document non-obvious logic changes with comments

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI
