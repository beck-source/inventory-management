---
name: vue-optimize
description: Analyze Vue 3 component structure and surface optimization opportunities across performance, code reuse, reactivity pitfalls, and accessibility/semantics. Use when the user asks to "optimize", "review", "audit", or "analyze" one or more .vue files. Outputs a single structured JSON report — no file edits.
---

# Vue Component Optimization Analyzer

This skill audits Vue 3 Single File Components (`.vue`) and returns a **single JSON object** describing optimization opportunities. It never modifies files — the report is consumed by a human or downstream tooling.

## Invocation

The skill takes one positional argument: a path to a `.vue` file or a directory.

```
/vue-optimize client/src/views/InventoryView.vue
/vue-optimize client/src/views/
/vue-optimize client/src/components/
```

**Argument resolution:**
1. If the path is a file ending in `.vue`, analyze just that file.
2. If the path is a directory, recursively find all `.vue` files (`**/*.vue`), excluding `node_modules/` and `dist/`.
3. If no argument is supplied, return an error finding with `id: "INPUT-001"` rather than guessing — do not scan the whole repo by default.
4. Paths are relative to the project root (the current working directory at invocation).

## Process

For each `.vue` file in scope:

1. **Read the file** via the Read tool.
2. **Split into sections**: `<template>`, `<script>` (and `<script setup>`), and `<style>`. Many checks are section-specific.
3. **Run every check** in the four categories below. Record the matching line number (1-indexed, file-relative) and a short snippet (≤120 chars, single line, trim whitespace).
4. **Emit one finding per match.** If the same issue appears N times in a file, emit N findings — do not dedupe within a file.
5. **Cross-file checks** (`REUSE-*`) run after all files are read.

