# UX Audit Findings — inventory-management

Reviewer: ux-reviewer (inventory-audit team)
Date: 2026-05-21
Scope: `client/src/**` — sidebar/shell redesign (App.vue, SidebarNav.vue) + all views, modals, FilterBar, ProfileMenu, LanguageSwitcher, locales. Live sanity check on `http://localhost:3001` at 375 px viewport.

**Context:** Brand-new Sia-Partners SaaS redesign shipped today. Existing FilterBar / modals / views were preserved but the shell is fresh. Findings focus on what the redesign introduced (or surfaced) plus a few latent issues the redesign now makes more visible. Calibrated against `CLAUDE.md` and `LEARNINGS.md` already shipped with the repo.

---

## 1. Modals have no Escape-to-close, no focus trap, no focus restore, no ARIA dialog role

- **Severity:** High
- **Location:** `client/src/components/InventoryDetailModal.vue`, `ProductDetailModal.vue`, `BacklogDetailModal.vue`, `CostDetailModal.vue`, `ProfileDetailsModal.vue`, `TasksModal.vue` (all six follow the same pattern; verified by grepping for `Escape|keydown|role=.dialog|aria-modal|focus\(\)` across `components/` — zero matches)
- **Description:** Every modal renders inside a `<Teleport to="body">` with an overlay-click handler, but: (a) pressing **Escape** does nothing — keyboard users can't dismiss the dialog; (b) Tab cycles **out of the modal into the backdrop page** because there is no focus trap; (c) when the modal closes, focus is **not restored** to the row/button that opened it — screen readers and keyboard users lose their place; (d) the container has no `role="dialog"`, `aria-modal="true"`, or `aria-labelledby` pointing at `.modal-title`, so assistive tech doesn't announce it as a dialog at all.
- **Recommended fix:** Add `@keydown.esc="close"` on the overlay (or a window listener), `role="dialog"`, `aria-modal="true"`, `aria-labelledby="modal-title-<id>"`, `tabindex="-1"` + auto-focus the close button on open, save `document.activeElement` on open and `.focus()` it on close. A small `useModal()` composable can encapsulate all six.

## 2. Sidebar nav uses hardcoded English for "Restocking" and "Reports"; "Collapse" footer also untranslated; search placeholder hardcoded; bell button label is English-only

