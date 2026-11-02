# Vue 3 audit checklist

What to look for once you are reading the code. The scanner only sees surface
patterns; most of the valuable findings below need you to understand the data
flow. Each entry says why it matters, so you can judge whether it applies.

## Contents
- Performance: rendering
- Performance: reactivity
- Performance: data loading
- Code reuse
- Structure
- Not worth flagging

## Performance: rendering

**Function calls in the template that derive data.** `v-for="x in getByStatus('open')"`
or `{{ total(items) }}` re-run on every re-render of the component, for any
reason, including unrelated state changes like opening a modal. A `computed`
caches until its own dependencies change. Fix: one computed per derived list,
or a computed returning a map (`byTrend.value.increasing`).
Calls that are cheap formatting of a single value (`formatDate(order.date)`)
are fine; flag only calls that filter, sort, reduce, or allocate arrays.

**Index or unstable keys in `v-for`.** `:key="index"` makes Vue reuse DOM and
component state by position, so filtering or sorting a list shows stale input
values, wrong animations, or mismatched child state. Use a stable id (`sku`,
`id`, `month`). Index keys are only harmless on static lists that never
reorder and hold no state, but still note them because this repo's CLAUDE.md
forbids them.

**`v-if` and `v-for` on the same element.** In Vue 3 `v-if` runs first and
cannot see the loop variable. Move the filter into a computed.

**Large static subtrees re-rendering.** A big block that never changes inside
a component that re-renders often can use `v-once`, or be split into a child
component so it has its own render boundary. Only worth it for genuinely large
blocks.

**Heavy inline SVG charts recomputed on each render.** Chart path/coordinate
math in the template or in methods should live in computeds so it is not redone
when unrelated state changes.

## Performance: reactivity

**Watchers that should be computeds.** `watch(a, () => { b.value = f(a.value) })`
duplicates state and can briefly be out of sync. Derive `b` with `computed`.

**Empty or no-op watchers.** `watch(x, () => {})` costs a subscription and
signals unfinished work. Remove, or implement what it was meant to do.

**`deep: true` on large objects.** Traverses everything on every change. Watch
the specific property (`() => obj.value.field`) instead.

**Large immutable data in deep `ref`/`reactive`.** Big arrays loaded once from
the API and never mutated item-by-item can use `shallowRef`, avoiding a proxy
per nested object. Worth it at thousands of rows, not dozens.

**Reactive state that does not need to be reactive.** Constants, lookup tables,
and config objects defined inside `setup` and wrapped in `ref` for no reason.

## Performance: data loading

**Watchers that refetch the same data several times.** If several views each
watch the same filter refs and each refetch, check whether a filter change
triggers duplicate requests, or whether requests can race (an older response
landing after a newer one and overwriting it). A shared composable can own the
fetch-on-filter-change logic once and guard against races.

**Loading everything to show a little.** Fetching full collections and slicing
in the client when the API supports filters.

## Code reuse

**The same helper redefined in several files.** `formatDate`, status-to-color
maps, `translateCategory`, percentage helpers. Check they really are the same:
compare bodies, not just names. Identical ones move to `utils/` (pure
functions) or `composables/` (if they need reactive state or i18n). Slightly
different ones: say how they differ and whether the difference looks
intentional.

**Copy-pasted filter wiring.** The same `watch([selectedPeriod, ...], load)` +
`onMounted(load)` block in every view is a composable waiting to happen, e.g.
`useFilteredData(fetcher)` returning `{ data, loading, error }`.

**Markup that re-implements an existing primitive.** Before suggesting a new
shared component, check what exists (`components/ui/`, other shared
components). Hand-rolled cards, badges, buttons, headers, and empty states in
views should use the existing primitive. Classes in a view's `<style>` that
match a primitive's class names are a strong hint.

**Repeated markup with no primitive yet.** Three or more near-identical blocks
(stat tiles, detail modals with the same shell, trend lists) suggest a new
component. Name it and sketch its props. Two copies usually are not enough to
justify an abstraction.

**Hard-coded colors and spacing.** Hex values in component styles instead of
the design tokens defined in the app's root styles drift from the theme and
break dark mode.

## Structure

**Very large components.** Over ~400 lines, or a template over ~200 lines,
usually means several responsibilities. Propose a concrete split along the
visual sections (each card or panel as a child), with props and emits for each.
Size alone is not a finding: say what the separate responsibilities are.

**Logic in the wrong layer.** Business rules (status thresholds, revenue goals)
duplicated across components belong in one module.

**Options API mixed with Composition API, or `setup()` returning large objects
instead of `<script setup>`.** Only mention as a consistency note; do not
propose rewriting working code just for style.

## Not worth flagging

- Micro-optimizations on lists of tens of items with no measurable cost. If you
  mention one, say the impact is small.
- Style-only preferences the codebase does not already follow.
- Abstractions for code that appears twice and is likely to diverge.
- Anything you have not confirmed by reading the code.
