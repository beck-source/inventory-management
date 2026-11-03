---
name: vue-saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a collapsible vertical sidebar on the left instead of a top nav bar, a consistent spacing scale and design tokens, and a polished professional look. Use this skill whenever the user wants to modernize, restyle, or "make it look like a real SaaS app" for a Vue 3 project, move navigation from a top bar to a left sidebar, add an app shell or dashboard layout, unify inconsistent spacing or styling across views, or asks for a more professional or polished UI, even if they never say "sidebar" or "redesign".
---

# Vue 3 SaaS redesign

Turn an existing Vue 3 app into a modern SaaS-style interface: a left sidebar for navigation, a slim top bar for page-level controls, a content area with consistent spacing, and one shared set of design tokens. The goal is a visual and structural upgrade. The app must behave exactly as before.

## Principles

- **Preserve behaviour.** Routes, props, emitted events, API calls, i18n keys and state logic stay as they are. A redesign that breaks a feature is worse than no redesign. Touch `<template>` structure and `<style>` blocks; leave `<script>` logic alone unless the layout needs a small addition (such as sidebar collapse state).
- **Tokens first, components second.** Inconsistency comes from hardcoded values scattered across files. Define spacing, color, radius, shadow and type tokens once as CSS variables, then replace literals with them. This is what makes the result look designed rather than patched.
- **Reuse the app's identity.** If the project documents a palette or design rules (CLAUDE.md, README, existing CSS), keep those colors and rules as the base and refine them. Only invent a palette when none exists.
- **Small, verifiable steps.** Shell first, then tokens, then views one at a time, building after each step. A broken build is cheap to fix when only one step changed.

## Workflow

### 1. Inspect before changing
Read, in this order: `package.json` (Vue version, router, UI libraries, i18n), the router file (every route and its label), `App.vue` (current layout, global styles, anything mounted globally such as modals, filter bars, language switcher, profile menu), and one or two representative views. Write down:
- The nav items (path, label or i18n key).
- Everything currently in the top bar besides links (logo, switchers, profile menu, search). Each needs a new home.
- Global UI mounted in `App.vue` (filter bars, modals) so it survives the move.
- Existing design rules and colors.
- Whether there is a component library. If so, restyle through its theming hooks rather than fighting it.

If the app has no router, or Vue 2 or Options-API-only code, say so and adapt: the shell pattern is the same, only the syntax differs.

### 2. Confirm the plan only if something is ambiguous
Most decisions have good defaults (below). Ask the user only about real forks: where to put an item that has no obvious home, whether to introduce an icon library, whether to keep a brand color that clashes with the neutral base.

### 3. Build the design tokens
Create `src/styles/tokens.css` (or the project's equivalent) from `references/design-tokens.md` and import it once in `main.js`. Adapt the accent color to the app's existing brand color. Keep the scale on a 4px grid.

### 4. Build the app shell
Replace the top nav with the layout in `references/app-shell.md`:
- **Sidebar** (left, fixed): logo and app name at the top, nav links with icons, secondary items (language, profile) at the bottom, a collapse toggle. Expanded 240px, collapsed 72px to icons only with `title` tooltips.
- **Top bar** (inside the content column): page title area and page-level controls such as filters, search, or actions. This is where a global filter bar goes.
- **Content area**: scrolls independently, max-width container, consistent page padding.
- **Mobile** (under 768px): the sidebar becomes an off-canvas drawer opened from a menu button in the top bar, with a backdrop.

Collapse state belongs in a small composable persisted to `localStorage`, so the choice survives reloads.

Icons: use inline SVG components (stroke 1.5 to 2, 20px) so no dependency is needed. Add an icon library only if the project already uses one or the user asks.

### 5. Restyle the views
Work view by view. In each: replace hardcoded spacing, colors, radii and shadows with tokens; wrap sections in the shared card pattern; align headings, tables, buttons and form controls to the shared component styles in `references/design-tokens.md`. Put shared patterns (card, table, badge, button, stat tile, empty state) in global styles rather than copying them per view. Keep chart colors and status colors semantic and consistent (green, blue, amber, red).

### 6. Verify
- Run the build (`npm run build` or the project's equivalent) and fix errors. Delete build output that was not there before.
- If a dev server and browser tooling are available, load every route and check: active nav state, collapse and expand, the mobile drawer, no horizontal scroll, modals layering above the sidebar, tables not overflowing.
- Grep for leftover hardcoded hex colors and pixel paddings in the files you touched, and for references to removed classes such as the old `.top-nav`.
- Check keyboard use: links reachable by Tab, visible focus ring, toggle button has an `aria-label`, nav has `aria-label` and the active link `aria-current="page"`.

## Defaults

| Decision | Default | Why |
|---|---|---|
| Sidebar width | 240px expanded, 72px collapsed | Fits labels without crowding content |
| Theme | Light, neutral slate surfaces, one accent | Reads as professional and is easy to retheme |
| Spacing | 4px grid; component padding 16 or 24; section gaps 24 or 32 | One rhythm everywhere removes the "patched" feel |
| Radius | 8px controls, 12px cards | Soft but not toy-like |
| Shadows | Border plus a very subtle shadow | Depth without noise |
| Type | System or Inter stack; 14px body, 20 to 24px page titles | Dense but legible dashboards |
| Motion | 150ms ease on color and width | Feels responsive; respect `prefers-reduced-motion` |

## Things that go wrong

- Modals and dropdowns with fixed `z-index` hidden behind or clipped by the sidebar or an `overflow: hidden` ancestor. Check stacking after the shell is in.
- `100vh` layouts that double-scroll once the shell is a flex row. Make the shell `height: 100vh` with only the content column scrolling.
- Items that lived in the top bar (language switcher, profile menu) disappearing. Account for each one found in step 1.
- Sticky table headers or page headers using the old top-bar height as an offset.
- Fixing spacing in one view with a one-off margin instead of the token, which brings the inconsistency back.

## Final report

Tell the user what changed (shell, tokens, which views), where each former top-bar item moved, what was verified and how, and anything not done or not checked. Do not claim a visual check you did not run.
