---
name: saas-sidebar-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style layout - a vertical left navigation sidebar (collapsible to an icon rail, off-canvas drawer on mobile) replacing a horizontal top nav, a slim top header bar, a consistent spacing/type/color token system, and polished cards, tables and page headers across every view. Use this whenever the user wants to modernize, restyle, or "make professional" a Vue app's look, move navigation to a side menu/sidebar/left rail, convert a top nav bar to a sidebar, build an admin/dashboard app shell, or fix inconsistent spacing and styling across Vue views - even if they don't say "SaaS" or "sidebar" explicitly.
---

# SaaS Sidebar Redesign (Vue 3)

Turn an existing Vue 3 app into a polished SaaS-style interface: left sidebar navigation, slim header bar, consistent design tokens, and uniform page layouts. This is a **visual and structural** redesign. Every route, filter, modal, data flow, and i18n string must keep working exactly as before. If the app looks great but a link or filter breaks, the redesign has failed.

## Target layout

```
+--------------+-------------------------------------------+
| [logo] Name  |  Page title            [filters] [lang][me]|  <- header (56-64px, sticky)
|              +-------------------------------------------+
| > Overview   |                                           |
|   Inventory  |   Page header (title + subtitle + actions)|
|   Orders     |                                           |
|   Finance    |   [ KPI ] [ KPI ] [ KPI ] [ KPI ]          |
|   ...        |                                           |
|              |   +-------------------------------------+ |
|              |   | Card                                | |
|              |   +-------------------------------------+ |
| ------------ |                                           |
| [<<] Collapse|                                           |
+--------------+-------------------------------------------+
  240px expanded / 64px collapsed / off-canvas below 1024px
```

## Workflow

### 1. Discover before changing anything

Read these first. The redesign has to fit the app's structure, so don't guess:

- **Project rules**: `CLAUDE.md`, `AGENTS.md`, `README`, or similar. Follow any rules about delegating `.vue` work to a specific subagent, color palettes, "no emojis", i18n, or docs to update. Project rules override this skill's defaults.
- **Root layout**: usually `src/App.vue`. Find the current nav, its links, and everything else in the header (logo, filters, language switcher, profile menu, notifications).
- **Router**: `src/router/*` or `main.js`. Get the route list, route names, and any `meta`. Nav items should come from the routes or a single nav config. Don't duplicate them in several places.
- **Global styles**: where they live (`App.vue` unscoped `<style>`, `src/assets/*.css`, `main.css`), the existing colors and fonts, and shared class names that views depend on (`.card`, `.stat-card`, `.page-header`, tables, badges).
- **Views**: skim every file in `src/views/` (or `pages/`) for repeated patterns and inconsistencies: ad-hoc margins, mixed paddings, different card styles, different heading sizes.
- **Tooling**: Tailwind, a component library (Vuetify, PrimeVue, Element Plus), or plain CSS? Work inside what exists. Don't add Tailwind or a UI library to a plain-CSS app.

Write a short plan for the user before editing: the files you'll touch, the nav items with the icon chosen for each, the token palette, and anything risky.

### 2. Establish design tokens

Define CSS custom properties once, in the global stylesheet, and use them everywhere. See `references/design-tokens.md` for the default token set. If the app already has a palette, map it onto these token names instead of replacing its colors.

The main source of the "polished" look is consistency: one spacing scale (4px base), one radius set, one shadow set, and a type scale with only a few sizes. Most "unprofessional" UIs differ from good ones mainly by having 15 slightly different paddings.

### 3. Build the app shell

Split the root layout into focused components (adjust names to the project's conventions):

- `AppSidebar.vue`: brand, nav list, collapse toggle. Template in `references/sidebar-template.md`.
- `AppHeader.vue`: hamburger (mobile only), current page title, and the controls moved out of the old top nav (filters, language switcher, profile menu).
- `App.vue`: a CSS grid shell: `grid-template-columns: var(--sidebar-width) 1fr`, with the header and `<router-view>` in the main column.

Requirements, and why each one matters:

- **Active state uses the router.** Use `router-link`'s `active-class`/`exact-active-class` or `useRoute()`. Use exact matching for `/` so "Overview" isn't always active.
- **Collapse to icon rail**: 240px to 64px. When collapsed, labels are hidden but stay available through `title`/`aria-label`, so the icons remain usable. Persist the state in `localStorage` wrapped in try/catch, because storage can throw in private mode.
- **Mobile drawer** below 1024px: the sidebar becomes `position: fixed`, translated off-screen, opened by the header hamburger. Add a backdrop that closes it. Escape closes it. Navigating to a route closes it (watch `route.path`). Lock body scroll while it's open.
- **Accessibility**: `<nav aria-label="Main">`, `aria-current="page"` on the active link, `aria-expanded` and `aria-controls` on the toggles, visible `:focus-visible` rings, and enough contrast for the muted nav text.
- **Icons**: small inline SVG line icons (20px, `stroke="currentColor"`, `stroke-width="1.75"`, `fill="none"`) so they inherit the link color. No emojis, and don't add an icon package unless one is already installed.
- **i18n**: if the app uses vue-i18n or similar, reuse the existing nav label keys. New strings ("Collapse", "Open menu") get keys in every locale file.
- **Header content migration**: everything that was in the old top nav must still exist after the redesign. Global filters usually belong in the header or in a filter row directly under it.

### 4. Sweep the views for consistency

Go through each view and apply the shared patterns:

- **Page header**: title (`--text-2xl`, semibold), optional one-line muted subtitle, actions aligned right. Use the same structure on every page.
- **Content container**: `padding: var(--space-6) var(--space-8)`, with an optional max width. No view adds its own outer margin.
- **Grids**: KPI/stat cards in `repeat(auto-fit, minmax(220px, 1fr))` with `gap: var(--space-4)` or `--space-6`.
- **Cards**: `--surface` background, 1px `--border`, `--radius-lg`, `--shadow-sm`, `padding: var(--space-5)` or `--space-6`. Card titles get one consistent style.
- **Tables**: muted uppercase small header row, `--space-3` cell padding, hairline row dividers, subtle row hover, numbers right-aligned with `tabular-nums`.
- **Badges/status**: pill shape, tinted backgrounds from the status tokens, and the same mapping everywhere.
- **Buttons/inputs**: one height (36px), one radius, one focus ring.

Prefer upgrading the shared class definitions over rewriting each view's markup. Changing `.card` once in the global stylesheet is safer than touching 7 templates. Only edit view templates where the structure itself is inconsistent.

Leave alone: data logic, computed properties, API calls, and chart math. Chart colors can be pointed at tokens if they're hardcoded.

### 5. Verify

1. Run the build (`npm run build` or the project's equivalent) and fix any errors.
2. Run the existing tests if there are any.
3. Check it in a browser (Playwright MCP if available; otherwise ask the user to look). Cover:
   - every nav link routes correctly and shows the correct active state, including `/`
   - the collapse toggle works and the state survives a reload
   - at 375px width the drawer opens, closes on backdrop click, on Escape, and on navigation, and nothing scrolls horizontally
   - global filters still change the data
   - modals still open above the sidebar (check the z-index order: sidebar < header < drawer backdrop < drawer < modals)
   - screenshots at 1440px (expanded), 1440px (collapsed), and 375px (drawer open)
4. Update architecture docs if the project keeps them and the layout structure changed.

## Report back

Summarize what changed: new components, token file location, the views touched, the features (collapse, drawer, icons, header), the verification results with screenshot paths, and anything you deliberately left alone or couldn't verify.
