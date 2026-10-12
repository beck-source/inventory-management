# CLAUDE.md - Client

This file provides guidance to Claude Code (claude.ai/code) when working with the Vue 3 frontend.

> **MANDATORY**: Always delegate `.vue` file creation or significant modification to the **vue-expert** subagent.

## Running

```bash
cd client && npm install && npm run dev   # http://localhost:3000
cd client && npm run build               # production build to client/dist/
```

## Key Patterns

### Filter Integration
Import `useFilters` in any view that needs to respond to filter changes:
```javascript
const { getCurrentFilters } = useFilters()

// Re-fetch when filters change
watch([() => useFilters().selectedPeriod, () => useFilters().selectedLocation, ...], loadData)

// Pass to API
const data = await api.getOrders(getCurrentFilters())
```

### i18n
Use `useI18n()` for all user-visible strings. Never hardcode English text in templates.
```javascript
const { t } = useI18n()
// In template: {{ t('nav.inventory') }}
```
Locale is stored in `localStorage`; currency is derived from locale (USD/JPY).

### View Data Pattern
- Store raw API responses in `ref`s (`allOrders`, `inventoryItems`)
- Derive display data in `computed` properties — never mutate refs from computed
- Always handle `loading` and `error` states

### SVG Charts
Chart data must be in a `computed` property. All SVG coordinates should be derived from `viewBox` dimensions, not hardcoded pixels.

## Common Pitfalls
- `v-for` keys must be unique IDs (SKU, order ID, month string) — never array index
- Validate dates before `.getMonth()`: `const d = new Date(s); if (!isNaN(d.getTime())) { ... }`
- Props are read-only — emit events to update parent state
- `useFilters` refs are module-level singletons; destructuring them breaks reactivity — always call `useFilters()` inline
