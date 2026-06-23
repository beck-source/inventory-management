# CLAUDE.md

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
  - Test against: `http://localhost:3080` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3080)
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
```

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions

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

## Coding rules
General rules:
- All code should have meaningful short code comments.
- Code comments have to be sentences ending with a dot.
- Do not ever use the em dash char (—), always use the hyphen char (-).

Python rules:
- Strings have to be double quoted.
- Code comments where quotes are needed, double quotes have to be used.
- Where inline quotes in strings are needed double quotes like \" have to be used.
- Changes in the src folder have to be checked against the current unit tests by running: uv run coverage run -m pytest && uv run coverage report --fail-under=80. If source code changes affect the tests or if unit tests are missing for new functionalities, the tests will have to be adjusted and / or expanded.
- Never generate __init__.py files.
- To execute Python code always use "uv run ...".
- When catching exceptions always do "... as error:" and not "... as e:".
- When logging caught excceptions always use logger.error(), write a helpful message and then the caught error message in this format: logger.error(f"Helpful error message: \"{error}\".").
- Imports can only be done at the top of a .py file and never inline somewhere in the code.
- Never use import abbreviations like "import pandas as pd", "import numpy as np" or similar.
- Always define paths relative to the "backend" folder and never use absolute paths with os.path.join() or similar.

Typescript rules:
- After making changes make sure to run "npm run lint" and "npm run build" and fix any issues that arise.
- Never use Camel-Case when writing UI texts like "Admin View Panel" but rather only capitalize the first letter and let the rest follow standard writing rules so it would be "Admin view panel".
- Never use hardcoded pixel values for UI elements.
