# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System - Full-stack demo with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

## Critical Tool Usage Rules

### Subagents
- **vue-expert**: **MANDATORY** — ANY time you create or significantly modify a `.vue` file, you MUST delegate to vue-expert. Also use for reactivity issues, state management, performance optimization.
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **Explore**: Use for codebase exploration, pattern searching, or understanding how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test**: Use when writing or modifying tests in `tests/backend/` with pytest and FastAPI TestClient

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only — use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI + Uvicorn (port 8001)
- **Data**: JSON files in `server/data/` loaded once at startup via `server/mock_data.py`
- **Package managers**: `uv` for Python, `npm` for Node

## Commands

```bash
# Backend
cd server && uv run python main.py

# Frontend
cd client && npm install && npm run dev

# Production build
cd client && npm run build

# All backend tests
cd tests && uv run pytest backend/ -v

# Single test file
cd tests && uv run pytest backend/test_inventory.py -v

# Single test
cd tests && uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v

# Tests with coverage
cd tests && uv run pytest backend/ --cov=../server --cov-report=term-missing

# Tests matching a pattern
cd tests && uv run pytest backend/ -k "warehouse" -v
```

## Architecture

### Data Flow
```
User interacts with filter (FilterBar.vue)
  → useFilters composable (singleton ref state, shared across all views)
  → api.js (centralized axios client, builds query params)
  → FastAPI endpoint (main.py, in-memory filtering)
  → mock_data.py (7 JSON files loaded at module import)
  → Pydantic validation
  → Vue ref updated → computed properties recalculate → template re-renders
```

### Filter System
All endpoints accept optional query params. Passing `'all'` skips that filter.
- `GET /api/inventory` — `warehouse`, `category` (no month — inventory has no time dimension)
- `GET /api/orders` — `warehouse`, `category`, `status`, `month`
- `GET /api/dashboard/summary` — all four filters
- `GET /api/demand`, `/api/backlog` — no filters
- `GET /api/spending/*` — summary, monthly, categories, transactions
- `GET /api/reports/quarterly` — quarterly aggregations (Q1-2025 format)
- `GET /api/reports/monthly-trends` — month-over-month trends

### Frontend State Pattern
Raw API responses are stored in Vue refs (`allOrders`, `inventoryItems`). Filtered/derived data lives in computed properties that watch filter state from `useFilters()`. Never store derived data in refs — keep that logic in computed.

### Key Files
- `client/src/api.js` — All HTTP calls; the only place to add/change API URLs
- `client/src/composables/useFilters.js` — Singleton filter state; imported by every view and FilterBar
- `client/src/App.vue` — Top-level layout, global styles, modals
- `server/main.py` — All FastAPI routes and filtering logic (~310 lines)
- `server/mock_data.py` — Data loading; add new JSON files here

### Test Structure
Backend tests only (no frontend tests). Located in `tests/backend/`:
- `conftest.py` — `client` fixture (FastAPI TestClient), sample data fixtures
- `test_inventory.py` — Inventory CRUD and filter tests
- `test_dashboard.py` — Dashboard summary aggregation tests
- `test_misc_endpoints.py` — Demand, backlog, spending, reports (~40 tests)

## Code Style
- Always document non-obvious logic changes with comments

## Common Issues
1. Use unique keys in `v-for` (never array index) — use `sku`, `month`, `id`, etc.
2. Validate dates before calling `.getMonth()` — some fields may be null/undefined
3. Sync Pydantic models in `main.py` whenever `server/data/*.json` structure changes
4. Inventory filters don't support `month` — no time dimension in inventory data
5. Revenue targets: $800K/month for single-month view, $9.6M YTD for all-months view

## Design System
- Colors: Slate/gray palette (`#0f172a`, `#64748b`, `#e2e8f0`)
- Status colors: green (delivered) / blue (shipped) / yellow (processing) / red (backordered/high priority)
- Charts: Custom SVG — no charting library
- Layout: CSS Grid
- No emojis in UI
