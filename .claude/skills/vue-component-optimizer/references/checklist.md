# Vue Component Analysis Checklist

Each check lists: what to look for, why it matters, the fix, and when it is NOT worth flagging.

## Performance

### P1. Unstable or missing `v-for` keys
- **Look for:** `:key="index"`, `:key="i"`, missing `:key`, keys built from non-unique fields.
- **Why:** Index keys make Vue patch the wrong DOM nodes when the list is filtered, sorted, or reordered - wrong row state and extra DOM work.
- **Fix:** Key by a stable domain id (`sku`, `id`, `month`, `quarter`). If none exists, derive one in a computed property.
- **Skip when:** Never skip in this project - it is a stated convention.

### P2. Function calls in template interpolations and bindings
- **Look for:** `{{ formatX(item.value) }}`, `:class="getClass(item)"`, `{{ calculatePercentage(a, b) }}` - especially inside `v-for`.
- **Why:** Methods run on every re-render of the component, for every row. Computed properties are cached.
- **Fix:** If the input is component-level state, move to a `computed`. If it is per-row, precompute a decorated list in one computed (`rows = computed(() => items.value.map(i => ({ ...i, pct: ..., statusClass: ... })))`).
- **Skip when:** The function is trivial and pure (e.g. `t('key')`, a simple currency format) and the list is small. Flag only if the function does filtering/sorting/searching or allocates per call.

### P3. Filtering/sorting/searching inside the template or per row
- **Look for:** `v-for="x in items.filter(...)"`, `.find()`/`.filter()` inside a method called per row, nested loops (O(n*m)) like `orders.filter(o => o.sku === item.sku)` per inventory item.
- **Why:** Re-executed every render; nested lookups scale quadratically.
- **Fix:** Move into a computed; replace per-row lookups with a `Map`/`Set` built once in a computed.

### P4. `v-if` and `v-for` on the same element
- **Why:** In Vue 3 `v-if` evaluates first and cannot see the loop variable - usually a bug, always unclear.
- **Fix:** Filter in a computed, or wrap with `<template v-for>`.

### P5. Watchers that should be computed, or overly broad watchers
- **Look for:** `watch` that only assigns a derived value to another ref; `deep: true` on large objects; `watch` + manual sync where `computed` suffices; multiple watchers triggering the same reload.
- **Fix:** Replace with `computed`; narrow the source to the specific fields; debounce if triggered by text input.
- **Skip when:** The watcher performs a side effect (API call, localStorage) - that is correct usage.

### P6. Redundant or racing data loads
- **Look for:** The same endpoint fetched by several components on one page; a filter watcher that fires a reload without cancelling/ignoring the previous in-flight request; loading data in `onMounted` and again in an immediate watcher.
- **Why:** Duplicate network calls; stale responses can overwrite fresh ones when filters change quickly.
- **Fix:** Track a request token/counter and ignore stale responses; share fetched data via a composable.

### P7. Large reactive payloads that never change
- **Look for:** Big static lookup tables or API results that are only read, held in `ref`/`reactive`.
- **Fix:** `shallowRef` for large arrays replaced wholesale; plain constants outside `setup` for static config; `markRaw` for non-reactive objects.
- **Skip when:** Payload is small (< a few hundred items) - not measurable here.

### P8. Heavy components loaded eagerly
- **Look for:** Modals and rarely-opened panels imported statically into a view; routes not lazy-loaded.
- **Fix:** `defineAsyncComponent(() => import('./HeavyModal.vue'))`; `component: () => import('./views/X.vue')` in the router.
- **Skip when:** The component is small or almost always shown.

### P9. Expensive SVG/chart recomputation
- **Look for:** Path strings, scales, or tick arrays computed in methods called from the template; recalculating max/min across data in multiple places.
- **Fix:** One computed for the chart geometry (scales, points, path `d`), consumed by the template.

### P10. Static content not marked static
- **Look for:** Large blocks of markup that never change (legends, static tables, icons) inside frequently re-rendering components.
- **Fix:** `v-once` or `v-memo="[deps]"` for big list rows whose inputs rarely change.
- **Skip when:** The block is small. This is a last-resort micro-optimization.

