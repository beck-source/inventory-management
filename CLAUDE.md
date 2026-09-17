# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Factory Inventory Management System Demo — full-stack Vue 3 + FastAPI application with in-memory mock data for factory inventory, order tracking, demand forecasting, and analytics.

> ⚠️ **This repository is PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored — leave both in place.

## Workspace Commands

### Development Setup
```bash
# Backend - from server/ directory
python -m venv venv          # Create venv (or use: python -m pip install -r requirements.txt)
source venv/bin/activate     # macOS/Linux: . venv/Scripts/activate (Windows)
pip install -r requirements.txt
python main.py               # Runs on http://localhost:8001

# Frontend - from client/ directory
npm install
npm run dev                   # Runs on http://localhost:3000

# One-command startup (macOS/Linux only)
./scripts/start.sh           # Starts both servers in background
./scripts/stop.sh            # Stops both servers
```

### Testing
```bash
cd tests
python -m pytest backend/ -v                          # Run all tests (55 total)
python -m pytest backend/test_inventory.py -v        # Run single test file
python -m pytest backend/test_inventory.py::TestInventoryEndpoints::test_get_all_inventory -v  # Run single test
python -m pytest --cov=../server --cov-report=html  # Coverage report
```

### Linting & Formatting
```bash
# Backend - no formal linting configured, follow server/CLAUDE.md patterns
# Frontend - no formal linting configured, follow client/CLAUDE.md patterns
```

### Building
```bash
# Frontend production build
cd client
npm run build                # Output: client/dist/
npm run preview              # Test production build locally
```

## Architecture Overview

