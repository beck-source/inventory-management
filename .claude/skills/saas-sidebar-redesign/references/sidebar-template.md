# App shell templates

Starting points to adapt, not to paste verbatim. Match the project's conventions: `<script setup>` vs Options API, i18n usage, file naming, and whether the shared state lives in a composable or a store.

## Shared layout state: `composables/useSidebar.js`

The sidebar and header both need to read and change this state, so it lives in a module-level ref and isn't passed around as props.

```js
import { ref, watch } from 'vue'

const STORAGE_KEY = 'sidebar-collapsed'

function readCollapsed() {
  // Storage can throw (private mode, blocked site data), so fall back to expanded
  try { return localStorage.getItem(STORAGE_KEY) === '1' } catch { return false }
}

const collapsed = ref(readCollapsed())
const mobileOpen = ref(false)

watch(collapsed, (v) => {
  try { localStorage.setItem(STORAGE_KEY, v ? '1' : '0') } catch { /* non-critical */ }
})

// Lock page scroll behind the open mobile drawer
watch(mobileOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

export function useSidebar() {
  return {
    collapsed,
    mobileOpen,
    toggleCollapsed: () => { collapsed.value = !collapsed.value },
    openMobile: () => { mobileOpen.value = true },
    closeMobile: () => { mobileOpen.value = false },
  }
}
```

## Nav config: one source of truth

```js
// navItems.js: labels are i18n keys if the app uses i18n, plain strings otherwise
export const navItems = [
  { to: '/',          label: 'nav.overview',  icon: 'home',   exact: true },
  { to: '/inventory', label: 'nav.inventory', icon: 'box' },
  { to: '/orders',    label: 'nav.orders',    icon: 'cart' },
  // ...
]
```

## Icons: `NavIcon.vue`

Inline 24x24-viewBox line icons rendered at 20px. Add paths only for the icons actually used.

```vue
<script setup>
defineProps({ name: { type: String, required: true } })
// Feather/Lucide-style paths (MIT); stroke inherits currentColor so active/hover colors apply
const paths = {
  home:     'M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z',
  box:      'M21 8 12 3 3 8v8l9 5 9-5zM3 8l9 5 9-5M12 13v8',
  cart:     'M3 3h2l2.4 12.2a1 1 0 0 0 1 .8h9.7a1 1 0 0 0 1-.8L21 7H6M9 21h.01M18 21h.01',
  dollar:   'M12 2v20M17 6H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',
  trend:    'M3 17l6-6 4 4 8-8M15 7h6v6',
  file:     'M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8zM14 3v5h5M9 13h6M9 17h6',
  list:     'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  chevrons: 'M11 17l-5-5 5-5M18 17l-5-5 5-5',
  menu:     'M3 6h18M3 12h18M3 18h18',
  close:    'M18 6 6 18M6 6l12 12',
}
</script>

<template>
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path :d="paths[name]" />
  </svg>
</template>
```

## `AppSidebar.vue`

