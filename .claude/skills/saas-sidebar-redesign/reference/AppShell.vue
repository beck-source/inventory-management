<!--
  Reference SaaS shell for the saas-sidebar-redesign skill.
  Adapt it into the app's root component: replace navItems with the app's routes,
  move the existing header widgets into the topbar slot, keep the app's own logic.
  Requires src/styles/tokens.css (templates/tokens.css) to be imported in main.js.
-->
<template>
  <div class="app" :class="{ 'is-collapsed': isCollapsed, 'drawer-open': isDrawerOpen }">
    <aside id="app-sidebar" class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-mark" aria-hidden="true">{{ brandInitial }}</div>
        <div class="brand-text">
          <span class="brand-name">{{ brandName }}</span>
          <span class="brand-subtitle">{{ brandSubtitle }}</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <!-- The root route needs exact matching, or it stays active on every page. -->
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :active-class="item.path === '/' ? '' : 'is-active'"
          exact-active-class="is-active"
          :title="item.label"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path v-for="(d, i) in item.icon" :key="`${item.path}-${i}`" :d="d" />
          </svg>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <button
        class="collapse-toggle"
        type="button"
        :aria-label="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :aria-expanded="!isCollapsed"
        @click="toggleCollapse"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M15 6l-6 6 6 6" />
        </svg>
      </button>
    </aside>

    <!-- Only rendered while the mobile drawer is open. -->
    <div v-if="isDrawerOpen" class="drawer-backdrop" @click="closeDrawer"></div>

    <div class="app-main">
      <header class="topbar">
        <button
          class="menu-button"
          type="button"
          aria-label="Open menu"
          aria-controls="app-sidebar"
          :aria-expanded="isDrawerOpen"
          @click="openDrawer"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
               stroke-linecap="round" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
        </button>
        <h1 class="page-title">{{ pageTitle }}</h1>
        <div class="topbar-actions">
          <!-- Move the app's existing header widgets here (language switcher, profile menu, ...). -->
          <slot name="actions" />
        </div>
      </header>

      <!-- A global filter bar or toolbar goes here, sticky at top: var(--topbar-h). -->
      <slot name="toolbar" />

      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

const STORAGE_KEY = 'sidebar-collapsed'

// localStorage throws in private windows and when site data is blocked,
// so every access is guarded and the shell falls back to the expanded state.
const readCollapsed = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

const writeCollapsed = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(value))
  } catch {
    // Storage unavailable: the choice just won't survive a reload.
  }
}

export default {
  name: 'AppShell',
  props: {
    brandName: { type: String, default: 'Company' },
    brandSubtitle: { type: String, default: '' }
  },
  setup(props) {
    const route = useRoute()
    const isCollapsed = ref(readCollapsed())
    const isDrawerOpen = ref(false)

    // Replace with the app's routes. Labels should come from i18n when the app has it.
    // Icons are lists of SVG path strings drawn on a 24x24 grid.
    const navItems = [
      { path: '/', label: 'Overview', icon: ['M3 12l9-8 9 8', 'M5 10v10h14V10'] },
      { path: '/inventory', label: 'Inventory', icon: ['M3 7l9-4 9 4-9 4-9-4z', 'M3 7v10l9 4 9-4V7'] },
      { path: '/orders', label: 'Orders', icon: ['M6 3h12v18l-3-2-3 2-3-2-3 2V3z', 'M9 8h6M9 12h6'] },
      { path: '/reports', label: 'Reports', icon: ['M4 20V10', 'M10 20V4', 'M16 20v-7', 'M22 20H2'] }
    ]

    // The topbar title comes from the nav item matching the current route,
    // so it stays in sync with the sidebar labels (and their translations).
    const pageTitle = computed(() => {
      const match = navItems.find(item => item.path === route.path)
      return match ? match.label : navItems[0].label
    })

    const brandInitial = computed(() => (props.brandName || '?').charAt(0).toUpperCase())

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      writeCollapsed(isCollapsed.value)
    }

    const openDrawer = () => { isDrawerOpen.value = true }
    const closeDrawer = () => { isDrawerOpen.value = false }

    // Navigating from the drawer should reveal the new page, not leave the drawer over it.
    watch(() => route.path, closeDrawer)

    const onKeydown = (event) => {
      if (event.key === 'Escape' && isDrawerOpen.value) closeDrawer()
    }
    onMounted(() => window.addEventListener('keydown', onKeydown))
    onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

    return {
      isCollapsed,
      isDrawerOpen,
      navItems,
      pageTitle,
      brandInitial,
      toggleCollapse,
      openDrawer,
      closeDrawer
    }
  }
}
</script>

