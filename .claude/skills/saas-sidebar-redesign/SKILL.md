---
name: saas-sidebar-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface, replacing the top navigation bar with a vertical sidebar on the left (collapsible to icons, mobile drawer, grouped sections, optional dark theme) and applying consistent spacing, typography and card styling through shared design tokens. Use this skill whenever the user wants to modernize, restyle, polish or "make professional" a Vue app's look, move navigation from a top bar or header to a left sidebar, add a dashboard-style app shell, or standardize spacing and visual consistency across views, even if they never say "sidebar" or "SaaS".
---

# SaaS Sidebar Redesign for Vue 3

Turn a Vue 3 app with a top navigation bar into a modern SaaS-style interface: a left sidebar, a clean page frame, and one consistent set of spacing, type and color tokens. The goal is a change in structure and polish without changing what the app does.

## Principles

- **Behavior stays put.** Routes, API calls, stores, composables, i18n keys and component props are not yours to change. Move and restyle them; do not rewrite them. A redesign that breaks a filter or a route has failed, however nice it looks.
- **Tokens first, then components.** Inconsistent spacing usually comes from every component picking its own numbers. Define the numbers once as CSS custom properties, then point the shell and shared classes at them. Per-view rewrites become small.
- **Reuse what exists.** The app already has a palette, class names (`.card`, `.badge`, `.stat-card`) and maybe a stated design system in its CLAUDE.md or README. Extend those. Introduce new colors only when the existing ones cannot express a state.
- **Respect project rules.** Read CLAUDE.md files before editing. If they say Vue files must go through a particular subagent, no emojis in the UI, or a specific component style (Options API vs `<script setup>`), follow them. Match the surrounding code's comment density, and add a short comment where logic is non-obvious (for example why the drawer closes on route change).

## Workflow

### 1. Discover

Read before you design. You need to know:

- **Entry and router:** `main.js`/`main.ts`, the router file. List the routes and their labels.
- **Current shell:** the root component (usually `App.vue`): its header/nav markup, its global styles, and what else lives in the header (language switcher, profile menu, search, notifications). Everything in the header needs a new home.
- **Global filter or toolbar components** rendered between header and content. Decide whether they stay at the top of the content area (usual) or move.
- **Existing styling:** where global CSS lives, the palette in use, whether there is already a variables block.
- **i18n:** how labels are produced (`t('nav.x')`). Reuse the keys; add new keys to every locale file, never hardcode English next to translated strings.
- **Component style:** Options API, `<script setup>`, TypeScript or not, so the new components match. Trust the existing components over what a CLAUDE.md says about style, since docs drift (this has happened: a doc said "Composition API" while every component used `export default { setup() }`). Only restyle components written in another style; do not convert them.

Summarise what you found in a few lines to the user before changing anything: routes, what the header contains, and where styles live. If you cannot ask questions (a non-interactive run), do not wait: put the same summary and your navigation grouping in the final report.

Also grep for `sticky`, `position: fixed` and `top:` in the shared components (a filter bar or toolbar often has `top: <old header height>`), not only in views.

### 2. Plan the navigation

Group routes into sections with short labels (for example Overview, Operations, Finance). Two to four groups is typical; a flat list is fine for fewer than six routes. Choose a text-free icon per route as inline SVG, since an icon font or icon package adds a dependency and the user may have rules against emojis. If the project already has an icon library, use that. Show the grouping to the user in one short list and proceed unless they object.

### 3. Add design tokens

Create the tokens block described in `references/design-tokens.md`: spacing scale, radii, shadows, type scale, semantic colors, sidebar dimensions, and the dark variant. Put it where global styles already live, or in a new `styles/tokens.css` imported from the entry file if there is no good home. Map the app's existing palette onto the tokens rather than replacing it.

### 4. Build the shell

Replace the top bar with the layout in `references/sidebar-patterns.md`. In outline:

- A `AppSidebar` component: brand block at the top, grouped `router-link` items with icons and active state, and a footer holding the controls that used to live in the header (language switcher, profile menu).
- An app shell in the root component: sidebar on the left, a scrolling main column on the right, with a slim top region inside the main column for the page title and global filters if the app has them.
- **Collapsible:** toggle between full width and icon-only; persist the choice in `localStorage` inside try/catch, since storage can be unavailable. Show a tooltip (`title`) on icons when collapsed.
- **Mobile:** below the breakpoint, the sidebar becomes an off-canvas drawer opened from a menu button, with a backdrop, closing on route change, backdrop click and Escape.
- **Dark theme option:** a toggle that sets `data-theme="dark"` on the root element, persisted the same way, with the tokens redefined for dark. Respect `prefers-color-scheme` as the default when nothing is saved.
- **Accessibility:** a `<nav aria-label>` landmark, `aria-current="page"` on the active link, visible focus rings, buttons that are real `<button>` elements with `aria-expanded`/`aria-label`.

