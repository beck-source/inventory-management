# Performance Audit Findings — inventory-management

**Auditor:** perf-analyst
**Scope:** server/main.py + client/src
**Dataset baseline:** 250 orders, 32 inventory items, 56 transactions, ~158KB orders.json. Findings scale linearly — re-rate severity at production volume (~10K orders).

Severity scale: Critical / High / Medium / Low. "Impact" is ballpark for the demo dataset unless noted.

---

## P-01 — Reports.vue is built almost entirely from render-time methods (no computed)
**Severity:** High
**File:** `client/src/views/Reports.vue:130-316`
**Description:** Reports.vue is the only Options-API component in the app. Every helper (`formatNumber`, `formatMonth`, `getBarHeight`, `getFulfillmentClass`, `getChangeValue`, `getChangeClass`, `getGrowthRate`) is a method, so Vue re-invokes them on every reactive tick — there is no caching. `getBarHeight` (line 255) is the worst: for each of the ~12 bars it walks the full `monthlyData` array to recompute `maxRevenue`, making chart render O(n²). Two `<tbody>` loops (lines 28, 82) plus `getChangeValue`/`getChangeClass`/`getGrowthRate` inside the M-o-M table call `formatNumber` per cell on every render.
**Recommended fix:** Convert to Composition API or wrap derived data in `computed()`. Hoist `maxRevenue` to a single computed. Replace handwritten `formatNumber` (lines 214-240) with `value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })`.
**Impact:** ~12 bars × O(n) per row = 144 ops per chart render today; with 60 months / 12 quarters this stays cheap, but every parent re-render (filter change, route flicker) re-runs the lot. More importantly, this is the only file that needs a refactor to bring perf hygiene to parity with the rest of the codebase.

## P-02 — `console.log` left in Reports.vue hot paths
**Severity:** High
**File:** `client/src/views/Reports.vue:215, 243, 256` (also `loadData` at 150/155/161/167/169/172/176)
**Description:** `formatNumber`, `formatMonth`, and `getBarHeight` each begin with `console.log(...)`. These are called from `v-for` rows and chart bars, so opening the Reports tab spams DevTools with hundreds of log lines per render. Console writes are non-trivial — each call serialises arguments and triggers DevTools UI work. With DevTools open, this can add 50-200ms per render in Chrome on a mid-range laptop.
**Recommended fix:** Delete every `console.log` in this file. They are debug residue.
**Impact:** Removes a measurable jank source whenever the user has DevTools open; trivial fix.

## P-03 — `:key="index"` violates the documented codebase rule on three v-for loops
**Severity:** Medium
**Files:**
- `client/src/views/Reports.vue:28` (quarterlyData rows)
- `client/src/views/Reports.vue:51` (monthly bar chart)
- `client/src/views/Reports.vue:82` (M-o-M table)
- `client/src/views/Orders.vue:58` and `client/src/views/Orders.vue:102` (`v-for="(item, idx) in order.items" :key="idx"`)
**Description:** Repo `CLAUDE.md` gotcha #1 explicitly bans index keys; `LEARNINGS.md` shows it has burned the team before. Beyond correctness, index keys defeat Vue's keyed diff so the entire subtree is patched on every reorder — measurable when orders are re-sorted by date in `Orders.vue:160` after each filter change.
**Recommended fix:** Reports.vue → use `q.quarter` / `month.month`. Orders.vue inner loop → composite `${order.id}-${item.sku}` since items have no id.
**Impact:** Eliminates a class of DOM-reuse bugs; modest render-cost win on sorted lists (Orders re-sorts every filter change, line 160).

## P-04 — Inventory search is undebounced and re-sorts the full list on every keystroke
**Severity:** Medium
**File:** `client/src/views/Inventory.vue:132-150` + template `v-model="searchQuery"` line 19
**Description:** `filteredItems` is a computed driven by `searchQuery`. Every keystroke triggers a filter pass and a full sort (`.slice().sort(...)`) over `items.value`. Vue batches into next tick, but each tick still does `O(n log n)` work plus a full table re-render. At 32 rows this is invisible; at the documented "<10K items" ceiling in `server/CLAUDE.md` it becomes 100-300ms per keystroke.
**Recommended fix:** Either (a) debounce `searchQuery` with `watchDebounced` from @vueuse/core (already mentioned in `client/CLAUDE.md`), or (b) cheaper: pre-sort `items.value` once in `loadInventory`, since the sort key (`STATUS_ORDER`) doesn't depend on the search.
**Impact:** Linear in dataset size. +150ms per keystroke at 10K rows.

