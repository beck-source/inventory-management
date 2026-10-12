# CLAUDE.md - Server

This file provides guidance to Claude Code (claude.ai/code) when working with the FastAPI backend.

## Running the Server

```bash
uv run python main.py
# http://localhost:8001, docs at /docs
```

## Running Tests

```bash
cd ../tests
uv run pytest -v
```

## Architecture

Everything lives in `main.py` — there's no `routers/`, `services/`, or `models.py` split. Data is loaded once at import time in `mock_data.py` (JSON files in `data/` → module-level Python lists) and imported directly into `main.py`. All filtering happens in-memory on plain dicts; Pydantic models (defined at the top of `main.py`) only validate the response shape.

**Filtering**: two shared helpers in `main.py` — `apply_filters(items, warehouse, category, status)` for the common three, and `filter_by_month(items, month)` for date filtering on `order_date` (accepts `YYYY-MM` or `QN-YYYY` quarter strings via `QUARTER_MAP`). New filterable endpoints should compose these rather than reimplementing filter logic. Any `'all'` value means "don't filter on this field."

**Reports endpoints** (`/api/reports/quarterly`, `/api/reports/monthly-trends`) don't use `apply_filters` — they bucket the full unfiltered `orders` list by date extracted with string slicing, not `filter_by_month`.

## Data Model Changes

When changing the shape of a JSON file in `data/`, update the matching Pydantic model in `main.py` in the same change — response validation will fail otherwise. Keep SKUs in `orders`/`backlog_items` consistent with `inventory.json`, and category names consistent across all data files (comparisons are case-insensitive but not fuzzy).

## Known Gap

`purchase_orders` data (`data/purchase_orders.json`) is loaded in `mock_data.py` and used internally to compute `has_purchase_order` on backlog items, but there's no `/api/purchase-orders` route. The frontend's `api.js` calls it anyway (`createPurchaseOrder`, `getPurchaseOrderByBacklogItem`) — those requests currently 404. Same for `/api/tasks`.