After scanning, output the JSON report as the **final assistant message body**, wrapped in a single ` ```json ` fenced code block. No prose before or after the block — downstream consumers parse the block directly.

## Output Schema

```json
{
  "schema_version": "1.0",
  "scanned_at": "ISO-8601 UTC timestamp",
  "target": "the argument path as given",
  "files_analyzed": <int>,
  "summary": {
    "total_findings": <int>,
    "by_severity": { "high": <int>, "medium": <int>, "low": <int> },
    "by_category": {
      "performance": <int>,
      "reuse": <int>,
      "reactivity": <int>,
      "accessibility": <int>
    }
  },
  "findings": [
    {
      "id": "<CATEGORY>-<NNN>",
      "category": "performance|reuse|reactivity|accessibility",
      "severity": "high|medium|low",
      "file": "<path relative to repo root>",
      "line": <int, or null for cross-file findings>,
      "snippet": "<≤120 chars, single line>",
      "issue": "<one sentence — what was detected>",
      "why": "<one sentence — why it matters>",
      "suggestion": "<one sentence — what to do>",
      "fix_example": "<short code fragment, optional, may be null>"
    }
  ]
}
```

**Ordering:** sort `findings` by `(file, line, id)`. Cross-file findings (no `line`) sort last per file.

**Severity calibration:**
- `high` — correctness or runtime-crash risk (prop mutation, date parsing without validation, missing `.value` causing a string-typed bug).
- `medium` — measurable perf cost or accessibility blocker (index keys on long lists, missing `alt`, missing form labels).
- `low` — style / maintainability (suggested composable extraction, v-if vs v-show on rarely-toggled content).

## Checks

Each check below lists the `id`, default severity, the section it scans, the detection heuristic, and the human-facing message. **The id and message wording are normative — use them verbatim** so reports stay diff-able across runs.

### Performance (`PERF-*`)

| ID | Severity | Section | Detection | Message |
|---|---|---|---|---|
| `PERF-001` | medium | template | `v-for="(<x>, <idx>) in <list>"` where `:key="<idx>"` references the index variable | "v-for uses the array index as :key, which causes incorrect DOM reuse on reorder." |
| `PERF-002` | medium | template | An expression in a `{{ … }}` interpolation or attribute binding calls a method (`foo()`) whose name starts with `format`, `compute`, `calculate`, `get`, `filter`, `sort`, `map`, `reduce` and the same call appears on ≥3 elements in the same template | "Repeated method call in template — extract to a computed property so the result is cached." |
| `PERF-003` | low | template | `v-if` on an element with an event/state binding suggesting frequent toggle (e.g., sibling has `@click="show…"`, `@toggle`, `:class` switching on the same ref) | "Element toggles frequently — prefer v-show to avoid mount/unmount cost." |
| `PERF-004` | medium | template | Prop binding with an inline object/array literal: `:foo="{ … }"` or `:foo="[ … ]"` containing >1 property/element | "Inline object/array literal creates a new reference each render, defeating child memoization. Hoist to a computed." |
| `PERF-005` | medium | template | Chained array transform inside a template expression: any of `.filter(`, `.map(`, `.sort(`, `.reduce(` appearing inside `{{ }}`, `:attr=""`, or `v-for="… in …"` | "Array transform runs on every render. Move to a computed property." |
| `PERF-006` | medium | script | `watch(` or `watchEffect(` whose callback contains `axios.`, `fetch(`, or `api.` and no `{ debounce` / `useDebouncedRef` / `debouncedWatch` nearby (within 5 lines) | "Watcher fires an API call without debouncing — rapid input changes will flood the network." |
| `PERF-007` | medium | script | `JSON.parse(JSON.stringify(` applied to a variable that also appears in a `ref(`/`reactive(`/`computed(` declaration | "Deep-cloning reactive data via JSON round-trip is slow and loses non-JSON values; use structuredClone or remap explicitly." |

### Code Reuse (`REUSE-*`)

These are cross-file. Run after all files have been read.

| ID | Severity | Detection | Message |
|---|---|---|---|
| `REUSE-001` | low | The same load pattern (`loading = ref(true)` + `try { … = await api.<X> } catch { … } finally { loading = false }`) appears in ≥3 files | "Duplicate async-load scaffolding across components — extract a `useAsyncData` composable." |
| `REUSE-002` | low | Two or more files declare a function with the same name (`formatCurrency`, `formatDate`, `formatMonth`, `priorityColor`, etc.) and structurally similar bodies (≥80% line overlap) | "Duplicate helper function — move to `composables/` or `utils/`." |
| `REUSE-003` | low | The same multi-line `computed(() => …)` body (≥4 lines) appears in ≥2 files | "Duplicate computed logic — extract a composable." |
| `REUSE-004` | low | A `<template>` block of ≥15 contiguous lines is byte-identical (after trimming) between two files | "Identical template block in multiple files — extract a shared component." |

For cross-file findings, set `line: null` and put the duplicated symbol/snippet in `snippet`. List one finding per *group* of duplicated occurrences, and enumerate each location in a `locations` array on that finding (extension to the schema, only allowed on `REUSE-*`).

### Reactivity Pitfalls (`REACT-*`)

| ID | Severity | Section | Detection | Message |
|---|---|---|---|---|
| `REACT-001` | high | script | Inside `setup(props` (or `setup(props,`), a destructuring assignment `const { … } = props` or `let { … } = props` | "Destructuring props in setup() breaks reactivity — use toRefs(props) or access props.<name> directly." |
| `REACT-002` | high | script | A line that calls `.value` on something declared via `computed(`, OR a line that *assigns* to a name declared via `ref(` without `.value` (e.g., `count = 5` where `const count = ref(0)` exists in the same file) | "Reactive access pattern is wrong — refs need `.value` in script, and computed values are read-only." |
| `REACT-003` | high | script | An assignment whose left-hand side matches `props.<name>` or `props.<name>.<sub>` | "Direct prop mutation — emit an event to the parent instead." |
| `REACT-004` | high | script | `new Date(<expr>)` followed within 3 lines by `.getMonth(`, `.getFullYear(`, `.getDate(`, `.toISOString(`, or `.toLocaleDateString(` without an intervening `isNaN(` / `Number.isNaN(` check on the parsed date | "Date parsed from external data without validation — `Invalid Date` will throw or yield NaN." |
| `REACT-005` | high | script | An assignment whose left-hand side names a `computed(` declaration in the same file | "Mutating a computed property — computed values are derived, not stored. Change the source ref instead." |
| `REACT-006` | low | script | `watch(<bareIdentifier>, …)` where `<bareIdentifier>` is not declared via `ref(`, `reactive(`, `computed(`, or `toRef(` in the same file (i.e., a plain value) | "watch source is not reactive — the callback will never fire. Wrap in `() => …` or use a ref." |

### Accessibility / Semantics (`A11Y-*`)

| ID | Severity | Section | Detection | Message |
|---|---|---|---|---|
| `A11Y-001` | medium | template | `<button …>` whose body is empty/whitespace-only AND has no `aria-label` / `:aria-label` / `title` attribute | "Button has no accessible name — add visible text, aria-label, or title." |
| `A11Y-002` | medium | template | `<img …>` without an `alt=` attribute (decorative images should use `alt=""`) | "Image is missing an alt attribute — provide alt text or `alt=\"\"` for decorative images." |
| `A11Y-003` | medium | template | `<a …>` without `href` / `:href` / `:to` / `to` attribute, with an `@click` handler | "Anchor used as a button — use `<button>` so it's keyboard-activatable and announced correctly." |
| `A11Y-004` | medium | template | `<input …>` (excluding `type="hidden"`, `type="submit"`, `type="button"`) not preceded within 3 lines by a `<label>` with matching `for=` to the input's `id=`, AND no `aria-label` / `aria-labelledby` on the input | "Form input has no associated label." |
| `A11Y-005` | medium | template | `<div …>` or `<span …>` with `@click=` / `v-on:click=` and no `role=` attribute and no `@keydown` / `@keyup` / `@keypress` handler | "Clickable non-interactive element — add role=\"button\", tabindex=\"0\", and a keyboard handler, or use <button>." |
| `A11Y-006` | low | template | A `<th>` element inside a `<table>` without a `scope=` attribute, when the table has both header rows and data rows | "<th> missing scope attribute — assistive tech needs scope=\"col\" or scope=\"row\" to associate headers." |

## False-Positive Discipline

These heuristics are intentionally textual and will mis-fire occasionally. Two rules:

1. **Never edit the file based on a finding.** This skill reports only.
2. **If a check requires ambiguous semantic judgement** (e.g., is this list "long"?), include the finding but set severity one level lower than the table specifies. Better to over-report at low severity than to silently drop a real issue.

## Worked Example

For `client/src/components/Demo.vue`:

```vue
<template>
  <div v-for="(item, i) in items" :key="i">
    {{ formatCurrency(item.price) }}
  </div>
  <img src="/logo.png" />
  <button @click="save"></button>
</template>

<script>
import { ref, watch } from 'vue'
import { api } from '@/api'

export default {
  setup(props) {
    const { user } = props
    const items = ref([])
    const total = computed(() => items.value.reduce((s, i) => s + i.price, 0))
    total.value = 0
    watch(items, async () => { await api.search() })
    return { items, total }
  }
}
</script>
```

Expected report (abridged):

```json
{
  "schema_version": "1.0",
  "scanned_at": "2026-05-19T18:00:00Z",
  "target": "client/src/components/Demo.vue",
  "files_analyzed": 1,
  "summary": {
    "total_findings": 6,
    "by_severity": { "high": 3, "medium": 3, "low": 0 },
    "by_category": { "performance": 1, "reuse": 0, "reactivity": 3, "accessibility": 2 }
  },
  "findings": [
    {
      "id": "PERF-001", "category": "performance", "severity": "medium",
      "file": "client/src/components/Demo.vue", "line": 2,
      "snippet": "<div v-for=\"(item, i) in items\" :key=\"i\">",
      "issue": "v-for uses the array index as :key, which causes incorrect DOM reuse on reorder.",
      "why": "Vue keys identify which DOM node belongs to which item; using the index ties a node to a position, not an item, so state desyncs on reorder/insert.",
      "suggestion": "Use a stable unique identifier from the item.",
      "fix_example": ":key=\"item.id\""
    },
    {
      "id": "A11Y-001", "category": "accessibility", "severity": "medium",
      "file": "client/src/components/Demo.vue", "line": 6,
      "snippet": "<button @click=\"save\"></button>",
      "issue": "Button has no accessible name — add visible text, aria-label, or title.",
      "why": "Screen readers announce only the accessible name; an empty button is announced as \"button\" with no purpose.",
      "suggestion": "Add visible text or aria-label.",
      "fix_example": "<button @click=\"save\" aria-label=\"Save\">Save</button>"
    },
    {
      "id": "A11Y-002", "category": "accessibility", "severity": "medium",
      "file": "client/src/components/Demo.vue", "line": 5,
      "snippet": "<img src=\"/logo.png\" />",
      "issue": "Image is missing an alt attribute — provide alt text or alt=\"\" for decorative images.",
      "why": "Without alt, screen readers fall back to the file path.",
      "suggestion": "Add alt text describing the image, or alt=\"\" if purely decorative.",
      "fix_example": "<img src=\"/logo.png\" alt=\"Company logo\" />"
    },
    {
      "id": "REACT-001", "category": "reactivity", "severity": "high",
      "file": "client/src/components/Demo.vue", "line": 14,
      "snippet": "const { user } = props",
      "issue": "Destructuring props in setup() breaks reactivity — use toRefs(props) or access props.<name> directly.",
      "why": "Destructuring captures the current value; future prop updates won't propagate to the local binding.",
      "suggestion": "Replace with `const { user } = toRefs(props)` or read `props.user` lazily.",
      "fix_example": "const { user } = toRefs(props)"
    },
    {
      "id": "REACT-005", "category": "reactivity", "severity": "high",
      "file": "client/src/components/Demo.vue", "line": 17,
      "snippet": "total.value = 0",
      "issue": "Mutating a computed property — computed values are derived, not stored.",
      "why": "Computed values are read-only; assignment is a no-op (and a runtime warning in dev).",
      "suggestion": "Change the source ref (`items`) instead, or convert `total` to a `ref` if it really needs to be writable.",
      "fix_example": null
    },
    {
      "id": "PERF-006", "category": "performance", "severity": "medium",
      "file": "client/src/components/Demo.vue", "line": 18,
      "snippet": "watch(items, async () => { await api.search() })",
      "issue": "Watcher fires an API call without debouncing — rapid input changes will flood the network.",
      "why": "Each items mutation triggers an immediate request; bursts of changes cause request storms.",
      "suggestion": "Use `watchDebounced` from @vueuse/core, or guard with a manual timer.",
      "fix_example": "watchDebounced(items, async () => { await api.search() }, { debounce: 300 })"
    }
  ]
}
```

## Errors

If the path doesn't exist or contains no `.vue` files, return a report with `files_analyzed: 0` and a single finding:

```json
{
  "id": "INPUT-001", "category": "performance", "severity": "low",
  "file": "<the path>", "line": null,
  "snippet": "",
  "issue": "No .vue files found at the given path.",
  "why": "The skill needs a .vue file or a directory containing them.",
  "suggestion": "Pass a path like `client/src/views/` or a specific `.vue` file.",
  "fix_example": null
}
```

(The `category` here is a placeholder — `INPUT-001` is the only allowed id outside the four real categories.)

## Quick Reference

- **One argument required**: file path or directory path, relative to repo root.
- **Output**: single fenced ```json``` block as the final assistant message — nothing else.
- **No edits**: report only; user applies fixes themselves.
- **Verbatim messages**: use the `issue` wording from the tables above so diffs across runs stay clean.
- **Ordering**: findings sorted by `(file, line, id)`; cross-file findings last.
