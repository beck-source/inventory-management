---
name: vue-component-audit
description: Analyzes Vue 3 component structure and suggests performance and code-reuse optimizations. Use this skill when auditing components in client/src, when asked to review Vue performance, reactivity, or duplication, or before extracting a shared composable or component.
---

# Vue Component Audit

Analyze Vue 3 components in `client/src/` and report structural, performance, and reuse
problems with concrete fixes.

**This skill reports; it does not rewrite.** Produce findings, let the user choose what to
apply. When they approve a fix that touches a `.vue` file, delegate the edit to the
**vue-expert** subagent per the mandate in CLAUDE.md.

Distinct from the `/optimize` command, which sweeps the whole codebase for dead code and
edits in place. This skill is Vue-only, analysis-first, and focused on render cost and
duplication.

## Scope

| Path | What lives there |
|---|---|
| `client/src/views/*.vue` | Route-level views, one per tab |
| `client/src/components/*.vue` | Modals, filter bar, menus |
| `client/src/composables/*.js` | `useFilters`, `useI18n`, `useAuth` — singleton shared state |
| `client/src/api.js` | Every network call funnels through here |

This project uses the **Options API `setup()`** form (`export default { setup() {...} }`),
**not** `<script setup>`. Do not suggest converting files wholesale — it is a large diff
with no runtime benefit here. Match the surrounding style.

There is **no Pinia or Vuex**. Shared state is module-level `ref`s inside composables. Never
suggest adding a store library to solve a sharing problem a composable already solves.

`@vueuse/core` is **not** installed. Do not suggest `useDebounceFn`, `useLocalStorage`, or
any other VueUse helper unless the user agrees to add the dependency; hand-roll instead.

## Procedure

Run the detection passes below, then rank findings by **user-visible impact first**, not by
how easy they are to fix. Order the report:

1. **Correctness-affecting reactivity** — stale renders, list-identity bugs, missing cleanup
2. **Network waste** — un-debounced watchers, redundant fetches
3. **Render cost** — recomputation, unkeyed lists, layout thrash
4. **Reuse** — duplication worth extracting
5. **Structure** — file size, mixed concerns

Report every finding with: file:line, what happens today, why it matters, and the fix.
Never report a suspicion without opening the file to confirm it.

## Detection passes

### 1. Index keys in `v-for`

```bash
grep -rn ':key="idx\|:key="index\|:key="i"' --include='*.vue' client/src
```

An index key makes Vue reuse the wrong DOM node when the list reorders or an item is removed
— component state (open `<details>`, focus, input text) sticks to the wrong row. Use a stable
domain field: `sku`, `id`, `order_number`, `month`.

Listed as Common Issue #1 in CLAUDE.md. Currently present at
`views/Reports.vue:28,51,82` and `views/Orders.vue:112`.

**Not a finding** when the list is static and never reorders *and* rows hold no state — say
so rather than filing noise. `Orders.vue:112` is a real finding because those rows sit inside
an expandable `<details>`.

### 2. `v-for` keys spanning lines

```bash
grep -rn 'v-for' --include='*.vue' client/src | grep -v ':key'
```

**High false-positive rate.** Multi-line element openings put `:key` on the next line, so
this grep flags correct code. Always `sed -n 'N,N+4p'` the hit before reporting. Every
current hit in this repo (`Inventory.vue:53`, `Dashboard.vue:188,253`, `Spending.vue:148`,
`TasksModal.vue:73`, `LanguageSwitcher.vue:35`) is correctly keyed on the following line.

### 3. Watchers that fetch without debounce

```bash
grep -rn -B2 -A6 'watch(' --include='*.vue' client/src | grep -i 'load\|fetch\|api\.'
```

A `watch` on a continuous input (`type="range"`, `type="text"`) that calls the API fires once
per emitted value. A range slider emits at every step it crosses, so one drag across a
44-step track is 44 requests.

Fix: hold a timer module-side, `clearTimeout` then `setTimeout` in the watcher, and clear it
in `onUnmounted` so leaving the view mid-interaction cannot fire against a dead component.
Also gate any submit action while a fetch is pending, or the user can submit a plan the input
has already moved past.

`views/Restocking.vue:275-290` is the reference implementation (`BUDGET_DEBOUNCE_MS`,
`planPending`).

**Not a finding** when the watcher only recomputes locally. `Inventory.vue:108-137` filters
32 in-memory rows through a `computed` on `searchQuery` with no network call — debouncing it
would add latency for nothing. Distinguish *network-triggering* from *local* reactivity
before filing.

Watchers on the four global filters (`selectedPeriod`, `selectedLocation`,
`selectedCategory`, `selectedStatus`) are also **not** findings — those are discrete
`<select>` changes, one event per user action.

### 4. Composables called outside `setup()`

```bash
grep -rn -A4 'const formatDate\|const format' --include='*.vue' client/src | grep 'useI18n()\|useFilters()\|useAuth()'
```

Calling a composable inside a helper function re-runs its setup on every invocation. For a
formatter called once per table cell, that is hundreds of calls per render. It also detaches
the returned refs from the component's reactive scope, so the function reads a fresh instance
rather than the one the template tracks.

Fix: destructure once at the top of `setup()` and close over the result.

Present at `views/Orders.vue:215` and `views/Dashboard.vue:637` — both call
`useI18n()` inside `formatDate`, which every date cell invokes.

