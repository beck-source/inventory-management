# CLAUDE.md - Server

This file provides guidance to Claude Code (claude.ai/code) when working with the FastAPI backend.

## Commands

```bash
uv sync                  # Install dependencies
uv run python main.py    # Start on http://localhost:8001 (API docs at /docs)
```

## Architecture

- `main.py` — all FastAPI endpoints plus `apply_filters()` and `filter_by_month()` helpers. Everything lives here (no separate modules).
- `mock_data.py` — loads `data/*.json` into module-level globals at startup. Data is in-memory; restart to reload.
- `data/*.json` — source of truth: `inventory.json`, `orders.json`, `spending.json`, `demand_forecasts.json`, `backlog_items.json`, `purchase_orders.json`, `transactions.json`.

## Key Patterns

**Never mutate globals**: Always filter on a copy — `results = [r for r in all_items if ...]`.

**Filter params**: All endpoints accept `warehouse`, `category`, `status`, `month` as optional query params. Skip filter when value is `'all'` or `None`. Inventory endpoints do **not** support `month` (no time dimension on inventory data).

**Date/quarter formats**: `apply_filters` handles both `2025-01` (month) and `Q1-2025` (quarter). Parse safely and skip records with null dates.

**Adding an endpoint**:
1. Define Pydantic response model
2. Add `@app.get` route, filter on copy of data, return typed response
3. Write tests in `tests/backend/`

**Adding data**: Update JSON in `server/data/` → update Pydantic model if structure changed → restart server.
