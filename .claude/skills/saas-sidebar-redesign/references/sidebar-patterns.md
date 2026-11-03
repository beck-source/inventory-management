# Sidebar and app shell patterns

Reference implementation for the shell. Adapt names, API style (Options vs `<script setup>`) and i18n calls to the project; the structure and behaviors are what matter.

## Contents

- Shell layout
- Sidebar component
- State: collapsed, drawer, theme
- Styles
- Where the old header controls go

## Shell layout

```vue
<div class="app-shell" :class="{ 'is-collapsed': collapsed }">
  <AppSidebar
    :collapsed="collapsed"
    :drawer-open="drawerOpen"
    @toggle-collapse="toggleCollapse"
    @close-drawer="drawerOpen = false"
  />
  <div class="app-main">
    <header class="app-topbar">
      <button class="icon-btn menu-btn" aria-label="Open navigation" :aria-expanded="drawerOpen" @click="drawerOpen = true">
        <!-- hamburger svg -->
      </button>
      <h1 class="app-topbar-title">{{ pageTitle }}</h1>
    </header>
    <!-- global filter bar, if the app had one, stays here -->
    <main class="main-content"><router-view /></main>
  </div>
</div>
```

`pageTitle` comes from route meta or the matched nav item's label. The mobile menu button is only visible below the drawer breakpoint.

Check the views first: if each view already renders its own page heading (an `h2` in a `.page-header`), do not add a desktop title bar, since it would show the title twice. In that case the top bar exists only on mobile, to hold the menu button.

## Sidebar component

Data-driven so adding a route is one line:

```js
const sections = [
  { label: 'Overview', items: [{ to: '/', icon: 'home', labelKey: 'nav.overview' }] },
  { label: 'Operations', items: [
    { to: '/inventory', icon: 'box', labelKey: 'nav.inventory' },
    { to: '/orders', icon: 'list', labelKey: 'nav.orders' },
  ] },
]
```

Template outline:

```vue
<!-- Single root: with two sibling roots the component is a fragment and $el is a comment node -->
<div class="sidebar-root">
<aside class="sidebar" :class="{ 'is-open': drawerOpen }" aria-label="Primary">
  <div class="sidebar-brand"><!-- logo mark + app name (name hidden when collapsed) --></div>
  <nav class="sidebar-nav">
    <div v-for="section in sections" :key="section.label" class="sidebar-section">
      <div class="sidebar-section-label">{{ section.label }}</div>
      <router-link v-for="item in section.items" :key="item.to" :to="item.to"
                   class="sidebar-link" :title="collapsed ? t(item.labelKey) : null">
        <svg class="sidebar-icon" aria-hidden="true"><!-- icon --></svg>
        <span class="sidebar-label">{{ t(item.labelKey) }}</span>
      </router-link>
    </div>
  </nav>
  <div class="sidebar-footer">
    <!-- LanguageSwitcher, theme toggle, ProfileMenu, collapse button -->
  </div>
</aside>
<div v-if="drawerOpen" class="sidebar-backdrop" @click="$emit('close-drawer')"></div>
</div>
```

`.sidebar-root` needs no styling of its own (`display: contents` keeps it out of the flex layout). If the rules that depend on `.is-collapsed` live in a scoped block of a child component, they will not match; put them in an unscoped `<style>` block in the shell or pass the state down as a class.

`router-link` adds `router-link-active` and `router-link-exact-active` and sets `aria-current="page"` on exact matches. Style `.router-link-active` for the highlight; for the home route `/` use the exact class only, otherwise it is active on every page.

Section labels are i18n keys too if the app is translated.

## State: collapsed, drawer, theme

Keep state in a small composable (`useLayout`) so both the shell and sidebar share it.

```js
// Storage can be blocked (private mode, disabled cookies), so every access is wrapped.
const read = (key, fallback) => { try { return localStorage.getItem(key) ?? fallback } catch { return fallback } }
const write = (key, value) => { try { localStorage.setItem(key, value) } catch { /* non-fatal: preference just won't persist */ } }

// Initialised from storage at module load so the first paint is already correct (no layout jump).
const collapsed = ref(read('sidebar-collapsed', 'false') === 'true')
const theme = ref(read('theme', window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
const drawerOpen = ref(false)

watch(collapsed, v => write('sidebar-collapsed', String(v)))
watch(theme, v => { document.documentElement.dataset.theme = v; write('theme', v) }, { immediate: true })
```

Drawer behavior:

- Close on route change (`watch(() => route.path, () => drawerOpen.value = false)`), on backdrop click, and on Escape (add the keydown listener in `onMounted`, remove in `onBeforeUnmount`).
- Lock body scroll while open (`document.body.style.overflow = 'hidden'`, restored on close) so the page behind does not scroll.
- Move focus into the drawer when it opens and back to the menu button on close.
- On desktop widths ignore `drawerOpen`; the collapsed flag does not apply to the mobile drawer, which is always full width.

