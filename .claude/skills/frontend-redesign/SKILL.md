---
name: frontend-redesign
description: Redesigns this Vue 3 application's UI into a modern, polished, professional SaaS-style interface - layout shell (e.g. top nav to vertical sidebar), spacing consistency, and visual refinement. Use when asked to redesign, modernize, restyle, or "make it look more professional/SaaS-like".
---

# Frontend Redesign

General guidance for redesigning this app's UI toward a modern SaaS look
(Linear, Vercel, Stripe dashboard, Notion). Covers two kinds of work:

1. **Layout shell changes** - e.g. converting the top nav bar to a vertical
   left sidebar. See [Sidebar conversion](#sidebar-conversion) below for the
   concrete plan.
2. **Polish passes** - spacing/rhythm consistency, color and typography
   cleanup, card/table/badge refinement - without necessarily changing the
   overall shell.

Confirm with the user which of these (or both) is in scope before starting;
"redesign the UI" alone is ambiguous between a full shell change and a polish
pass on the existing layout.

**Any of this work touches `.vue` files significantly. Delegate the
implementation to the `vue-expert` subagent per the project's mandatory
rule.** Use this skill to gather the plan and constraints, then hand them to
`vue-expert` verbatim.

## Visual language to carry over

Keep the existing design tokens from [App.vue](client/src/App.vue) (lines
~185-480) rather than inventing a new palette, unless the user explicitly
asks for a new color scheme:

- Background/surface: `#ffffff`, border `#e2e8f0`
- Text: heading `#0f172a`, muted `#64748b`, body `#334155`/`#475569`
- Accent/active: `#2563eb` text on `#eff6ff` background
- Status colors: success `#059669`/`#d1fae5`, warning `#ea580c`/`#fed7aa`,
  danger `#dc2626`/`#fecaca`, info `#2563eb`/`#dbeafe`
- Border radius `6px`-`10px` across cards, badges, buttons, inputs.

General polish principles to apply across any redesign work:

- Consistent spacing scale (`0.25rem` increments: `0.25, 0.5, 0.75, 1, 1.25,
  1.5, 2rem`) - audit existing `padding`/`margin`/`gap` values and snap them
  to this scale rather than leaving ad-hoc numbers.
- Consistent type scale: page titles `1.875rem`/700, card titles
  `1.125rem`/700, body `0.875rem`-`0.938rem`, labels/uppercase micro-text
  `0.75rem`/600 with letter-spacing - reuse the scale already in `App.vue`
  rather than introducing new sizes.
- Hover/active states on every interactive element (rows, nav items, buttons)
  using the existing `0.15s-0.2s ease` transition convention.
- Use CSS spacing in `rem`, never hardcoded pixel values, per the project's
  Typescript/coding rules.
- No emojis in UI, per the project's design system rules.

## Sidebar conversion

The most common shell change: converting the top horizontal nav bar in
[App.vue](client/src/App.vue) into a fixed vertical left sidebar.

### What changes

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

### Layout structure (target)

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

### Sidebar-specific visual conventions

- Sidebar background slightly distinct from content (e.g. `#f8fafc` or white
  with a `1px solid #e2e8f0` right border) so it reads as a separate surface.
- Active nav item: left accent bar or filled pill (`#eff6ff` background,
  `#2563eb` text), same as the current `.nav-tabs a.active` treatment but
  applied to a full-width row instead of `::after` underline.
- Vertical rhythm: consistent `0.25rem`-`0.5rem` gaps between nav items,
  `0.75rem`-`1rem` internal padding per item, generous `1.5rem`+ padding
  around the logo and footer blocks.

### Sidebar implementation steps

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

### Sidebar-specific watch-outs

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

## General redesign verification (applies to any scope)

1. Run `npm run lint` and `npm run build` in `client/` and fix any issues.
2. Start the app (`start` skill or manual) and check every route
   (`/`, `/inventory`, `/orders`, `/spending`, `/demand`, `/reports`) in the
   browser via Playwright MCP: layout holds at typical desktop widths,
   interactive elements (nav, ProfileMenu, LanguageSwitcher, modals, filters)
   still function, no visual regressions on tables/charts/cards.
