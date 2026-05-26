---
description: Redesign a Vue 3 app's UI into a modern SaaS-style interface with a vertical sidebar, design tokens, and consistent spacing
---

# Redesign UI — SaaS Sidebar Layout

Transform the current top-navbar layout into a modern SaaS-style interface: fixed vertical sidebar on the left, consistent spacing via CSS design tokens, and a polished professional look. The main content area occupies the remaining width to the right of the sidebar.

---

## Step 1: Read Before Touching Anything

Read these files first so you have the exact current state:
- `client/src/App.vue` — current layout shell, nav links, global styles
- `client/src/components/FilterBar.vue` — sticky positioning to adjust
- `client/src/main.js` — all route paths and component imports

Note: every view in `client/src/views/*.vue` lives inside `<router-view>` and requires **no changes** — they automatically inherit the new layout.

---

## Step 2: Delegation Rule

**MANDATORY**: You must delegate ALL `.vue` file changes to the `vue-expert` subagent. Do not edit `.vue` files directly. For each file, write a single detailed prompt to `vue-expert` that includes the full specification from the steps below.

---

## Step 3: Redesign `App.vue`

Delegate to `vue-expert` with the following specification:

### New template structure

Replace the existing template with this shape:

```
<div class="app">
  <aside class="sidebar">
    <div class="sidebar-brand">       <!-- logo + subtitle -->
    <nav class="sidebar-nav">         <!-- router-link list -->
    <div class="sidebar-footer">      <!-- language switcher + profile menu -->
  </aside>

  <div class="main-wrapper">
    <FilterBar />                     <!-- sticky toolbar, top: 0 within wrapper -->
    <main class="main-content">
      <router-view />
    </main>
  </div>

  <!-- Keep all existing modal components unchanged -->
  <ProfileDetailsModal ... />
  <TasksModal ... />
</div>
```

### Sidebar nav links

Use the same routes and i18n keys as the current top nav tabs. Apply `exact-active-class="active"` on the `/` (dashboard) route-link and `active-class="active"` on all others, so Vue Router controls the active state automatically.

### New global CSS (replace or extend the existing `<style>` block — keep it non-scoped)

