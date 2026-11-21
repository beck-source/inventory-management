# Sidebar layout

## Target structure

```
.app-shell
├── .sidebar                  fixed width, full height, own scroll if long
│   ├── .sidebar-brand        company name and subtitle (from the old header)
│   ├── .sidebar-nav          the existing router-links, one per route
│   └── .sidebar-footer       language switcher and profile menu
├── .sidebar-backdrop         only visible while the mobile drawer is open
└── .main
    ├── .topbar (mobile only) menu button and brand
    ├── .toolbar              page-level filters, sticky
    └── .content              <router-view />, max width and gutters
```

Keep the existing child components (`LanguageSwitcher`, `ProfileMenu`, the filter bar) and their events. Move them in the template; do not change their props or handlers.

## Template pattern

Replace the old `<header class="top-nav">` block. Reuse each `router-link` as is, including its `to`, its label expression and any existing `:class` binding.

```vue
<div class="app-shell">
  <aside class="sidebar" :class="{ open: sidebarOpen }">
    <div class="sidebar-brand">
      <!-- keep the original brand markup and its i18n expressions -->
    </div>

    <nav class="sidebar-nav" aria-label="Primary">
      <router-link to="/" class="nav-item">
        <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">...</svg>
        <span>{{ t('nav.overview') }}</span>
      </router-link>
      <!-- one per existing route, same order as before -->
    </nav>

    <div class="sidebar-footer">
      <!-- original LanguageSwitcher and ProfileMenu, with their original listeners -->
    </div>
  </aside>

  <div class="sidebar-backdrop" v-if="sidebarOpen" @click="sidebarOpen = false"></div>

  <div class="main">
    <header class="topbar">
      <button class="menu-button" @click="sidebarOpen = true" aria-label="Open navigation">
        <svg viewBox="0 0 24 24" aria-hidden="true">...</svg>
      </button>
    </header>
    <!-- original filter bar, if any, goes here -->
    <main class="content"><router-view /></main>
  </div>
</div>
```

`sidebarOpen` is the only new state. Add it as a `ref(false)` in the shell's existing setup and return it. If the shell already has a drawer or menu flag, reuse that instead. Close the drawer when the route changes, using the router's `afterEach` hook or a `watch` on `$route.path` in the shell.

## Base CSS

```css
.app-shell { display: flex; min-height: 100vh; background: var(--bg-app); color: var(--text); font: var(--text-base)/var(--leading-normal) var(--font-sans); }

.sidebar {
  position: sticky; top: 0; align-self: flex-start;
  width: var(--sidebar-width); height: 100vh; flex: none;
  display: flex; flex-direction: column; gap: var(--space-6);
  padding: var(--space-4);
  background: var(--bg-surface); border-right: 1px solid var(--border);
  overflow-y: auto;
}
.sidebar-brand { padding: var(--space-2) var(--space-3); }
.sidebar-nav { display: flex; flex-direction: column; gap: var(--space-1); flex: 1; }
.sidebar-footer { display: flex; flex-direction: column; gap: var(--space-3); padding-top: var(--space-4); border-top: 1px solid var(--border); }

.nav-item {
  display: flex; align-items: center; gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  color: var(--text-muted); font-size: var(--text-base); font-weight: 500; text-decoration: none;
}
.nav-item:hover { background: var(--bg-subtle); color: var(--text); }
.nav-item.router-link-exact-active { background: var(--accent-soft); color: var(--accent); }
.nav-item:focus-visible { outline: none; box-shadow: var(--focus-ring); }
.nav-icon { width: 18px; height: 18px; flex: none; fill: none; stroke: currentColor; stroke-width: 1.75; stroke-linecap: round; stroke-linejoin: round; }

.main { flex: 1; min-width: 0; display: flex; flex-direction: column; } /* min-width: 0 lets wide tables scroll inside .main instead of widening the page */
.content { width: 100%; max-width: var(--content-max); margin: 0 auto; padding: var(--space-6); }
.topbar, .sidebar-backdrop { display: none; }
```

Use `router-link-exact-active` for the `/` route so it is not active on every page. Other routes can use `router-link-active`. If the old nav used an explicit `:class="{ active: $route.path === '/x' }"` binding, keep that binding and style `.nav-item.active` instead.

## Mobile drawer (below 900px)

```css
@media (max-width: 900px) { /* 900px: sidebar plus a usable content column no longer fit side by side */
  .sidebar {
    position: fixed; inset: 0 auto 0 0; z-index: 40;
    transform: translateX(-100%); transition: transform 0.2s ease;
    box-shadow: var(--shadow-md);
  }
  .sidebar.open { transform: translateX(0); }
  .sidebar-backdrop { display: block; position: fixed; inset: 0; z-index: 30; background: rgb(15 23 42 / 0.4); }
  .topbar { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3) var(--space-4); background: var(--bg-surface); border-bottom: 1px solid var(--border); }
  .content { padding: var(--space-4); }
}
@media (prefers-reduced-motion: reduce) { .sidebar { transition: none; } }
```

## Toolbar for page-level filters

```css
.toolbar {
  position: sticky; top: 0; z-index: 20;
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-3);
  padding: var(--space-3) var(--space-6);
  background: var(--bg-surface); border-bottom: 1px solid var(--border);
}
```
On mobile, the toolbar sits below the topbar; set its `top` to the topbar height or make only one of them sticky.

## Checklist

- [ ] Every route from the old nav has a sidebar item, in the same order, with the same label expression.
- [ ] Old header controls (language, profile, tasks, search) are all present in the sidebar footer or topbar, with original listeners.
- [ ] Exact-active styling is correct for `/`.
- [ ] Sidebar scrolls by itself if there are many items; the page does not.
- [ ] Drawer closes on backdrop click, on route change and on Escape if the project already handles key events.
- [ ] Focus order: sidebar, then toolbar, then content.
