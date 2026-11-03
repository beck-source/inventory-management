---
name: saas-sidebar-layout
description: Redesign a Vue 3 app's UI into a modern SaaS-style layout with a vertical navigation sidebar on the left instead of a top nav bar, consistent spacing, and a polished professional look. Use when asked to restyle the app shell, move navigation to a sidebar, or make the UI look more like a modern SaaS dashboard.
---

# SaaS Sidebar Layout

Turn the top navigation bar in `client/src/App.vue` into a left-hand vertical sidebar, then bring the rest of the shell and pages onto one spacing and type system. This changes presentation only. Routes, API calls, data, and i18n keys stay the same.

## When to use

- The user asks for a sidebar, a SaaS look, a modern dashboard layout, or consistent spacing.
- The user asks to redesign the app shell or navigation.

Do not use it for changes to a single component's content or behavior.

## Project rules that apply

- **`.vue` files go to vue-expert.** Per the project `CLAUDE.md`, any time you create or significantly modify a `.vue` file, delegate that work to the `vue-expert` agent. Give it this skill's spec, not your own conclusions. You may edit `.js` files (for example `main.js` or locale files) directly.
- **Keep the palette.** Use the slate/gray tokens from `CLAUDE.md`: `#0f172a` (text and sidebar), `#64748b` (muted text), `#e2e8f0` (borders). Status colors are green, blue, yellow, and red.
- **No emojis in the UI.** Use text or inline SVG icons.
- **Keep the existing structure.** Do not rename routes, change `t('...')` keys, or edit the `api.js` contract. Keep `<router-view />`, `FilterBar`, `LanguageSwitcher`, `ProfileMenu`, and the modals.

## Steps

### 1. Audit the current shell

Read these before changing anything:

- `client/src/App.vue`: the header, the `nav-tabs` router links, and the global styles at the bottom (the `<style>` block starts near line 167).
- `client/src/main.js`: the route list.
- `client/src/components/FilterBar.vue`, `LanguageSwitcher.vue`, and `ProfileMenu.vue`: their placement and any header-specific sizing.
- Two or three views (for example `Dashboard.vue` and `Orders.vue`) to see how they pad and size their own content.

Note the current nav items, their order, and their `t()` keys. Restocking and Reports are included; check which items use hardcoded English labels.

### 2. Design the shell

Use this structure:

```
.app (CSS grid: sidebar | content)
├── aside.sidebar          (fixed width ~240px, full height, dark slate)
│   ├── brand block        (company name, subtitle)
│   ├── nav                (router-links as vertical items, active state)
│   └── footer             (LanguageSwitcher, ProfileMenu)
└── div.workspace
    ├── header.topbar      (slim: page title, FilterBar, actions)
    └── main.main-content  (<router-view />)
```

- Sidebar items are full-width rows with an icon slot, label, and an active state (background tint plus a left accent bar in blue).
- Put `LanguageSwitcher` and `ProfileMenu` at the bottom of the sidebar, not in the top bar.
- Keep `FilterBar` in the top bar or directly above the content. Do not move it into the sidebar.
- Under 768px, hide the sidebar behind a menu button that opens it as a drawer. Close the drawer on route change.

### 3. Spacing and typography

- Use a 4px base scale: 4, 8, 12, 16, 24, 32, 48. Use only these values for padding, margin, and gap.
- Set one type scale: page title 24px semibold, section heading 16px semibold, body 14px, caption 12px. Use the same scale in every view.
- Give cards one radius (for example 8px), one border (`1px solid #e2e8f0`), and one shadow level (none or subtle).
- Page content gets one horizontal padding (for example 24px) and a max width (for example 1280px), centered.

### 4. Apply the look

- Background: `#f8fafc` for the content area, white for cards and tables.
- Tables: sticky header, row dividers, no zebra stripes, numeric columns right-aligned.
- Buttons: one primary style (solid slate or blue), one secondary style (outline), consistent heights (36px).
- Focus rings must stay visible for keyboard users.

### 5. Implementation order

1. Update the global styles in `App.vue` (tokens, spacing, base typography). Delegate the `.vue` edit to vue-expert.
2. Convert the header and nav into the sidebar layout in `App.vue`. Delegate to vue-expert.
3. Restyle the shared components (`FilterBar`, `LanguageSwitcher`, `ProfileMenu`) to fit the sidebar and top bar. Delegate to vue-expert.
4. Apply the spacing and type scale to each view. Do this in small batches, one or two views per vue-expert task, so each review stays small.

### 6. Verify

- Run `cd client && npm run build`. It must pass.
- Check every route in the browser (`/`, `/inventory`, `/orders`, `/spending`, `/demand`, `/restocking`, `/reports`) at desktop width and at 375px. Use the Playwright MCP tools against `http://localhost:3000`. If the browser tool fails, say so and stop short of claiming visual checks.
- Confirm the active nav item matches the current route, and the language switch still works in both `en` and `ja`.
- Confirm no route, API call, or data-loading behavior changed. Run `cd server && uv run pytest ../tests/backend -c ../tests/pytest.ini` to confirm the backend is untouched.

## Anti-patterns

- Adding a UI library or CSS framework. The project has no dependencies for styling, and this change should not add one.
- Mixing spacing values outside the 4px scale.
- Leaving the top nav in place alongside the sidebar.
- Changing `t()` keys or route paths to fit the new layout.
- Redesigning a view's data or charts. Only restyle them.
