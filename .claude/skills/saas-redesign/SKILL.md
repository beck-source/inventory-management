---
name: saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface with a vertical navigation sidebar on the left instead of a top nav bar, consistent spacing, and a polished professional look. Use when asked to redesign, modernize, restyle or "make it look like a SaaS app", or to move navigation from a top bar to a sidebar, in a Vue 3 project. Visual changes only; does not alter routes, logic or data fetching.
---

# SaaS Redesign for Vue 3

Turns a Vue 3 app with a top navigation bar into a sidebar-based SaaS layout with a consistent design system. The work is visual only: templates and styles change, behavior does not.

Reference files (read them when you reach the matching step):
- `references/design-tokens.md` for the spacing, type, radius, shadow and color scales
- `references/sidebar-layout.md` for the app shell, nav item states and the mobile drawer
- `references/component-patterns.md` for page headers, cards, tables, buttons, badges, forms and modals

## Rules that always apply

1. **Project rules win.** Read `CLAUDE.md` (root and client) and any token or theme file first. If the project already defines a palette, status colors, icon policy (for example "no emojis") or says certain files must be edited by a specific agent, follow that. Use this skill's defaults only where the project is silent.
2. **Visual only.** Do not change `<script>` logic, props, emits, composables, API calls, router config, route paths or locale keys. The one exception is the sidebar's open and collapsed state described in step 3. Do not rename or remove existing `router-link` targets, event handlers or `v-model` bindings. If a change needs logic, stop and tell the user instead.
3. **Keep the framework conventions already in use.** If the project uses the Composition API, stay in it. Keep `v-for` keys unique and stable.
4. **No new dependencies.** Use CSS custom properties and inline SVG icons. Do not add a UI library or icon package unless the user asks.
5. **Tokens, not literals.** Every color, space, radius and shadow in new or touched CSS comes from a token. Add a short comment wherever a value is non-obvious (for example why a z-index or a breakpoint was chosen).

## Workflow

### 1. Discover
Find and read, in this order:
- The shell component: the file containing `<router-view />` (usually `App.vue`).
- The router: route paths and which view each loads.
- Global styles: `App.vue` style blocks, `src/assets`, `src/styles`, `index.html`.
- Nav labels: plain text, or an i18n call such as `t('nav.x')`. Reuse the same expression.
- Header controls to relocate: language switcher, profile menu, search, notifications.
- Page-level bars that sit between the nav and the content, such as a filter bar.

Write a short inventory for yourself: routes, controls to move, existing palette, existing breakpoints. Work from it.

### 2. Define tokens
Read `references/design-tokens.md`. Add the tokens once, on `:root`, in the shell's global style block or one shared stylesheet. Map the project's existing palette onto the token names instead of introducing a second palette. If the app has a dark mode, define dark values in the same token set.

### 3. Build the shell
Read `references/sidebar-layout.md`. Replace the top nav with a two-column shell: a fixed-width sidebar and a scrollable main column.
- Sidebar contents: brand at the top, nav links in the middle, language and profile controls at the bottom.
- Reuse the existing `router-link` elements and label expressions. Active state uses `router-link-active` or the project's existing `$route` check.
- Give each nav item an inline SVG icon and a visible label, with the same label as a `title` tooltip.
- The sidebar is collapsible. At 1200px and up it starts expanded and a toggle collapses it to an icons-only rail (about 64px). From 901px to 1199px it starts as the rail. At 900px and below it becomes an off-canvas drawer opened by a menu button, always with labels. The collapsed choice is saved in `localStorage`, inside try/catch.
- Hidden labels stay in the DOM, visually hidden, so screen readers keep each link's name.
- The shell state is two refs, `sidebarOpen` (drawer) and `sidebarCollapsed` (icons-only), plus a `watch` to save the choice. These are the only script changes the skill makes; reuse existing flags if the shell has them, and list them in the summary.
- Move a page-level filter bar into a sticky toolbar at the top of the main column.

### 4. Restyle the views
Read `references/component-patterns.md`. Go view by view, editing scoped CSS and class names so that headers, cards, tables, buttons, badges, inputs and modals match one pattern. Replace one-off spacing and color values with tokens. Do not restructure data loading or computed logic.

### 5. Verify
- Run the project's build (for example `npm run build`) and fix any errors you introduced.
- Start the dev server and open every route at about 1440px (expanded), about 1000px (icons-only rail) and about 390px (drawer) wide. At 1440px also click the collapse toggle and reload to confirm the choice persists. Prefer Playwright if the session provides it.
- Check: no horizontal page scroll, no clipped text, the active nav item matches the route, the drawer opens and closes on phone width, no new console errors.
- Run `git diff --stat` and confirm no changes to router, API client, composables or locale files, and that `<script>` blocks are unchanged apart from the drawer toggle if you added one.

### 6. Report
Summarize what changed, which routes were checked at which widths, and anything not checked. List any place where the old design depended on logic you chose not to change.

## Quality bar

- One spacing scale, one type scale, one radius set. A reviewer should not find a stray `13px` or `#3a3a3a`.
- Borders and whitespace separate content; use shadows sparingly so hierarchy stays readable.
- Numbers in tables and stat tiles use tabular figures and right alignment.
- Every interactive element has hover, focus-visible and disabled states.
- Text contrast meets WCAG AA in every theme the app supports.
