# Shell Example

Adapt names, routes, and i18n keys to the target app. Options API or Composition API: match what the app uses.

```vue
<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-brand">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-sub">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav" aria-label="Main">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          @click="sidebarOpen = false"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path :d="item.icon" />
          </svg>
          <span>{{ t(item.label) }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu />
      </div>
    </aside>

    <div v-if="sidebarOpen" class="scrim" @click="sidebarOpen = false" />

    <div class="app-main">
      <header class="topbar">
        <button class="menu-btn" :aria-expanded="sidebarOpen" aria-label="Menu"
                @click="sidebarOpen = !sidebarOpen">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor"
               stroke-width="1.5" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
        </button>
        <FilterBar />
      </header>
      <main class="content"><router-view /></main>
    </div>
  </div>
</template>
```

`navItems` is a static array of `{ to, label, icon }` built from the old `<router-link>` list (`icon` is an SVG path string; keep the route order).

```css
:root {
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px;
  --space-4: 16px; --space-5: 20px; --space-6: 24px; --space-8: 32px;
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px;
  --bg: #f8fafc;  --surface: #fff;  --border: #e2e8f0;
  --text: #0f172a; --text-muted: #64748b;
  --accent: #2563eb; --accent-soft: #eff6ff;
  --sidebar-w: 240px; --topbar-h: 56px;
}

.app-shell { display: grid; grid-template-columns: var(--sidebar-w) 1fr; min-height: 100vh; }

.sidebar {
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
  display: flex; flex-direction: column; gap: var(--space-6);
  padding: var(--space-5) var(--space-3);
  background: var(--surface); border-right: 1px solid var(--border);
}
.sidebar-nav { display: flex; flex-direction: column; gap: var(--space-1); flex: 1; }
.nav-item {
  display: flex; align-items: center; gap: var(--space-2);
  height: 40px; padding: 0 var(--space-3);
  border-radius: var(--radius-md); color: var(--text-muted);
  font-size: 14px; font-weight: 500; text-decoration: none;
  transition: background-color 150ms, color 150ms;
}
.nav-item:hover { background: #f1f5f9; color: var(--text); }
.nav-item:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.nav-item.router-link-exact-active { background: var(--accent-soft); color: var(--accent); }
.nav-icon { width: 20px; height: 20px; flex: none; }

.app-main { min-width: 0; }
.topbar {
  position: sticky; top: 0; z-index: 10; min-height: var(--topbar-h);
  display: flex; align-items: center; gap: var(--space-3);
  padding: 0 var(--space-6);
  background: var(--surface); border-bottom: 1px solid var(--border);
}
.content { max-width: 1440px; margin: 0 auto; padding: var(--space-6); }
.menu-btn { display: none; }

@media (max-width: 900px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar {
    position: fixed; inset: 0 auto 0 0; width: var(--sidebar-w); z-index: 40;
    transform: translateX(-100%); transition: transform 200ms ease;
  }
  .sidebar.open { transform: none; }
  .scrim { position: fixed; inset: 0; background: rgba(15, 23, 42, .4); z-index: 30; }
  .menu-btn { display: inline-flex; }
  .topbar, .content { padding-left: var(--space-4); padding-right: var(--space-4); }
}
```

Active styling uses `router-link-exact-active`; if the app marks `/` active for every route, that class (not `router-link-active`) avoids the bug.
