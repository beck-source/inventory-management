<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-brand">
      <h1 class="brand-name">{{ t('nav.companyName') }}</h1>
      <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      <span class="brand-mark" aria-hidden="true">{{ brandInitials }}</span>
    </div>

    <nav class="sidebar-nav" aria-label="Main">
      <ul>
        <li v-for="item in navItems" :key="item.path">
          <router-link
            :to="item.path"
            class="nav-link"
            :class="{ 'nav-link-active': isActive(item.path) }"
            :aria-current="isActive(item.path) ? 'page' : null"
            :title="item.label"
          >
            <span class="nav-icon" v-html="item.icon"></span>
            <span class="nav-label">{{ item.label }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <div class="sidebar-footer">
      <button
        type="button"
        class="sidebar-toggle"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :aria-expanded="!collapsed"
        @click="toggleCollapsed"
      >
        <span class="nav-icon" v-html="chevronIcon" aria-hidden="true"></span>
        <span class="nav-label">Collapse</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()
const route = useRoute()

const STORAGE_KEY = 'sidebar-collapsed'

const getInitialCollapsed = () => {
  try {
    if (typeof localStorage !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored !== null) return stored === 'true'
    }
  } catch (err) {
    // localStorage unavailable (e.g. private mode) - fall through to default
  }
  if (typeof window !== 'undefined') {
    return window.innerWidth < 1024
  }
  return false
}

const collapsed = ref(getInitialCollapsed())

const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, String(collapsed.value))
    }
  } catch (err) {
    // ignore persistence errors
  }
}

const chevronIcon = computed(() => (
  collapsed.value
    ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>'
    : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>'
))

const icons = {
  overview: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>',
  inventory: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8L12 3 3 8v8l9 5 9-5V8z"/><path d="M3 8l9 5 9-5"/><path d="M12 13v8"/></svg>',
  orders: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="4" width="14" height="17" rx="1.5"/><path d="M9 3h6a1 1 0 011 1v1H8V4a1 1 0 011-1z"/><path d="M8 11h8M8 15h5"/></svg>',
  restocking: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0115.5-6.3L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 01-15.5 6.3L3 16"/><path d="M3 21v-5h5"/></svg>',
  finance: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20"/><path d="M17 5.5c0-1.7-2-2.5-5-2.5s-5 1-5 3 2 2.7 5 3 5 1.2 5 3-2 3-5 3-5-.8-5-2.5"/></svg>',
  demand: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 17l6-6 4 4 8-8"/><path d="M15 6h6v6"/></svg>',
  reports: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20V10M10 20V4M16 20v-7M4 20h16"/></svg>'
}

const navItems = computed(() => [
  { path: '/', label: t('nav.overview'), icon: icons.overview },
  { path: '/inventory', label: t('nav.inventory'), icon: icons.inventory },
  { path: '/orders', label: t('nav.orders'), icon: icons.orders },
  { path: '/restocking', label: 'Restocking', icon: icons.restocking },
  { path: '/spending', label: t('nav.finance'), icon: icons.finance },
  { path: '/demand', label: t('nav.demandForecast'), icon: icons.demand },
  { path: '/reports', label: 'Reports', icon: icons.reports }
])

const isActive = (path) => route.path === path

const brandInitials = computed(() => {
  return t('nav.companyName')
    .split(/\s+/)
    .filter(Boolean)
    .map(word => word[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
})
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  height: 100vh;
  position: sticky;
  top: 0;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.18s ease;
}

.sidebar-brand {
  padding: var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--sidebar-border);
}

.brand-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--sidebar-brand);
  letter-spacing: -0.02em;
  line-height: 1.3;
}

.brand-subtitle {
  display: block;
  font-size: 0.75rem;
  color: var(--sidebar-text);
  margin-top: var(--space-1);
}

.brand-mark {
  display: none;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--sidebar-brand);
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
}

.sidebar-nav ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  position: relative;
  border-left: 3px solid transparent;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-link:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-hover);
}

.nav-link-active {
  background: var(--sidebar-active-bg);
  color: var(--sidebar-active-text);
  border-left-color: var(--color-primary);
  font-weight: 600;
}

.nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.sidebar-footer {
  border-top: 1px solid var(--sidebar-border);
  padding: var(--space-3);
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-sm);
  background: transparent;
  border: none;
  color: var(--sidebar-text);
  font-size: 0.875rem;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.sidebar-toggle:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-hover);
}

.sidebar-toggle:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.sidebar.collapsed {
  width: 68px;
}

.sidebar.collapsed .sidebar-brand {
  padding: var(--space-4) var(--space-2);
  text-align: center;
}

.sidebar.collapsed .brand-subtitle {
  display: none;
}

.sidebar.collapsed .brand-name {
  display: none;
}

.sidebar.collapsed .brand-mark {
  display: block;
}

.sidebar.collapsed .nav-link {
  justify-content: center;
  padding: var(--space-3) var(--space-2);
}

.sidebar.collapsed .nav-label {
  display: none;
}

.sidebar.collapsed .sidebar-toggle {
  justify-content: center;
  padding: var(--space-3) var(--space-2);
}
</style>