### 5. Duplicated logic worth extracting

```bash
# same currency-symbol computed in 6 files
grep -rln "currentCurrency.value === 'JPY'" --include='*.vue' client/src
# same date formatter in 6 files
grep -rln 'const formatDate' --include='*.vue' client/src
```

Two clusters exist today, each duplicated across six files:

- **`currencySymbol`** — identical `currentCurrency.value === 'JPY' ? '¥' : '$'` computed in
  `Orders.vue`, `Inventory.vue`, `Spending.vue`, `CostDetailModal.vue`,
  `ProductDetailModal.vue`, `InventoryDetailModal.vue`
- **`formatDate`** — locale-mapped `toLocaleDateString` in `Orders.vue`, `Dashboard.vue`,
  `Spending.vue`, `BacklogDetailModal.vue`, `ProductDetailModal.vue`,
  `ProfileDetailsModal.vue`

Both belong in `composables/useI18n.js`, which already owns locale and currency. Extracting
them also fixes pass 4 at the same time.

Apply a **three-strike rule**: two copies is acceptable, three or more justifies extraction.
Do not propose extracting something used twice — the indirection costs more than it saves.

### 6. Uncleaned timers and listeners

```bash
grep -rn 'setTimeout\|setInterval\|addEventListener' --include='*.vue' client/src
grep -rn 'onUnmounted\|clearTimeout\|removeEventListener' --include='*.vue' client/src
```

Every timer or listener created in `setup`/`onMounted` needs teardown in `onUnmounted`, or it
fires against an unmounted component.

Judge by consequence, not by rule. `ProfileMenu.vue:97` and `LanguageSwitcher.vue:80` both
set an uncleaned 200ms blur timer, but the callback only sets a local ref on a component that
is about to be discarded — a note, not a defect. An uncleaned *fetch* timer is a real bug.
Say which kind you found.

### 7. Recomputation and chained computeds

```bash
# Leading line count so a plain numeric sort works - keying on a "lines:N" field
# fails, because sort -n reads the non-numeric prefix as 0 and every row ties.
for f in client/src/views/*.vue client/src/components/*.vue; do
  printf "%5s lines  computed:%-3s watch:%-3s %s\n" \
    "$(wc -l < $f | tr -d ' ')" \
    "$(grep -c 'computed(' $f)" "$(grep -c 'watch(' $f)" "$f"
done | sort -rn
```

Computeds cache on their dependencies, so a chain is usually fine — flag it only when a link
in the chain does real work (a full re-sort, a nested loop over all 250 orders) and an
upstream ref changes often.

`views/Spending.vue` holds 13 computeds in 852 lines and `views/Dashboard.vue` holds 11 in
1271 — both are worth reading for chains that re-derive the same intermediate more than once.

Also check for work done in the template that belongs in a computed: `.filter().map()`,
`.toLocaleString()` on a large list, or object literals in `:style` (16 occurrences
currently) all re-evaluate on every render.

### 8. File size and mixed concerns

Flag a view over ~600 lines only when it holds separable concerns. For each oversized file,
name the specific extraction — "the SVG chart block in `Dashboard.vue` becomes
`<RevenueChart>`" — never just "consider splitting this file".

`Dashboard.vue` (1271), `Spending.vue` (852), and `TasksModal.vue` (621) exceed the
threshold. All charts here are hand-written SVG with no charting library, which is the usual
reason these files are long.

## Report format

```markdown
## Vue Component Audit — <scope>

### Reactivity correctness
1. **views/Reports.vue:28** — `:key="index"` on `quarterlyData`
   Today: DOM nodes reused by position, so a reorder attaches state to the wrong row.
   Fix: `:key="q.quarter"`.

### Network waste
...

### Reuse
1. **`currencySymbol` duplicated in 6 files** — Orders, Inventory, Spending + 3 modals
   Fix: move to `composables/useI18n.js`, which already owns currency.
   Touches 6 files; behavior identical.

### Checked and clean
- No `v-if` on the same element as `v-for`
- No `addEventListener` anywhere, so no listener leaks
- `Inventory.vue` search is local-only; debounce not needed
```

Always include a **"Checked and clean"** section. It tells the user what the audit covered,
so a short report reads as thorough rather than lazy.

## Rules

1. **Confirm before reporting.** Open every grep hit. Passes 2 and 6 are noisy by design.
2. **Name the consequence.** "Wrong row keeps its open dropdown on reorder" beats "anti-pattern".
3. **Suggest nothing that needs a new dependency** without flagging the dependency.
4. **Respect the local idiom** — `setup()` not `<script setup>`, composables not stores.
5. **Do not touch `.vue` files yourself.** Delegate approved edits to **vue-expert**.
6. **Quantify where you can.** "44 requests per drag" and "6 duplicate copies" are actionable;
   "may impact performance" is not.
7. **Say when something is fine.** A pattern that looks wrong but is correct in context is a
   finding worth reporting as clean, with the reason.

## Verification after any applied fix

```bash
cd client && npm run build          # must stay clean
python3 -m pytest tests/backend/ -q # 68 passing; catches API-shape breaks
```

Then exercise the changed view with Playwright MCP against `http://localhost:3000` per
CLAUDE.md. For a key change, specifically reorder or filter the list and confirm row state
follows the right row.
