---
name: redesign-ui-saas
description: Redesign the Vue 3 app's UI into a modern SaaS-style interface with a vertical left sidebar (replacing the top nav bar), consistent spacing, and a polished professional look. Use when asked to redesign, restyle, modernize the UI/layout, add a sidebar, move navigation to the side, or give the app a more "SaaS" or "polished" appearance.
---

# Redesign UI: SaaS Sidebar Layout

Converts this app's current top-nav layout into a modern SaaS-style shell: a fixed
vertical sidebar on the left for primary navigation, with page content (including
the existing filter bar) in a column to its right. This is a **layout and visual
design change** — it must not change API calls, composables' business logic, or
data flow. Every view keeps working exactly as before; only how it's arranged and
styled changes.

> **MANDATORY (per root `CLAUDE.md`):** any creation or significant modification of
> a `.vue` file must be delegated to the **vue-expert** subagent. This skill defines
> *what* to build and the design rules to follow — it does not replace that
> delegation requirement.

## Current State (what you're replacing)

Read these before changing anything — they define the baseline:

- `client/src/App.vue` — global shell: `.top-nav` (horizontal `nav-tabs`), `.main-content`, plus all shared styles (`.card`, `.stat-card`, `.badge`, `table`, etc.) in the global `<style>` block.
- `client/src/components/FilterBar.vue` — the 4-filter bar (Time Period, Warehouse, Category, Order Status), currently rendered below the top nav.
- `client/src/views/*.vue` — page bodies (Dashboard, Inventory, Orders, Spending, Demand, Backlog, Reports). These generally assume a full-width content column; they should not need structural changes, only room to breathe in the new layout.
- `client/src/components/ProfileMenu.vue`, `LanguageSwitcher.vue` — currently live in the top nav's right side.

## Target Structure

```
┌──────────────┬────────────────────────────────────────┐
│              │  FilterBar (sticky, top of content)     │
│   Sidebar    ├────────────────────────────────────────┤
│  (fixed,     │                                          │
│   left,      │            <router-view />               │
│   ~240px)    │         (Dashboard, Inventory, …)         │
│              │                                          │
│  logo        │                                          │
│  nav links   │                                          │
│  ...         │                                          │
│  profile/    │                                          │
│  language    │                                          │
│  (bottom)    │                                          │
└──────────────┴────────────────────────────────────────┘
```

- Sidebar is a fixed-width column (220–260px), full viewport height, `position: sticky` or `fixed`.
- Logo/brand at the top of the sidebar (moved from `.logo` in the old top nav).
- Nav links stacked vertically, each with an active-state highlight (left accent bar or filled background — reuse the existing `.nav-tabs a.active` color logic, just applied vertically).
- `ProfileMenu` and `LanguageSwitcher` move into the sidebar, typically pinned near the bottom.
- `FilterBar` stays in the content column (not the sidebar) since it's page-context, not navigation — render it as a sticky bar at the top of `.main-content`.
- Main content area fills the remaining width, keeps its existing `max-width` centering *within that column* if the app should stay readable on ultrawide screens.

## Design Rules

**Spacing** — pick one 4px/8px-based scale and use it everywhere (don't introduce ad-hoc values):
- Base unit `4px`. Common steps: `8px`, `12px`, `16px`, `24px`, `32px`.
- Sidebar internal padding: `24px` horizontal, `16px` vertical rhythm between nav items.
- Content area padding: keep consistent with existing `.main-content` (`1.5rem 2rem`) or tighten to the new scale — just be consistent across every view, don't let individual views set their own outer padding.

**Color** — stay inside the existing design system from root `CLAUDE.md`, don't invent a new palette:
- Base: Slate/gray (`#0f172a` text, `#64748b` muted, `#e2e8f0` borders).
- Accent/active state: `#2563eb` (already used for `.nav-tabs a.active`).
- Status colors unchanged: green/blue/yellow/red badges.
- Sidebar background can be a distinct surface (e.g. white or a very light slate) with a `1px` right border — avoid a heavy dark sidebar unless asked; keep it consistent with the app's light, clean aesthetic.

**Polish checklist:**
- Consistent border-radius across cards, buttons, nav items (check what's already used — `6–10px` in this app — and don't mix values).
- Subtle hover states on every interactive element (nav links, buttons, table rows) — reuse existing hover patterns (`background: #f1f5f9`, border color shifts) rather than inventing new ones.
- Active nav item should be unambiguous at a glance (background fill + accent color, not just a color change).
- No emojis anywhere in the UI (per project rule).
- Every view must still show loading/error states — don't regress this while restyling.
- Keep `v-for` keys, prop/emit patterns, and computed-vs-method usage untouched; this is a styling/structure task, not a logic rewrite.

## Implementation Steps

1. **Audit** — read `App.vue`, `FilterBar.vue`, and one or two views to confirm current class names and shared styles before touching anything.
2. **Delegate to vue-expert** to:
   a. Restructure `App.vue`: replace `.top-nav` horizontal layout with a `.sidebar` + `.content-area` two-column flex/grid layout. Move nav links, logo, `ProfileMenu`, and `LanguageSwitcher` into the sidebar markup.
   b. Update global `<style>` in `App.vue`: add sidebar styles, adjust `.main-content` to live inside the new content column, keep all existing component styles (`.card`, `.stat-card`, `.badge`, tables, etc.) working unchanged since views depend on them.
   c. Adjust `FilterBar.vue` styling only if needed for its new position (e.g. remove any margin assumptions tied to the old top nav) — its filter logic (`useFilters` composable) must not change.
   d. Spot-check each view in `client/src/views/` for any layout assumptions that broke (e.g. a view that assumed full browser width) and fix only the layout CSS, not the logic.
3. **Verify with Playwright MCP** (per root `CLAUDE.md` rule) against `http://localhost:3000`:
   - Sidebar renders on every route, active link matches current route.
   - Filters still work (change a filter, confirm data updates).
   - No horizontal overflow / broken layout at common widths (check at least desktop and a narrow ~1024px width).
   - Modals (`TasksModal`, `ProfileDetailsModal`, detail modals) still open correctly over the new layout.
4. **Report** what changed, file by file, and flag anything that needs a product decision (e.g. whether the sidebar should be collapsible, whether it should overlay on small screens).

## Explicitly Out of Scope

- Backend/API changes (`server/`) — none of this touches routes, filtering logic, or data models.
- Adding new routes, views, or features.
- Changing the filter system's behavior — only its visual placement.
- Introducing a new component library/CSS framework — keep using scoped `<style>` blocks and the existing hand-rolled design system, consistent with `client/CLAUDE.md`.