- **Severity:** High
- **Location:** `client/src/components/SidebarNav.vue:71` (`label: 'Restocking'`), `:74` (`label: 'Reports'`), `:46` (`Collapse`); `client/src/App.vue:21` (`placeholder="Search inventory, orders…"`), `:11` (`aria-label="Toggle sidebar"`), `:32` (`aria-label="Notifications"`). Confirmed: `locales/en.js` and `locales/ja.js` contain no `nav.restocking`, `nav.reports`, `nav.collapse`, `search.placeholder`. Japanese users see Japanese for Inventory/Orders/Finance but English for two of seven sidebar items — a jarring mid-list language switch.
- **Recommended fix:** Add `nav.restocking`, `nav.reports`, `nav.collapse`, `search.placeholder`, `aria.toggleSidebar`, `aria.notifications` to both `en.js` and `ja.js`. Wire all six through `t()`. (Same review: `Restocking.vue` and `Reports.vue` views are 100% English — see finding #6.)

## 3. Sidebar nav links are missing `aria-current="page"` for the active route

- **Severity:** Medium
- **Location:** `client/src/components/SidebarNav.vue:21-36`
- **Description:** The active route is conveyed only visually — a 2-px blue bar on the left and a slightly lighter background via `active-class="!text-white !bg-white/10"`. Screen-reader users have no way to know which page they are on. `router-link` exposes `aria-current="page"` by default *only* when the matched route equals exactly the link's `to`, and visually the redesign relies on the custom `isActive(path)` (which uses `startsWith`) — so the visual indicator and the implicit `aria-current` can disagree on nested routes.
- **Recommended fix:** Bind `:aria-current="isActive(item.path) ? 'page' : undefined"` on the `router-link`. Free fix, no visual change.

## 4. Sia-blue `#00B6F0` body text and the new soft-blue `info` badge fail WCAG AA contrast

- **Severity:** Medium
- **Location:** `client/src/App.vue:291` (`.stat-card.info .stat-value { color: #00B6F0; }`), `:361` (`.badge.info { background: #DEECFC; color: #0a3a5e; }` — this one is fine), and any place `text-sia-blue` is applied to body text. Active-tab indicator at `SidebarNav.vue:32` uses the same blue on navy — that one passes (large-area + dark bg).
- **Description:** `#00B6F0` on white = **2.78 : 1** contrast ratio. WCAG AA requires **4.5 : 1** for normal text and **3 : 1** for large text (≥18 pt / 24 px, or ≥14 pt / 18.66 px bold). The `.stat-value` is 2 rem = 32 px and bold, so it just barely qualifies as large text and squeaks past 3 : 1 — but the same color is used in `info` accent text elsewhere in the redesign that is *not* large. Anyone color-tuning the brand later by darkening the blue saves work by fixing it now.
- **Recommended fix:** Use `#00B6F0` only for large/bold elements and on dark backgrounds. For body/small text, swap to a darker brand variant (e.g., `#0085B2` = 4.6 : 1 on white). The `.badge.info` combination (`#0a3a5e` on `#DEECFC`) measures ~8 : 1 and is fine — keep it.

## 5. Filter bar overflows horizontally at 375 px — no responsive collapse

- **Severity:** High
- **Location:** `client/src/components/FilterBar.vue:121-152` — `.filters-grid` uses `display: flex` with four `<select>` elements each `min-width: 140px`, no `@media` query, no `flex-wrap`. App shell uses `overflow-x-hidden` on `<main>` but the FilterBar sits **above** main inside the same flex column, so the bar itself scrolls horizontally.
- **Description:** Confirmed live at 375 × 812 viewport (`audit-375px.png`): four filter selects + reset button = ~720 px of content shoved into a 375-px-wide bar. "Location" label gets cut off as "Loca…", the rightmost selects and the reset button are invisible without horizontal scroll. The ProfileMenu in the header is also pushed off-screen at this width (header is flex with no wrap, and the LanguageSwitcher + ProfileMenu can't both fit). Mobile users effectively cannot change filters or log out.
- **Recommended fix:** Add `flex-wrap: wrap` to `.filters-grid` and the `header` row; below 640 px, stack filter groups vertically (`flex-direction: column; align-items: stretch`) and make `.filter-select { min-width: 0; flex: 1 1 auto; }`. For the header at narrow widths, collapse LanguageSwitcher to icon-only and prioritize keeping the ProfileMenu visible.

## 6. Restocking.vue and Reports.vue have zero i18n coverage and hardcoded `$` currency symbol

- **Severity:** High
- **Location:** `client/src/views/Restocking.vue:1-103` (every label, button, error message, table header, hint text), `client/src/views/Reports.vue:1-100+` (every chart title, table column, growth-rate label)
- **Description:** Both views were added recently but skipped i18n entirely. The Japanese-locale user lands on `/restocking` and sees "Budget", "Place Order", "Over budget — reduce quantities to submit.", "Submitting...", "Lead Time (days)" all in English while the sidebar around them is Japanese. Same on `/reports` ("Quarterly Performance", "Month-over-Month Analysis", "Growth Rate"). Additionally both views hardcode `${{ formatNumber(...) }}` — the currency context (`useI18n().currentCurrency`) is ignored, so a JPY-locale user still sees `$` prefixes. Restocking.vue line 81 and Reports.vue lines 31/32/56/85 are the offenders.
- **Recommended fix:** Add `restocking.*` and `reports.*` namespaces to both locale files; import `useI18n` in each view; use `currencySymbol` computed (already pattern-established in Inventory.vue/Orders.vue) instead of literal `$`. Also wire `tasksModal.deleteTitle` for `TasksModal.vue:88` (currently `title="Delete task"`).

## 7. Empty search-result and empty filter-result states are missing across views

- **Severity:** Medium
- **Location:** `client/src/views/Inventory.vue:36-74` (no `v-if filteredItems.length === 0` branch — empty `<tbody>` rendered as a blank card), `client/src/views/Orders.vue:80-120` (same — no empty state for "no orders match these filters"), `client/src/views/Demand.vue:11-30` (trend cards render with `count: 0` and an empty list — no "no items in this trend" message). The pattern exists already in `TasksModal.vue:67-69` (`<div v-if="sortedTasks.length === 0">`) and `Dashboard.vue` shortages (`noShortages` key) — it just wasn't applied here.
- **Description:** When a user searches "xyz" in Inventory or filters by a warehouse with no orders for a month, they see what looks like a broken page: card header showing "Stock Levels (0 SKUs)" with an empty table beneath. No guidance to clear filters, no acknowledgement that the filter matched nothing.
- **Recommended fix:** Add a `v-if="!filteredItems.length"` branch with a single-row table message ("No items match your search — clear filters?") and a Reset Filters action. Reuse `t('common.noData')` plus a new key per view.

## 8. Bell (notifications) icon is a dead click — focusable, looks interactive, does nothing

- **Severity:** Medium
- **Location:** `client/src/App.vue:29-34`
- **Description:** The header renders `<button … aria-label="Notifications"><Bell /></button>` with hover styling — keyboard users tab into it, screen readers announce "Notifications, button", clicking does nothing. There is no `@click`, no popover, no `disabled` state, no badge to show notifications would even appear here. Confusing for everyone, but especially screen-reader users who are told there's a button and then it doesn't do anything. Same risk-class as the breadcrumbs slot if added later.
- **Recommended fix:** Either delete the button until the notifications feature exists, OR keep it but render with `aria-disabled="true"`, remove from tab order (`tabindex="-1"`), add tooltip text "Notifications — coming soon", and disable hover affordance.

## 9. ProfileMenu and LanguageSwitcher dropdowns break keyboard accessibility

- **Severity:** Medium
- **Location:** `client/src/components/ProfileMenu.vue:3-23,77-100`, `client/src/components/LanguageSwitcher.vue:3-31,72-88`
- **Description:** Both dropdowns use the `@blur` + `setTimeout(200)` "fake outside-click" pattern. Consequences: (a) **Tab from the trigger button immediately closes the menu** before the user reaches the first menu item, because the trigger blurs; (b) no `aria-expanded`, no `aria-haspopup="menu"`, no `role="menu"` / `role="menuitem"`; (c) no Escape handler; (d) clicking with mouse works only because items use `@mousedown.prevent` to suppress the blur — a clever trick that simultaneously breaks keyboard activation, because `keyup.enter` on a menu item *after* tabbing in (if tabbing in worked) would not fire `mousedown`. Net effect: these menus are mouse-only.
- **Recommended fix:** Replace the `@blur` hack with a click-outside listener on `document` (or `@focusout` with `relatedTarget` check). Add `aria-haspopup="menu"`, `aria-expanded="<isOpen>"` on the button; `role="menu"` on the dropdown; `role="menuitem"` on each item. Handle `@keydown.esc` to close and refocus the trigger. Handle `@keydown.down/up` to move focus between items.

## 10. Modal overlays use a click-outside-to-close pattern with no warning for forms-in-progress (TasksModal)

- **Severity:** Medium
- **Location:** `client/src/components/TasksModal.vue:4` (`@click="close"` on `.modal-overlay`)
- **Description:** TasksModal contains an unsaved-add-task form (title, priority, due-date fields). One stray click on the dim backdrop wipes whatever the user typed — no confirmation, no recovery. Standard form-modal pattern is to only close on overlay-click when the form is pristine. The other read-only modals (InventoryDetailModal, ProductDetailModal, etc.) are fine to close-on-overlay since there's no input.
- **Recommended fix:** In TasksModal specifically, guard the overlay click: if `newTask.title.trim() || newTask.dueDate`, show a "Discard changes?" confirm before closing. Or, simpler: disable overlay-close in TasksModal entirely and require the X or Cancel button.

## 11. `<label>` elements in FilterBar are not associated with their `<select>` (no `for`/`id`)

- **Severity:** Low
- **Location:** `client/src/components/FilterBar.vue:6,25,35,47`
- **Description:** Labels like `<label>{{ t('filters.timePeriod') }}</label>` are visually adjacent to their selects but not programmatically linked. Click-on-label-to-focus-select doesn't work; screen readers don't announce "Time Period, combobox, All Months" — they announce just "combobox, All Months". Easy fix, real accessibility win.
- **Recommended fix:** Give each `<select>` an `id` (`filter-period`, `filter-location`, etc.) and the matching `<label for="...">`. Five-line change.

## 12. TasksModal delete button uses a bare `×` glyph with English-only `title`, no `aria-label`

- **Severity:** Low
- **Location:** `client/src/components/TasksModal.vue:88-90`
- **Description:** `<button @click="$emit('delete-task', task.id)" class="task-delete-btn" title="Delete task">×</button>`. The `×` is a Unicode multiplication-sign read aloud as "times" by some screen readers; the `title` attribute isn't reliably exposed by all assistive tech, and it's hardcoded English. Same pattern repeats with the close-button SVGs in every modal — they have no accessible name at all (no `aria-label`, no visually hidden text).
- **Recommended fix:** Add `:aria-label="t('tasks.deleteTask')"` (new locale key) to the delete button; same for `aria-label="t('common.close')"` on every modal's close button. Mark the `×` glyph itself `aria-hidden="true"`.

## 13. Dashboard renders `<PurchaseOrderModal>` that is never imported — silent broken UI

- **Severity:** Medium
- **Location:** `client/src/views/Dashboard.vue:289-295`
- **Description:** Live page console (captured at `http://localhost:3001/`) shows: `[Vue warn]: Failed to resolve component: PurchaseOrderModal at <Dashboard>`. The template references `<PurchaseOrderModal :is-open="showPOModal" …>` but no `import` statement and no `components:` registration exist in the Dashboard.vue script block. Vue renders it as a literal `<purchaseordermodal>` tag — so the entire "Create PO" flow from any clickable backlog row is dead. Users see no modal, no error, just nothing happens. Related: the API client (`api.js`) defines `getTasks/createTask/...` and `purchase-orders` endpoints that 404 on every load (`Failed to load tasks: AxiosError` in console on every page-mount).
- **Recommended fix:** Either restore the missing `PurchaseOrderModal.vue` component and import it, or delete the `<PurchaseOrderModal>` block from `Dashboard.vue` (lines 289-295) and the related state (`showPOModal`, `selectedBacklogForPO`, `poModalMode`, `handlePOCreated`). Same housekeeping for the dead `/api/tasks` and `/api/purchase-orders*` calls in `api.js` — silence the 404s users see in DevTools. (Cross-ref: security-findings #8 flagged the missing endpoints from the security angle; this is the user-visible counterpart.)

## 14. Reports.vue uses `v-for :key="index"` — explicitly forbidden by repo's CLAUDE.md / LEARNINGS

- **Severity:** Low (correctness/maintenance, not pure UX, but UX-adjacent: reused DOM nodes cause flickering form state when lists update)
- **Location:** `client/src/views/Reports.vue:28,51,82`
- **Description:** Three `v-for` loops use the array index as `:key` (`v-for="(q, index) in quarterlyData" :key="index"`, etc.). Repo CLAUDE.md gotcha #1 and LEARNINGS.md explicitly call out this anti-pattern. For pure read-only tables it's harmless today; the moment Reports.vue grows interactive elements (inputs, expandable rows), Vue will reuse DOM nodes incorrectly across sorts/filters.
- **Recommended fix:** Use `q.quarter` and `month.month` as keys (already unique in the data). Two-line change.

## 15. Cross-cutting: header bar is not focus-managed for the mobile menu toggle

- **Severity:** Low
- **Location:** `client/src/App.vue:8-14`
- **Description:** The mobile-only sidebar toggle (`<button @click="toggleSidebar">…`) opens/collapses the sidebar but doesn't move focus into the now-visible nav. On a touch device this is fine; on a keyboard-only narrow-viewport user (tablet with Bluetooth keyboard), they hit Enter on the toggle, the sidebar slides open, and focus stays on the toggle button — they then need to Tab past every header control to reach the nav items they just revealed.
- **Recommended fix:** When `sidebarCollapsed` flips false via this toggle (vs. via resize), `.focus()` the first `<router-link>` in the sidebar.

---

# Top-of-mind for consolidation

If I had to pick three must-fix items for the consolidated action plan, they would be:

1. **Modals lack Escape/focus-trap/focus-restore/ARIA** (finding #1) — fixes a Plan-A accessibility failure across six modals at once. Cheap composable.
2. **Missing i18n for new redesign surfaces** (findings #2 + #6) — Restocking, Reports, sidebar labels, search placeholder, ARIA labels. The Japanese build is currently broken on two whole routes.
3. **`PurchaseOrderModal` silently fails on Dashboard + 404s on `/api/tasks` on every page load** (finding #13) — production-feeling UX bug visible in every console session; cross-references security-finding #8.

Open to challenge on severity, especially:
- I rated **#5 (filter bar overflow at 375 px) as High** because mobile users literally can't reach the reset button or profile menu. Perf-analyst may consider mobile not in scope for a demo — happy to step it to Medium if "not a target form factor" is the team posture.
- I rated **#2 (untranslated nav labels) as High** because the Japanese build is the only locale switch shipped, and the mid-list English break is glaringly visible. Could be argued Medium if the team treats `ja` as best-effort.
- I rated **#1 (modal a11y) as High** rather than Critical because the app has no auth and no destructive operations behind these modals — but for a SaaS-grade redesign it is the kind of finding that would block release in most shops.

Cross-ref with security-findings:
- I **agree with security-auditor #4 staying Low** — the fake-auth ProfileMenu still says "Logout" and currently does nothing; from a pure-UX angle that's annoying-not-dangerous, but combined with #13 (and the fact that `Logout` is rendered prominently in red in the dropdown), it does make the app feel half-built. I'd merge with #13 as a single "ship-blocker checklist for the demo" rather than raise it.
- I'd **raise security-auditor #7 (Reports.vue console.logs) by a hair** — finding it gives a real impression of "this is dev code" when a workshop attendee opens DevTools, which is the entire UX of a Sia-Partners-branded demo. Keep at Low but flag for the same sprint as the strip-console-on-build chore.
