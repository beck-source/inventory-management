# SaaS UI Redesign Design Spec

**Date:** 2026-06-22
**Output:** Modified `App.vue`, new `AppSidebar.vue`, modified `FilterBar.vue`

## Goal

Redesign the inventory management app's UI from a horizontal top navigation bar to a modern SaaS-style interface with a vertical sidebar, elevated card layouts, and a polished professional aesthetic — using only global CSS changes (no view files touched).

## Decisions Made

| Decision | Choice | Reason |
|---|---|---|
| Sidebar style | Dark (`#0f172a`) | High contrast, Linear/Vercel aesthetic, already in the app's palette |
| Card style | Elevated | White cards + drop shadow on `#f1f5f9` bg — most common SaaS pattern |
| Scope | Global CSS only | Views unchanged; all card/typography improvements via unscoped globals in App.vue |
| Responsive | Desktop only | No mobile breakpoints in this pass |
| Scroll model | Viewport scroll (Option A) | `.main-area` has no overflow — page scrolls naturally, sidebar sticks via viewport |

## Layout Architecture

### App.vue Template Skeleton

The root element changes from `.app` to `.app-shell`. The full new template structure:

```html
<template>
  <div class="app-shell">
    <AppSidebar
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
    />
    <div class="main-area">
      <div class="topbar">
        <FilterBar />
      </div>
      <main class="main-content">
        <router-view />
      </main>
    </div>
    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />
    <TasksModal
      :is-open="showTasks"
      @close="showTasks = false"
    />
  </div>
</template>
```

`FilterBar` lives inside `.topbar`. Modals stay in `App.vue` — owned by `showProfileDetails` and `showTasks` refs, which remain in `App.vue`'s script.

### Shell CSS (App.vue)

```css
/* Replaces .app */
.app-shell {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  /* NO overflow on this element — viewport is the scroll container */
}

.main-area {
  display: flex;
  flex-direction: column;
  /* NO overflow-y: auto — page scrolls via viewport, not this element */
  background: #f1f5f9;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 90;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  padding: 0.6rem 1.5rem;
}

.main-content {
  flex: 1;
  padding: 1.5rem 2rem;
  /* No max-width — sidebar already constrains width */
}
```

**Why no `overflow-y: auto` on `.main-area`:** For `position: sticky` to work on the sidebar, the scroll container must be an ancestor of the sidebar — not a sibling. Putting `overflow-y: auto` on `.main-area` (a sibling of the sidebar in the grid) creates a separate scroll context that the sidebar cannot respond to. With viewport scrolling, the sidebar sticks correctly to the top of the browser window as the user scrolls down.

### Sidebar CSS (AppSidebar.vue)

```css
.sidebar {
  position: sticky;   /* NOT fixed — stays in grid flow */
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  overflow-y: auto;
}
```

### AppSidebar.vue Structure

**Logo block:**
```html
<div class="sidebar-logo">
  <div class="logo-name">Factory IMS</div>
  <div class="logo-sub">Inventory Management</div>
</div>
```

**Nav items — data-driven, using existing i18n keys:**
```js
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n.js'

const route = useRoute()
const { t } = useI18n()

const navItems = [
  { path: '/',          labelKey: 'nav.overview',        icon: 'grid'      },
  { path: '/inventory', labelKey: 'nav.inventory',       icon: 'box'       },
  { path: '/orders',    labelKey: 'nav.orders',          icon: 'clipboard' },
  { path: '/spending',  labelKey: 'nav.finance',         icon: 'dollar'    },
  { path: '/demand',    labelKey: 'nav.demandForecast',  icon: 'trend'     },
  { path: '/reports',   labelKey: 'nav.reports',         icon: 'file'      },
]

const isActive = (item) =>
  item.path === '/' ? route.path === '/' : route.path.startsWith(item.path)
```

**Nav item template:**
```html
<a
  v-for="item in navItems"
  :key="item.path"
  :href="item.path"
  class="nav-item"
  :class="{ active: isActive(item) }"
  @click.prevent="$router.push(item.path)"
>
  <!-- inline SVG icon here -->
  <span class="nav-label">{{ t(item.labelKey) }}</span>
</a>
```