## P-05 — Dashboard `topProducts` does O(orders × items × inventory) lookup
**Severity:** Medium
**File:** `client/src/views/Dashboard.vue:489-546`
**Description:** For each order, for each line item, it calls `inventoryItems.value.find(i => i.sku === sku)` (line 501) — linear scan of inventory. With 250 orders averaging ~3 items × 32 inventory = ~24K comparisons; at 10K orders × 5 items × 1K inventory = 50M comparisons per filter change.
**Recommended fix:** Build a `Map` once at the top of the computed: `const invBySku = new Map(inventoryItems.value.map(i => [i.sku, i]))`, then `invBySku.get(sku)`.
**Impact:** Today: ~2-5ms per filter change. Production-shaped: 200-500ms freeze per filter toggle.

## P-06 — Backend `/api/backlog` is O(backlog × purchase_orders) on every request
**Severity:** Medium
**File:** `server/main.py:244-255`
**Description:** For each backlog item, `any(po["backlog_item_id"] == item["id"] for po in purchase_orders)` walks the full `purchase_orders` list. Today `purchase_orders.json` is literally `[]` (4 bytes), so the impact is zero. The pattern is the bug: as soon as POs are populated this becomes O(n×m).
**Recommended fix:** Pre-bucket once per request: `po_ids = {po["backlog_item_id"] for po in purchase_orders}`, then `has_po = item["id"] in po_ids`. O(n+m).
**Impact:** Latent; bites hard once `purchase_orders.json` has data (it's referenced by the Backlog modal flow).

## P-07 — `apply_filters` chains build N intermediate lists per request
**Severity:** Low
**File:** `server/main.py:34-48`
**Description:** Sequential list-comprehensions — each filter step allocates a new list and walks the previous one. For `/api/orders` with 4 filters, that's up to 4 full passes and 4 list allocations over `orders` (250 items today, but recall `mutations don't persist` so it grows during a session). Functionally correct; the constant factor matters only at 10K+ items.
**Recommended fix:** Single-pass filter: combine predicates inside one comprehension. Pre-build lower-cased indexes (`{cat.lower(): [...]}`) at module import for the static filter dimensions if the dataset grows.
**Impact:** Today: sub-ms per request. At 10K orders × 4 filters: ~5-15ms saved.

## P-08 — `/api/orders` returns the full list with no pagination
**Severity:** Medium
**Files:** `server/main.py:166-176` (orders), `server/main.py:300-303` (transactions), `server/main.py:150-156` (inventory)
**Description:** No `limit`/`offset`/`cursor`. `orders.json` is 158KB on disk and the API response is similar — every Dashboard mount, every filter change, every Orders/Spending view fetches the whole list. Dashboard fires `getOrders` + `getInventory` + `getBacklog` + `getDashboardSummary` in parallel (`Dashboard.vue:566-571`), so a single filter toggle re-downloads ~200KB of JSON.
**Recommended fix:** Add `limit` (default 100) + `offset` query params; the dashboard's "Top 12 products" and summary cards don't need the full list — make a dedicated `/api/orders/summary` endpoint that returns the aggregated counts/totals server-side.
**Impact:** +20-80ms per filter change on localhost (JSON parse + axios overhead); much higher on a real network.

## P-09 — `/api/dashboard/summary` ignores its own cached work and recomputes from filtered lists
**Severity:** Low
**File:** `server/main.py:257-283`
**Description:** Re-applies the same filter pipeline that `/api/orders` and `/api/inventory` already run server-side. Acceptable because the frontend currently fires both endpoints in parallel anyway, but the duplication means filter changes do 3× the filter work backend-side per Dashboard refresh.
**Recommended fix:** Either drop `/api/dashboard/summary` and aggregate client-side from already-fetched data, or have it be the only call and return inventory/orders lists with it.
**Impact:** ~3× redundant filter passes per dashboard load.

## P-10 — Sync I/O at startup loads all JSON files synchronously
**Severity:** Low
**File:** `server/mock_data.py:14-36`
**Description:** `load_json_file` uses blocking `open()` + `json.load()` at module import. Eight files, ~190KB total — cold-start cost is ~5-10ms total on SSD. Not a problem at this scale.
**Recommended fix:** None worth doing for the demo. If migrated to real DB, use async drivers. Flagged only because the prompt asked.
**Impact:** Negligible (<10ms cold start).

## P-11 — No code-splitting; every route's view is eagerly imported
**Severity:** Medium
**File:** `client/src/main.js:4-23`
**Description:** All seven views (`Dashboard`, `Inventory`, `Orders`, `Restocking`, `Demand`, `Spending`, `Reports`) are statically imported at app bootstrap. The user pays the JS parse cost for views they may never visit. With Vite the prod build will inline them all into the main chunk.
**Recommended fix:** Lazy routes: `{ path: '/reports', component: () => import('./views/Reports.vue') }`. Spending and Reports are the heaviest views (chart logic + long templates) and the least visited from a typical workflow.
**Impact:** Estimated ~20-40% reduction in initial JS bundle. First-paint win on slow connections.

## P-12 — Lucide icons: `App.vue` registers icons via `components: { Menu, Bell, Search }` (works, but namespace risk)
**Severity:** Low
**Files:** `client/src/App.vue:71`, `client/src/components/SidebarNav.vue:55-58`
**Description:** Imports are named (`import { Menu } from 'lucide-vue-next'`) — that's correct for tree-shaking, no namespace import. Verified across the codebase. No action needed; logged as confirmed-clean.
**Recommended fix:** None.
**Impact:** N/A — confirmation finding.

## P-13 — Reports.vue handwritten `formatNumber` allocates per character
**Severity:** Low
**File:** `client/src/views/Reports.vue:214-240`
**Description:** Loops char-by-char building a comma-separated string with string concatenation (line 224-230 prepends to `formatted` on each digit — quadratic on string length in some engines). Called from at least 8 template positions per row × 12 rows = ~96 calls per render.
**Recommended fix:** `value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })` — one line, faster, locale-aware. Already done in `Inventory.vue:64`.
**Impact:** Minor on its own; compounds with P-01 and P-02 to make Reports.vue the slowest tab.

## P-14 — `App.vue` calls `api.getTasks()` against a non-existent endpoint on every mount
**Severity:** Medium
**Files:** `client/src/App.vue:131-137`, `client/src/api.js:84-102`
**Description:** `loadTasks()` hits `GET /api/tasks` on every page load. That route doesn't exist in `server/main.py` (no `/api/tasks` handler). FastAPI returns 404, axios throws, the error is caught and `console.error`'d. The user always pays the round-trip cost plus a noisy console error on every navigation that remounts App.vue. Same for `api.createTask`, `api.deleteTask`, `api.toggleTask`, `api.createPurchaseOrder`, `api.getPurchaseOrderByBacklogItem` — all reference endpoints that don't exist.
**Recommended fix:** Either implement the endpoints or remove the dead API methods + the `loadTasks()` call from App.vue's `onMounted`.
**Impact:** ~50-100ms wasted on every cold load + ongoing 404 spam. This is correctness-adjacent — confirm with team-lead whether it's a perf finding or a security/UX finding.

## P-15 — Sorting inside `loadOrders` mutates and re-sorts the API response every filter change
**Severity:** Low
**File:** `client/src/views/Orders.vue:160-164`
**Description:** Backend returns orders in insertion order; frontend re-sorts on every filter change. Combined with the index-key issue in P-03, every refilter causes Vue to patch every row.
**Recommended fix:** Sort server-side (or once on mount), and use the stable `order.id` key.
**Impact:** Compounds P-03.

---

## Summary — top 3 must-fix
1. **P-01 + P-02 + P-13** (Reports.vue refactor): combine these — converting Reports.vue to Composition API + computed properties + removing console.log + replacing handwritten formatter fixes the slowest tab in the app in one PR.
2. **P-05** (Dashboard.vue `topProducts` map lookup): one-line fix, prevents the 200-500ms freeze at production scale.
3. **P-08** (orders/transactions pagination): the only finding here that becomes user-visible at modest dataset growth. Pair with P-09 to halve dashboard load work.

P-14 (dead /api/tasks call) is a tie for #3 if treated as "fix the 404 storm" — coordinating with security-auditor on whether they're also flagging it.
