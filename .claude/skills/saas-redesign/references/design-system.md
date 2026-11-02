# Design System Reference

Default values for the SaaS redesign. Map these onto the app's existing palette. The defaults below match a slate/blue scheme.

## 1. Design Tokens

Put this in the global stylesheet (an unscoped `<style>` in `App.vue`, or `src/assets/tokens.css` imported in `main.js`).

```css
:root {
  /* Color: surfaces */
  --color-bg: #f8fafc;              /* page background */
  --color-surface: #ffffff;         /* cards, sidebar, top bar */
  --color-surface-muted: #f1f5f9;   /* hover rows, subtle fills */
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;

  /* Color: text */
  --color-text: #0f172a;            /* headings, primary text */
  --color-text-secondary: #475569;  /* body, table cells */
  --color-text-muted: #64748b;      /* labels, captions */

  /* Color: brand and status */
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-soft: #eff6ff;
  --color-success: #059669;
  --color-success-soft: #d1fae5;
  --color-warning: #d97706;
  --color-warning-soft: #fef3c7;
  --color-danger: #dc2626;
  --color-danger-soft: #fee2e2;
  --color-info: #2563eb;
  --color-info-soft: #dbeafe;

  /* Sidebar (light by default; see the dark variant below) */
  --sidebar-bg: var(--color-surface);
  --sidebar-border: var(--color-border);
  --sidebar-text: var(--color-text-muted);
  --sidebar-text-hover: var(--color-text);
  --sidebar-item-hover: var(--color-surface-muted);
  --sidebar-item-active-bg: var(--color-primary-soft);
  --sidebar-item-active-text: var(--color-primary);

  /* Spacing: 4px grid. Use only these values. */
  --space-1: 0.25rem;   /*  4px */
  --space-2: 0.5rem;    /*  8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */

  /* Radius */
  --radius-sm: 6px;     /* badges, small controls */
  --radius-md: 8px;     /* buttons, inputs, nav items */
  --radius-lg: 12px;    /* cards, modals */

  /* Shadow: keep these quiet; borders carry most of the structure */
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.06);
  --shadow-lg: 0 12px 32px rgba(15, 23, 42, 0.12);  /* modals, popovers */

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --text-xs: 0.75rem;     /* 12px - badges, table headers */
  --text-sm: 0.8125rem;   /* 13px - captions, labels */
  --text-base: 0.875rem;  /* 14px - body, table cells, nav */
  --text-md: 1rem;        /* 16px - card titles */
  --text-lg: 1.25rem;     /* 20px - section titles */
  --text-xl: 1.5rem;      /* 24px - page titles */
  --text-2xl: 1.875rem;   /* 30px - hero metrics */

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 72px;
  --topbar-height: 64px;
  --content-max-width: 1440px;
  --page-gutter: var(--space-8);

  /* Motion */
  --transition-fast: 150ms ease;

  /* Stacking: sidebar < top bar < mobile drawer < modals */
  --z-sidebar: 40;
  --z-topbar: 50;
  --z-drawer: 200;
  --z-modal: 1000;
}

@media (max-width: 767px) {
  :root { --page-gutter: var(--space-4); }
}
```

**Dark sidebar variant:** override only the sidebar tokens.

```css
:root {
  --sidebar-bg: #0f172a;
  --sidebar-border: #1e293b;
  --sidebar-text: #94a3b8;
  --sidebar-text-hover: #f1f5f9;
  --sidebar-item-hover: #1e293b;
  --sidebar-item-active-bg: #1e293b;
  --sidebar-item-active-text: #ffffff;
}
```

## 2. Spacing Rules

| Context | Value |
|---|---|
| Page padding (content area) | `--page-gutter` (32px desktop, 16px mobile) |
| Page header to first section | `--space-6` |
| Between sections/cards (vertical) | `--space-6` |
| Grid gap: stat cards, card grids | `--space-4` (dense) or `--space-6` |
| Card padding | `--space-5` (dense data) or `--space-6` |
| Card header to body | `--space-4` |
| Stack inside a card (label/value, form rows) | `--space-2` to `--space-3` |
| Inline gap (icon + text, button groups) | `--space-2` |
| Table cell padding | `--space-3` vertical, `--space-4` horizontal |
| Control height (buttons, inputs, selects) | 36px |
| Sidebar nav item | 36-40px tall, `--space-3` horizontal padding |

Never use values outside the scale (no `0.313rem`, `0.938rem`, `14px`). Round to the nearest token.

## 3. App Shell Template

Adapt this to the app. Keep the existing header widgets, modals, and filter bar exactly as they are wired now, and only move where they sit.

