# Sidebar layout

The sidebar has three modes:

| Viewport | Mode | Behavior |
|---|---|---|
| 1200px and up | Expanded (default) | Icons and labels, `--sidebar-width` wide. A toggle collapses it to icons only. |
| 901px to 1199px | Icons-only rail (default) | `--sidebar-width-collapsed` wide, labels hidden. The same toggle expands it. |
| 900px and below | Off-canvas drawer | Always shows labels. Opened by the topbar menu button. The collapse toggle is hidden. |

## Target structure

```
.app-shell
├── .sidebar                  fixed width, full height, own scroll if long; gets .collapsed in icons-only mode
│   ├── .sidebar-toggle       collapse/expand button (hidden in drawer mode)
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
  <aside class="sidebar" :class="{ open: sidebarOpen, collapsed: sidebarCollapsed }">
    <div class="sidebar-brand">
      <!-- keep the original brand markup and its i18n expressions; wrap its text in .nav-label so it hides in icons-only mode -->
    </div>

    <nav class="sidebar-nav" aria-label="Primary">
      <!-- title gives a native tooltip when labels are hidden; reuse the same label expression -->
      <router-link to="/" class="nav-item" :title="t('nav.overview')">
        <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">...</svg>
        <span class="nav-label">{{ t('nav.overview') }}</span>
      </router-link>
      <!-- one per existing route, same order as before -->
    </nav>

    <div class="sidebar-footer">
      <!-- original LanguageSwitcher and ProfileMenu, with their original listeners -->
    </div>

    <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed"
            :aria-expanded="!sidebarCollapsed" aria-label="Toggle sidebar width"
            :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
      <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">...</svg>
    </button>
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

## New state (the only logic this skill adds)

Two refs in the shell's existing setup, both returned for the template. If the shell already has equivalent flags, reuse them.

```js
// sidebarOpen: mobile drawer visibility.
const sidebarOpen = ref(false)

// sidebarCollapsed: icons-only mode. A saved choice wins; otherwise start collapsed on
// medium screens (under 1200px) so the content column keeps enough room.
const STORAGE_KEY = 'sidebar-collapsed'
const readSaved = () => {
  try { return localStorage.getItem(STORAGE_KEY) } catch { return null } // storage can throw in private windows
}
const saved = readSaved()
const sidebarCollapsed = ref(
  saved !== null ? saved === 'true' : window.matchMedia('(max-width: 1199px)').matches
)
watch(sidebarCollapsed, (value) => {
  try { localStorage.setItem(STORAGE_KEY, String(value)) } catch { /* persistence is optional */ }
})
```

Import `watch` from `vue` if the shell does not already. Close the drawer when the route changes, using the router's `afterEach` hook or a `watch` on `$route.path` in the shell. Report both refs in the summary as the only script changes.

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

.sidebar-toggle {
  display: inline-flex; align-items: center; justify-content: center;
  height: 36px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: var(--bg-surface); color: var(--text-muted); cursor: pointer;
}
.sidebar-toggle:hover { background: var(--bg-subtle); color: var(--text); }
.sidebar-toggle:focus-visible { outline: none; box-shadow: var(--focus-ring); }
.sidebar-toggle .nav-icon { transition: transform 0.2s ease; }
.sidebar.collapsed .sidebar-toggle .nav-icon { transform: scaleX(-1); } /* flips the chevron to point outward */

/* Icons-only mode */
.sidebar { transition: width 0.2s ease; }
.sidebar.collapsed { width: var(--sidebar-width-collapsed); padding-inline: var(--space-2); }
.sidebar.collapsed .nav-item { justify-content: center; padding-inline: 0; }
/* Visually hidden, not display:none, so screen readers still get each link's name */
.sidebar.collapsed .nav-label {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip-path: inset(50%); white-space: nowrap;
}
.sidebar.collapsed .sidebar-brand { padding-inline: 0; text-align: center; }
.sidebar.collapsed .sidebar-footer { align-items: center; }

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
  /* The drawer always shows labels, so undo icons-only styling and hide the collapse toggle */
  .sidebar.collapsed { width: var(--sidebar-width); padding-inline: var(--space-4); }
  .sidebar.collapsed .nav-item { justify-content: flex-start; padding-inline: var(--space-3); }
  .sidebar.collapsed .nav-label { position: static; width: auto; height: auto; overflow: visible; clip-path: none; }
  .sidebar.collapsed .sidebar-brand { padding-inline: var(--space-3); text-align: left; }
  .sidebar.collapsed .sidebar-footer { align-items: stretch; }
  .sidebar-toggle { display: none; }
  .sidebar-backdrop { display: block; position: fixed; inset: 0; z-index: 30; background: rgb(15 23 42 / 0.4); }
  .topbar { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3) var(--space-4); background: var(--bg-surface); border-bottom: 1px solid var(--border); }
  .content { padding: var(--space-4); }
}
@media (prefers-reduced-motion: reduce) { .sidebar, .sidebar-toggle .nav-icon { transition: none; } }
```

## Footer controls in icons-only mode

`LanguageSwitcher` and `ProfileMenu` were built for a wide header, so check each in the 64px rail. Hide secondary text with CSS (for example `.sidebar.collapsed .sidebar-footer .profile-name { display: none }`) and keep the avatar or icon. Dropdowns and menus must open to the right of the rail (`left: 100%`), not inside it. If a control cannot fit without changing its script or props, leave it as is, tell the user, and do not edit its logic.

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
- [ ] Icons-only mode: every nav link keeps an accessible name and a `title` tooltip, and the active item is still clearly highlighted.
- [ ] Toggle has `aria-expanded`, a visible focus state, and its choice survives a reload; the page works with storage blocked.
- [ ] Medium widths (about 1000px) start in rail mode with no horizontal scroll; wide widths (1440px) start expanded.
- [ ] Drawer mode (about 390px) shows labels and hides the collapse toggle, even if the saved choice is collapsed.
- [ ] Modals opened from footer controls sit above the sidebar (`z-index` above the drawer's 40).
