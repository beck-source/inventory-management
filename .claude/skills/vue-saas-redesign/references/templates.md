# Templates to adapt

These are starting points, not final code. Replace colors with the app's own palette, swap labels for the app's i18n calls, and match its component style (this project uses Options-style `export default { setup() }`; follow whatever the host app does).

## Design tokens

```css
:root {
  /* Color: seed from the app's existing palette */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-primary: #2563eb;
  --color-primary-soft: #eff6ff;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-danger: #dc2626;

  /* Sidebar */
  --sidebar-width: 240px;
  --sidebar-bg: #ffffff;
  --sidebar-item-hover: #f1f5f9;

  /* Spacing scale (4px base) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;

  /* Shape and depth */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  /* Type */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
}
```

## App shell markup

```vue
<template>
  <div class="app-shell">
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false" />

    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-brand">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-sub">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav" aria-label="Main">
        <!-- one router-link per existing route; keep original i18n labels -->
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          @click="sidebarOpen = false"
        >
          <svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path :d="item.icon" />
          </svg>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <!-- relocate existing LanguageSwitcher / ProfileMenu here -->
      </div>
    </aside>

    <div class="main-column">
      <header class="topbar">
        <button class="menu-button" aria-label="Open navigation"
                :aria-expanded="sidebarOpen" @click="sidebarOpen = !sidebarOpen">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor"
               stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </header>
      <main class="page">
        <router-view />
      </main>
    </div>
  </div>
</template>
```

Script notes: keep `sidebarOpen = ref(false)`; build `navItems` as a computed from the existing links so labels stay reactive to language changes (`computed(() => [{ to: '/', label: t('nav.overview'), icon: '...' }, ...])`). Close on Escape with a `keydown` listener added in `onMounted` and removed in `onUnmounted`. Use unique `to` values as keys.

## Shell CSS

```css
.app-shell { display: flex; min-height: 100vh; background: var(--color-bg); }

.sidebar {
  position: fixed; inset: 0 auto 0 0;
  width: var(--sidebar-width);
  display: flex; flex-direction: column;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--color-border);
  z-index: 200;
}
.sidebar-brand { padding: var(--space-6) var(--space-4) var(--space-4); }
.brand-name { display: block; font-size: var(--text-xl); font-weight: 700; color: var(--color-text); letter-spacing: -0.02em; }
.brand-sub { font-size: var(--text-xs); color: var(--color-text-muted); }

.sidebar-nav { flex: 1; overflow-y: auto; padding: var(--space-2) var(--space-3); display: flex; flex-direction: column; gap: var(--space-1); }
.sidebar-link {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--color-text-muted); text-decoration: none;
  font-size: var(--text-sm); font-weight: 500;
  transition: background 0.15s, color 0.15s;
}
.sidebar-link:hover { background: var(--sidebar-item-hover); color: var(--color-text); }
.sidebar-link.router-link-exact-active,
.sidebar-link[aria-current='page'] { background: var(--color-primary-soft); color: var(--color-primary); }
.sidebar-link:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.sidebar-icon { width: 20px; height: 20px; flex-shrink: 0; }

.sidebar-footer { padding: var(--space-4); border-top: 1px solid var(--color-border); display: flex; flex-direction: column; gap: var(--space-3); }

.main-column { flex: 1; min-width: 0; margin-left: var(--sidebar-width); display: flex; flex-direction: column; }
.page { width: 100%; max-width: 1400px; margin: 0 auto; padding: var(--space-8); }
.topbar, .menu-button { display: none; }
.sidebar-backdrop { display: none; }

@media (max-width: 1024px) {
  .sidebar { transform: translateX(-100%); transition: transform 0.2s ease; box-shadow: var(--shadow-md); }
  .sidebar.open { transform: translateX(0); }
  .sidebar-backdrop { display: block; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.4); z-index: 150; }
  .main-column { margin-left: 0; }
  .topbar { display: flex; align-items: center; padding: var(--space-3) var(--space-4); background: var(--color-surface); border-bottom: 1px solid var(--color-border); position: sticky; top: 0; z-index: 100; }
  .menu-button { display: inline-flex; padding: var(--space-2); border: 0; background: transparent; border-radius: var(--radius-sm); color: var(--color-text); cursor: pointer; }
  .page { padding: var(--space-4); }
}
```

## Page header pattern

```vue
<div class="page-header">
  <div>
    <h2 class="page-title">{{ t('...') }}</h2>
    <p class="page-description">{{ t('...') }}</p>
  </div>
  <div class="page-actions"><!-- buttons --></div>
</div>
```

```css
.page-header { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-6); }
.page-title { font-size: var(--text-2xl); font-weight: 700; color: var(--color-text); letter-spacing: -0.02em; }
.page-description { margin-top: var(--space-1); font-size: var(--text-sm); color: var(--color-text-muted); }
.card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-lg); box-shadow: var(--shadow-sm); padding: var(--space-6); }
```
