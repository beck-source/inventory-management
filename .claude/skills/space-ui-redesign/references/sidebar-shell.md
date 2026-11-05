# Sidebar shell: replacing a top nav with a left sidebar

This is the pattern for `App.vue`. Adapt the names to the target app, but keep the class names so `theme.css` applies.

## Template

```vue
<template>
  <div
    class="app-shell"
    :class="{ 'is-collapsed': collapsed, 'is-mobile-open': mobileOpen }"
  >
    <div class="cosmos-horizon" aria-hidden="true"></div>

    <aside class="sidebar" aria-label="Primary">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true"></span>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-sub">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <div>
        <div class="nav-section-label">Navigation</div>
        <nav class="side-nav">
          <router-link
            v-for="(item, i) in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-item"
            exact-active-class="is-active"
            :title="collapsed ? item.label : undefined"
            @click="mobileOpen = false"
          >
            <span v-html="item.icon" aria-hidden="true" style="display:contents"></span>
            <span class="nav-label">{{ item.label }}</span>
            <span class="nav-index">{{ String(i + 1).padStart(2, '0') }}</span>
          </router-link>
        </nav>
      </div>

      <div class="sidebar-footer">
        <div class="system-status" role="status">
          <span class="status-dot" aria-hidden="true"></span>
          <span class="status-text">ALL SYSTEMS NOMINAL</span>
        </div>
        <button class="collapse-btn" type="button" @click="toggleCollapsed"
                :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
          <svg viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6"/></svg>
          <span class="nav-label">Collapse</span>
        </button>
      </div>
    </aside>

    <div v-if="mobileOpen" class="sidebar-scrim" @click="mobileOpen = false"></div>

    <div class="shell-main">
      <header class="topbar">
        <button class="btn btn-icon btn-ghost menu-toggle" type="button"
                aria-label="Open navigation" @click="mobileOpen = true">
          <svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h10"/></svg>
        </button>
        <div class="topbar-filters"><FilterBar /></div>
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu @show-profile-details="showProfileDetails = true" @show-tasks="showTasks = true" />
        </div>
      </header>

      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- modals stay at root level, unchanged -->
  </div>
</template>
```

**Keep existing behaviour:** every original link, i18n key, emitted event and modal must still be there. If a nav label was a hard-coded string (e.g. `Reports`), leave it as it was or add an i18n key in both locale files. Don't drop it silently.

If `exact-active-class` doesn't match nested routes the app relies on, use `active-class` for non-root items and `exact-active-class` only for `/`.

## Script additions (inside existing `setup()`)

```js
import { ref, computed } from 'vue'

const collapsed = ref(localStorage.getItem('sidebar-collapsed') === '1')
const mobileOpen = ref(false)
const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
  localStorage.setItem('sidebar-collapsed', collapsed.value ? '1' : '0')
}

const navItems = computed(() => [
  { to: '/',          label: t('nav.overview'),       icon: ICONS.overview },
  { to: '/inventory', label: t('nav.inventory'),      icon: ICONS.inventory },
  // ...one entry per original link, same order
])

// return { collapsed, mobileOpen, toggleCollapsed, navItems, ... }
```

Define `ICONS` as a module-level constant (static SVG strings that the app controls, so `v-html` is safe here). Don't pass user data through it.

## Icon set (24×24, stroke = currentColor, 1.6 stroke width set by CSS)

```js
const svg = (d) => `<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`
const ICONS = {
  overview:  svg('<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" stroke-dasharray="3 3"/><path d="M12 1v3M12 20v3M1 12h3M20 12h3"/>'),        // radar
  inventory: svg('<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/>'),                                                   // cargo cube
  orders:    svg('<path d="M4 4h16v16H4z"/><path d="M8 9h8M8 13h8M8 17h5"/>'),                                                                              // manifest
  finance:   svg('<path d="M3 17l5-5 4 4 8-8"/><path d="M15 8h5v5"/>'),                                                                                     // trajectory
  demand:    svg('<path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/>'),                                                                       // star
  reports:   svg('<circle cx="12" cy="12" r="9"/><path d="M12 3v9l6.5 6.5"/>'),                                                                            // orbit dial
  backlog:   svg('<path d="M12 2v4M12 18v4M4.9 4.9l2.8 2.8M16.3 16.3l2.8 2.8M2 12h4M18 12h4"/><circle cx="12" cy="12" r="4"/>'),                           // signal
  settings:  svg('<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z"/>'),
}
```

## Filter bar in the top bar

A filter bar that used to be a full-width strip under the header should become a compact horizontal row:
- Root: `display:flex; flex-wrap:wrap; gap: var(--space-3); align-items:center;`
- Each filter: a small mono `label` above or before a `.select`. Drop old white backgrounds and borders.
- A "reset" action becomes a `.btn .btn-ghost`.
- On narrow screens let it wrap below the menu toggle (`.topbar` already wraps under 760 px).

## Page header pattern for views

```vue
<div class="page-header">
  <div>
    <div class="page-kicker">Sector 02 · Inventory</div>
    <h2 class="page-title">{{ t('inventory.title') }}</h2>
    <p class="page-subtitle">{{ t('inventory.description') }}</p>
  </div>
  <!-- optional actions -->
</div>
```

Number the sectors to match the order of the sidebar's `nav-index`, so the two stay in sync.
