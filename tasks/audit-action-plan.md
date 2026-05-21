# Inventory Management — Consolidated Audit Action Plan

**Consolidated by:** team-lead (inventory-audit team)
**Auditors:** security-auditor · perf-analyst · ux-reviewer
**Inputs:** [`security-findings.md`](./security-findings.md) (9 items) · [`performance-findings.md`](./performance-findings.md) (15 items) · [`ux-findings.md`](./ux-findings.md) (15 items)
**Posture context:** Workshop / demo app. No real auth, no DB, Sia-branded UI, English + Japanese locales, localhost-only. Action plan prioritises items that (a) bite *today* in the demo and (b) the kind of issues that would block "promote to real product" later.

---

## Cross-review — severity adjustments after peer challenge

| Finding | Original severity | Adjusted | Reason |
|---|---|---|---|
| **`PurchaseOrderModal` missing import + dead `/api/tasks` calls** (UX #13 ⨯ Sec #8 ⨯ Perf P-14) | UX Medium, Sec Low, Perf Medium | **High** | Three angles converge — silent broken UI on Dashboard, 404 storm in console, and a security-adjacent gap when those endpoints are eventually written. Combined visibility justifies High. |
| **`console.log` in Reports.vue hot paths** (Perf P-02 High, Sec #7 Low) | Split | **High** | Perf's rationale wins: 50-200ms render jank with DevTools open + dataset-shape leakage = High. |
| **FilterBar overflow at 375 px** (UX #5 High) | High | **High (confirmed)** | ux-reviewer correctly anticipated the challenge. App is Sia-branded and client-facing-adjacent; mobile is in scope. |
| **Untranslated nav labels / new views** (UX #2 + #6 High) | High | **High (confirmed)** | Japanese build is the only shipped second locale; mid-list English break is a release-blocker for that locale. |
| **Reports.vue `:key="index"`** (Perf P-03 Medium, UX #14 Low) | Split | **Medium** | Perf wins — Reports re-renders on every filter change, so the keyed-diff cost is real even though the user-visible bug is latent. |
| **CORS `*` + `allow_credentials=True`** (Sec #1 latent High / current Medium) | Latent High | **Medium** for action ranking | 5-line fix; latent risk vanishes the moment real auth lands. Cheap insurance. |
| **Modal a11y (no Escape / focus trap / ARIA)** (UX #1 High) | High | **High (confirmed)** | No destructive flows behind them, but the redesign explicitly targets a SaaS-grade aesthetic — modal a11y is table stakes for that posture. |
| **`isAuthenticated = ref(true)`** (Sec #4 Low) | Low | **Low (confirmed)** | UX peer agreed; merge with the dead-flow cleanup in item #1 below. |

No items were *lowered* by peer challenge. Two were raised (PurchaseOrderModal package, console.log) because the cross-cutting impact only becomes visible when you read the three reports together.

---

## Ranked action plan (severity × user-visible impact ÷ effort)

### Tier 1 — Ship-blockers for the redesigned demo (do this week)

#### 1. Fix the "silently broken" trio: `PurchaseOrderModal` import + dead `/api/tasks` + dead `/api/purchase-orders*` 🟥 High · Effort: S
**Files:** `client/src/views/Dashboard.vue:289-295`, `client/src/App.vue:131-137,149`, `client/src/api.js:84-112`
**Sketch:** Either restore `PurchaseOrderModal.vue` and import it, or delete the `<PurchaseOrderModal>` block and its state (`showPOModal`, `selectedBacklogForPO`, `poModalMode`, `handlePOCreated`). Strip the dead `getTasks/createTask/deleteTask/toggleTask/createPurchaseOrder/getPurchaseOrderByBacklogItem` API methods and the `loadTasks()` call in `App.vue`. Silences the 404 storm + the `[Vue warn]: Failed to resolve component: PurchaseOrderModal` on every Dashboard load.
**Owner discipline:** frontend (any). Cross-references: Sec #8, Perf P-14, UX #13.

#### 2. Modal a11y composable — Escape / focus-trap / focus-restore / ARIA, applied to all 6 modals 🟥 High · Effort: M
**Files:** `client/src/components/{Inventory,Product,Backlog,Cost,ProfileDetails,Tasks}DetailModal.vue` (+ rename non-detail) — and any future `PurchaseOrderModal.vue`
**Sketch:** Write `composables/useModal.js` that, on open: stores `document.activeElement`, focuses the close button, traps Tab inside the modal container, listens for `@keydown.esc`. On close: restores focus to the saved element. Add `role="dialog"`, `aria-modal="true"`, `aria-labelledby` to each modal root. ~1 composable + 6 small component edits.
**Owner:** frontend (a11y-sensitive). Cross-ref: UX #1.

#### 3. Refactor Reports.vue: strip console.log, convert to Composition API + computed, replace handwritten `formatNumber` 🟥 High · Effort: M
**Files:** `client/src/views/Reports.vue` (single file, full rewrite of `<script>` block)
**Sketch:** Migrate to `<script setup>`, hoist `maxRevenue`/`growthRate`/`fulfillmentClass` etc. into `computed`. Delete every `console.log` (lines 145-256). Replace `formatNumber` with `value.toLocaleString('en-US', { ... })`. Fix `:key="index"` on lines 28/51/82 (use `q.quarter`, `month.month`). Add empty states for quarterly/monthly tables.
**Owner:** frontend (Vue). Cross-ref: Perf P-01, P-02, P-03, P-13, Sec #7, UX #14.

#### 4. Responsive: FilterBar + top bar wrap below 768 px 🟥 High · Effort: S
**Files:** `client/src/components/FilterBar.vue` (styles), `client/src/App.vue` (top-bar `<header>` row)
**Sketch:** Add `flex-wrap: wrap` on `.filters-grid` and on the top-bar inner div. Below 640 px: stack filter groups vertically, set `.filter-select { min-width: 0; flex: 1 1 auto; }`. Header: at narrow widths, hide the search input on `< md` (`hidden md:flex` already in place — verify), and collapse `LanguageSwitcher` to flag-only.
**Owner:** frontend. Cross-ref: UX #5.

#### 5. Wire i18n through the redesign — sidebar "Restocking" / "Reports" / "Collapse", search placeholder, ARIA labels, Restocking.vue + Reports.vue 🟥 High · Effort: M-L
**Files:** `client/src/locales/{en,ja}.js`, `client/src/components/SidebarNav.vue:71,74,46`, `client/src/App.vue:11,21,32`, `client/src/views/Restocking.vue` (full pass), `client/src/views/Reports.vue` (full pass)
**Sketch:** Add `nav.restocking`, `nav.reports`, `nav.collapse`, `search.placeholder`, `aria.toggleSidebar`, `aria.notifications`, plus `restocking.*` and `reports.*` namespaces. Replace literal `$` with `currencySymbol` from `useI18n` (pattern already in Inventory/Orders).
**Owner:** frontend + locale reviewer. Cross-ref: UX #2, UX #6.

### Tier 2 — Cheap insurance (do next sprint)

#### 6. CORS tighten — explicit origin list OR `allow_credentials=False` 🟧 Medium (latent High) · Effort: XS
**Files:** `server/main.py:51-57`
**Sketch:** Replace `allow_origins=["*"]` with `["http://localhost:3000","http://localhost:3001","http://localhost:3002"]`, OR set `allow_credentials=False`. 5-line change; eliminates a latent High before real auth ships.
**Cross-ref:** Sec #1.

#### 7. Pydantic constraints on POST models 🟧 Medium · Effort: S
**Files:** `server/main.py:99-143` (`RestockOrderItemPayload`, `RestockOrderPayload`, `CreatePurchaseOrderRequest`)
**Sketch:** Add `Field(ge=…, le=…, min_length=…, max_length=…)` to each. Bound list sizes (`max_length=500` on `items`). Prevents the memory-DoS vector and downstream float overflow.
**Cross-ref:** Sec #2.

#### 8. Dashboard `topProducts`: build SKU → inventory `Map` once 🟧 Medium · Effort: XS
**Files:** `client/src/views/Dashboard.vue:489-546`
**Sketch:** `const invBySku = new Map(inventoryItems.value.map(i => [i.sku, i]))` inside the computed, then `invBySku.get(sku)` instead of `.find()`. One-line fix; cuts a future 200-500ms freeze.
**Cross-ref:** Perf P-05.

#### 9. Strip `console.log` in production build 🟧 Medium · Effort: XS
**Files:** `client/vite.config.js`
**Sketch:** Add `esbuild: { drop: ['console', 'debugger'] }` to the prod config. Defence-in-depth for finding #3 + any other forgotten console.log.
**Cross-ref:** Sec #7, Perf P-02.

#### 10. Add `aria-current="page"` to sidebar links 🟧 Medium · Effort: XS
**Files:** `client/src/components/SidebarNav.vue:21-36`
**Sketch:** `:aria-current="isActive(item.path) ? 'page' : undefined"` on the `router-link`. Free a11y win.
**Cross-ref:** UX #3.

#### 11. Empty-state branches on Inventory / Orders / Demand 🟧 Medium · Effort: S
**Files:** `client/src/views/Inventory.vue:36-74`, `client/src/views/Orders.vue:80-120`, `client/src/views/Demand.vue:11-30`
**Sketch:** `v-if="!filteredItems.length"` → friendly empty card with "Reset filters" CTA. Reuse `t('common.noData')` + per-view subtitle key.
**Cross-ref:** UX #7.

### Tier 3 — Long-tail / next refactor pass

| # | Item | Severity | Effort | Cross-ref |
|---|---|---|---|---|
| 12 | Pagination on `/api/orders` + `/api/transactions`; consider folding `dashboard/summary` into it | Medium | M | Perf P-08, P-09 |
| 13 | ProfileMenu + LanguageSwitcher: replace `@blur+setTimeout` with click-outside listener + ARIA menu pattern | Medium | M | UX #9 |
| 14 | Lazy-load route components (`Reports`, `Spending`, `Restocking`) | Medium | XS | Perf P-11 |
| 15 | Debounce Inventory search (`watchDebounced`, 250ms) | Medium | XS | Perf P-04 |
| 16 | Bell icon: remove or mark `aria-disabled` until notifications ship | Medium | XS | UX #8 |
| 17 | TasksModal: confirm before overlay-click discards unsaved form | Medium | S | UX #10 |
| 18 | FilterBar `<label for>` ↔ `<select id>` association | Low | XS | UX #11 |
| 19 | Sia-blue `#00B6F0` body text → swap to `#0085B2` for non-large text | Medium | XS | UX #4 |
| 20 | Rename `useAuth.isAuthenticated` → `isAuthenticatedMock` + comment | Low | XS | Sec #4 |
| 21 | Global FastAPI exception handler (no traceback / no path leakage) | Low | XS | Sec #5 |
| 22 | Backlog endpoint: pre-bucket purchase-order ids (O(n+m)) | Medium (latent) | XS | Perf P-06 |
| 23 | Stop committing `uv.lock` and `package-lock.json` gitignore — commit them | Informational | XS | Sec #9 |
| 24 | Aria-labels on every modal close button; mark `×` `aria-hidden` | Low | S | UX #12 |
| 25 | Focus first sidebar link when narrow-viewport toggle opens it | Low | XS | UX #15 |

---

## Recommended sprint slicing

- **Sprint 1 (1 week):** Items **#1, #2, #3, #4, #5** (Tier 1) + **#6, #9, #10** (cheap Tier 2). Visible polish + a11y baseline + the latent CORS fix.
- **Sprint 2 (1 week):** Items **#7, #8, #11, #13, #14, #15** + the remaining "XS" Tier-3 items (#16, #18, #19, #20, #21, #22, #25).
- **Sprint 3 (longer):** Pagination + dashboard refactor (#12), TasksModal confirm flow (#17), aria-labels pass (#24).

## Items each auditor argued *should not* be on the must-fix list

- security-auditor — **#23** (lock files): worth doing but not security-blocking; defer is fine.
- perf-analyst — **P-10** (sync I/O at startup): no real impact at demo scale; recorded for the eventual real-DB migration only.
- ux-reviewer — **#15** (mobile keyboard toggle focus): only fires on a narrow edge case (tablet + Bluetooth keyboard); easy fix, but no user has hit it yet.

## Items each auditor flagged as *negative findings* (worth recording)

- Path traversal — **none** (security-auditor verified `open()` / `FileResponse` / `StaticFiles` usage; only hardcoded JSON paths exist).
- Lucide tree-shaking — **clean** (perf-analyst verified named imports across `App.vue` and `SidebarNav.vue`).
- `.badge.info` (`#0a3a5e` on `#DEECFC`) — **passes WCAG AA at ~8 : 1** (ux-reviewer).

---

## What changed today vs. what was pre-existing

The Sia-Partners redesign that landed earlier today **introduced** the bulk of Tier 1: untranslated sidebar labels (#5), missing ARIA on the new search/bell buttons (#5, item flagged in #1), the `#00B6F0` contrast risk (Tier-3 #19), the responsive overflow at narrow widths (#4). The redesign **did not introduce** the modal a11y gap (#2), the Reports.vue mess (#3), the missing `PurchaseOrderModal` import (#1), the CORS misconfig (#6), or the dead `/api/tasks` calls (#1) — those were pre-existing and just became more visible against a more polished shell.

Action: ship the Tier-1 bundle and re-screenshot — the redesign will look complete instead of "polished but with rough corners".