## Code reuse

### R1. Duplicated formatting/helper functions
- **Look for:** `formatCurrency`, `formatDate`, `formatNumber`, `getStatusClass`, `calculatePercentage` defined in multiple components; inline `toLocaleString`/`Intl.NumberFormat` calls with identical options.
- **Fix:** Move to `client/src/utils/` (check `currency.js` first - extend it rather than creating a parallel helper).

### R2. Duplicated data-loading + filter-watching logic
- **Look for:** The same shape in multiple views: `loading`/`error` refs, `onMounted(load)`, `watch([selectedLocation, selectedCategory, ...], load)`, try/catch/finally around an `api.*` call.
- **Fix:** A composable, e.g.:
  ```js
  // composables/useFilteredResource.js
  export function useFilteredResource(fetcher, filterKeys) {
    const data = ref(null), loading = ref(true), error = ref(null)
    // fetcher receives current filters; filterKeys limits which filters trigger reloads
    ...
    return { data, loading, error, reload }
  }
  ```
  Preserve per-view differences (which filters apply - inventory has no month filter).

### R3. Duplicated component shells
- **Look for:** Several modals/cards/panels with the same overlay, header, close button, escape-key handling, and footer structure.
- **Fix:** A base component with slots (`BaseModal` with `header`/default/`footer` slots, `v-model:open` or `@close`). Keep each modal's content in its own file.

### R4. Repeated markup blocks within or across views
- **Look for:** KPI tiles, stat cards, status badges, table headers, empty/loading/error states repeated with only data differences.
- **Fix:** Small presentational components (`StatCard`, `StatusBadge`, `LoadingState`) with props. Only extract when there are 3+ copies or the copies already diverged in a buggy way.

### R5. Duplicated scoped CSS
- **Look for:** Identical rule blocks for the same class name in multiple `<style scoped>` sections (`.modal-overlay`, `.badge`, `.card`, table styles).
- **Fix:** Move to a shared stylesheet in `client/src/styles/` (or into the shared component from R3, which removes the CSS duplication for free).

### R6. Repeated derived-data logic
- **Look for:** The same `computed` logic (totals, status counts, grouping by month/category) in multiple views.
- **Fix:** A composable or pure util function taking the raw array.

### R7. Duplicated constants
- **Look for:** Status lists, color maps, month name arrays, goal values (e.g. revenue goals) hard-coded in several files.
- **Fix:** A shared constants module.

### R8. Not using existing shared code
- **Look for:** Components re-implementing something already in `composables/` or `utils/`.
- **Fix:** Use the existing helper. Highest-value reuse finding because it costs nothing to add.

## Structure

### S1. Inconsistent script style
- **Look for:** Mix of Options API, `setup()` returning an object, and `<script setup>`.
- **Fix:** Recommend `<script setup>` for files being touched anyway. Not a standalone task unless the user wants consistency.

### S2. Oversized components
- **Look for:** Files > ~400 lines, or templates with several independent sections (KPIs, charts, tables, modals) in one SFC.
- **Fix:** Split by section into child components; keep data loading in the parent or a composable, pass data via props.

### S3. Props/emits hygiene
- **Look for:** Missing `defineProps` types/defaults, props mutated in the child, undeclared emits, deep prop drilling (3+ levels).
- **Fix:** Typed props, `defineEmits`, `v-model` for two-way props, `provide/inject` or a composable for drilling.

### S4. Side effects without cleanup
- **Look for:** `addEventListener`, `setInterval`, `setTimeout`, observers created in `onMounted` without matching removal in `onUnmounted`.
- **Why:** Memory leaks and handlers firing after navigation.
- **Fix:** Add cleanup or use a composable that manages it.

### S5. Template logic density
- **Look for:** Long ternaries, chained conditions, inline arithmetic in templates.
- **Fix:** Name the logic with a computed. Improves readability and enables caching (overlaps with P2).
