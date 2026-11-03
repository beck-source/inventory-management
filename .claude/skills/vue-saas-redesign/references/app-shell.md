# App shell: sidebar, top bar, content

Adapt names, nav items and icons to the app. Keep global things the old `App.vue` mounted (modals, filter bar, language switcher, profile menu) and re-home them as described in SKILL.md.

## Collapse state composable

```js
// src/composables/useSidebar.js
import { ref, watch } from 'vue'

const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
const mobileOpen = ref(false)
watch(collapsed, v => localStorage.setItem('sidebar-collapsed', String(v)))

export function useSidebar() {
  return {
    collapsed,
    mobileOpen,
    toggle: () => { collapsed.value = !collapsed.value },
    openMobile: () => { mobileOpen.value = true },
    closeMobile: () => { mobileOpen.value = false }
  }
}
```

## Layout (App.vue)

```vue
<template>
  <div class="shell" :class="{ collapsed }">
    <div v-if="mobileOpen" class="backdrop" @click="closeMobile" />
    <aside class="sidebar" :class="{ open: mobileOpen }">
      <div class="sidebar-head">
        <!-- logo mark + app name (name hidden when collapsed) -->
      </div>
      <nav class="sidebar-nav" aria-label="Main">
        <router-link v-for="item in navItems" :key="item.to" :to="item.to"
                     class="nav-link" active-class="active" exact-active-class="active"
                     :title="collapsed ? item.label : null" @click="closeMobile">
          <component :is="item.icon" class="nav-icon" />
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-foot">
        <!-- language switcher, profile menu, then the collapse button -->
        <button class="collapse-btn" :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'" @click="toggle" />
      </div>
    </aside>

    <div class="main-col">
      <header class="topbar">
        <button class="menu-btn" aria-label="Open navigation" @click="openMobile" />
        <!-- page title slot or filters / global controls -->
      </header>
      <main class="content"><div class="content-inner"><router-view /></div></main>
    </div>
  </div>
</template>
```

Use `exact-active-class` for the root route (`/`) so it is not active on every page. Keep labels going through the app's i18n if it has one.

## Styles

```css
.shell { display: flex; height: 100vh; background: var(--bg); color: var(--text); font-family: var(--font); font-size: var(--text-base); }
.sidebar { width: var(--sidebar-w); flex: none; display: flex; flex-direction: column; background: var(--surface); border-right: 1px solid var(--border); transition: width var(--ease); z-index: 200; }
.collapsed .sidebar { width: var(--sidebar-w-collapsed); }
.sidebar-head { height: var(--topbar-h); display: flex; align-items: center; padding: 0 var(--space-5); border-bottom: 1px solid var(--border); }
.sidebar-nav { flex: 1; overflow-y: auto; padding: var(--space-4) var(--space-3); display: flex; flex-direction: column; gap: var(--space-1); }
.nav-link { display: flex; align-items: center; gap: var(--space-3); height: 40px; padding: 0 var(--space-3); border-radius: var(--radius-md); color: var(--text-muted); text-decoration: none; font-weight: 500; transition: background var(--ease), color var(--ease); }
.nav-link:hover { background: var(--surface-muted); color: var(--text); }
.nav-link.active { background: var(--accent-soft); color: var(--accent); }
.nav-link:focus-visible { outline: none; box-shadow: 0 0 0 3px var(--accent-soft); }
.nav-icon { width: 20px; height: 20px; flex: none; }
.collapsed .nav-label, .collapsed .brand-name { display: none; }
.collapsed .nav-link { justify-content: center; padding: 0; }
.sidebar-foot { padding: var(--space-3); border-top: 1px solid var(--border); }
.main-col { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar { height: var(--topbar-h); flex: none; display: flex; align-items: center; gap: var(--space-4); padding: 0 var(--space-8); background: var(--surface); border-bottom: 1px solid var(--border); }
.content { flex: 1; overflow-y: auto; }
.content-inner { max-width: var(--content-max); margin: 0 auto; padding: var(--space-8); }
.menu-btn, .backdrop { display: none; }

@media (max-width: 768px) {
  .sidebar { position: fixed; inset: 0 auto 0 0; transform: translateX(-100%); transition: transform var(--ease); width: var(--sidebar-w); }
  .collapsed .sidebar { width: var(--sidebar-w); }
  .collapsed .nav-label, .collapsed .brand-name { display: inline; }
  .collapsed .nav-link { justify-content: flex-start; padding: 0 var(--space-3); }
  .sidebar.open { transform: none; box-shadow: var(--shadow-md); }
  .backdrop { display: block; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.4); z-index: 150; }
  .menu-btn { display: inline-flex; }
  .topbar { padding: 0 var(--space-4); }
  .content-inner { padding: var(--space-4); }
}
```

Modals should use a `z-index` above 200 (the sidebar) and be teleported to `body` if an ancestor clips them.