## Styles

```css
.app-shell { display: flex; min-height: 100vh; background: var(--color-bg); color: var(--color-text); font-family: var(--font-sans); }
.app-main { flex: 1; min-width: 0; /* min-width: 0 lets wide tables scroll inside instead of stretching the page */ display: flex; flex-direction: column; }
.main-content { padding: var(--space-5); max-width: var(--content-max-width); width: 100%; margin: 0 auto; }

.sidebar {
  width: var(--sidebar-width); flex-shrink: 0;
  position: sticky; top: 0; height: 100vh;
  /* No overflow on the aside itself: any overflow other than visible clips the footer popovers.
     Only .sidebar-nav scrolls, so the footer stays pinned and its menus can open upward. */
  display: flex; flex-direction: column;
  background: var(--sidebar-bg); color: var(--sidebar-text);
  transition: width 0.2s ease;
  z-index: var(--z-sidebar);
}
.is-collapsed .sidebar { width: var(--sidebar-width-collapsed); }
.is-collapsed .sidebar-label,
.is-collapsed .sidebar-section-label,
.is-collapsed .sidebar-brand-name { display: none; }

.sidebar-link {
  display: flex; align-items: center; gap: var(--space-3);
  height: 40px; padding: 0 var(--space-3); margin: 2px var(--space-3);
  border-radius: var(--radius-sm); color: inherit; text-decoration: none;
  font-size: var(--text-base); font-weight: var(--weight-medium);
}
.sidebar-link:hover { background: var(--sidebar-item-hover); }
.sidebar-link.router-link-active { background: var(--sidebar-item-active); color: var(--sidebar-text-active); }
.sidebar-link:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }
.sidebar-icon { width: 20px; height: 20px; flex-shrink: 0; stroke: currentColor; fill: none; stroke-width: 1.75; }

.sidebar-nav { flex: 1; min-height: 0; overflow-y: auto; }
/* Sentence case, muted: tracked-out all-caps labels are a template tell and add nothing the grouping does not already say */
.sidebar-section-label { padding: var(--space-4) var(--space-4) var(--space-1); font-size: var(--text-xs); font-weight: var(--weight-medium); opacity: 0.6; }
.sidebar-footer { margin-top: auto; padding: var(--space-3); border-top: 1px solid var(--sidebar-border); }

.app-topbar, .menu-btn { display: none; }
.sidebar-backdrop { display: none; }

/* 900px matches --breakpoint-drawer; custom properties cannot be used in media queries */
@media (max-width: 900px) {
  /* z-index must sit ABOVE the backdrop (the backdrop covers the page, the drawer sits on top of it),
     otherwise the backdrop swallows clicks meant for the drawer.
     visibility:hidden (delayed until the slide-out ends) removes the closed drawer from the tab order,
     which a translate alone does not. */
  .sidebar { position: fixed; inset: 0 auto 0 0; width: var(--sidebar-width); transform: translateX(-100%); visibility: hidden;
             transition: transform 0.2s ease, visibility 0s linear 0.2s; box-shadow: var(--shadow-lg); z-index: calc(var(--z-backdrop) + 1); }
  .sidebar.is-open { transform: none; visibility: visible; transition-delay: 0s; }
  .is-collapsed .sidebar { width: var(--sidebar-width); }          /* drawer ignores collapsed state */
  .is-collapsed .sidebar-label, .is-collapsed .sidebar-section-label, .is-collapsed .sidebar-brand-name { display: revert; }
  .sidebar-backdrop { display: block; position: fixed; inset: 0; background: rgb(15 23 42 / 0.5); z-index: var(--z-backdrop); }
  .app-topbar { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-3) var(--space-4); background: var(--color-surface); border-bottom: 1px solid var(--color-border); position: sticky; top: 0; z-index: var(--z-sticky); }
  .menu-btn { display: inline-flex; }
  .main-content { padding: var(--space-4); }
}

@media (prefers-reduced-motion: reduce) { .sidebar { transition: none; } }
```

## Where the old header controls go

| Old header item | New home |
| --- | --- |
| Logo / app name | Sidebar brand block (name hidden when collapsed) |
| Nav tabs | Sidebar nav sections |
| Language switcher, profile menu | Sidebar footer; make popovers open upward and check they are not clipped by the sidebar's `overflow` |
| Global filter bar | Top of the content area, below the page title, unchanged |
| Search / notifications (if any) | Top bar inside the main column on desktop |

If a control's popover is clipped, render it with `position: fixed` or teleport it to `body` rather than loosening the sidebar's overflow.