### Full-Stack Data Flow
1. **Vue component** (client/src/views/*.vue) collects filter state (warehouse, category, status, month)
2. **API layer** (client/src/api.js) builds query params and calls backend
3. **FastAPI** (server/main.py) receives request, applies Pydantic validation
4. **Filter functions** (apply_filters, filter_by_month) process in-memory data
5. **Mock data** (server/data/*.json) is loaded once at startup via server/mock_data.py
6. **Response model** (Pydantic BaseModel) serializes to JSON
7. **Component** receives data, computed properties derive UI state, v-for renders with unique keys

### Key Design Decisions

**In-Memory Data Only**
- All JSON loaded at server startup from `server/data/*.json`
- No database; changes don't persist across restarts
- Fast reads, no indexing needed
- Suitable for demo; scale with database + async queries if needed

**Shared Filter Pattern Across All Endpoints**
- 4 core filters: warehouse, category, status, month (query params)
- Some endpoints ignore filters they don't apply to (e.g., inventory ignores month/status)
- Filter name `'all'` means "no filter on this dimension"
- Filters applied client-side to query params → normalized in backend

**Client-Side State Management**
- Composables (useFilters, useAuth, useI18n) export reactive refs
- Views import composables and use refs directly in templates
- No Vuex/Pinia; simple and appropriate for current scale
- Raw data in refs (allOrders, inventoryItems), derived data in computed properties

**Custom SVG Charts**
- No charting library; SVG with CSS Grid layouts
- Responsive via viewBox; accessible with ARIA labels
- Color system: slate/gray + status colors (green, blue, yellow, red)

### Directory Structure

```
├── client/
│   ├── src/
│   │   ├── views/             # Page-level components (Dashboard, Inventory, Orders, etc.)
│   │   ├── components/        # Reusable UI components (FilterBar, modals, etc.)
│   │   ├── composables/       # Shared logic (useFilters, useAuth, useI18n)
│   │   ├── utils/             # Helper functions (formatters, validators)
│   │   ├── locales/           # i18n translations
│   │   ├── App.vue            # Root component + global styles
│   │   ├── api.js             # Axios instance + API client functions
│   │   └── main.js            # Vue app + router setup
│   ├── vite.config.js         # Vite build config
│   ├── package.json           # Frontend dependencies
│   └── .npmrc                 # Public registry lock (DO NOT REMOVE)
│
├── server/
│   ├── main.py                # FastAPI app + endpoints + filter logic
│   ├── mock_data.py           # Loads JSON data at startup
│   ├── requirements.txt        # Backend dependencies (pip)
│   ├── pyproject.toml          # Project metadata + dev dependencies
│   └── data/
│       ├── inventory.json      # Inventory items (sku, warehouse, quantity, cost)
│       ├── orders.json         # Orders with items, status, dates, totals
│       ├── demand_forecasts.json
│       ├── backlog_items.json
│       ├── spending.json       # Spending summary by category
│       ├── transactions.json
│       └── purchase_orders.json
│
├── tests/
│   ├── backend/
│   │   ├── conftest.py        # Pytest fixtures (FastAPI TestClient)
│   │   ├── test_inventory.py  # Inventory endpoint tests (10)
│   │   ├── test_orders.py     # Orders endpoint tests (15)
│   │   ├── test_dashboard.py  # Dashboard endpoint tests (13)
│   │   └── test_misc_endpoints.py # Demand, backlog, spending (13)
│   ├── pytest.ini
│   └── README.md              # Test suite documentation
│
├── scripts/
│   ├── start.sh               # Start both servers (macOS/Linux)
│   └── stop.sh                # Stop both servers (macOS/Linux)
│
├── CLAUDE.md                  # This file
├── README.md                  # User-facing project overview
└── docs/
    └── dashboard-screenshot.png
```

## API Endpoints Reference

All endpoints accept optional query params for filtering. When param is `'all'` or missing, no filter applied on that dimension.

### Inventory
- `GET /api/inventory?warehouse=<warehouse>&category=<category>`
  - Returns: `List[InventoryItem]` (id, sku, name, category, warehouse, quantity_on_hand, reorder_point, unit_cost, location, last_updated)
  - Filters: warehouse, category (no month support; no time dimension in inventory)

### Orders
- `GET /api/orders?warehouse=<warehouse>&category=<category>&status=<status>&month=<month_or_quarter>`
  - Returns: `List[Order]` (id, order_number, customer, items, status, order_date, expected_delivery, total_value, actual_delivery, warehouse, category)
  - Filters: warehouse, category, status (Delivered/Shipped/Processing/Backordered), month (YYYY-MM) or quarter (Q1-2025 format)
  - Status values: "Delivered", "Shipped", "Processing", "Backordered"

### Dashboard Summary
- `GET /api/dashboard/summary?warehouse=<warehouse>&category=<category>&status=<status>&month=<month_or_quarter>`
  - Returns summary metrics: pending_orders, low_stock_items, total_inventory_value, etc. (all filters apply)

### Demand Forecasts
- `GET /api/demand` — No filters; returns all forecasts (item_sku, item_name, current_demand, forecasted_demand, trend, period)
- Trend values: "increasing", "stable", "decreasing"

### Backlog
- `GET /api/backlog` — No filters; returns backlog items (order_id, item_sku, item_name, quantity_needed, quantity_available, days_delayed)

### Spending
- `GET /api/spending/summary` — Spending by cost category
- `GET /api/spending/monthly?month=<month>` — Monthly spending breakdown
- `GET /api/spending/categories` — Category-level spending
- `GET /api/spending/transactions` — Recent transaction records

## Common Workflows

### Adding a New View/Page
1. Create `.vue` file in `client/src/views/` using Composition API
2. Import and add route in `client/src/main.js`
3. Add navigation link in `client/src/App.vue`
4. Use `useFilters()` composable for filter state
5. Call `api.js` functions to fetch data
6. Use computed properties to transform raw data for display

### Adding a New API Endpoint
1. Define Pydantic model in `server/main.py`
2. Create endpoint function with filtering logic (use helper functions `apply_filters()`, `filter_by_month()`)
3. Add route decorator with endpoint path and response_model
4. Write tests in `tests/backend/test_*.py` using TestClient fixture
5. Run tests to verify

### Filtering Data on Backend
Use existing helper functions in `server/main.py`:
- `apply_filters(items, warehouse=None, category=None, status=None)` — Common warehouse/category/status filters
- `filter_by_month(items, month)` — Filter by YYYY-MM or Q1-2025 format on order_date field

### Adding New Component
1. Create `.vue` file in `client/src/components/`
2. Use Composition API with props for data input, emits for actions
3. Use scoped styles
4. Export in views that need it (import + include in template)

### Working with Test Data
- Mock data in `server/data/*.json` reflects realistic factory data: 4 product categories, 3 warehouses, 12 months of orders
- Data is loaded once at startup; changes persist only in memory for current session
- Tests run against live FastAPI app with mock data (TestClient)
- To add new data category: create JSON file, load in `server/mock_data.py`, define Pydantic model, create endpoint

## Agentwork Rules

### Subagents
- **vue-expert**: Delegate ANY Vue 3 component creation or significant modification (MANDATORY)
- **code-reviewer**: Use after significant features to review quality
- **Explore**: For broad codebase searches and understanding patterns

### MCP Tools
- **GitHub MCP**: Use for all GitHub operations (PRs, branches, issues)
- **Playwright MCP**: Use for browser testing against http://localhost:3000 and http://localhost:8001

## Key Patterns & Anti-Patterns

### ✅ DO
- Use unique IDs as v-for keys (not index): `:key="item.sku"` or `:key="item.id"`
- Validate dates before calling `.getMonth()`: `new Date(dateStr).getTime()` check first
- Wrap raw data in refs, computed properties for derived data
- Update Pydantic models when changing JSON structure
- Return typed Pydantic models from endpoints (`response_model=List[MyModel]`)
- Keep filter logic in server (no client-side filtering of final results)
- Always document non-obvious logic changes with comments

### ❌ DON'T
- Use `index` as v-for key (causes DOM reuse bugs when list changes)
- Mutate props directly (emit events instead)
- Hardcode calculations in components (use computed properties)
- Forget "all" filter check (`if filter_param and filter_param != 'all'`)
- Return raw dicts from FastAPI (always use Pydantic models)
- Mutate global mock data in memory

## Design System Reference

**Colors:** Slate/gray palette (#0f172a, #64748b, #e2e8f0, #f1f5f9)
**Status Colors:** 
- Green (#10b981) — Delivered, success
- Blue (#3b82f6) — Shipped, info
- Yellow (#f59e0b) — Processing, warning
- Red (#ef4444) — Backordered, error
**Typography:** System fonts (no custom web fonts)
**Layout:** CSS Grid for dashboard, Flexbox for components

## Test Coverage

**55 total tests** covering all API endpoints:
- Inventory (10): All CRUD, filters, edge cases
- Orders (15): Filters, date/quarter handling, validation
- Dashboard (13): Calculations (pending orders, low stock, inventory value)
- Demand/Backlog/Spending (13): Data structure, business logic, new features
- Root endpoint (2): API info

Run with: `cd tests && python -m pytest backend/ -v`

See `tests/README.md` and `tests/TEST_SUMMARY.md` for detailed coverage.