```vue
<script setup>
import { watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'          // drop if the app has no i18n
import { useSidebar } from '../composables/useSidebar'
import { navItems } from '../navItems'
import NavIcon from './NavIcon.vue'

const { t } = useI18n()
const route = useRoute()
const { collapsed, mobileOpen, toggleCollapsed, closeMobile } = useSidebar()

// Close the drawer after navigating on mobile
watch(() => route.path, closeMobile)

const onKey = (e) => { if (e.key === 'Escape') closeMobile() }
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div v-if="mobileOpen" class="sidebar-backdrop" @click="closeMobile" />
  <aside id="app-sidebar" class="sidebar"
         :class="{ 'is-collapsed': collapsed, 'is-open': mobileOpen }">
    <div class="sidebar-brand">
      <div class="brand-mark" aria-hidden="true">IM</div>
      <span class="brand-name">{{ t('nav.companyName') }}</span>
    </div>

    <nav class="sidebar-nav" aria-label="Main">
      <router-link v-for="item in navItems" :key="item.to" :to="item.to" custom
                   v-slot="{ href, navigate, isActive, isExactActive }">
        <a :href="href" @click="navigate" class="nav-item"
           :class="{ active: item.exact ? isExactActive : isActive }"
           :aria-current="(item.exact ? isExactActive : isActive) ? 'page' : undefined"
           :title="collapsed ? t(item.label) : undefined">
          <NavIcon :name="item.icon" />
          <span class="nav-label">{{ t(item.label) }}</span>
        </a>
      </router-link>
    </nav>

    <button class="sidebar-collapse" type="button" @click="toggleCollapsed"
            :aria-expanded="!collapsed" aria-controls="app-sidebar"
            :aria-label="collapsed ? t('nav.expand') : t('nav.collapse')">
      <NavIcon name="chevrons" :class="{ flipped: collapsed }" />
      <span class="nav-label">{{ t('nav.collapse') }}</span>
    </button>
  </aside>
</template>

<style scoped>
.sidebar {
  position: sticky; top: 0; height: 100vh;
  width: var(--sidebar-width-expanded);
  display: flex; flex-direction: column;
  background: var(--sidebar-bg); color: var(--sidebar-text);
  transition: width var(--duration) var(--ease);
  z-index: var(--z-sidebar); overflow: hidden;
}
.sidebar.is-collapsed { width: var(--sidebar-width-collapsed); }

.sidebar-brand { display: flex; align-items: center; gap: var(--space-3);
  height: var(--header-height); padding: 0 var(--space-4);
  border-bottom: 1px solid rgba(255,255,255,0.08); }
.brand-mark { flex: none; width: 32px; height: 32px; border-radius: var(--radius-md);
  display: grid; place-items: center; background: var(--accent); color: #fff;
  font-weight: 700; font-size: var(--text-sm); }
.brand-name { color: #fff; font-weight: 600; white-space: nowrap; }

.sidebar-nav { flex: 1; padding: var(--space-3); display: flex; flex-direction: column;
  gap: var(--space-1); overflow-y: auto; }
.nav-item, .sidebar-collapse {
  display: flex; align-items: center; gap: var(--space-3);
  height: 40px; padding: 0 var(--space-3); border-radius: var(--radius-md);
  color: var(--sidebar-text); text-decoration: none; white-space: nowrap;
  font-size: var(--text-base); font-weight: 500;
  transition: background var(--duration) var(--ease), color var(--duration) var(--ease);
}
.nav-item svg, .sidebar-collapse svg { flex: none; }
.nav-item:hover { background: var(--sidebar-item-hover); color: var(--sidebar-text-active); }
.nav-item.active { background: var(--sidebar-item-active); color: var(--sidebar-text-active);
  box-shadow: inset 3px 0 0 var(--accent); }

.sidebar-collapse { margin: var(--space-3); background: none; border: 0; cursor: pointer;
  border-top: 1px solid rgba(255,255,255,0.08); border-radius: 0; padding-top: var(--space-3); height: auto; }
.flipped { transform: rotate(180deg); }

/* Icon rail: hide labels, center icons */
.is-collapsed .nav-label, .is-collapsed .brand-name { display: none; }
.is-collapsed .nav-item, .is-collapsed .sidebar-brand { justify-content: center; padding: 0; }

.sidebar-backdrop { display: none; }

/* Mobile: off-canvas drawer, always expanded when open */
@media (max-width: 1023px) {
  .sidebar { position: fixed; left: 0; top: 0; z-index: var(--z-drawer);
    width: var(--sidebar-width-expanded); transform: translateX(-100%);
    transition: transform var(--duration) var(--ease); box-shadow: var(--shadow-lg); }
  .sidebar.is-open { transform: translateX(0); }
  .sidebar.is-collapsed { width: var(--sidebar-width-expanded); }
  .is-collapsed .nav-label, .is-collapsed .brand-name { display: inline; }
  .is-collapsed .nav-item { justify-content: flex-start; padding: 0 var(--space-3); }
  .sidebar-collapse { display: none; }
  .sidebar-backdrop { display: block; position: fixed; inset: 0;
    background: rgba(15, 23, 42, 0.45); z-index: var(--z-backdrop); }
}
</style>
```

## `App.vue` shell

```vue
<template>
  <div class="app-shell">
    <AppSidebar />
    <div class="app-main">
      <AppHeader />            <!-- hamburger + page title + filters + lang + profile -->
      <main class="app-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style>
.app-shell { display: flex; min-height: 100vh; background: var(--bg); }
.app-main { flex: 1; min-width: 0; display: flex; flex-direction: column; } /* min-width:0 stops wide tables from causing page overflow */
.app-content { flex: 1; }
</style>
```

## `AppHeader.vue` essentials

- `position: sticky; top: 0; height: var(--header-height); background: var(--surface); border-bottom: 1px solid var(--border); z-index: var(--z-header);`
- Hamburger button is visible only below 1024px: `@click="openMobile"`, `aria-controls="app-sidebar"`, `:aria-expanded="mobileOpen"`.
- Page title comes from `route.meta.title` (or the matching nav item's label).
- Right side: the existing global controls (FilterBar, LanguageSwitcher, ProfileMenu), moved from the old top nav unchanged. If the filters are too wide for the header, render them as a second sticky row below it.
