# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo — Vue 3 frontend, Python FastAPI backend, in-memory mock data loaded from JSON (no database).

## Nested Guidance
- `client/CLAUDE.md` — Vue 3 / Composition API patterns, reactivity rules, chart/styling conventions
- `server/CLAUDE.md` — FastAPI endpoint patterns, Pydantic models, filter conventions
- `tests/README.md` — Test layout and per-file/class/function invocation examples

## Critical Tool Usage Rules

### Subagents
- **vue-expert** — **MANDATORY: any time you create or significantly modify a `.vue` file, you MUST delegate to vue-expert.** Also use for reactivity issues, performance, complex state.
- **code-reviewer** — Use after writing significant code to review quality.
- **Explore** — Use for codebase searches/architecture questions.
- **general-purpose** — Multi-step tasks that don't fit the others.

### Skills
- **backend-api-test** — Use when writing or modifying tests in `tests/backend/` (pytest + FastAPI TestClient).

### MCP Tools
- **GitHub MCP** (`mcp__github__*`) for ALL GitHub operations. Exception: local branches use `git checkout -b`.
- **Playwright MCP** (`mcp__playwright__*`) for browser testing against `http://localhost:3000` (frontend) / `http://localhost:8001` (API).

## Common Commands

```bash
# Backend (port 8001) — from server/
uv venv && uv sync          # first-time setup
uv run python main.py       # run

# Frontend (port 3000) — from client/
npm install                 # first-time setup
npm run dev                 # run
npm run build               # production build → client/dist/

# Tests — run from tests/ (has its own pytest.ini)
cd tests && uv run pytest -v
uv run pytest backend/test_inventory.py -v                                  # one file
uv run pytest backend/test_inventory.py::TestInventoryEndpoints -v          # one class
uv run pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v  # one test
uv run pytest --cov=../server --cov-report=html                             # coverage
```

**Platform note:** `scripts/start.sh` / `scripts/stop.sh` are bash-only (macOS/Linux). On Windows, run backend and frontend manually in separate terminals.

API docs (Swagger) live at `http://localhost:8001/docs` once the backend is running.

## Architecture

**Stack:** Vue 3 + Composition API + Vite + vue-router + axios (client); FastAPI + Pydantic + uvicorn (server); JSON files (data).

**Data flow:**
1. Global filter state lives in the `useFilters` composable as a **singleton** (refs declared at module scope, not inside the function — same state is shared across every `useFilters()` call). `FilterBar.vue` mutates this state.
2. Views call `getCurrentFilters()` to build a query, pass it to `client/src/api.js`, which appends non-`'all'` values as query params.
3. FastAPI endpoints in `server/main.py` apply filters in-memory via two helpers: `apply_filters()` (warehouse/category/status) and `filter_by_month()` (month or quarter, using `QUARTER_MAP`).
4. Mock data loads once at import time in `server/mock_data.py` from `server/data/*.json`. Mutations are non-persistent (server restart reloads from disk).
5. Vue views store raw API data in `ref`s and expose derived data via `computed` properties.

**Filter system:** Four global filters — Time Period (month or `Q1-2025`…`Q4-2025`), Warehouse, Category, Order Status — flow through query params. Inventory has no time dimension, so `month` doesn't apply there.

**i18n:** `useI18n` composable + `client/src/locales/{en,ja}.js`. Use `t('key')` in templates.

## API Endpoints (all `GET`)

- `/api/inventory` — filters: warehouse, category
- `/api/inventory/{id}` — 404 on missing
- `/api/orders` — filters: warehouse, category, status, month
- `/api/orders/{id}` — 404 on missing
- `/api/demand` — no filters
- `/api/backlog` — no filters; injects `has_purchase_order` flag from `purchase_orders.json`
- `/api/dashboard/summary` — all four filters
- `/api/spending/{summary,monthly,categories,transactions}` — no filters
- `/api/reports/{quarterly,monthly-trends}` — no filters

## Common Issues

1. **v-for keys:** use unique IDs (`sku`, `id`, `month`), never `index`.
2. **Date parsing:** validate with `!isNaN(date.getTime())` before `.getMonth()`.
3. **JSON ↔ Pydantic drift:** when changing `server/data/*.json` shape, update the matching Pydantic model in `server/main.py` and the corresponding test fixtures.
4. **No month filter on inventory** — inventory items have no time dimension.
5. **Revenue goals (demo constants):** $800K/month single, $9.6M YTD all months.

## File Locations

- Views: `client/src/views/*.vue` (Dashboard, Inventory, Orders, Demand, Spending, Reports, Backlog)
- Components: `client/src/components/*.vue` (FilterBar, modals, ProfileMenu, LanguageSwitcher)
- Composables: `client/src/composables/{useFilters,useAuth,useI18n}.js`
- API client: `client/src/api.js`
- Router: `client/src/main.js`
- Global styles: `client/src/App.vue`
- Backend: `server/main.py` (endpoints + Pydantic models), `server/mock_data.py` (JSON loader)
- Data: `server/data/*.json`
- Tests: `tests/backend/`, with shared fixtures in `tests/backend/conftest.py`

## Design System
- Colors: slate/gray (`#0f172a`, `#64748b`, `#e2e8f0`)
- Status colors: green / blue / yellow / red
- Charts: hand-rolled SVG; layouts use CSS Grid
- **No emojis in UI**

## Additional Instructions

- Always document non-obvious logic changes with comments