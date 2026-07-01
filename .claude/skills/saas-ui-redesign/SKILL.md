---
name: saas-ui-redesign
description: Redesign the Vue 3 client in client/ into a modern SaaS-style interface with a left vertical navigation sidebar (replacing the top nav bar), a design-token system, consistent spacing, and a polished professional look. Use this skill when the user asks to redesign, modernize, or polish the frontend UI; move navigation to a sidebar / vertical nav / left nav; give the app a "SaaS look"; improve spacing, layout, or visual consistency; or restyle App.vue and the shell.
---

# SaaS UI Redesign

This skill converts the Factory Inventory Management client (`client/`, Vue 3 + Vite) from its
current sticky **top nav bar** into a modern SaaS layout: a **left vertical sidebar** for
navigation, a **CSS custom-property design-token system**, a **consistent spacing scale**, and
a clean, professional finish. The existing slate/blue palette and Inter typeface are kept — this
is about layout structure, consistency, and polish, not a new color scheme.

## Operating rules (non-negotiable)

- **Delegate every `.vue` edit to the `vue-expert` subagent.** Per this repo's CLAUDE.md, any
  time you create or significantly modify a `.vue` file you MUST use the `vue-expert` subagent.
  Give it the relevant reference file content and the preservation checklist below.
- **Verify in a real browser with Playwright MCP** (`mcp__playwright__*`) against
  `http://localhost:3000`. Start the servers with the `start` skill first.
- **Preserve behavior.** This is a visual/layout redesign. Routing, data loading, i18n, filters,
  and modals must work exactly as before (see the checklist in Phase 6).
- **Document non-obvious changes with a brief comment** explaining the "why", matching the
  surrounding style.

## Target design language

- **Left sidebar** (~248px): brand at top, vertical nav in the middle, `LanguageSwitcher` +
  `ProfileMenu` in the footer. Collapses on narrow viewports.
- **Token-driven** color, spacing, radius, shadow, and z-index — one source of truth on `:root`.
- **8px spacing rhythm** so gaps, padding, and margins are consistent across cards, tables, and grids.
- **Card-based surfaces** on a soft `--color-bg`, restrained shadows, clear active-nav state.

## Reference files

- `references/design-tokens.md` — the `:root` custom-property block to add to `App.vue`, plus a
  literal→token refactor map. **Read this before Phase 1.**
- `references/sidebar-layout.md` — the target `App.vue` template + shell CSS, FilterBar
  repositioning, and dropdown notes. **Read this before Phase 2.**

## Procedure

Work in phases. After each phase that touches a `.vue` file, hand the change to `vue-expert`.

### Phase 1 — Establish design tokens
1. Read `references/design-tokens.md`.
2. Have `vue-expert` add the `:root` token block to the top of the global `<style>` in
   `client/src/App.vue` (before the `*` reset).
3. Refactor the existing global rules to consume tokens using the mapping table. Snap arbitrary
   rem values to the nearest spacing step. This is the foundation for "consistent spacing".

### Phase 2 — Build the sidebar shell
1. Read `references/sidebar-layout.md`.
2. Have `vue-expert` restructure `App.vue`'s **template** from `.top-nav` (flex column) to the
   two-column `.app` (flex row) → `aside.sidebar` + `.main`. Move the logo to `.sidebar-brand`,
   the six `router-link`s into a vertical `.sidebar-nav`, and `LanguageSwitcher` + `ProfileMenu`
   into `.sidebar-footer`.
3. Add the shell CSS from the reference. The `<script>` block does not change.

### Phase 3 — Reposition FilterBar & content
1. `FilterBar` moves from `top: 70px` sticky to `top: 0` within the main column
   (`client/src/components/FilterBar.vue`).
2. Update `.main-content` to center at `--content-max` with token padding.

### Phase 4 — Polish pass
1. Sweep App.vue global styles for any remaining hardcoded colors/spacing and replace with tokens.
2. Unify card / table / badge / stat-card padding and gaps to the spacing scale so every surface
   shares the same rhythm. Confirm hover, focus-ring, and active states read as intentional.

### Phase 5 — Responsive
1. Add the sidebar collapse behavior (icon rail under `1024px`; consider off-canvas + a toggle on
   mobile). The main column stays fluid with `min-width: 0` so wide tables don't overflow.

### Phase 6 — Verify (Playwright MCP)
1. Ensure servers run (`start` skill), then drive `http://localhost:3000`.
2. Screenshot and check **every route**: `/`, `/inventory`, `/orders`, `/spending`, `/demand`,
   `/reports`.
3. Confirm the **preservation checklist** below all holds. Fix regressions before finishing.

## Preservation checklist

The redesign must keep all of this working:

- **Routes & nav:** all six `router-link`s (`/`, `/inventory`, `/orders`, `/spending`, `/demand`,
  `/reports`), their `t('nav.*')` i18n labels, and the manual
  `:class="{ active: $route.path === '…' }"` active binding. Add `aria-current="page"` to the
  active link.
- **Profile & tasks:** `ProfileMenu` still emits `@show-profile-details` and `@show-tasks`;
  `ProfileDetailsModal` and `TasksModal` keep their existing props and the
  `add/delete/toggle-task` handlers.
- **Filters:** `FilterBar` and its four filters behave exactly as before.
- **i18n:** `LanguageSwitcher` still toggles locale/currency; no hardcoded strings introduced
  (except the already-hardcoded "Reports" label).
- **Layering:** modals (`--z-modal`) render above the sidebar; dropdowns
  (`--z-dropdown`) above the sidebar but below modals; reposition sidebar-footer dropdowns to
  open upward so they aren't clipped.
- **Views untouched:** the 7 files in `client/src/views/` rely on `.main-content` padding — keep
  that contract so views need no changes.

## Done when

Every route renders in the new sidebar layout with consistent token-driven spacing, the active
nav item is clearly marked, the layout is responsive, and the full preservation checklist passes
in Playwright with no console errors.
