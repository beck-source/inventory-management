<template>
  <aside
    id="app-sidebar"
    class="sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-mobile-open': mobileOpen }"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
      <span class="brand-text">
        <span class="brand-name" :title="brandName">{{ brandName }}</span>
        <span v-if="brandTagline" class="brand-tagline" :title="brandTagline">{{ brandTagline }}</span>
      </span>
      <button
        type="button"
        class="icon-button sidebar-close"
        :aria-label="t('nav.closeNavigation')"
        @click="closeMobile"
      >
        <AppIcon name="close" />
      </button>
    </div>

    <nav class="sidebar-nav" :aria-label="t('nav.mainNavigation')">
      <ul class="nav-list">
        <li v-for="item in items" :key="item.to">
          <!-- RouterLink sets aria-current="page" on the exact-active link by itself. -->
          <router-link
            :to="item.to"
            class="nav-item"
            :title="collapsed ? item.label : undefined"
            @click="closeMobile"
          >
            <AppIcon :name="item.icon" />
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="sidebar-footer">
      <button
        type="button"
        class="nav-item collapse-toggle"
        :aria-expanded="String(!collapsed)"
        aria-controls="app-sidebar"
        :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        :title="collapsed ? t('nav.expandSidebar') : undefined"
        @click="toggleCollapsed"
      >
        <AppIcon :name="collapsed ? 'chevron-right' : 'chevron-left'" />
        <span class="nav-label">{{ t('nav.collapse') }}</span>
      </button>
    </div>
  </aside>

  <div v-if="mobileOpen" class="sidebar-backdrop" aria-hidden="true" @click="closeMobile" />
</template>

<script>
import { computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from './AppIcon.vue'
import { useSidebar } from '../composables/useSidebar'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'AppSidebar',
  components: { AppIcon },
  props: {
    brandName: { type: String, required: true },
    brandTagline: { type: String, default: '' },
    // Flat list of { to, label, icon }.
    items: { type: Array, required: true }
  },
  setup(props) {
    const { collapsed, mobileOpen, toggleCollapsed, closeMobile } = useSidebar()
    const { t } = useI18n()
    const route = useRoute()

    const brandInitial = computed(() => props.brandName.trim().charAt(0).toUpperCase())

    // Close the drawer on navigation and on Escape so it never traps the user.
    watch(() => route.fullPath, closeMobile)
    const onKey = (event) => { if (event.key === 'Escape') closeMobile() }
    onMounted(() => window.addEventListener('keydown', onKey))
    onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

    return { t, collapsed, mobileOpen, toggleCollapsed, closeMobile, brandInitial }
  }
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: var(--sidebar-width);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  transition: width var(--duration) var(--ease);
  z-index: var(--z-sidebar);
  overflow: hidden;
}
.sidebar.is-collapsed { width: var(--sidebar-width-collapsed); }

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.brand-mark {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: var(--color-on-accent);
  display: grid;
  place-items: center;
  font-weight: var(--weight-bold);
  font-size: var(--text-md);
  flex-shrink: 0;
}
.brand-text { display: flex; flex-direction: column; min-width: 0; }
.brand-name {
  font-weight: var(--weight-semibold);
  font-size: var(--text-base);
  line-height: var(--leading-tight);
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.brand-tagline {
  font-size: var(--text-xs);
  line-height: var(--leading-tight);
  color: var(--color-text-subtle);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-3);
}
.nav-list { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-1); }

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-width: 0;
  height: 36px;
  padding: 0 var(--space-3);
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease), color var(--duration-fast) var(--ease);
}
.nav-item:hover { background: var(--color-surface-hover); color: var(--color-text); }
.nav-item.router-link-active,
.nav-item[aria-current="page"] {
  background: var(--color-accent-soft);
  color: var(--color-accent-text);
}
/* min-width: 0 lets flex shrink the label so long (Japanese) text truncates. */
.nav-label { min-width: 0; overflow: hidden; text-overflow: ellipsis; }

.sidebar-footer {
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
  display: grid;
  gap: var(--space-1);
}

/* Collapsed rail: hide text, center icons. */
.is-collapsed .brand-text,
.is-collapsed .nav-label { display: none; }
.is-collapsed .sidebar-brand { justify-content: center; padding: 0; }
.is-collapsed .nav-item { justify-content: center; padding: 0; }

.icon-button {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}
.icon-button:hover { background: var(--color-surface-hover); color: var(--color-text); }
.sidebar-close { display: none; margin-left: auto; }

/*
 * Below 1024px the sidebar becomes an off-canvas drawer. The persisted
 * "collapsed" rail state is ignored here (the drawer is always full width with
 * labels) because an icon rail would eat too much of a phone screen.
 */
@media (max-width: 1023px) {
  .sidebar,
  .sidebar.is-collapsed {
    position: fixed;
    left: 0;
    top: 0;
    width: min(280px, 85vw);
    transform: translateX(-100%);
    transition: transform var(--duration) var(--ease);
    box-shadow: var(--shadow-lg);
    z-index: calc(var(--z-backdrop) + 1); /* drawer sits above its own backdrop */
  }
  .sidebar.is-mobile-open { transform: translateX(0); }
  .is-collapsed .brand-text { display: flex; }
  .is-collapsed .nav-label { display: inline; }
  .is-collapsed .sidebar-brand { justify-content: flex-start; padding: 0 var(--space-4); }
  .is-collapsed .nav-item { justify-content: flex-start; padding: 0 var(--space-3); }
  .sidebar-close { display: inline-grid; }
  .collapse-toggle { display: none; }
  .sidebar-footer { display: none; }
  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    background: var(--overlay);
    z-index: var(--z-backdrop);
  }
}
</style>