```css
/* ── Design tokens ──────────────────────────────────── */
:root {
  --sidebar-width: 240px;
  --content-max-width: 1600px;

  --color-sidebar-bg:          #0f172a;
  --color-sidebar-text:        #94a3b8;
  --color-sidebar-text-active: #ffffff;
  --color-sidebar-accent:      #3b82f6;
  --color-sidebar-hover-bg:    rgba(255, 255, 255, 0.06);
  --color-sidebar-active-bg:   rgba(59, 130, 246, 0.15);

  --color-bg:           #f1f5f9;
  --color-surface:      #ffffff;
  --color-border:       #e2e8f0;
  --color-text-primary: #0f172a;
  --color-text-secondary: #64748b;
  --color-primary:      #2563eb;
  --color-primary-hover: #1d4ed8;

  --space-1:  0.25rem;
  --space-2:  0.5rem;
  --space-3:  0.75rem;
  --space-4:  1rem;
  --space-6:  1.5rem;
  --space-8:  2rem;
  --space-12: 3rem;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
}

/* ── Reset & base ───────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--color-bg);
  color: var(--color-text-primary);
  -webkit-font-smoothing: antialiased;
}

/* ── App shell ──────────────────────────────────────── */
.app {
  display: flex;
  min-height: 100vh;
}

/* ── Sidebar ────────────────────────────────────────── */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: var(--sidebar-width);
  background: var(--color-sidebar-bg);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

.sidebar-brand {
  padding: var(--space-6) var(--space-6) var(--space-4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-brand h1 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-sidebar-text-active);
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.sidebar-brand span {
  display: block;
  margin-top: var(--space-1);
  font-size: 0.7rem;
  color: var(--color-sidebar-text);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-sidebar-text);
  text-decoration: none;
  transition: background 0.15s ease, color 0.15s ease;
  position: relative;
}

.sidebar-nav a:hover {
  background: var(--color-sidebar-hover-bg);
  color: var(--color-sidebar-text-active);
}

.sidebar-nav a.active {
  background: var(--color-sidebar-active-bg);
  color: var(--color-sidebar-text-active);
  font-weight: 600;
}

/* Left accent bar on active item */
.sidebar-nav a.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 20%;
  height: 60%;
  width: 3px;
  background: var(--color-sidebar-accent);
  border-radius: 0 2px 2px 0;
}

.sidebar-footer {
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* ── Main wrapper ───────────────────────────────────── */
.main-wrapper {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-width: 0; /* prevent flex overflow */
}

/* ── Main content ───────────────────────────────────── */
.main-content {
  flex: 1;
  padding: var(--space-8) var(--space-8);
  max-width: var(--content-max-width);
  width: 100%;
}

/* ── Cards & surfaces (global) ──────────────────────── */
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

/* ── Stat cards ─────────────────────────────────────── */
.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  transition: box-shadow 0.15s ease;
}
.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.stat-card.success { border-top: 3px solid #10b981; }
.stat-card.warning { border-top: 3px solid #f59e0b; }
.stat-card.danger  { border-top: 3px solid #ef4444; }
.stat-card.info    { border-top: 3px solid #3b82f6; }

/* ── Badges ─────────────────────────────────────────── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2em 0.6em;
  border-radius: var(--radius-sm);
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.badge.success { background: #dcfce7; color: #15803d; }
.badge.warning { background: #fef3c7; color: #b45309; }
.badge.danger  { background: #fee2e2; color: #b91c1c; }
.badge.info    { background: #dbeafe; color: #1d4ed8; }

/* ── Tables ─────────────────────────────────────────── */
.table-container { overflow-x: auto; }

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
thead th {
  padding: var(--space-3) var(--space-4);
  background: #f8fafc;
  border-bottom: 1px solid var(--color-border);
  text-align: left;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-secondary);
}
tbody td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
}
tbody tr:last-child td { border-bottom: none; }
.clickable-row { cursor: pointer; }
.clickable-row:hover td { background: #f8fafc; }

/* ── Page headers ───────────────────────────────────── */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-6);
}
.page-header h2 {
  margin: 0;
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}
.page-header p {
  margin: var(--space-1) 0 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

/* ── State messages ─────────────────────────────────── */
.loading, .error, .no-data, .no-backlog {
  padding: var(--space-12);
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}
.error { color: #b91c1c; }
```

---

## Step 4: Update `FilterBar.vue`

Delegate to `vue-expert` with this specification:

The FilterBar is now positioned inside `.main-wrapper` (not below a top nav). Update its sticky positioning:

- Change `position: sticky; top: 70px;` → `position: sticky; top: 0;`
- Keep `z-index: 90` (below the sidebar's z-index: 100)
- Remove any `margin-top` that compensated for the top nav height
- The filter bar background should remain white/surface so it visually separates from content when scrolling

No other changes needed in FilterBar.vue.

---

## Step 5: Verification

After both files are updated:

1. Confirm the dev server at `http://localhost:3000` is running (start it if not)
2. Use Playwright MCP tools to open `http://localhost:3000` and take a screenshot
3. Verify:
   - [ ] Sidebar is visible on the left, top nav is gone
   - [ ] All 6 nav links are present and clicking them changes the route
   - [ ] Active route link is highlighted (left accent bar + bright text)
   - [ ] FilterBar appears at the top of the main content area
   - [ ] Changing a filter updates the page data (no regressions)
   - [ ] No console errors
4. If any route or filter is broken, investigate and fix before reporting done

---

## Notes

- Keep all existing i18n `t()` calls intact — do not hardcode nav label text
- Keep `<ProfileMenu>`, `<LanguageSwitcher>`, and all modal components (`<ProfileDetailsModal>`, `<TasksModal>`) — just reposition them into the sidebar footer
- The existing `useFilters`, `useAuth`, `useI18n` composables require no changes
- Do not touch any file in `client/src/views/`
