---
name: vue-component-analysis
description: Analyze Vue 3 component structure and produce a prioritized report of performance and code-reuse improvements for the inventory-management client. Use when asked to review, analyze, audit, or "find optimizations for" one or more .vue files or the client as a whole. This skill only reads and reports — it does not edit .vue files (hand fixes to the vue-expert agent).
---

# Vue Component Analysis

A repeatable method for analyzing Vue 3 components in `client/src/` and reporting **performance** and **code-reuse** improvements, ranked by impact. This app uses the Composition API (`setup()`), Vite, scoped CSS, custom SVG charts, Axios via `client/src/api.js`, and shared state in composables (`useFilters`, `useI18n`, `useAuth`).

## What this skill does and does not do

- **Does:** read components, measure them against the checks below, and emit a prioritized report with concrete file:line references and a suggested fix for each finding.
- **Does not:** edit `.vue` files. This repo's rule is that any create/significant-modify of a `.vue` file goes through the **vue-expert** agent. Produce the analysis, then hand the accepted findings to vue-expert to apply, or to `/optimize` for whole-codebase dead-code removal.
- **Not a bug hunt.** Correctness bugs belong to `/code-review`. Stay on performance and reuse.

## Procedure

1. **Scope the target.** One component, a folder (`views/` or `components/`), or the whole client. If unscoped, default to `client/src/views/*.vue` and `client/src/components/*.vue`.
2. **Measure first.** For each target: total lines and the template / script / style split (`grep -n -E '^<template>|^<script|^<style' file.vue`). Size flags candidates; it is not itself a finding.
3. **Run the two lenses** below (Performance, Reuse) against each component. Record every hit with `file:line`, the pattern, and the fix.
4. **Cross-component pass.** Reuse findings usually span files — look for the same boilerplate repeated across views before concluding.
5. **Rank and report** using the output format at the end. Lead with the highest impact-to-effort findings.

## Lens 1 — Performance

Check each component for these, in roughly descending impact:

### P1. Methods called in templates (should be `computed`)
A function invoked in `{{ }}`, `:prop`, or `v-if` re-runs on **every** re-render; a `computed` caches until its deps change. Flag any `{{ someMethod(...) }}` doing real work, especially inside a `v-for`.
- Real examples: `views/Backlog.vue` calls `getBacklogByPriority('high').length` three times in the template (three full filters per render); `views/Inventory.vue:68` runs `getStockStatus(item)` per row; `views/Reports.vue:88,94` run `getChangeValue`/`getGrowthRate` per row.
- Fix: convert to a `computed` (parametric cases → a `computed` map keyed by the argument, or precompute the derived field once when data loads).

### P2. `:key` bound to array index
Index keys make Vue reuse DOM nodes incorrectly when a list reorders or items are inserted/removed — stale rows, wrong state, subtle render cost. This repo's `client/CLAUDE.md` explicitly forbids it.
- Real examples: `views/Reports.vue:28,51,82` (`:key="index"`), `views/Orders.vue:61,110` (`:key="idx"`).
- Fix: key by a stable unique id — `sku`, `order_number`, `month`, etc.

### P3. `v-if` on frequently-toggled content (prefer `v-show`)
`v-if` mounts/unmounts; for something toggled often (tab panels, chart overlays, expandable rows) `v-show` (CSS `display`) is cheaper. Reserve `v-if` for rarely-shown or expensive subtrees.

### P4. Un-debounced reactive work
A `watch` on a filter or search input that fires an API call or heavy recompute on every keystroke. Real `watch` sites to inspect: `Inventory.vue:169`, `Orders.vue:181`, `Dashboard.vue:676`, `Demand.vue:165`, `Spending.vue:374`, `Backlog.vue:138`. Flag any that watch a text input without debounce.
- Fix: debounce the handler, or watch a derived value that changes less often.

### P5. Work repeated in the template that could be hoisted
Same expression computed in multiple bindings (e.g. `month.revenue.toLocaleString()` recomputed for bar height, title, and label). Hoist into one `computed`/derived field.

### P6. Oversized single-file components
Large components re-render as a unit and are hard to reason about. Treat these as thresholds, then confirm with the reuse lens before recommending a split:
- template > ~150 lines, script > ~200 lines, or file > ~400 lines.
- Real examples: `views/Dashboard.vue` (1271 lines: template 1–298, script 299–728, style 729–1271), `views/Spending.vue` (852), `components/TasksModal.vue` (621).
- Fix: extract cohesive template blocks into child components and cohesive logic into composables (see R2/R3).

