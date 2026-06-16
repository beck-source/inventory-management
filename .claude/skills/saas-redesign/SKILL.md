---
name: saas-redesign
description: Redesigns a Vue 3 application's UI into a modern SaaS-style interface with a vertical navigation sidebar, consistent spacing, and a polished professional look. Use when the user asks to modernize, redesign, or make the app look like a SaaS product.
---

# SaaS Redesign Skill

Transform this Vue 3 application's UI into a modern SaaS-style interface. This skill covers the full redesign: layout structure, design system, sidebar navigation, typography, spacing, and visual polish.

---

## Phase 1 — Audit the Current App

Before writing any code, read these files to understand what exists:

1. **`client/src/App.vue`** — current root layout, global CSS, nav structure
2. **`client/src/main.js`** — router config and all route paths
3. **`client/src/views/*.vue`** — all page components (skim for page-level classes and layout patterns)
4. **`client/src/components/FilterBar.vue`** — to understand where it lives in the layout

Map out:
- All nav links and their routes
- All global CSS class names used across views (`.card`, `.stat-card`, `.badge`, `.table-container`, etc.)
- Any hardcoded colors or fonts in scoped styles that conflict with the new system

---

## Phase 2 — Design System

Apply this token set consistently. Define CSS custom properties in `:root` inside `App.vue`'s global `<style>` block:

```css
:root {
  /* Sidebar */
  --sidebar-width: 240px;
  --sidebar-bg: #0f172a;
  --sidebar-text: #94a3b8;
  --sidebar-text-active: #f8fafc;
  --sidebar-accent: #3b82f6;
  --sidebar-hover-bg: rgba(255,255,255,0.06);
  --sidebar-active-bg: rgba(59,130,246,0.15);
  --sidebar-border: rgba(255,255,255,0.08);

  /* Surface */
  --bg: #f1f5f9;
  --surface: #ffffff;
  --surface-2: #f8fafc;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;

  /* Text */
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;

  /* Brand */
  --accent: #3b82f6;
  --accent-hover: #2563eb;

  /* Status */
  --success: #059669;
  --success-bg: #d1fae5;
  --warning: #d97706;
  --warning-bg: #fef3c7;
  --danger: #dc2626;
  --danger-bg: #fee2e2;
  --info: #2563eb;
  --info-bg: #dbeafe;

  /* Radius & shadow */
  --radius-sm: 6px;
  --radius: 10px;
  --radius-lg: 14px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow: 0 4px 12px rgba(0,0,0,0.08);
  --shadow-lg: 0 10px 24px rgba(0,0,0,0.12);

  /* Spacing */
  --content-padding: 2rem;
  --card-padding: 1.5rem;
  --gap: 1.25rem;
}
```

---

## Phase 3 — Rewrite App.vue Layout

Replace the top-nav layout with a sidebar + content shell. The new structure:

```
┌──────────────────────────────────────┐
│  sidebar (fixed, full height)        │
│  ┌────────┐  ┌─────────────────────┐ │
│  │ 240px  │  │   main content      │ │
│  │        │  │                     │ │
│  │ logo   │  │  FilterBar (if any) │ │
│  │ nav    │  │                     │ │
│  │ items  │  │  <router-view />    │ │
│  │        │  │                     │ │
│  │ user   │  │                     │ │
│  └────────┘  └─────────────────────┘ │
└──────────────────────────────────────┘
```

### App.vue template skeleton

```vue
<template>
  <div class="app-shell">

    <!-- Sidebar -->
    <aside class="sidebar">
      <!-- Logo / brand -->
      <div class="sidebar-brand">
        <div class="brand-icon"><!-- initials or icon --></div>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-sub">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item) }"
        >
          <!-- SVG icon slot -->
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>

      <!-- Spacer pushes user section to bottom -->
      <div class="sidebar-spacer"></div>

      <!-- Bottom: language + user -->
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <!-- Main content area -->
    <div class="content-area">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- Modals (unchanged) -->
    <ProfileDetailsModal :is-open="showProfileDetails" @close="showProfileDetails = false" />
    <TasksModal ... />
  </div>
</template>
```

### navItems array (define in setup())

Build the nav from the router config. Each item:
```js
const navItems = [
  { path: '/',           labelKey: 'nav.overview',       icon: '<svg>...</svg>' },
  { path: '/inventory',  labelKey: 'nav.inventory',      icon: '<svg>...</svg>' },
  { path: '/orders',     labelKey: 'nav.orders',         icon: '<svg>...</svg>' },
  { path: '/spending',   labelKey: 'nav.finance',        icon: '<svg>...</svg>' },
  { path: '/demand',     labelKey: 'nav.demandForecast', icon: '<svg>...</svg>' },
  { path: '/reports',    labelKey: 'nav.reports',        icon: '<svg>...</svg>' },
  { path: '/restocking', labelKey: 'nav.restocking',     icon: '<svg>...</svg>' },
]
```

