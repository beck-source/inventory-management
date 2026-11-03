---
name: vue-saas-redesign
description: Redesign a Vue 3 app's UI into a modern SaaS-style interface - replace the top navigation bar with a vertical left sidebar, introduce design tokens (CSS variables), a consistent spacing scale, and polished page headers, cards, tables and filter bars. Use this skill whenever the user wants to modernize, restyle, polish or "make it look like a SaaS product" for a Vue 3 frontend, asks for a left sidebar or side navigation instead of a top nav/navbar, wants consistent spacing or a more professional look, or says things like "redesign the UI", "dashboard layout", "app shell", or "admin template look", even if they do not name the skill.
---

# Vue 3 SaaS redesign

Turn a Vue 3 app with a top nav into a modern SaaS app shell: fixed left sidebar, a content area with consistent page headers and spacing, and a small set of design tokens that every view uses.

The goal is a presentation-only change. Routes, state, API calls, i18n keys, and tests keep working exactly as before. Reviewers trust a redesign only if they can see that nothing behavioral moved, so keep the diff to templates and styles.

## Workflow

### 1. Survey before touching anything

Read, do not guess:
- The root component (usually `App.vue`) - find the top nav, router links, header widgets (language switcher, profile menu), global filter bars, and `<router-view>`.
- Router config and the list of views, so the sidebar covers every route.
- How styling is done (global CSS in `App.vue`, scoped styles, Tailwind, a UI library). Match it instead of introducing a second system.
- Existing colors, fonts and radii. Collect the palette in use (e.g. slate text, blue accent, status colors). Keep it: the user's brand should survive the redesign.
- Project instructions (CLAUDE.md): honor rules such as "no emojis in UI", "use X agent for .vue files", i18n requirements, or required keys in `v-for`.

If the dev server can run, take "before" screenshots of 2-3 representative views (a dashboard, a table view, a view with filters) so you can compare afterwards.

### 2. Define tokens first

Add CSS variables on `:root` (in the global stylesheet) before restyling components, so every later change references tokens rather than magic numbers. Use `references/templates.md` for the token block. Rules:
- Seed color tokens from the palette you found in step 1, not from the template defaults.
- One spacing scale (4px base: 4, 8, 12, 16, 24, 32, 48) and one radius/shadow set. Consistency is what reads as "polished"; a hundred slightly different paddings is what reads as "template mashup".
- Replace hard-coded values in the files you touch with tokens. Do not sweep untouched files just to rename values.

### 3. Build the app shell

Layout: `[sidebar | main column]`, where the main column holds an optional top bar and the page content.

- Move the nav links into a sidebar component or section: brand/logo at top, nav items grouped with small section labels where the app has natural groups, user/profile and language controls pinned at the bottom (or in a slim top bar if the app already has many header widgets).
- Keep every existing route link and its i18n label. Use `router-link` with `exact-active-class`/`active-class` for the active state rather than recomputing from `$route.path`, unless the existing code needs custom logic.
- Fixed width around 240px, sticky full height, its own scroll if the list overflows. Main content gets `margin-left`/grid column for that width and a max content width with consistent padding.
- Icons: use small inline SVG (stroke style, 20px, `currentColor`) so they follow the text color and need no dependency. If the project forbids emojis in the UI, that also rules out emoji as icons.
- Move the global filter bar (if any) into the content area beneath the page header, not the sidebar; filters are page context, not navigation.

Responsive and accessibility, which are the parts people skip and then regret:
- Below ~1024px collapse the sidebar into an off-canvas drawer opened by a hamburger button in a top bar; close it on route change and on backdrop click or Escape.
- Optionally support a collapsed icon-only mode on desktop; persist the choice in `localStorage` wrapped in try/catch.
- Use a `<nav aria-label="Main">`, `aria-current="page"` on the active link (router-link sets this), visible `:focus-visible` outlines, and buttons for the toggle with `aria-expanded`.

### 4. Polish the pages

Apply the tokens consistently across views:
- A page header pattern: title, short description, and actions on the right.
- Cards: surface background, 1px border, token radius, token padding, subtle shadow only.
- Tables: sticky or clearly separated header row, row hover, right-aligned numbers, consistent cell padding.
- Buttons, inputs and selects: shared height and radius; one primary style, one secondary.
- Status colors stay semantic (green/blue/yellow/red) with soft background + strong text pairs for badges.
- Typography: one scale, tabular numerals for figures.

Work view by view and keep each change small. If a project rule says `.vue` files must be edited by a specialist agent, delegate to it with this skill's step list as the brief.

### 5. Verify

- Run the app and compare against the "before" screenshots at desktop (1440), tablet (~900) and mobile (~390) widths. Use the project's browser tooling (e.g. Playwright MCP) when present.
- Click through every nav item: each route loads, the active state is correct, the drawer closes on navigation.
- Check the browser console for new warnings and run the existing frontend tests and build. A redesign that breaks `npm run build` is not done.
- Report what changed, which files, and anything you intentionally left alone (e.g. modals or charts that need a separate pass).

## Things that go wrong

- Introducing a new color palette uninvited. Preserve the existing one; offer alternatives only if asked.
- Sidebar `position: fixed` without offsetting the main content, so content hides underneath it.
- Using `100vw` for layout widths, which causes horizontal scroll from the scrollbar; use `100%` or grid.
- Deleting header widgets (language switcher, profile menu) instead of relocating them.
- Hard-coding link labels; keep using the app's i18n function.
- Over-reaching into data logic. If something looks like a bug outside presentation, mention it rather than fixing it in the redesign diff.

See `references/templates.md` for the token block, sidebar markup, and shell CSS to adapt.