Give `AppSidebar` a single root element (wrap the `<aside>` and its backdrop together). With two roots the component is a fragment, `$el` becomes a comment node, and any `$el.querySelector` for focus management throws; alternatively expose a `focusFirst()` method.

Styles that cross component boundaries need care in scoped CSS. Rules that depend on the shell's collapsed or drawer state and reach into child components belong in an unscoped `<style>` block (selectors like `.app-shell.is-collapsed .sidebar-label`), or in a modifier class passed down as a prop. To restyle or flip an existing child's popover (language switcher, profile menu), use `:deep()` from the parent rather than editing the child's logic.

Keep the new shell in components that take no data from the views. The sidebar reads the route list and i18n; it should not know about inventory or orders.

### 5. Apply tokens to shared styles

Update the shared classes (page header, cards, stat cards, tables, badges, buttons, form controls, modals) to use the tokens: consistent padding, one radius per surface level, one border color, one shadow per elevation. Do this in the global stylesheet first. Then scan the views for hardcoded values that fight the system (`padding: 17px`, off-palette hex colors, inconsistent gaps) and replace them with tokens. Leave chart internals and data logic alone.

Stay inside "shell plus tokens" unless the user asked for more: do not restructure each view's template or rework charts.

### 6. Verify

Run the app and look at it; a build passing is not enough because layout bugs are invisible to a compiler.

- Start the dev server and open each route at desktop width, in collapsed state, in dark theme, and at a phone width (about 390px). Use browser automation if the project provides it, otherwise ask the user to look.
- Check: no horizontal page scroll, sidebar does not overlap content, active item matches the route (including nested routes), drawer opens and closes, header controls still work, modals sit above the sidebar, text stays readable in dark theme.
- Open your own browser tab first: the automation browser may be shared with other sessions or agents, and navigating someone else's tab corrupts both runs. Prefer small `evaluate` checks (`document.documentElement.scrollWidth`, `getComputedStyle`) over full page snapshots on data-heavy pages.
- Measure `document.documentElement.scrollWidth` against the viewport on every route at 390px. Wide charts, tables and inline filter rows commonly overflow; a fix inside the offending view is allowed even though charts are otherwise left alone (usually `min-width: 0`, `overflow-x: auto` on the container, or `max-width: 100%`). Report it if you leave it.
- Check the browser console for warnings, and run the build (`npm run build`) to catch compile errors.
- Existing tests still pass.

### 7. Report

Tell the user what changed, which files are new, where the tokens live, and how to adjust the brand color or sidebar width (one variable each). Mention anything you chose not to touch, such as chart colors or view layouts, so they can ask for a follow-up.

## Things that commonly go wrong

- **Content hidden behind a fixed sidebar:** use a flex or grid shell where the sidebar takes its own column, rather than `position: fixed` plus guessed margins. A fixed sidebar needs a matching `margin-left` that changes with the collapsed state.
- **Header controls orphaned:** the language switcher, profile menu and similar popovers were designed to open downward from the top. Check they open in a sensible direction from the sidebar footer (usually upward), and that they are not clipped by `overflow: hidden`.
- **Sticky or full-height elements** inside views that assumed `100vh` minus a header height now overflow. Search for `100vh` and `top:` offsets.
- **z-index collisions:** modals must stay above the drawer backdrop, and the drawer must stay above its own backdrop. Define z-index layers as tokens, and match the app's existing modal z-index rather than assuming a value.
- **Closed drawer still focusable:** an off-screen drawer moved with `transform` alone stays in the tab order. Hide it with `visibility: hidden` once closed.
- **Dark-mode invisible elements:** hardcoded dark fills (a bar or legend dot in `#0f172a`) vanish on a dark page. Look at charts and legends in dark theme, not just cards and text.
- **Dark theme gaps:** hardcoded white backgrounds and dark text in individual views stay unchanged in dark mode. Grep for literal `#fff`, `white` and the old palette hexes, and swap them for tokens. That bulk swap is a mechanical, style-only change and is within scope when the user wants the dark option. If the user did not ask for dark theme and many literals remain, leave the toggle out rather than ship a half-themed one, and say so in the report. Soft status backgrounds (yellow/red tints) and `color: white` on buttons are easy to miss.
- **Wide filter rows:** a row of several inline selects that fit under a top nav can overflow once a 248px sidebar takes width. Let it wrap (`flex-wrap: wrap`), and reset any sticky `top:` that assumed the old header.
- **Active link on `/` and nested routes:** `router-link-active` matches `/` on every page and does not distinguish nested routes. Use the exact-active class for `/`, or a small `isActive(path)` helper.
- **Resize across the breakpoint:** the drawer's `transform` transition makes the sidebar visibly slide out when the window crosses the breakpoint. Minor; disable the transition inside a `@media (min-width: 901px)` rule if it bothers you.
- **Layout flash on reload:** read the saved collapsed/theme state before first render (initialize the ref from storage) so the page does not jump.
