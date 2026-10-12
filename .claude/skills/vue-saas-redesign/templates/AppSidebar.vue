<!--
  AppSidebar.vue — literal starting point for a COLLAPSIBLE SaaS sidebar.

  HOW TO USE: replace the `navItems` entries and `ICON` map with the target app's
  real routes/labels (keep its i18n calls), and swap the brand. Keep the STRUCTURE
  and the collapse behaviour:
    - Below the breakpoint the rail is FORCED to icons-only (small screens).
    - On larger screens the user toggles it and the choice is persisted.
    - Collapsed items expose their label via a native `title` tooltip.
  Icons are decorative inline SVG (no emojis). Styling consumes design-tokens.css.
-->
<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">◆</span>
      <span class="brand-name">{{ brand }}</span>
    </div>

    <nav class="sidebar-nav" aria-label="Primary">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: isActive(item.to) }"
        :aria-current="isActive(item.to) ? 'page' : null"
        :title="collapsed ? item.label : null"
      >
        <span class="nav-icon" aria-hidden="true" v-html="ICON[item.icon]"></span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Toggle only matters on larger screens; small screens are forced to icons-only. -->
    <button
      v-if="!isSmall"
      type="button"
      class="sidebar-toggle"
      :aria-label="collapsed ? expandLabel : collapseLabel"
      :aria-expanded="!collapsed"
      @click="toggleCollapsed"
    >
      <span class="toggle-icon" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
      </span>
      <span class="toggle-label">{{ collapseLabel }}</span>
    </button>

    <div class="sidebar-footer">
      <slot name="footer" />
    </div>
  </aside>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

const COLLAPSE_BREAKPOINT = '(max-width: 1024px)'
const STORAGE_KEY = 'sidebar-collapsed'

// Minimal inline SVG icons (20px). Add one entry per destination.
const ICON = {
  dashboard: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>',
  list: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>'
}

export default {
  name: 'AppSidebar',
  props: {
    brand: { type: String, default: 'Product' },
    navItems: { type: Array, required: true }, // [{ to, label, icon }]
    collapseLabel: { type: String, default: 'Collapse sidebar' },
    expandLabel: { type: String, default: 'Expand sidebar' }
  },
  setup() {
    const route = useRoute()
    const isActive = (to) => (to === '/' ? route.path === '/' : route.path.startsWith(to))

    const manualCollapsed = ref(localStorage.getItem(STORAGE_KEY) === 'true')
    const isSmall = ref(false)

    // Small screens force icons-only; otherwise honor the user's saved preference.
    const collapsed = computed(() => isSmall.value || manualCollapsed.value)

    const toggleCollapsed = () => {
      manualCollapsed.value = !manualCollapsed.value
      localStorage.setItem(STORAGE_KEY, String(manualCollapsed.value))
    }

    let mq
    const onMqChange = (e) => { isSmall.value = e.matches }
    onMounted(() => {
      mq = window.matchMedia(COLLAPSE_BREAKPOINT)
      isSmall.value = mq.matches
      mq.addEventListener('change', onMqChange)
    })
    onBeforeUnmount(() => { if (mq) mq.removeEventListener('change', onMqChange) })

    return { isActive, ICON, collapsed, isSmall, toggleCollapsed }
  }
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  height: 100vh;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  transition: width 0.18s ease;
}
.sidebar.collapsed { width: var(--sidebar-width-collapsed); }

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-4);
  font-size: var(--text-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  overflow: hidden;
}
.brand-mark { color: var(--color-accent); flex-shrink: 0; }
.sidebar.collapsed .sidebar-brand { justify-content: center; padding-left: 0; padding-right: 0; }

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
  transition: background 0.15s ease, color 0.15s ease;
}
.nav-item:hover { background: var(--color-surface-alt); color: var(--color-text); }
.nav-item.active { background: var(--color-accent-weak); color: var(--color-accent); }
.nav-icon { display: inline-flex; flex-shrink: 0; }
.sidebar.collapsed .nav-item { justify-content: center; padding-left: 0; padding-right: 0; }

.sidebar.collapsed .brand-name,
.sidebar.collapsed .nav-label,
.sidebar.collapsed .toggle-label { display: none; }

.sidebar-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin: 0 var(--space-3) var(--space-2);
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.sidebar-toggle:hover { background: var(--color-surface-alt); color: var(--color-text); }
.sidebar.collapsed .sidebar-toggle { justify-content: center; margin-left: 0; margin-right: 0; padding-left: 0; padding-right: 0; }
.toggle-icon { display: inline-flex; transition: transform 0.18s ease; }
.sidebar.collapsed .toggle-icon { transform: rotate(180deg); }

.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border);
}
.sidebar.collapsed .sidebar-footer { flex-direction: column; padding-left: var(--space-2); padding-right: var(--space-2); }
</style>