Use `useRoute()` from vue-router for active detection:
```js
import { useRoute } from 'vue-router'
const route = useRoute()
const isActive = (item) => {
  if (item.path === '/') return route.path === '/'
  return route.path.startsWith(item.path)
}
```

### Icon set — use Heroicons outline SVGs (inline, no library needed)

Suggested icon SVGs (24×24, `stroke="currentColor"`, `fill="none"`):
- Overview/Dashboard: squares-2×2 or chart-bar
- Inventory: archive-box or cube
- Orders: clipboard-document-list
- Finance/Spending: banknotes or currency-dollar
- Demand Forecast: arrow-trending-up or chart-line
- Reports: document-chart-bar
- Restocking: arrow-path or shopping-cart

Find the correct SVG path data at https://heroicons.com — use the **outline** variant. Each icon should be:
```html
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="18" height="18">
  <path stroke-linecap="round" stroke-linejoin="round" d="..." />
</svg>
```

---

## Phase 4 — App.vue Global CSS

Replace ALL existing global styles with this new system. Keep class names compatible with what the views already use (`.card`, `.stat-card`, `.badge`, etc.) so views don't need changes.

```css
/* ── Shell layout ── */
.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--bg);
}

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 100;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem 1.25rem 1.25rem;
  border-bottom: 1px solid var(--sidebar-border);
}

.brand-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--sidebar-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.brand-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--sidebar-text-active);
  display: block;
  line-height: 1.2;
}

.brand-sub {
  font-size: 0.688rem;
  color: var(--sidebar-text);
  display: block;
  margin-top: 2px;
  line-height: 1.2;
}

/* ── Nav items ── */
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 1rem 0.75rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
  cursor: pointer;
}

.nav-item:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.nav-item.active {
  background: var(--sidebar-active-bg);
  color: var(--sidebar-accent);
}

.nav-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-spacer { flex: 1; }

.sidebar-footer {
  padding: 1rem 0.75rem;
  border-top: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* ── Content area ── */
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0; /* prevents flex overflow */
}

.main-content {
  flex: 1;
  padding: var(--content-padding);
  max-width: 1400px;
  width: 100%;
}

/* ── Typography ── */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg);
  color: var(--text-primary);
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
}

/* ── Page header ── */
.page-header {
  margin-bottom: 1.75rem;
}

.page-header h2 {
  font-size: 1.625rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
  margin-bottom: 0.25rem;
}

.page-header p {
  color: var(--text-muted);
  font-size: 0.875rem;
}

/* ── Cards ── */
.card {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: var(--card-padding);
  margin-bottom: var(--gap);
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

/* ── Stat cards ── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--gap);
  margin-bottom: var(--gap);
}

.stat-card {
  background: var(--surface);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  padding: 1.25rem var(--card-padding);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow);
  border-color: var(--border-strong);
}

.stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.03em;
  line-height: 1;
}

.stat-card.success .stat-value { color: var(--success); }
.stat-card.warning .stat-value { color: var(--warning); }
.stat-card.danger  .stat-value { color: var(--danger); }
.stat-card.info    .stat-value { color: var(--info); }
.stat-card.restocking .stat-value { color: #7c3aed; }

/* ── Tables ── */
.table-container { overflow-x: auto; }

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-2);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: 0.625rem 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.688rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
}

td {
  padding: 0.625rem 0.875rem;
  border-top: 1px solid #f1f5f9;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

tbody tr { transition: background 0.1s ease; }
tbody tr:hover { background: var(--surface-2); }

/* ── Badges ── */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  font-size: 0.688rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.badge.success    { background: var(--success-bg); color: #065f46; }
.badge.warning    { background: var(--warning-bg); color: #92400e; }
.badge.danger     { background: var(--danger-bg);  color: #991b1b; }
.badge.info       { background: var(--info-bg);    color: #1e40af; }
.badge.increasing { background: var(--success-bg); color: #065f46; }
.badge.decreasing { background: var(--danger-bg);  color: #991b1b; }
.badge.stable     { background: #e0e7ff;           color: #3730a3; }
.badge.high       { background: var(--danger-bg);  color: #991b1b; }
.badge.medium     { background: var(--warning-bg); color: #92400e; }
.badge.low        { background: var(--info-bg);    color: #1e40af; }
.badge.restocking { background: #ede9fe;           color: #5b21b6; }

/* ── Loading / error states ── */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.error {
  background: var(--danger-bg);
  border: 1px solid #fca5a5;
  color: #991b1b;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-sm);
  margin: 1rem 0;
  font-size: 0.875rem;
}
```

