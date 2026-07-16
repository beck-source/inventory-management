# App Smoke Test Findings — 2026-07-16

Tested via Playwright against `localhost:3000` (frontend) / `localhost:8001` (backend). All 7 nav tabs (Overview, Inventory, Orders, Finance, Demand Forecast, Restocking, Reports) load and render data correctly.

## Issues

1. **Unresolved component** — `Failed to resolve component: PurchaseOrderModal` (Vue warning, fires on every page load from `Dashboard.vue`). Component is referenced but not imported/registered.

2. **404 on `/api/tasks`** — `loadTasks` (`App.vue:35` → `api.js:78`) calls `GET /api/tasks`, which doesn't exist on the backend. Fails on every page load.

3. **Display bug on Demand Forecast page** — Increasing-demand percentages render with a doubled plus sign, e.g. `++50.0%`, `++20.0%`, `++18.8%`.

4. **Leftover debug logging in `Reports.vue`** — Numerous `console.log` calls (lines 18, 23, 28, 31, 34, 37, 40, 42, 49, 88, 116, 129) fire on every render; noisy but not functionally broken.
