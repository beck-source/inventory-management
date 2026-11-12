---
name: vue-component-optimizer
description: Analyze Vue 3 single-file components for structure, rendering performance, and code reuse, then produce a prioritized optimization report with concrete before/after fixes. Use this whenever the user asks to audit, analyze, review, optimize, refactor, speed up, or "clean up" Vue components or views; asks why a Vue page is slow or re-renders too much; wants to find duplicated logic/markup/styles across components; or asks what should be extracted into a composable or shared component - even if they don't say "optimize" explicitly.
---

# Vue Component Optimizer

Analyze Vue 3 SFCs and suggest optimizations in two areas:

1. **Performance** - unnecessary re-renders, expensive template expressions, unstable `v-for` keys, heavy computed/watch chains, large lists, eager-loaded heavy components.
2. **Code reuse** - logic, markup, and styles duplicated across components that belong in a composable, a shared component, a utility, or a shared stylesheet.

The output is a **report**, not a refactor. Do not modify `.vue` files during analysis. If the user then asks to apply fixes, delegate `.vue` edits to the `vue-expert` subagent (this project's CLAUDE.md requires it), one finding group at a time, and verify behavior afterwards.

## Workflow

### 1. Scope

Decide what to analyze from the request:
- A single file/view -> analyze it deeply, but still check siblings for duplication of what you find.
- "The app" / "all components" / unspecified -> analyze everything under `client/src/views` and `client/src/components`, plus `client/src/composables` and `client/src/utils` (to know what shared code already exists).

### 2. Run the scanner

Get the mechanical metrics first so the manual review can focus on judgement calls:

```bash
node .claude/skills/vue-component-optimizer/scripts/scan-vue.mjs client/src
# or a single file / folder:
node .claude/skills/vue-component-optimizer/scripts/scan-vue.mjs client/src/views/Dashboard.vue
# machine-readable:
node .claude/skills/vue-component-optimizer/scripts/scan-vue.mjs client/src --json
```

It reports per-file size, script style, index keys, `v-if`+`v-for` on one element, function calls in interpolations, deep watchers, and cross-file duplication (identical CSS rule blocks, repeated `watch([...])` source lists, repeated helper function names). Treat its output as **leads, not verdicts** - every item must be confirmed by reading the code.

### 3. Read and analyze

Read each in-scope file. Walk through the checklist in `references/checklist.md` (performance checks P1-P10, reuse checks R1-R8, structure checks S1-S5). Before reporting a reuse opportunity, check whether a shared helper already exists (e.g. `utils/currency.js`, `composables/useFilters.js`) - "use the existing X" is a better suggestion than "create X".

For each candidate finding, confirm:
- **It is real** - quote the exact lines. No speculative "might be slow" findings without a concrete mechanism.
- **It matters at this scale** - this app uses in-memory mock data with lists of tens to low hundreds of rows. Virtual scrolling for a 40-row table is noise; a `.filter()` inside a `v-for` that runs per row per render is not. Calibrate severity to actual data size and render frequency.
- **The fix preserves behavior** - same output, same reactivity, same i18n, same filter behavior.

### 4. Write the report

Use this structure:

```markdown
# Vue Component Analysis: <scope>

## Summary
<2-4 sentences: overall health, the top 3 things worth doing, rough effort.>

| # | Finding | Category | Impact | Effort | Files |
|---|---------|----------|--------|--------|-------|
| 1 | ...     | Reuse    | High   | M      | 6     |

## Findings

### 1. <Title> (<Category>, Impact: High, Effort: M)
**Where:** [File.vue:L12-L30](client/src/views/File.vue#L12-L30), ...
**Problem:** <What is wrong and the concrete cost - extra renders, N copies to keep in sync, etc.>
**Fix:** <What to do.>
<before/after code - minimal, real code from the file, not pseudo-code>
**Risk / verify:** <What could break and how to check it.>

## Suggested order
<Sequence that minimizes risk: quick wins first, then extractions that later findings depend on.>

## Not worth doing
<Things that look like optimizations but aren't justified here, with one-line reasons. Keeps the user from chasing them.>
```

Ranking: Impact = how much it improves runtime cost or maintenance burden; Effort = S (<30 min, one file), M (a few files), L (structural, multiple views). Sort by impact/effort ratio, highest first. Cap the main list at ~10 findings; fold minor items into a short "Minor" list at the end.

### 5. Offer next steps

End by offering to apply a specific subset (e.g. "findings 1-3 are low-risk; want me to apply them?"). When applying:
- Delegate `.vue` changes to `vue-expert` with the exact finding text and before/after snippets.
- New composables go in `client/src/composables/`, utilities in `client/src/utils/`, shared components in `client/src/components/`, shared styles in `client/src/styles/`.
- After changes, verify with the Playwright MCP tools against `http://localhost:3000`: load each touched view, exercise all four filters, open affected modals, check the console for errors.
- Comment non-obvious logic changes (project convention).

## Project-specific context

Things to know about this codebase (verify they are still true before relying on them):
- Views mostly use `setup()` in `<script>`; newer components use `<script setup>`. Mixed style is a structure finding (S1), not a bug - recommend converging when touching a file, not a big-bang rewrite.
- Filter state is a module-level singleton in `useFilters.js`. Views each `watch` the filter refs and reload data - a prime candidate for a shared `useFilteredData`-style composable (R2).
- Modals (`*DetailModal.vue`, `TasksModal.vue`, `ProfileDetailsModal.vue`) each carry their own copy of overlay/container styles - check for a shared `BaseModal` opportunity (R3/R5).
- Raw data lives in refs, derived data in computed properties - suggestions must keep that pattern.
- Charts are custom SVG; there is no chart library to swap in.
- `v-for` keys must be stable domain ids (`sku`, `month`, `id`), never `index` (CLAUDE.md Common Issues #1).
- No emojis in UI; design tokens are slate/gray.