```vue
<template>
  <div :class="['app-shell', { 'sidebar-collapsed': sidebarCollapsed }]">
    <AppSidebar
      :items="navItems"
      :collapsed="sidebarCollapsed"
      :mobile-open="mobileNavOpen"
      @toggle-collapse="toggleCollapse"
      @navigate="mobileNavOpen = false"
    >
      <template #brand>
        <!-- existing logo/company name -->
      </template>
    </AppSidebar>

    <!-- Backdrop is only rendered on mobile while the drawer is open -->
    <div v-if="mobileNavOpen" class="sidebar-backdrop" @click="mobileNavOpen = false" />

    <div class="main-column">
      <header class="topbar">
        <button
          class="icon-button menu-button"
          :aria-expanded="mobileNavOpen"
          aria-label="Open navigation"
          @click="mobileNavOpen = true"
        >
          <!-- hamburger icon -->
        </button>
        <h1 class="topbar-title">{{ currentTitle }}</h1>
        <div class="topbar-actions">
          <!-- existing widgets: LanguageSwitcher, ProfileMenu, etc. -->
        </div>
      </header>

      <!-- existing global filter bar, if any -->

      <main class="content">
        <router-view />
      </main>
    </div>

    <!-- existing modals stay here, unchanged -->
  </div>
</template>
```

