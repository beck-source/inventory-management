---
name: saas-redesign
description: Redesign a Vue 3 application's UI into a modern SaaS-style interface - replaces a top navigation bar with a vertical left sidebar, introduces design tokens for consistent spacing/typography/color, and polishes every view to a professional standard without changing behavior. Use when asked to modernize, restyle, or "make the app look like a SaaS product", or to move navigation into a sidebar.
---

# SaaS UI Redesign (Vue 3)

Turn an existing Vue 3 app into a polished SaaS-style interface:

- **Vertical sidebar** on the left replaces the top nav bar (collapsible on desktop, off-canvas on mobile)
- **Design tokens** (CSS custom properties) for color, spacing, radius, shadow, and type
- **Consistent spacing** on a 4px grid across every view
- **Professional polish**: clear hierarchy, quiet borders, real hover/focus states, responsive layout

This is a **visual redesign only**. Routes, data flow, API calls, filters, i18n, events, and modals must work exactly as before.

Templates and token values live in [references/design-system.md](references/design-system.md). Read it before Step 3.

## Ground Rules

1. **Behavior is frozen.** Don't change business logic, API calls, store/composable state, route paths, or emitted events. If a markup change forces a logic change (for example, nav state moving into a new component), keep the change minimal and comment why.
2. **Follow project instructions first.** Read the root and client `CLAUDE.md` files. If they require delegating `.vue` work to an agent (this repo requires `vue-expert`), send each implementation step to that agent with a precise brief: the files to touch, the token file, and these ground rules. Include the rule "document non-obvious logic changes with comments".
3. **No new dependencies** unless the user approves. Use inline SVG for icons and plain CSS for styling, with no UI kits, Tailwind, or icon packages.
4. **Keep the existing palette** unless the user asks for a new one. Map the app's current colors onto the tokens so the result is a refinement, not a rebrand.
5. **No emojis** in the UI.
6. **Comment non-obvious decisions**: layout hacks, `minmax(0, 1fr)`, z-index layering, breakpoint logic, active-route matching, and anything else a reader would question.
7. **Work incrementally.** Shell first, then views one at a time, checking after each. Never rewrite every file in one pass.

## Workflow

### Step 1: Audit the current UI

Before changing anything, find and record:

- **App shell**: usually `src/App.vue` or `src/layouts/*`. Note where the top nav, header widgets (profile menu, language switcher, search, notifications), global filter bars, and `<router-view>` sit.
- **Navigation items**: the route paths, labels (including i18n keys such as `t('nav.inventory')`), and how the active state is computed.
- **Router config**: `src/main.js` or `src/router/*`, to get the full route list and spot routes missing from the nav.
- **Global styles**: where they live (often an unscoped `<style>` in `App.vue` or `src/assets/*.css`), and which shared classes views depend on (`.card`, `.stat-card`, `.page-header`, `.badge`, tables, and so on).
- **Hard-coded values**: run a grep for ad-hoc spacing and colors to scope the normalization pass:
  ```bash
  grep -rnoE "(padding|margin|gap):[^;]+;" src --include=*.vue | sort | uniq -c | sort -rn | head -40
  grep -rnoE "#[0-9a-fA-F]{3,8}\b" src --include=*.vue | awk -F: '{print $NF}' | sort | uniq -c | sort -rn | head -30
  ```
- **Behavior to preserve**: modal open/close wiring, events from header components, and anything sticky or fixed-position.

Give the user a short audit summary and the planned layout before editing. Only ask a question when the answer changes the design, for example a light vs dark sidebar or whether a new brand color is wanted. Otherwise use the defaults in the reference file.

### Step 2: Capture a baseline

Make sure the dev servers are running (use the project's `start` skill or command if it has one). Then use Playwright MCP to screenshot every route at **1440px** and **390px** width, and save them as `baseline-<route>-<width>.png`. These are used for the before/after comparison and to catch regressions.

Also record the console state with `browser_console_messages`, so that only *new* errors count as regressions.

### Step 3: Introduce design tokens

Add the token block from the reference file to the global stylesheet, mapped to the app's existing colors. Then convert the **existing global classes** (cards, stat cards, tables, badges, page header, buttons, inputs) to use tokens. This one change restyles much of the app at once.

Don't touch individual views yet.

### Step 4: Build the sidebar and app shell

Follow the templates in the reference file:

1. Create `AppSidebar.vue` with the brand area, nav items with inline SVG icons, and a footer slot. Nav items come from the same paths and labels the old top nav used, so keep the i18n keys.
2. Restructure the shell into a CSS Grid: `sidebar | main column`. The main column holds a slim **top bar** (page title or breadcrumb on the left; existing header widgets such as the language switcher and profile menu on the right) and then the content area.
3. Move existing global filter bars into the top bar or directly under it, inside the main column, never across the full width above the sidebar.
4. Add a **desktop collapse** toggle (icon-only sidebar, with labels in `title` tooltips). Persist the state in `localStorage` wrapped in try/catch.
5. Add a **mobile off-canvas** sidebar below 1024px: a menu button in the top bar, a backdrop, and close on navigate, on backdrop click, and on Escape.
6. Delete the old top-nav markup and its CSS. Don't leave dead styles behind.

Check in the browser: every nav link routes correctly, the active state is right (including `/` not matching every route), the header widgets and modals still work, and there's no horizontal scroll.

### Step 5: Normalize each view

Go through the views **one at a time**. For each view:

- Use the standard page header pattern (title, optional description, optional actions on the right).
- Replace ad-hoc padding, margin, gap, font-size, and color values with tokens, using the spacing rules in the reference file.
- Use one consistent card treatment and grid gaps.
- Use `font-variant-numeric: tabular-nums` for metric values and numeric table columns.
- Make sure loading, error, and empty states use the shared styles.
- Leave chart *logic* alone. Only restyle axes, labels, gridlines, and colors through tokens.

After each view, screenshot it at 1440px and 390px and compare against the baseline. Fix anything that broke before moving on.

### Step 6: Polish pass

Go through the polish checklist in the reference file: focus-visible rings, hover states, transitions, reduced motion, contrast, and consistent radii and borders.

### Step 7: Verify

With Playwright, for **every route** at 1440px, 1024px, and 390px:

- The page renders with no new console errors.
- The sidebar link routes correctly and shows the active state with `aria-current="page"`.
- Collapse and expand work on desktop, and the state survives a reload.
- The off-canvas menu opens and closes on mobile (menu button, backdrop, Escape, navigating).
- Global filters still change the data.
- Modals and dropdowns open above the sidebar (check z-index).
- There's no horizontal page scroll, except inside table containers that are meant to scroll.

Keyboard check: Tab moves through the sidebar, top bar, then content in order, and every interactive element has a visible focus ring.

### Step 8: Report

Tell the user:

- What changed: the shell, the token file location, and which views were normalized.
- Before/after screenshots for the main routes, or their file paths.
- Anything you couldn't finish or that needs a decision: hard-coded strings found (for example a nav label not using i18n), routes with no nav entry, or charts with colors that clash with the tokens.
- That behavior wasn't changed, and how you checked that.

Don't commit unless the user asks. If they do, commit in logical steps (tokens, shell, views, polish).
