# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System — full-stack demo app with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

## Commands

**Backend** (from `server/`):
```bash
uv sync                          # Install dependencies
uv run python main.py            # Start server on http://localhost:8001
```

**Frontend** (from `client/`):
```bash
npm install && npm run dev       # Start dev server on http://localhost:3000
npm run build                    # Production build to client/dist/
```

**Tests** (from `tests/`):
```bash
uv run pytest backend/ -v                          # All 51 tests
uv run pytest backend/test_inventory.py -v         # Single file
uv run pytest --cov=../server --cov-report=html    # With coverage
```

**Windows note:** `scripts/start.sh` is macOS/Linux only. Start backend and frontend in separate terminals manually.

## Architecture

```
client/src/
  api.js          # Centralized Axios client — all HTTP calls go here
  composables/    # Shared state: useFilters.js (4-filter system), useAuth.js, useI18n.js
  views/          # Page components (Dashboard, Inventory, Orders, Spending, Demand, Reports)
  components/     # Reusable UI (FilterBar, *DetailModal, TasksModal, ProfileMenu)

server/
  main.py         # All FastAPI endpoints + apply_filters() + filter_by_month()
  mock_data.py    # Loads server/data/*.json into memory at startup
  data/*.json     # Source of truth — inventory, orders, spending, demand_forecasts, backlog_items
```

Data flow: Vue filter composable → `api.js` query params → FastAPI → in-memory filtering → Pydantic response → Vue computed properties.

## Critical Tool Usage

- **vue-expert subagent**: MANDATORY for any `.vue` file creation or significant modification
- **code-reviewer subagent**: Use after writing significant code
- **backend-api-test skill**: Use when writing/modifying tests in `tests/backend/`
- **GitHub MCP** (`mcp__github__*`): Use for ALL GitHub operations (exception: local branch creation with `git checkout -b`)
- **Playwright MCP** (`mcp__playwright__*`): Use for browser testing against `http://localhost:3000` / `http://localhost:8001`

## Key Patterns

**Filter system**: 4 filters — Time Period, Warehouse, Category, Order Status — passed as query params to every endpoint. Filter values of `'all'` are skipped. Inventory endpoints do **not** support month filtering (no time dimension on inventory data).

**Backend filtering**:
```python
# Never mutate global data — filter on copies
if warehouse and warehouse != 'all':
    results = [r for r in results if r.get('warehouse') == warehouse]
```

**Date/quarter filtering**: Supports `2025-01` (month) and `Q1-2025` (quarter) formats. Parse safely and handle null dates.

**Frontend reactivity**:
- Raw data in `ref()`, derived data in `computed()` — never the reverse
- Always use unique IDs (not array index) as `v-for` keys
- Validate dates before calling `.getMonth()`: `if (!isNaN(date.getTime()))`
- In `<script>`: `.value` required. In `<template>`: automatic unwrapping.

**Adding a backend endpoint**:
1. Define Pydantic model → add route → filter on copy of data → return typed response → write test in `tests/backend/`

**Adding data**: Update JSON in `server/data/` → update Pydantic model if structure changed → restart server.

## Known Constants

- Revenue goals: $800K/month (single warehouse), $9.6M YTD (all months)
- API docs: http://localhost:8001/docs
- Mock data scope: Circuit Boards, Sensors, Actuators, Controllers across 12 months

## Design System

- Colors: Slate/gray (`#0f172a`, `#64748b`, `#e2e8f0`); status uses green/blue/yellow/red
- Charts: Custom SVG with CSS Grid layouts
- No emojis in UI
