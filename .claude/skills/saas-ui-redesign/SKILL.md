---
name: saas-ui-redesign
description: Redesigns a Vue 3 application's UI into a modern SaaS-style interface with a vertical navigation sidebar, consistent spacing system, and polished professional look. Replaces the existing top nav bar in App.vue.
---

# SaaS UI Redesign Skill

This skill converts a Vue 3 app with a horizontal top-nav bar into a modern SaaS-style layout with a fixed vertical sidebar, consistent spacing, and a polished professional look. All changes are made through the `vue-expert` agent — never edit `.vue` files directly.

---

## Overview of Changes

| Before | After |
|---|---|
| `.top-nav` horizontal bar at top | Fixed vertical sidebar, 220px wide |
| Nav links in a row | Nav links stacked vertically with icons |
| Logo + subtitle inline in nav bar | Logo block at top of sidebar |
| `FilterBar` below the nav bar | `FilterBar` in a slim horizontal bar below the topbar |
| `ProfileMenu` + `LanguageSwitcher` in top-right of nav | Footer section at the bottom of the sidebar |
| Full-width main content area | `margin-left: 220px` main content area |

---

## Layout Structure to Implement

```
┌─────────────────────────────────────────────────────┐
│  SIDEBAR (220px fixed, full height)                  │  TOPBAR (header, 56px, left: 220px)
│  ┌──────────────────┐                               │  ┌───────────────────────────────────┐
│  │  Logo / App name  │                               │  │  Page title        [FilterBar]    │
│  ├──────────────────┤                               │  └───────────────────────────────────┘
│  │  Nav links        │                               │
│  │  > Dashboard      │                               │  MAIN CONTENT (padding: 24px)
│  │  > Inventory      │                               │  ┌───────────────────────────────────┐
│  │  > Orders         │                               │  │  <router-view />                  │
│  │  > Finance        │                               │  │                                   │
│  │  > Demand         │                               │  └───────────────────────────────────┘
│  │  > Reports        │                               │
│  ├──────────────────┤
│  │  LanguageSwitcher │
│  │  ProfileMenu      │
│  └──────────────────┘
└──────────────────────
```

---

## Step-by-Step Implementation

### Step 1 — Audit the current App.vue

Read `client/src/App.vue` before making any changes. Note:
- The `.top-nav` / `.nav-container` / `.nav-tabs` selectors — these will be removed
- The `.main-content` selector — its padding/max-width must be preserved
- Global CSS classes (`.card`, `.badge`, `.table`, etc.) — these do NOT change
- All `<script>` logic — this does NOT change

### Step 2 — Redesign App.vue template

Replace the `<header class="top-nav">...</header>` block with a sidebar + topbar structure:

```vue
<template>
  <div class="app-shell">

    <!-- Vertical Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-logo">
        <span class="sidebar-logo-mark">FI</span>
        <div class="sidebar-logo-text">
          <span class="sidebar-app-name">{{ t('nav.companyName') }}</span>
          <span class="sidebar-app-sub">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/"          class="sidebar-link" :class="{ active: $route.path === '/' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M3 4a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm0 8a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3zm8-8a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1V4zm0 8a1 1 0 011-1h3a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-3z"/></svg>
          {{ t('nav.overview') }}
        </router-link>
        <router-link to="/inventory" class="sidebar-link" :class="{ active: $route.path === '/inventory' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm3 2h6v4H7V5zm-2 8h10v2H5v-2z"/></svg>
          {{ t('nav.inventory') }}
        </router-link>
        <router-link to="/orders"    class="sidebar-link" :class="{ active: $route.path === '/orders' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11 4a1 1 0 10-2 0v4a1 1 0 102 0V7zm-3 1a1 1 0 10-2 0v3a1 1 0 102 0V8zM8 9a1 1 0 00-2 0v2a1 1 0 102 0V9z" clip-rule="evenodd"/></svg>
          {{ t('nav.orders') }}
        </router-link>
        <router-link to="/spending"  class="sidebar-link" :class="{ active: $route.path === '/spending' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"/><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.028 2.353 1.118V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.028-2.354-1.118V5z" clip-rule="evenodd"/></svg>
          {{ t('nav.finance') }}
        </router-link>
        <router-link to="/demand"    class="sidebar-link" :class="{ active: $route.path === '/demand' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/></svg>
          {{ t('nav.demandForecast') }}
        </router-link>
        <router-link to="/reports"   class="sidebar-link" :class="{ active: $route.path === '/reports' }">
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm2 10a1 1 0 10-2 0v3a1 1 0 102 0v-3zm2-3a1 1 0 011 1v5a1 1 0 11-2 0v-5a1 1 0 011-1zm4-1a1 1 0 10-2 0v7a1 1 0 102 0V8z" clip-rule="evenodd"/></svg>
          Reports
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <!-- Right-side wrapper -->
    <div class="app-body">
      <header class="topbar">
        <FilterBar />
      </header>
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- Modals — unchanged -->
    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />
    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>
```

### Step 3 — Replace App.vue layout CSS

Remove the old `.top-nav`, `.nav-container`, `.nav-tabs` blocks entirely.
Replace the `*`, `body`, and `.app` blocks and add the new sidebar CSS.

Keep ALL existing global utility classes unchanged:
`.card`, `.card-header`, `.card-title`, `.stats-grid`, `.stat-card`, `.stat-label`, `.stat-value`, `.table-container`, `table`, `thead`, `th`, `td`, `tbody tr`, `.badge`, `.loading`, `.error`, `.page-header`