## Lens 2 — Code Reuse

### R1. Duplicated data-loading boilerplate → a composable
Every view repeats the same shape: `const loading = ref(true)` / `error` / `items`, a `loadX()` with `try { loading.value=true … } catch { error.value=… } finally { loading.value=false }`, a `watch([...filters], loadX)`, and `onMounted(loadX)`. All seven views (`Backlog, Dashboard, Inventory, Demand, Orders, Spending, Restocking`) carry this.
- Fix: extract a `composables/useApiResource.js` — `useApiResource(fetcher, { watch: [...] })` returning `{ data, loading, error, reload }` that wires the `watch` + `onMounted` internally. Report it once as a single cross-cutting finding, not seven times.

### R2. Formatting done inline instead of via the existing util
`utils/currency.js` already exports `formatCurrency` / `formatCurrencyWithDecimals` / `convertAmount`, yet views contain ~24 inline `toLocaleString()` / `.toFixed()` sites (e.g. `views/Spending.vue:59–95`). Inline formatting is not just duplication — a bare `amount.toLocaleString()` **skips the USD→JPY conversion**, so those figures are wrong when the locale is Japanese.
- Fix: route every money/number format through the util (and percentages through one shared helper if the pattern recurs, e.g. `Reports.vue:313`).

### R3. Repeated template/markup blocks → shared components
Look for the same structural block copy-pasted across views: KPI stat cards (`stats-grid` / `stat-card`), the loading/error/empty triad, SVG chart scaffolding, detail modals. The `components/` dir already holds several `*DetailModal.vue`; new repetition should join it rather than live inline.
- Fix: extract a presentational component (props down, events up); keep data-fetching in the parent/composable.

### R4. Logic that belongs in a composable, not a view
Shared, stateful, or reusable logic sitting inside a single view's `setup()` — filter derivation, selection state, currency/locale wiring, polling. If two views need it, it's a composable (this app's `useFilters` / `useI18n` / `useAuth` are the models to match).

### R5. Prop / event hygiene (blocks reuse)
Components that mutate props directly, or reach into global composable state instead of taking props, are hard to reuse. Flag direct prop mutation and suggest `emit` instead.

## Output format

Emit one ranked table plus a short per-finding detail. Rank by impact-to-effort (a 3-line filter run per render on every row beats a cosmetic split).

```
## Vue Analysis — <scope>

| # | Sev  | Lens        | Location                     | Finding                                   |
|---|------|-------------|------------------------------|-------------------------------------------|
| 1 | High | Reuse (R1)  | all 7 views                  | Duplicated fetch/loading boilerplate      |
| 2 | High | Perf (P2)   | Reports.vue:28,51,82         | :key="index" on dynamic lists             |
| 3 | Med  | Reuse (R2)  | Spending.vue:59–95 (+~20)    | Inline formatting; skips JPY conversion   |
| … |      |             |                              |                                           |

### 1. Duplicated fetch/loading boilerplate  (Reuse · High)
**Where:** Backlog/Dashboard/Inventory/Demand/Orders/Spending/Restocking `setup()`
**Why it matters:** <impact>
**Suggested fix:** extract `useApiResource(fetcher, { watch })` … <sketch>
**Effort:** M · **Apply via:** vue-expert
```

Rules for the report:
- Every finding cites real `file:line`(s) you verified this run — never a generic "somewhere".
- State impact concretely (what re-runs, what breaks in JPY, how many call sites), not "improves performance".
- Give a fix sketch, not the full diff. Application is vue-expert's job.
- Collapse cross-file repetition into one finding with all locations, not N copies.
- If a target is clean on a lens, say so briefly rather than inventing findings.

## Handoff

After the user picks findings to act on:
- **`.vue` changes** → delegate to the **vue-expert** agent (mandatory for this repo).
- **New composable / util** (`composables/*.js`, `utils/*.js`) → vue-expert as well, since views must be rewired to use it.
- **Whole-codebase dead-code / unused-dependency removal** → the `/optimize` command, which already covers that ground.
- Re-run this skill after changes to confirm the finding cleared.