Script additions (match the project's style; this repo uses `export default { setup() }`):

```js
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

const STORAGE_KEY = 'sidebar-collapsed'

// localStorage can throw (private mode, blocked storage); fall back to expanded
const readCollapsed = () => {
  try { return localStorage.getItem(STORAGE_KEY) === '1' } catch { return false }
}

// inside setup():
const route = useRoute()
const sidebarCollapsed = ref(readCollapsed())
const mobileNavOpen = ref(false)

const toggleCollapse = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  try { localStorage.setItem(STORAGE_KEY, sidebarCollapsed.value ? '1' : '0') } catch { /* non-critical */ }
}

// Close the drawer on any route change, including browser back/forward,
// which doesn't go through the sidebar's navigate event
watch(() => route.path, () => { mobileNavOpen.value = false })

const onKeydown = (e) => { if (e.key === 'Escape') mobileNavOpen.value = false }
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

// computed so labels update when the locale changes
const navItems = computed(() => [
  { to: '/', label: t('nav.overview'), icon: ICONS.home },
  // ... one entry per route in the old top nav, same paths and labels
])

const currentTitle = computed(() => navItems.value.find(i => isActivePath(i.to))?.label ?? '')
```

Shell CSS:

```css
.app-shell {
  display: grid;
  /* minmax(0, 1fr) rather than 1fr: wide tables or charts would otherwise
     force the column wider than the viewport and cause page-level horizontal scroll */
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  background: var(--color-bg);
  transition: grid-template-columns var(--transition-fast);
}

.app-shell.sidebar-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) minmax(0, 1fr);
}

.main-column {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: 0 var(--page-gutter);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--color-border);
}

.topbar-title {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text);
}

.topbar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.menu-button { display: none; }

.content {
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--page-gutter);
}

.sidebar-backdrop { display: none; }

/* Below 1024px the sidebar leaves the grid and becomes a drawer.
   Collapsed mode is a desktop-only concept, so it's ignored here. */
@media (max-width: 1023px) {
  .app-shell,
  .app-shell.sidebar-collapsed {
    grid-template-columns: minmax(0, 1fr);
  }
  .menu-button { display: inline-flex; }
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: calc(var(--z-drawer) - 1);
    background: rgba(15, 23, 42, 0.4);
  }
}
```

## 4. AppSidebar.vue Template

```vue
<template>
  <aside
    :class="['sidebar', { collapsed, 'mobile-open': mobileOpen }]"
    aria-label="Main navigation"
  >
    <div class="sidebar-brand">
      <slot name="brand" />
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        :class="['nav-item', { active: isActive(item.to) }]"
        :aria-current="isActive(item.to) ? 'page' : undefined"
        :title="collapsed ? item.label : undefined"
        @click="$emit('navigate')"
      >
        <!-- icons are static SVG strings defined in code, never user data -->
        <span class="nav-icon" aria-hidden="true" v-html="item.icon" />
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <slot name="footer" />
      <button
        class="nav-item collapse-toggle"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="$emit('toggle-collapse')"
      >
        <span class="nav-icon" aria-hidden="true" v-html="collapsed ? ICONS.expand : ICONS.collapse" />
        <span class="nav-label">Collapse</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { useRoute } from 'vue-router'
import { ICONS } from './icons'

export default {
  name: 'AppSidebar',
  props: {
    items: { type: Array, required: true },
    collapsed: { type: Boolean, default: false },
    mobileOpen: { type: Boolean, default: false }
  },
  emits: ['navigate', 'toggle-collapse'],
  setup() {
    const route = useRoute()

    // '/' is a prefix of every path, so it must match exactly; other items also
    // match nested routes (e.g. /orders/123 keeps "Orders" highlighted)
    const isActive = (to) =>
      to === '/' ? route.path === '/' : route.path === to || route.path.startsWith(to + '/')

    return { isActive, ICONS }
  }
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-brand {
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  padding: 0 var(--space-5);
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
}

.sidebar-footer {
  padding: var(--space-3);
  border-top: 1px solid var(--sidebar-border);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 38px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--sidebar-text);
  font: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.nav-item:hover {
  background: var(--sidebar-item-hover);
  color: var(--sidebar-text-hover);
}

.nav-item.active {
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-item-active-text);
  font-weight: 600;
}

.nav-item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.collapse-toggle { width: 100%; }

.nav-icon {
  display: inline-flex;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-icon :deep(svg) { width: 100%; height: 100%; }

/* Collapsed: icons only, centered. Labels remain available via the title tooltip. */
.sidebar.collapsed .nav-label { display: none; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 0; }
.sidebar.collapsed .sidebar-brand { justify-content: center; padding: 0; }

@media (max-width: 1023px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--sidebar-width);
    z-index: var(--z-drawer);
    transform: translateX(-100%);
    transition: transform 200ms ease;
    box-shadow: var(--shadow-lg);
  }
  .sidebar.mobile-open { transform: translateX(0); }

  /* The drawer always shows full labels, even if desktop collapse is on */
  .sidebar.collapsed .nav-label { display: inline; }
  .sidebar.collapsed .nav-item { justify-content: flex-start; padding: 0 var(--space-3); }
  .collapse-toggle { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar, .nav-item { transition: none; }
}
</style>
```

## 5. Icons

Keep the icons in `src/components/icons.js` as static SVG strings: 24x24 viewBox, `stroke="currentColor"`, `stroke-width="1.75"`, `fill="none"`, round caps and joins. Using stroke icons in one consistent style is what makes them read as a set. Draw simple geometric shapes; don't copy a branded icon set's paths.

```js
const svg = (paths) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`

export const ICONS = {
  home: svg('<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>'),
  box: svg('<path d="M3 7.5 12 3l9 4.5v9L12 21l-9-4.5z"/><path d="M3 7.5 12 12l9-4.5M12 12v9"/>'),
  cart: svg('<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.5 12h12L22 7H6.2"/>'),
  wallet: svg('<rect x="3" y="6" width="18" height="14" rx="2"/><path d="M3 10h18M16 15h2"/>'),
  trend: svg('<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>'),
  report: svg('<path d="M6 3h9l4 4v14H6z"/><path d="M9 13h6M9 17h6M9 9h3"/>'),
  menu: svg('<path d="M4 6h16M4 12h16M4 18h16"/>'),
  collapse: svg('<path d="M15 6l-6 6 6 6"/>'),
  expand: svg('<path d="M9 6l6 6-6 6"/>')
}
```

## 6. Shared Component Patterns

**Page header** (top of every view):

```css
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}
.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-text);
}
.page-header p {
  margin-top: var(--space-1);
  font-size: var(--text-base);
  color: var(--color-text-muted);
}
```

**Card:**

```css
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);
}
.card + .card { margin-top: var(--space-6); }
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}
.card-title { font-size: var(--text-md); font-weight: 600; color: var(--color-text); }
```

**Stat card:** label on top (muted, `--text-sm`, weight 500, sentence case, not shouted uppercase), value below (`--text-2xl`, weight 700, `tabular-nums`), optional delta line (`--text-sm`, status color).

**Table:** header row `--color-surface-muted`, `--text-xs` uppercase with 0.04em tracking, `--color-text-muted`; cells `--text-base`, `--color-text-secondary`; row borders `--color-border`; hover `--color-surface-muted`; numeric columns right-aligned with `tabular-nums`. Wrap the table in `.table-container { overflow-x: auto; }` so wide tables scroll inside their card.

**Badge:** `--radius-sm`, `--text-xs`, weight 600, `padding: 2px var(--space-2)`, `*-soft` background with the matching status text color.

**Buttons:** 36px tall, `--radius-md`, `--text-base` weight 500. Primary is solid `--color-primary`. Secondary is a surface background with a `--color-border` outline. Ghost is transparent with a muted-surface hover.

## 7. Polish Checklist

- [ ] One font family; sizes only from the type scale
- [ ] Every spacing value comes from the scale; no leftover ad-hoc rem values
- [ ] Radii consistent: cards `lg`, controls `md`, badges `sm`
- [ ] Structure comes from borders; shadows stay subtle (`sm` on cards, `lg` only on overlays)
- [ ] Every interactive element has hover, active, and `:focus-visible` states
- [ ] Transitions are 150ms and limited to color, background, and transform; `prefers-reduced-motion` respected
- [ ] Numbers use `tabular-nums`; currency and percentages formatted consistently
- [ ] Text contrast is at least 4.5:1 (muted `#64748b` on white passes; don't go lighter for body text)
- [ ] Loading, error, and empty states styled and the same across views
- [ ] Modals and dropdowns layer above the sidebar and top bar (`--z-modal`)
- [ ] No horizontal page scroll at 390px; tables scroll inside their container
- [ ] Sidebar uses `<nav>` with `aria-label`; the active link has `aria-current="page"`; the menu button has `aria-expanded`
- [ ] No emojis; no dead CSS left from the old top nav