---

## Phase 5 — FilterBar Integration

The FilterBar sits between the sidebar and the view content. Style it as a sticky subheader inside `.content-area`, above `<main>`:

```css
/* In FilterBar.vue scoped styles — or in App.vue global */
.filter-bar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0.75rem var(--content-padding);
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  position: sticky;
  top: 0;
  z-index: 50;
  box-shadow: var(--shadow-sm);
}
```

---

## Phase 6 — LanguageSwitcher and ProfileMenu in the Sidebar

These components live in the sidebar footer. They may need style adjustments since they were designed for a top nav. Check their scoped styles and update colors/backgrounds to match the dark sidebar:

- Buttons inside should use `color: var(--sidebar-text)` and `hover: var(--sidebar-hover-bg)`
- Dropdowns/modals should still open in `var(--surface)` white — no change needed there
- If either component uses hardcoded dark text that becomes invisible on the dark sidebar, add a scoped override in `App.vue`:

```css
/* Override for sidebar context */
.sidebar-footer :deep(.language-switcher button),
.sidebar-footer :deep(.profile-menu-trigger) {
  color: var(--sidebar-text);
  background: transparent;
}
.sidebar-footer :deep(.language-switcher button):hover,
.sidebar-footer :deep(.profile-menu-trigger):hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}
```

---

## Phase 7 — View-Level Polish (optional but recommended)

After the layout is working, scan each view for these quick wins:

| Issue | Fix |
|---|---|
| `.page-header h2` font-size is too small | Already handled by global styles — verify |
| Stat cards have hardcoded border colors | Remove scoped overrides, let global `.stat-card` handle |
| Table `th` has excessive padding | Handled by global `th` — check for scoped overrides that fight it |
| Empty state messages are unstyled | Wrap in `<div class="empty-state">` with centered text and muted color |
| Buttons have no shared style | Add a `.btn`, `.btn-primary`, `.btn-secondary` global class |

Suggested global button styles:
```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}
.btn-primary {
  background: var(--accent);
  color: white;
}
.btn-primary:hover { background: var(--accent-hover); }
.btn-primary:disabled { background: var(--border-strong); color: var(--text-muted); cursor: not-allowed; }
.btn-secondary {
  background: var(--surface-2);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}
.btn-secondary:hover { border-color: var(--border-strong); color: var(--text-primary); }
```

---

## Phase 8 — Verification

After writing all code, verify in the browser using Playwright MCP tools:

1. **Navigate to each route** — sidebar active state highlights correctly, content renders
2. **Sidebar** — logo, all nav links, language switcher, profile menu visible
3. **FilterBar** — renders as sticky subheader, filters still function
4. **Cards and tables** — spacing, borders, hover states look correct
5. **Badges and stat cards** — colors match the design system
6. **Modals** — ProfileDetails and Tasks modals still open correctly
7. **Responsive check** — scroll horizontally if viewport is narrow; sidebar should not collapse (out of scope unless user requests)

Use `mcp__playwright__browser_take_screenshot` at each major route to confirm the visual result. Fix any broken layout before reporting done.

---

## Implementation Order

Execute in this order to minimize broken states:

1. Read all files listed in Phase 1
2. Rewrite `App.vue` — template + global CSS (Phases 3–4)
3. Update `FilterBar.vue` scoped styles if needed (Phase 5)
4. Fix `LanguageSwitcher` and `ProfileMenu` sidebar colors if needed (Phase 6)
5. Quick view-level polish pass (Phase 7)
6. Browser verification (Phase 8)

**Delegate all `.vue` file writes to the `vue-expert` subagent** as required by CLAUDE.md. Pass the full context (current file content + exact changes needed) in the agent prompt.

---

## Common Pitfalls

- **Sidebar width and `min-width`** — always set both on `.sidebar` or flex will shrink it
- **`min-width: 0` on `.content-area`** — required to prevent flex children from overflowing
- **`position: sticky; top: 0; height: 100vh`** on sidebar — keeps it in place while content scrolls
- **Removing `max-width` from `main-content`** — old layout had `max-width: 1600px` centered; new layout fills the space right of the sidebar, so remove the `margin: 0 auto`
- **Active route for root `/`** — use exact match `route.path === '/'` not `startsWith('/')` or every link will be active
- **Dark sidebar + white dropdowns** — ProfileMenu and LanguageSwitcher dropdowns open in white, which is correct; only the trigger buttons need sidebar color overrides
