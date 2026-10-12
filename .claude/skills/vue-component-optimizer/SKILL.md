---
name: vue-component-optimizer
description: Analyzes Vue 3 component structure in client/src for performance and code-reuse issues (reactivity misuse, unmemoized computations, unstable v-for keys, duplicated markup/logic across components) and applies the fixes. Use when asked to review, optimize, audit, or refactor Vue components.
---

# Vue Component Optimizer

Analyzes components under `client/src/views/` and `client/src/components/` for two categories of issues, then applies fixes.

## Process

1. **Discover** — read every `.vue` file in `client/src/views/` and `client/src/components/`.
2. **Analyze** each file for the checks below, noting file:line for every finding.
3. **Cross-reference** across files to find duplication (same markup pattern, same formatting logic, same API-calling pattern repeated in 2+ components).
4. **Report** findings to the user first: group by category, cite file:line, state the concrete fix. Keep it short — a table or bullet list, not prose per finding.
5. **Apply fixes**, per [CLAUDE.md](../../../CLAUDE.md)'s mandatory rule: delegate all `.vue` edits to the **vue-expert** subagent. Batch related fixes into one vue-expert call per file rather than one call per finding.
6. **Verify** — after fixes land, run the app (`run` skill or dev servers already running) and check the affected pages still render and the browser console is clean.
7. **Summarize** what changed, file by file, and flag anything you deliberately left alone (e.g., a structural extraction that's high-risk enough to want the user's sign-off first).

## Performance Checks

- **Reactivity misuse** — derived values computed inside a method, watcher, or inline in the template instead of a `computed()`. This codebase's convention (see CLAUDE.md) is: raw data in `ref()`, derived data in `computed()`.
- **Watcher-should-be-computed** — a `watch()` whose only job is to recompute a value and assign it to another ref. Replace with `computed()`.
- **Unstable `v-for` keys** — `:key="index"` instead of a stable identifier (`sku`, `id`, `month`, order number). Array reordering/filtering will misrender with index keys.
- **Inline literals in templates** — object/array/function literals created directly in template expressions (`:style="{ color: x }"`, `@click="() => foo(x)"`) that get re-created every render. Hoist to a computed or method.
- **Unmemoized expensive work** — filtering/sorting/reducing large arrays inside the `<template>` or on every render instead of behind a `computed()`.
- **Oversized components** — a single `.vue` file mixing multiple unrelated concerns (e.g., a view that also implements a generic stat-card or table that other views duplicate). Flag as a code-reuse issue too (see below) since the fix is the same: extract.

## Code-Reuse Checks

- **Duplicated formatting utilities** — currency/number formatting (`toLocaleString` with the same options) repeated across multiple files instead of a shared helper (e.g., `client/src/utils/format.js`).
- **Duplicated API-calling composition** — the same load-on-mount / loading-state / error-state pattern hand-rolled in multiple views instead of a shared composable (e.g., `useAsyncData`).
- **Duplicated markup** — stat cards, badges, filter bars, tables with near-identical structure copy-pasted across views instead of a shared component under `client/src/components/`.
- **Duplicated filter-handling logic** — this app has 4 shared filters (Time Period, Warehouse, Category, Order Status); flag any view that re-implements filter-to-query-param logic instead of reusing the existing filter composable/pattern.

## Fix Guidelines

- Prefer small, mechanical, low-risk fixes (extract a `formatCurrency` helper, fix a `v-for` key, convert a watcher to a computed) — apply these directly.
- For larger structural extractions that touch several files (pulling a repeated stat-card block into a new shared component used by 3+ views), still apply them, but call this out explicitly in the summary so the user knows to review that diff closely and re-test the affected pages.
- Never change existing API contracts or Pydantic models as part of this — this skill is frontend-only (`client/src/`).
- Match existing code style: Composition API, no comments unless explaining non-obvious WHY (see CLAUDE.md Code Style).
