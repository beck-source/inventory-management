---
name: vue-component-analyzer
description: Use when asked to analyze Vue 3 components for performance problems or code reuse opportunities — symptoms include slow renders, heavy computed chains, repeated logic across components, large single-file components, or duplicate state management patterns.
---

# Vue Component Analyzer

Structured checklist for auditing Vue 3 + Composition API components. Covers performance and reuse in one pass. Output findings with line numbers, category, impact (High/Med/Low), and a concrete fix.

## Scan Order

Work through these five zones sequentially. Do not skip zones even if they look clean — most misses happen in zones the reader thought were fine.

### Zone 1: Template scan

| Check | What to look for |
|---|---|
| `v-for` keys | Every `v-for` must have `:key` on a stable unique ID (not `index`) |
| Inline functions | `@click="() => fn(arg)"` creates a new function every render — extract to a named method |
| Heavy expressions | `{{ expensive(item) }}` in loops — move to `computed` |
| `v-if` vs `v-show` | Toggle-heavy elements (tabs, modals triggered frequently) → `v-show`; conditionally-rendered branches that mount rarely → `v-if` |
| `v-memo` candidates | `v-for` lists where each item's render depends only on the item itself → add `v-memo="[item.id, item.status]"` |
| Repeated method calls | Same method called 2+ times with same args on one render cycle — use a computed or pre-call result |

### Zone 2: Script setup — reactive state

| Check | What to look for |
|---|---|
| `ref` vs `shallowRef` | Large arrays/objects fetched from API and never mutated deeply → prefer `shallowRef`; Vue won't walk the tree |
| `reactive` on simple scalars | `reactive({ count: 0 })` → just `ref(0)` |
| `markRaw` on static objects | Config objects, Mapbox instances, Chart.js instances passed to `reactive` → wrap in `markRaw()` to skip proxy overhead |
| `toRaw` before passing down | Passing reactive data to a non-Vue library? Call `toRaw(data)` first |

### Zone 3: Script setup — computed properties

| Check | What to look for |
|---|---|
| Single fat computed | One computed that iterates the same list 2+ times → split into smaller computeds that depend on each other (Vue caches each) |
| Redundant rebuilds | Multiple computeds each calling `.filter()` on the same source → extract one `filteredBase` computed that others derive from |
| Object construction in computed | `computed(() => ({ ...a, ...b }))` creates a new object reference every run, breaking child `v-if` memo chains → return primitives where possible |
| `watch` doing what `computed` should | `watch(x, () => { y.value = x.value * 2 })` → replace with `computed(() => x.value * 2)` |
| Date/heavy operations in sort | `array.sort((a, b) => new Date(a.date) - new Date(b.date))` in a computed → pre-parse dates into timestamps during load |

### Zone 4: Script setup — async / lifecycle

| Check | What to look for |
|---|---|
| Modal content loaded eagerly | If a modal or drawer is conditionally shown, wrap the import in `defineAsyncComponent` so the chunk isn't parsed on initial render |
| All fetches in `onMounted` | Any fetch that doesn't need DOM → can be triggered earlier or lazily |
| Duplicated try/catch/finally | Same loading/error/data pattern across 2+ components → candidate for `useDataLoader` composable |

### Zone 5: Cross-component reuse

**Always run this grep first** — do not rely on memory or inference. Anchor findings to actual output:

```bash
grep -rn "function translate\|function format\|function get.*Class\|const loading\|const error\|const currency" client/src/views/
```

Patterns worth extracting only when they appear in **2 or more components** with **identical or near-identical logic**:

| Pattern | Extract to |
|---|---|
| Translation/label maps (`translateCategory`, `translatePriority`) | `composables/useTranslations.js` |
| Date/currency formatting | `composables/useFormatting.js` |
| Modal open/close/data state (3+ refs per modal) | `composables/useModal.js` |
| Loading + error + try/catch/finally | `composables/useDataLoader.js` |
| Status → CSS class mapping | `composables/useStatusClasses.js` |
| Identical table or list structures | Shared `<DataTable>` / `<ItemList>` component with slots |

**Do NOT extract** if: the pattern appears only once, the abstraction would require 5+ props to be equivalent to the original, or it's a 3-line function with no logic.

## Output Format

For each finding:

```
[Zone] Line XX-XX | Category | Impact: High/Med/Low
Problem: <one sentence>
Fix: <one sentence or code snippet>
```

Group by zone. At the end, add a **Top 3 Quick Wins** section — changes under 30 minutes that give the highest return.

## Impact Guide

| High | Med | Low |
|---|---|---|
| Prevents unnecessary re-render of 10+ children | Reduces a computed from O(n²) to O(n) | Cosmetic / style only |
| Duplicate logic in 3+ files | Missing key on v-for list | Single inline function in template |
| Heavy chunk loaded on initial paint | `reactive` on 50+ field API object | `watch` doing what `computed` should |

## Common Mistakes to Skip

- **Don't flag `computed` wrapping a simple property access** — Vue's overhead here is negligible.
- **Don't recommend `v-show` on elements rendered only once** — `v-if` is correct there; `v-show` wastes initial paint.
- **Don't suggest extracting a composable for a function called in one place** — premature abstraction.
- **Don't suggest `shallowRef` if the template or children read nested properties reactively** — it will silently break reactivity.
