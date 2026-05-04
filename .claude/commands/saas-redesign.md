---
description: Redesign a Vue 3 app's UI into a modern SaaS-style interface with a vertical left sidebar navigation
---

Redesign this Vue 3 application's UI into a polished, modern SaaS-style interface. Replace the top navigation bar with a vertical sidebar on the left. Follow every step below in order.

---

## Step 1 — Analyse the current layout

Read the following files before touching anything:
- `client/src/App.vue` — understand the current nav structure, routes referenced, and all existing CSS custom properties
- `client/src/main.js` — extract the full route list (path + component name)
- Any CSS files imported globally (check `main.js` imports)

Record:
- Every nav link (label, path, icon if any)
- All CSS custom properties (`--*`) already defined
- The current colour palette (background, surface, text, accent)

---

## Step 2 — Design the new layout structure

The new layout must follow this shell structure inside `App.vue`:

```
┌──────────────────────────────────────────────────┐
│  Sidebar (240px fixed)  │  Main content area      │
│                         │                         │
│  [Logo / App name]      │  <router-view />        │
│                         │                         │
│  Nav items (icons +     │                         │
│  labels, active state)  │                         │
│                         │                         │
│  ── bottom ──           │                         │
│  [User / profile area]  │                         │
└──────────────────────────────────────────────────┘
```

Rules:
- Sidebar width: `240px`, fixed/sticky, full viewport height
- Sidebar does NOT scroll with content; main area scrolls independently
- Active nav item gets a solid left border accent (`3–4px`) and highlighted background
- Each nav item has an SVG icon (inline, `18px`) to the left of the label
- Group nav items logically if there are more than 5 (e.g. a thin `<hr>` separator)
- Bottom of sidebar: user avatar / initials circle + name + a settings or logout icon

---

## Step 3 — Define the design tokens

Replace (or extend) the CSS custom properties in `App.vue`'s `<style>` with this token set. Adapt the specific colour values to match or complement the app's existing palette — do not blindly paste; choose values that look cohesive:

```css
:root {
  /* Sidebar */
  --sidebar-width: 240px;
  --sidebar-bg: #0f172a;          /* deep navy — adjust if existing palette differs */
  --sidebar-text: #94a3b8;
  --sidebar-text-active: #f1f5f9;
  --sidebar-active-bg: rgba(255,255,255,0.07);
  --sidebar-active-border: #3b82f6;  /* accent colour */
  --sidebar-hover-bg: rgba(255,255,255,0.04);

  /* Main content */
  --content-bg: #f8fafc;
  --surface: #ffffff;
  --surface-border: #e2e8f0;

  /* Typography */
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;

  /* Spacing scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Shadow */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04);
}
```

---

## Step 4 — Rewrite App.vue

**MANDATORY: Delegate this entire step to the `vue-expert` agent.**

Prompt for the vue-expert:

> Rewrite `client/src/App.vue` to implement a vertical left sidebar layout using the design tokens defined in Step 3. Requirements:
>
> - Outer shell: CSS Grid `grid-template-columns: var(--sidebar-width) 1fr`, `min-height: 100vh`
> - Sidebar (`<nav>`): fixed left column, flex column, `background: var(--sidebar-bg)`, no top header bar
> - Top of sidebar: app logo or name in `var(--sidebar-text-active)`, `font-weight: 700`
> - Nav items: `router-link` components, flex row with icon + label, `padding: var(--space-3) var(--space-4)`, `border-radius: var(--radius-md)`, hover and active states using CSS variables
> - Active state detection: `:class="{ active: $route.path === item.path }"` pattern
> - Bottom user area: initials avatar circle (`32px`, accent background), user name, optional icon
> - Main content: `background: var(--content-bg)`, `overflow-y: auto`, `padding: var(--space-8)`
> - Remove ALL top navigation bar markup and styles
> - Keep the existing `<FilterBar />`, `<ProfileMenu />`, `<LanguageSwitcher />`, and modal components — move any header-area components into the sidebar bottom section or a slim top bar inside `<main>` if needed
> - Apply `box-sizing: border-box` globally; reset `margin`/`padding` on `body` and `#app`
> - Use scoped styles throughout

---

## Step 5 — Apply consistent card and content styles

**MANDATORY: Delegate to `vue-expert` for any `.vue` file changes.**

For every view file in `client/src/views/`, ensure:

1. **Page header**: each view's top section uses:
   ```css
   .page-header { margin-bottom: var(--space-8); }
   .page-title  { font-size: 1.5rem; font-weight: 700; color: var(--text-primary); }
   .page-subtitle { font-size: 0.875rem; color: var(--text-secondary); margin-top: var(--space-1); }
   ```

2. **Stat cards**: uniform card shell:
   ```css
   .stat-card {
     background: var(--surface);
     border: 1px solid var(--surface-border);
     border-radius: var(--radius-lg);
     padding: var(--space-6);
     box-shadow: var(--shadow-sm);
   }
   ```

3. **Tables**: remove hard-coded background colours; use:
   ```css
   table   { background: var(--surface); border-radius: var(--radius-lg); overflow: hidden; }
   thead   { background: #f8fafc; }
   th, td  { padding: var(--space-3) var(--space-4); border-bottom: 1px solid var(--surface-border); }
   ```

4. **Buttons**: primary buttons use `--sidebar-active-border` as background; secondary use outlined style.

5. **Badges / status pills**: keep existing colour logic but set `border-radius: 999px` and `font-size: 0.7rem`.

Only update styles that conflict with the new layout or are hard-coded in ways that break consistency. Do not rewrite component logic.

---

## Step 6 — Verify in browser

Use Playwright MCP tools to verify the result at `http://localhost:3000`:

1. Take a screenshot of the home/dashboard route — confirm sidebar is visible on the left, no top nav bar
2. Click each nav item — confirm active state highlights and route changes
3. Resize the viewport to 1280×800 — confirm no layout breakage
4. Take a screenshot of at least one data-heavy view (e.g. `/orders` or `/inventory`) — confirm cards and tables render with the new token-based styles

Report any issues found and fix them before declaring the redesign complete.

---

## Step 7 — Summary

After all changes are applied, output:
- List of files modified
- Before/after description of the layout change
- Any tokens that were adjusted from the defaults and why
- Any components that needed special treatment (e.g. modals, FilterBar placement)
