---
name: vue-optimize
description: Analyze Vue 3 component structure and suggest optimizations for performance and code reuse. Use when reviewing client/src components/views for refactor opportunities, prop drilling, duplicated markup/logic, or render performance.
---

# Vue Component Optimization Analysis

Produce a prioritized, evidence-backed report of performance and code-reuse
improvements for the Vue 3 (Composition API) frontend in `client/src/`.

This skill is **analysis only** — do not edit `.vue` files here. If the user
wants a fix applied, delegate the implementation to the **vue-expert** subagent
(mandatory per CLAUDE.md for any `.vue` change).

## Scope

- `client/src/views/*.vue` — page-level components
- `client/src/components/*.vue` — shared components
- `client/src/composables/*.js` — shared logic
- `client/src/api.js`, `client/src/App.vue`

## Procedure

1. **Inventory the tree.** List every view/component with line count
   (`wc -l`), the components each one imports, and which composables it uses.
   Flag any single-file component over ~400 lines as a decomposition candidate.
2. **Map data flow.** For each view note: raw refs vs `computed`, what it
   fetches from `api.js`, how filters reach it (`useFilters`), and any state
   passed more than one level deep (prop drilling → candidate for a composable
   or provide/inject).
3. **Detect duplication.** Grep for repeated blocks: table/card markup,
   currency/number/date formatters, modal open/close patterns, SVG chart
   scaffolding, loading/error/empty states, fetch-on-filter-change watchers.
   Repeated 3+ times = extract to a component, composable, or util.
4. **Assess render performance** against the checklist below.
5. **Write the report.**

## Performance checklist

- `v-for` with `index` as `:key` (CLAUDE.md issue #1 — use `sku`, `month`, id).
- `v-for` + `v-if` on the same element; filter in a `computed` instead.
- Large lists (>100 rows) rendered without pagination/virtualization.
- Expensive work in the template or in methods that should be `computed`
  (sorting, filtering, reducing, `.getMonth()` on every render).
- Missing `v-once` / `v-memo` on static or rarely-changing subtrees.
- Non-lazy route components in the router (use `() => import(...)`).
- Wide reactive objects where `shallowRef` / `shallowReactive` would do
  (e.g. large fetched datasets never mutated in place).
- Watchers with `deep: true` on big structures, or watchers that refetch
  without debounce when multiple filters change together.
- Inline object/array/arrow literals passed as props (new identity each render).
- Components re-mounting instead of updating due to unstable `:key`.
- SVG charts recomputing path geometry on unrelated state changes.
- Duplicate API calls: multiple components fetching the same endpoint instead
  of sharing via a composable.

## Code-reuse checklist

- Formatters (currency `$800K`, percentages, dates) redefined per component →
  `client/src/utils/format.js`.
- Repeated detail-modal shell → one `<BaseModal>` with slots.
- Repeated data table → `<DataTable>` with column config.
- Filter-driven fetch logic copy-pasted across views → `useFilteredResource(endpoint)`
  composable wrapping `api.js` + `useFilters`.
- Loading/error/empty UI repeated → `<AsyncSection>` wrapper or composable state.
- Chart primitives (axes, gridlines, bars) → shared `components/charts/`.
- Constants (warehouses, categories, statuses, revenue goals $800K/$9.6M)
  duplicated → single module.

## Report format

```
## Vue Optimization Report

### Summary
<2-3 sentences: biggest wins>

### Component inventory
<table: component | LOC | imports | composables | notes>

### Findings (ranked)
1. [PERF|REUSE] <title> — impact: High/Med/Low, effort: S/M/L
   - Where: client/src/views/Foo.vue:123
   - Problem: <what and why it costs>
   - Suggested change: <concrete refactor; name the new component/composable/util>
   - Delegate to: vue-expert

### Quick wins
<one-liners safe to do immediately>
```

Rank by impact/effort. Cite `file:line` for every finding. Prefer 5-10 solid
findings over an exhaustive dump.