```css
/* ---- Reset & base ---- */
*, *::before, *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f8fafc;
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---- Shell ---- */
.app-shell {
  display: flex;
  min-height: 100vh;
}

/* ---- Sidebar ---- */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: #0f172a;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 200;
  border-right: 1px solid #1e293b;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 20px;
  border-bottom: 1px solid #1e293b;
}

.sidebar-logo-mark {
  width: 32px;
  height: 32px;
  background: #2563eb;
  color: #fff;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  letter-spacing: 0.02em;
}

.sidebar-logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sidebar-app-name {
  font-size: 0.85rem;
  font-weight: 700;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}

.sidebar-app-sub {
  font-size: 0.68rem;
  color: #475569;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ---- Sidebar nav links ---- */
.sidebar-nav {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
  white-space: nowrap;
}

.sidebar-link:hover {
  background: #1e293b;
  color: #e2e8f0;
}

.sidebar-link.active {
  background: #1e3a5f;
  color: #93c5fd;
}

.nav-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  opacity: 0.8;
}

.sidebar-link.active .nav-icon {
  opacity: 1;
}

/* ---- Sidebar footer (profile + language) ---- */
.sidebar-footer {
  padding: 12px 10px;
  border-top: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* ---- Right-side body ---- */
.app-body {
  margin-left: 220px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ---- Topbar (filter bar row) ---- */
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}

/* ---- Main content ---- */
.main-content {
  flex: 1;
  padding: 24px 28px;
}
```

---

## Spacing System

Use this consistent spacing scale throughout all views. Do not introduce arbitrary px values.

| Token | Value | Usage |
|---|---|---|
| `4px` | `0.25rem` | Tight gaps within a component |
| `8px` | `0.5rem` | Icon-to-label gaps |
| `12px` | `0.75rem` | Internal card padding (small) |
| `16px` | `1rem` | Standard card padding |
| `20px` | `1.25rem` | Between cards in a grid |
| `24px` | `1.5rem` | Page section vertical spacing |
| `28px` | `1.75rem` | Page content horizontal padding |
| `32px` | `2rem` | Between major sections |

---

## Colour Tokens

These are the design system colours already in use. Do not introduce new ones.

```
Background page:    #f8fafc
Sidebar bg:         #0f172a
Sidebar border:     #1e293b
Sidebar active bg:  #1e3a5f
Sidebar active txt: #93c5fd
Sidebar muted txt:  #94a3b8
Topbar / card bg:   #ffffff
Card border:        #e2e8f0
Body text:          #1e293b
Muted text:         #64748b
Accent blue:        #2563eb
```

---

## Sidebar Footer: ProfileMenu and LanguageSwitcher

Both components render as small interactive elements. In the sidebar footer they stack vertically. Wrap each in the `.sidebar-footer` container — no additional wrapper needed.

If `ProfileMenu` or `LanguageSwitcher` have hardcoded horizontal layout styles (e.g., `display: flex; flex-direction: row`) that look wrong in a vertical context, patch their `<style scoped>` to add `width: 100%` and adjust padding. Do not change their emitted events or props.

---

## FilterBar Placement

`FilterBar` moves from being a full-width block below the top-nav to living inside the `.topbar` `<header>` element. The `FilterBar` component itself does not need to change — only where it is rendered in `App.vue`.

If `FilterBar` has a hardcoded top-level `max-width` or centering wrapper matching the old nav's `1600px` container, update it to `width: 100%` with `padding: 8px 24px` so it fills the topbar naturally.

---

## Checklist Before Finishing

- [ ] Old `.top-nav`, `.nav-container`, `.nav-tabs` CSS removed from App.vue
- [ ] New `.app-shell`, `.sidebar`, `.app-body`, `.topbar`, `.main-content` CSS in place
- [ ] `.main-content` has `margin-left: 220px` via `.app-body` (not direct)
- [ ] All 6 route links are present in sidebar with correct paths and active class bindings
- [ ] Sidebar icons are inline SVG (no external icon library)
- [ ] Logo mark (2-letter monogram) renders in sidebar header
- [ ] `ProfileMenu` and `LanguageSwitcher` render in `.sidebar-footer`
- [ ] `FilterBar` renders inside `.topbar` header
- [ ] All modal components and their event bindings are unchanged
- [ ] All `<script>` logic is unchanged
- [ ] All global utility classes (`.card`, `.badge`, `.table`, etc.) are unchanged
- [ ] App renders without console errors at `http://localhost:3000`
- [ ] Active nav link highlights correctly on route change

---

## Common Pitfalls

**Sidebar overlapping content**: Ensure `.app-body` has `margin-left: 220px` to match the fixed sidebar width, not padding-left.

**FilterBar misaligned**: If `FilterBar.vue` has `max-width: 1600px; margin: 0 auto` on its root element, the topbar height will look off. Remove the centering constraint from `FilterBar.vue` when it moves into the topbar.

**ProfileMenu dropdown clipping**: The sidebar has `overflow: hidden` if not explicitly set. If the ProfileMenu dropdown appears clipped, add `overflow: visible` to `.sidebar-footer` and ensure the dropdown uses `position: fixed` rather than `absolute`.

**Sidebar link underlines**: `router-link` renders as `<a>` tags. Make sure `text-decoration: none` is set on `.sidebar-link` and there's no inherited `a { text-decoration: underline }` rule from a CSS reset.

**Active class mismatch**: This project uses `:class="{ active: $route.path === '/...' }"` for active detection instead of Vue Router's `linkActiveClass`. Keep this pattern — do not switch to `linkActiveClass`.

---

## Delegation Rule

**Every `.vue` file change in this skill MUST be made via the `vue-expert` subagent.**

Do not edit `.vue` files directly. Pass the full specification above plus the current file contents to `vue-expert` with clear before/after intent.