<style>
.app {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
}

/* ---------- Sidebar ---------- */
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: var(--sidebar-w);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  z-index: var(--z-sidebar);
  transition: width var(--transition-fast), transform var(--transition-fast);
  overflow: hidden;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-h);
  padding: 0 var(--space-5);
  border-bottom: 1px solid var(--sidebar-divider);
}

.brand-mark {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--sidebar-accent);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
}

.brand-text { display: flex; flex-direction: column; min-width: 0; }
.brand-name { color: #fff; font-weight: 600; font-size: 0.938rem; white-space: nowrap; }
.brand-subtitle { font-size: 0.75rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.nav-link:hover { background: var(--sidebar-hover-bg); color: var(--sidebar-text-hover); }

.nav-link.is-active { background: var(--sidebar-active-bg); color: var(--sidebar-active-text); }

/* Accent bar at the sidebar's left edge for the active link. */
.nav-link.is-active::before {
  content: '';
  position: absolute;
  left: calc(-1 * var(--space-3));
  top: var(--space-2);
  bottom: var(--space-2);
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--sidebar-accent);
}

.nav-icon { width: 20px; height: 20px; flex-shrink: 0; }

.collapse-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: var(--space-3);
  height: 36px;
  border: 1px solid var(--sidebar-divider);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--sidebar-text);
  cursor: pointer;
}

.collapse-toggle:hover { background: var(--sidebar-hover-bg); color: var(--sidebar-text-hover); }
.collapse-toggle svg { width: 18px; height: 18px; transition: transform var(--transition-fast); }

/* Icon rail: shared by the user-collapsed state (>= 1024px) and the medium tier. */
.app.is-collapsed .sidebar { width: var(--sidebar-w-collapsed); }
.app.is-collapsed .collapse-toggle svg { transform: rotate(180deg); }
.app.is-collapsed .brand-text,
.app.is-collapsed .nav-label { display: none; }
.app.is-collapsed .sidebar-brand,
.app.is-collapsed .nav-link { justify-content: center; }
.app.is-collapsed .sidebar-brand { padding: 0; }

/* ---------- Main column ---------- */
.app-main {
  flex: 1;
  /* Without min-width: 0, wide tables force the whole page to scroll sideways. */
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-topbar);
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-6);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.page-title { font-size: 1.125rem; font-weight: 600; letter-spacing: -0.01em; margin: 0; }
.topbar-actions { margin-left: auto; display: flex; align-items: center; gap: var(--space-3); }

.menu-button {
  display: none;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
}
.menu-button svg { width: 20px; height: 20px; }

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-w);
  padding: var(--space-6);
}

.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: var(--z-drawer-backdrop);
}

/* ---------- Medium: 640-1023px, always the icon rail ---------- */
@media (max-width: 1023px) {
  .sidebar { width: var(--sidebar-w-collapsed); }
  .brand-text,
  .nav-label,
  .collapse-toggle { display: none; }
  .sidebar-brand,
  .nav-link { justify-content: center; }
  .sidebar-brand { padding: 0; }
}

/* ---------- Small: < 640px, off-canvas drawer ---------- */
@media (max-width: 639px) {
  /* The drawer always shows labels, whatever the saved collapsed state is:
     a narrow drawer of bare icons would waste the space it opens into. */
  .sidebar,
  .app.is-collapsed .sidebar {
    position: fixed;
    left: 0;
    width: var(--sidebar-w);
    transform: translateX(-100%);
  }
  .app.drawer-open .sidebar { transform: translateX(0); }
  .app .brand-text,
  .app .nav-label { display: flex; }
  .app .sidebar-brand { padding: 0 var(--space-5); justify-content: flex-start; }
  .app .nav-link { justify-content: flex-start; }

  .menu-button { display: inline-flex; }
  .topbar { padding: 0 var(--space-4); }
  .main-content { padding: var(--space-4); }
}
</style>
