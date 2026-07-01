# CLAUDE.md - Server

This file provides guidance to Claude Code (claude.ai/code) when working with the FastAPI backend.

## Running

```bash
cd server && uv run python main.py   # http://localhost:8001, docs at /docs
cd tests && uv run pytest -v         # run all backend tests
```

## Adding an Endpoint

1. Define a Pydantic model in `main.py`
2. Add a route function with explicit path and `response_model`
3. Apply filters using the `apply_filters()` / `filter_by_month()` pattern (check for `'all'`, use `.lower()` for case-insensitive matching)
4. Write tests in `tests/backend/` using the **backend-api-test** skill

```python
@app.get("/api/resource", response_model=List[MyModel])
def get_resources(warehouse: Optional[str] = None, category: Optional[str] = None):
    results = all_resources
    if warehouse and warehouse != 'all':
        results = [r for r in results if r['warehouse'] == warehouse]
    if category and category != 'all':
        results = [r for r in results if r['category'].lower() == category.lower()]
    return results
```

## Data

- JSON files in `server/data/` are loaded at startup into module-level variables in `mock_data.py`
- All changes are lost on restart — edit the JSON files directly, then restart
- SKUs in orders must reference valid inventory items; category names must be consistent across files
