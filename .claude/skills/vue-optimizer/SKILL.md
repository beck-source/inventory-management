---
name: vue-optimizer
description: Analyzes Vue 3 component structure and produces a prioritized, report-only set of performance and code-reuse optimization suggestions. Use this skill when asked to review, audit, profile, or optimize Vue components (.vue files) for performance, re-renders, reactivity efficiency, or duplicated UI/logic. Does NOT modify files.
---

# Vue Component Optimizer (Analyze & Report)

This skill inspects the Vue 3 Composition API frontend and reports **prioritized
optimization opportunities**. It is **report-only**: it never edits `.vue` files.
Surface findings; let the user decide what to apply. If they ask you to apply a
finding afterward, delegate the `.vue` edit to the **vue-expert** subagent per
the project's mandatory rule.

## When to use

- "Analyze / audit / review / optimize the Vue components"
- "Why is this page slow / re-rendering too much?"
- "Find duplicated components or logic we can share"
- Before a refactor, to scope where the wins are

## Scope & priorities

Primary focus: **performance**. Secondary: **code reuse**. Stay conservative —
report opportunities with evidence (`file:line`), never guess. Do not invent
problems; if a component is already clean, say so.

## Analysis workflow

1. **Inventory the components.** List `client/src/views/*.vue` and
   `client/src/components/*.vue`. Note each component's template size and
   `setup()` logic size.
2. **Read each component** (template, `<script>`, `<style scoped>`).
3. **Run the performance checklist** (below) against every component.
4. **Run the code-reuse checklist** across the whole set (cross-file).
5. **Produce the report** in the format below — ranked by impact.

Keep the analysis grounded in the patterns documented in `client/CLAUDE.md`.

## Performance checklist (primary)

For each component, check for and record line numbers of:

1. **Methods used where computed belongs.** Functions called in the template
   that derive data from reactive state and re-run on every render. These belong
   in `computed()` (cached until deps change).
   - Smell: `getForecastsByTrend(...)`, `getChangePercent(item)` etc. invoked
     multiple times inside the template / inside `v-for`.
2. **`v-for` keys.** Flag `:key="index"` or missing keys. Recommend a stable
   unique key (`sku`, `id`, `month`).
3. **Filtering/sorting/mapping inside the template or inside `v-for`.** Heavy
   array ops in render should move to `computed`.
4. **Repeated computation in a loop.** The same derived value computed per row
   instead of once.
5. **`v-if` vs `v-show`.** Frequently toggled blocks (tabs, charts, modals shown
   often) using `v-if` should consider `v-show`; rarely shown heavy content
   using `v-show` should consider `v-if`.
6. **Inline object/array/function literals in templates** passed as props or
   bound (`:style="{...}"`, `:class="[...]"`, `@click="() => ..."`) inside large
   lists — these create new references each render.
7. **Unbounded lists.** Tables/lists rendering all rows with no pagination,
   `slice`, or virtualization (the orders dataset is large — 250 rows).
8. **Watchers that refetch too broadly.** `watch` triggering full reloads on
   every keystroke/filter change without debounce (`watchDebounced`).
9. **Missing lazy-loading / code-splitting.** Heavy or rarely-used components
   (modals, charts) imported eagerly instead of via `defineAsyncComponent`.
10. **Reactivity overhead.** `ref`/`reactive` on large static data that never
    changes; destructured props losing reactivity.

## Code-reuse checklist (secondary)

Cross-file, look for:

1. **Duplicated template blocks** — near-identical card/table/badge markup
   repeated across views → candidate shared component in `components/`.
2. **Duplicated logic** — the same helper reimplemented in multiple views
   (e.g., percent-change, color-by-trend, currency formatting) → candidate
   composable in `composables/` or util in `utils/`.
3. **Repeated API/data-loading boilerplate** (`loading/error/try-catch-finally`)
   → candidate `useAsyncData`-style composable.
4. **Repeated inline styles / magic colors** (`#10b981`, `#ef4444`) → candidate
   shared CSS variables / design tokens.

## Severity rubric

- **High** — measurable render cost on large lists, or correctness-adjacent
  (index keys causing DOM reuse bugs).
- **Medium** — repeated work that scales with data but on small sets today.
- **Low** — cleanliness / future-proofing; minor wins.

## Report format

Output a single Markdown report. Do not edit files.

```markdown
# Vue Optimization Report

## Summary
- Components analyzed: N (views: X, components: Y)
- Findings: H high, M medium, L low
- Top 3 wins: <one line each>

## Findings

### [HIGH] <Short title> — `client/src/views/Foo.vue:42`
**Category:** Performance · Methods→computed
**What:** <what the code does now, with the snippet/line>
**Why it matters:** <impact, e.g. re-runs N times per render over 250 rows>
**Suggested change:** <concrete fix; show a small before/after if helpful>

### [MEDIUM] ...

## Code-reuse opportunities
- `Foo.vue:120` and `Bar.vue:88` repeat the trend-badge block → extract `TrendBadge.vue`.

## Recommended order of work
1. ...
2. ...

## Notes
- Report-only. To apply any item, delegate the .vue edit to the vue-expert subagent.
```

## Guardrails

- **Never modify `.vue` files** in this skill — report only.
- **Cite evidence** (`file:line`) for every finding; no vague claims.
- **Don't over-report.** Prefer a short list of real wins over an exhaustive
  list of nitpicks. If something is already optimal, note it and move on.
- **Match house style** — recommendations must align with `client/CLAUDE.md`
  (Composition API, computed for derived data, unique keys, centralized API).