**Active indicator** — nav item needs `position: relative`, then `::before`:
```css
.nav-item {
  position: relative;   /* required for ::before to position correctly */
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.45rem 0.75rem;
  margin: 0.125rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
}
.nav-item:hover { color: #f1f5f9; background: rgba(255,255,255,0.06); }
.nav-item.active { color: #ffffff; background: rgba(255,255,255,0.12); }
.nav-item.active::before {
  content: '';
  position: absolute;
  left: -0.5rem;       /* flush with the margin edge */
  top: 15%;
  height: 70%;
  width: 3px;
  background: #2563eb;
  border-radius: 0 2px 2px 0;
}
```

**Footer — ProfileMenu + LanguageSwitcher:**
```html
<div class="sidebar-footer">
  <LanguageSwitcher />
  <ProfileMenu
    @show-profile-details="$emit('show-profile-details')"
    @show-tasks="$emit('show-tasks')"
  />
</div>
```

`ProfileMenu` emits `show-profile-details` and `show-tasks` — forward both up to App.vue.
`LanguageSwitcher` manages its own state internally — no event forwarding needed.

Both components use light-background scoped styles (white bg, dark text). They will render as white/light pills inside the dark sidebar footer — this is intentional and acceptable. No overrides needed.

**AppSidebar emits:**
```js
const emit = defineEmits(['show-profile-details', 'show-tasks'])
```

## Design Tokens (all existing palette values)

| Element | Value |
|---|---|
| Sidebar bg | `#0f172a` |
| Page bg | `#f1f5f9` |
| Topbar bg | `#ffffff` |
| Card bg | `#ffffff` |
| Card shadow | `0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04)` |
| Card border-radius | `10px` |
| Nav default text | `#64748b` |
| Nav hover | `#f1f5f9` text + `rgba(255,255,255,0.06)` bg |
| Nav active | `#ffffff` text + `rgba(255,255,255,0.12)` bg |
| Active indicator | `3px solid #2563eb` |
| Sidebar dividers | `rgba(255,255,255,0.07)` |
| Topbar border | `1px solid #e2e8f0` |

## Global CSS Changes (App.vue unscoped styles)

### Cards
```css
.card, .metric-card {
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04);
  border: none;   /* remove existing 1px border */
}
```

### KPI metric cards
```css
.metric-label {
  font-size: 0.65rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.metric-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}
```

### Tables
```css
.table-container {
  background: #ffffff;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.04);
  overflow: hidden;
}
thead th {
  background: #f8fafc;
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}
```

### Page-level typography
```css
.page-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #0f172a;
}
.page-subtitle {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 2px;
}
```

## FilterBar Changes

`FilterBar` is placed inside `.topbar` in `App.vue` — it is no longer sticky itself (`.topbar` owns stickiness). Two CSS properties to remove from `FilterBar.vue`'s scoped styles:

```css
/* FilterBar.vue scoped styles — update these values */
.filters-bar {
  position: static;       /* was: sticky */
  top: auto;              /* was: 70px (old nav height offset — remove) */
  max-width: none;        /* was: 1600px */
  padding: 0;
  border-bottom: none;    /* topbar owns the border */
  background: transparent;
}
.filters-container {
  max-width: none;        /* was: 1600px */
  margin: 0;
  padding: 0;
  width: 100%;
}
```

## Icons

Use inline SVG for each nav item — no icon library. Six small SVGs directly in `AppSidebar.vue`'s template. Each `<svg>` is `width="16" height="16"`, `stroke="currentColor"`, `fill="none"`, `stroke-width="2"`. The `currentColor` inherits from the nav item's `color` property so hover/active states automatically update icon color.

## Files Changed

| File | Type | Change |
|---|---|---|
| `client/src/App.vue` | Modify | Grid shell, remove top-nav template + CSS, add global card/table/typography styles |
| `client/src/components/AppSidebar.vue` | Create | Logo, nav items (v-for + i18n), ProfileMenu/LanguageSwitcher footer, modal emits |
| `client/src/components/FilterBar.vue` | Modify | Remove sticky offset + max-width from scoped CSS |

## Out of Scope

- `src/views/*.vue` — untouched
- `src/main.js` — untouched
- `src/api.js`, `src/composables/` — untouched
- Mobile/responsive breakpoints
- Icon library (inline SVGs only)
- Dark mode content area
- ProfileMenu / LanguageSwitcher internal style overrides
