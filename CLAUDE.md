# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System demo (Claude Code workshop) - Vue 3 frontend, Python FastAPI backend, in-memory mock data (no database).

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

## Commands

```bash
# Run both servers (installs deps if missing; logs to /tmp/inventory-*.log). macOS/Linux only.
./scripts/start.sh        # stop with ./scripts/stop.sh

# Backend (port 8001, docs at /docs)
cd server && uv run python main.py

# Frontend (port 3000)
cd client && npm install && npm run dev
cd client && npm run build   # output: client/dist/

# Backend tests (pytest + FastAPI TestClient; run from server/ so uv picks up server/pyproject.toml)
cd server && uv run pytest ../tests/backend
cd server && uv run pytest ../tests/backend/test_inventory.py::<TestClass>::<test_name>
cd server && uv run pytest ../tests/backend -k "<expr>"
```

There is no linter and no frontend test suite configured. `/start`, `/stop`, and `/test` slash commands wrap the above (`.claude/commands/`). `uv.lock` and `*.lock` are gitignored.

## Architecture

**Data flow**: Vue view → `client/src/api.js` (axios, hardcoded `http://localhost:8001/api`) → FastAPI endpoint in `server/main.py` → list comprehensions over module-level lists loaded from `server/data/*.json` by `server/mock_data.py` at import time → Pydantic `response_model` validation → back to the view, where derived data lives in `computed` properties (raw data in refs such as `allOrders`, `inventoryItems`).

**Backend** is a single file, `server/main.py`: Pydantic models, `apply_filters` (warehouse/category/status, `'all'` means no filter, category/status compared case-insensitively), `filter_by_month` (accepts `2025-03` or `Q1-2025`, matched by substring against `order_date`), then the endpoints. All data is in-memory and mutations are not persisted across restarts. Changing a JSON file's shape requires updating the matching Pydantic model, or responses fail validation. `server/generate_data.py` regenerates the JSON data.

**Frontend filters** are a module-level singleton in `client/src/composables/useFilters.js` (period, location, category, status), so every view and `FilterBar.vue` share one state. `getCurrentFilters()` maps these to the API query params (`period` → `month`). Not all endpoints accept all filters: inventory takes only warehouse/category (no time dimension), `/api/demand` and `/api/backlog` take none, and `/api/dashboard/summary` takes all four.

**Other frontend structure**: routes are defined in `client/src/main.js` (vue-router, history mode). i18n is hand-rolled (`composables/useI18n.js`, strings in `locales/en.js` and `ja.js`), so new UI text needs entries in both locales. `useAuth.js` holds mock auth state. Detail views open as `*DetailModal.vue` components.

**Known gaps between client and server** (check before assuming a feature works end to end):
- `api.js` calls `/api/tasks` (GET/POST/PATCH/DELETE) and `/api/purchase-orders` (POST, GET by backlog item id), but `main.py` implements none of them. It only defines the `PurchaseOrder`/`CreatePurchaseOrderRequest` models and reads `purchase_orders.json` to set `has_purchase_order` on `/api/backlog`.
- `views/Backlog.vue` exists but has no route in `main.js`.

## Code Style
- Use comments sparingly and only to document assumptions or non-obvious relations to other subsystems not readable from the source code itself

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- Global styles live in `client/src/App.vue`
- No emojis in UI

## Nested CLAUDE.md files
`client/CLAUDE.md` and `server/CLAUDE.md` hold longer Vue and FastAPI conventions and are loaded when working in those directories.
