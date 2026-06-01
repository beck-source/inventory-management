# CLAUDE.md - Client

This file provides guidance to Claude Code (claude.ai/code) when working with the Vue 3 frontend.

## Commands

```bash
npm install && npm run dev   # Dev server on http://localhost:3000
npm run build                # Production build to dist/
```

## Architecture

- `src/api.js` — single Axios client, all HTTP calls go here. Filters passed as URLSearchParams query params, skipping values of `'all'`.
- `src/composables/useFilters.js` — shared singleton state for the 4-filter system (Time Period, Warehouse, Category, Order Status). All views import from here.
- `src/composables/useAuth.js`, `useI18n.js` — auth and i18n state.
- `src/views/` — page-level components (Dashboard, Inventory, Orders, Spending, Demand, Reports). Each loads data via `onMounted` + watches on filter composable.
- `src/components/` — reusable UI: `FilterBar.vue`, `*DetailModal.vue`, `TasksModal.vue`, `ProfileMenu.vue`.

## Key Patterns

**Filter reactivity**: Views watch the composable's filter refs and reload data on change. Always call `getCurrentFilters()` from `useFilters` when building API params.

**Date safety**: Always validate before parsing — `const d = new Date(val); if (!isNaN(d.getTime())) { ... }`. Raw date strings from mock data can be null.

**SVG charts**: All charts are custom SVG (no chart library). Use `computed` to transform data for chart coordinates. Define `viewBox` for responsive scaling.

**v-for keys**: Always use `item.id`, never array index.
