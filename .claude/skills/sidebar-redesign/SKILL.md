---
name: sidebar-redesign
description: Redesigns this Vue 3 application's UI from a top navigation bar into a modern SaaS-style layout with a vertical left sidebar, consistent spacing, and a polished professional look. Use when asked to redesign the nav, add a sidebar, or modernize the overall app layout.
---

# Sidebar Redesign

Converts the top horizontal nav bar in [App.vue](client/src/App.vue) into a fixed
vertical left sidebar, in the style of modern SaaS products (Linear, Vercel,
Stripe dashboard). This is a layout-shell change: it touches `App.vue` and
global styles, not individual views.

**This is a significant `.vue` file change. Delegate the implementation to the
`vue-expert` subagent per the project's mandatory rule.** Use this skill to
gather the plan and constraints, then hand them to `vue-expert` verbatim.

## What changes

- `<header class="top-nav">` becomes `<aside class="sidebar">`, moved to the
  left, full viewport height, fixed/sticky position.
- The app root layout switches from `flex-direction: column` to a two-column
  layout: `display: flex` with the sidebar at a fixed width and the content
  area filling the remainder (`flex: 1`).
- `nav-tabs` links go from horizontal pills to stacked vertical items, each
  full-width, with an icon slot + label.
- The logo/company name moves to the top of the sidebar; `ProfileMenu` and
  `LanguageSwitcher` move to the bottom of the sidebar (avoid leaving them
  orphaned in a now-removed top bar).
- `FilterBar` and `<main class="main-content">` stay in the right-hand content
  column, with `main-content` keeping its own internal `max-width` and padding
  for readability on wide screens (don't let the content stretch edge-to-edge
  on the sidebar's side).

## Layout structure (target)

```
.app                      (display: flex, min-height: 100vh)
├── .sidebar              (width: 260px, flex-shrink: 0, fixed left, full height)
│   ├── .sidebar-logo     (company name + subtitle, top)
│   ├── .sidebar-nav      (vertical nav-tabs, flex: 1)
│   └── .sidebar-footer   (LanguageSwitcher + ProfileMenu, bottom)
└── .content-area         (flex: 1, display: flex, flex-direction: column, min-width: 0)
    ├── FilterBar
    └── main.main-content (router-view)
```

Use `min-width: 0` on `.content-area` so wide tables/charts don't blow out the
flex layout.

## Visual language to carry over

Keep the existing design tokens from [App.vue](client/src/App.vue) (lines
~185-480) rather than inventing a new palette:

- Background/surface: `#ffffff`, border `#e2e8f0`
- Text: heading `#0f172a`, muted `#64748b`, body `#334155`/`#475569`
- Accent/active: `#2563eb` text on `#eff6ff` background
- Border radius `6px`-`10px`, existing `.card`, `.stat-card`, `.badge` styles
  are unchanged - only the nav shell changes shape.

For the sidebar itself, typical SaaS conventions to apply:

- Sidebar background slightly distinct from content (e.g. `#f8fafc` or white
  with a `1px solid #e2e8f0` right border) so it reads as a separate surface.
- Active nav item: left accent bar or filled pill (`#eff6ff` background,
  `#2563eb` text), same as the current `.nav-tabs a.active` treatment but
  applied to a full-width row instead of `::after` underline.
- Vertical rhythm: consistent `0.25rem`-`0.5rem` gaps between nav items,
  `0.75rem`-`1rem` internal padding per item, generous `1.5rem`+ padding
  around the logo and footer blocks.
- Use CSS spacing in `rem`, never hardcoded pixel values, per the project's
  Typescript/coding rules.

## Implementation steps

1. Read [App.vue](client/src/App.vue) in full to capture every element
   currently in `top-nav` (logo, nav-tabs, LanguageSwitcher, ProfileMenu) and
   every modal/global element that must stay outside the sidebar.
2. Restructure the template: header → aside, nav-tabs → vertical list, move
   LanguageSwitcher/ProfileMenu into a sidebar footer block.
3. Rewrite the layout CSS (`.app`, `.top-nav` → `.sidebar`, `.nav-container`,
   `.nav-tabs`, `.main-content`) for the two-column flex structure above.
   Leave card/table/badge styles untouched.
4. Verify [FilterBar.vue](client/src/components/FilterBar.vue) still renders
   correctly directly under the new sidebar layout (it's inside
   `.content-area`, not inside the sidebar).
5. Run `npm run lint` and `npm run build` in `client/` and fix any issues.
6. Start the app (`start` skill or manual) and check every route
   (`/`, `/inventory`, `/orders`, `/spending`, `/demand`, `/reports`) in the
   browser via Playwright MCP: sidebar stays fixed while content scrolls,
   active state highlights the right item, responsive at narrower widths
   (collapse or scroll, not overflow/clip), ProfileMenu and LanguageSwitcher
   still function (open modals, switch language).

## Things to watch for

- `router-link` active-state logic (`$route.path === '/...'`) must be
  preserved when restructuring the markup - don't lose the active highlight.
- Z-index/stacking: modals (`ProfileDetailsModal`, `TasksModal`) must still
  render above the sidebar.
- Sidebar width should be a CSS variable or single source of truth (e.g.
  `--sidebar-width: 260px`) reused by both `.sidebar` and `.content-area` if
  the sidebar is `position: fixed` (in that case content needs `margin-left`
  equal to the sidebar width).
- Don't introduce a mobile hamburger/collapse toggle unless asked - keep scope
  to the layout shell change. If the user wants collapsible/responsive
  behavior, confirm before adding it.
