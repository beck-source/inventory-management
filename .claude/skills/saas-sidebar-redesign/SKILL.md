---
name: saas-sidebar-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface - replaces a top nav bar with a collapsible vertical sidebar on the left (icon-only rail on medium screens, drawer on mobile), introduces CSS design tokens for consistent spacing, and restyles cards, tables and badges for a polished professional look. Use when asked to modernize, restyle, or "make SaaS-like" a Vue 3 app, or to move its navigation into a left sidebar.
---

# SaaS Sidebar Redesign for Vue 3

Turn a Vue 3 app with a top navigation bar into a SaaS-style layout: a dark left sidebar, a slim sticky topbar, token-driven spacing, and clean cards. The redesign is **visual only**. Data loading, routing, state and business logic must come out unchanged.

Supporting files in this skill's directory:
- `templates/tokens.css`: the design-token file to copy into the app.
- `reference/AppShell.vue`: a working shell (sidebar, topbar, three responsive tiers) to adapt.

## Target layout

```
+------------+---------------------------------------------+
|  Brand     |  [=] Page title          [lang]  [profile]  |  topbar (sticky)
|            +---------------------------------------------+
|  > Nav 1   |  optional toolbar / filters (sticky)        |
|    Nav 2   +---------------------------------------------+
|    Nav 3   |                                             |
|            |   page header                               |
|            |   [card] [card] [card]                      |
|            |   [ table card                         ]    |
|  [<<]      |                                             |
+------------+---------------------------------------------+
```

Responsive tiers (the sidebar is never simply hidden on desktop):

| Width | Sidebar |
|---|---|
| >= 1024px | Full width (240px) with labels. The user can collapse it to the icon rail; the choice persists in localStorage. |
| 640-1023px | Always the icon rail (72px). Icons only, labels as tooltips, no collapse toggle. Done in CSS. |
| < 640px | Off-canvas drawer with full labels, opened by a hamburger in the topbar. Closes on backdrop click, Escape and route change. |

## Workflow

### 1. Discover the app before changing anything

Find, don't assume:
- **Entry and router:** `src/main.(js|ts)`, the router file, and the route list. Every route gets a sidebar link.
- **Current shell:** usually `src/App.vue`. Note the nav markup, its height (for example `height: 70px`), and the global `<style>` block.
- **Layout dependencies on the old nav.** Grep for them and keep the results; each one must be updated:
  ```bash
  grep -rnE "position: *(sticky|fixed)|top: *[0-9]+(px|rem)|100vh|max-width: *[0-9]{4}px" --include='*.vue' src
  ```
  Sticky elements offset by the old nav height (for example a filter bar at `top: 70px`) are the usual breakage.
- **Shared class names** that views rely on (`.card`, `.stat-card`, `.badge.*`, table rules). Keep these names working.
- **Palette:** count the colors already in use so the tokens match the existing brand rather than replacing it:
  ```bash
  grep -rhoE "#[0-9a-fA-F]{6}\b" --include='*.vue' src | tr 'A-F' 'a-f' | sort | uniq -c | sort -rn | head -15
  ```
- **Overlay z-indexes:** modals usually sit at 1000 or more. Shell layers must stay below them.
- **i18n:** if the app has locale files, nav labels go through them, including any label that is currently hardcoded.
- **Project rules:** read `CLAUDE.md` files and `.claude/agents/`. If a project agent owns `.vue` edits, delegate to it.

### 2. Add design tokens

Copy `templates/tokens.css` to `src/styles/tokens.css` and import it once at the top of `main.js`, before `App.vue`. Then:
- Replace the template's colors with the app's dominant ones from step 1. Keep the token names.
- Keep the z-index order: `--z-topbar` < `--z-drawer-backdrop` < `--z-sidebar`, and all of them below the app's modal z-index. The backdrop has to sit under the sidebar, or it covers the open drawer.
- CSS variables can't be used in `@media` queries, so the breakpoints are hardcoded in the CSS. The token file documents them in a comment.

### 3. Rebuild the shell

Adapt `reference/AppShell.vue` into the app's root component:
- One `router-link` per route, each with an inline SVG icon (24x24, `stroke="currentColor"`, no icon library needed) and a `<span class="nav-label">`. Give each link a `:title` so the icon rail shows tooltips.
- Use vue-router's active classes. Match the root route `/` **exactly**; otherwise Overview is highlighted on every page.
- Move the existing header widgets (language switcher, profile menu, notifications) into the topbar's right side, with their props and events unchanged.
- Put any global filter or toolbar directly under the topbar, in the content column, sticky at `top: var(--topbar-h)`.
- Wrap every `localStorage` access in try/catch. It throws in private windows and when storage is blocked, and the app must still render.
- Give `.app-main` `min-width: 0`. Without it, a wide table forces the whole page to scroll sideways.
- Preserve all of the root component's existing script logic. Only add the shell state: collapsed, drawer open, page title.

### 4. Restyle the shared and page styles

- Rewrite the global styles with tokens, **keeping every existing class name**.
- In each view and component's scoped styles, replace hex colors, ad-hoc paddings and radii with tokens. Use the 4px spacing scale only.
- Cards: `--color-surface`, a 1px `--color-border`, `--radius-md`, `--shadow-sm`, and `--space-5` padding. Card header: the title on the left, actions on the right, and a bottom border.
- Grids: `repeat(auto-fit, minmax(<min>, 1fr))` so they reflow beside the sidebar.
- Tables: an uppercase, muted header row, a subtle row hover, and a wrapper with `overflow-x: auto`.
- Leave modal overlays (`position: fixed` and their z-index) alone. Only restyle their panels.
- **Do not edit** template logic, `v-if`/`v-for` conditions, computed values, API calls or event handlers. If a style change seems to need a markup change, keep it to wrapper elements and classes.

### 5. Verify

1. Build: `npx vite build --outDir /tmp/vite-check --emptyOutDir`. This keeps build output out of the repo.
2. Visit every route at 1440px, 800px and 390px, and check that:
   - exactly one sidebar link is active, and it follows the route,
   - collapsing at 1440px persists after a reload; at 800px the rail shows icons and tooltips; at 390px the drawer opens, dims the page, and closes on backdrop click, Escape and navigation,
   - sticky toolbars sit directly under the topbar while scrolling,
   - modals still open above the sidebar and topbar,
   - there is no horizontal page scroll at 390px,
   - existing behavior still works (filters reload data, forms submit, language switching updates the nav labels).
3. Review the diff for any change to script logic. Revert anything that isn't styling or shell state.

## Rules

- Visual changes only. Never change APIs, data shapes or business logic as part of the redesign.
- Keep the app's existing brand colors. Restructure them; don't replace them.
- No emojis in the UI. Icons are inline SVG.
- Every new `v-for` needs a unique key (the route path, never the index).
- Add a short comment wherever shell logic isn't obvious, such as the storage try/catch, the exact match on `/`, and why the drawer ignores the collapsed state.
- Accessibility: buttons have `aria-label`s, the collapse toggle sets `aria-expanded`, the drawer closes on Escape, and the active link gets `aria-current="page"` (vue-router adds it).
- Light theme by default. Tokens make dark mode a later addition: one `prefers-color-scheme` override block in `tokens.css`.
