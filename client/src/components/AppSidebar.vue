<template>
  <aside class="sidebar" :class="{ collapsed: collapsed }">
    <!-- Logo -->
    <div class="sidebar-logo">
      <div class="logo-text" v-show="!collapsed">
        <div class="logo-name">{{ t('nav.companyName') }}</div>
        <div class="logo-sub">{{ t('nav.subtitle') }}</div>
      </div>
      <button class="collapse-btn" @click="$emit('toggle-collapse')" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <polyline :points="collapsed ? '9 18 15 12 9 6' : '15 18 9 12 15 6'"></polyline>
        </svg>
      </button>
    </div>

    <!-- Nav -->
    <nav class="sidebar-nav">
      <a
        v-for="item in navItems"
        :key="item.path"
        class="nav-item"
        :class="{ active: isActive(item) }"
        @click.prevent="$router.push(item.path)"
        href="#"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span v-show="!collapsed" class="nav-label">{{ item.label || t(item.labelKey) }}</span>
      </a>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <LanguageSwitcher v-show="!collapsed" />
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script>
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from '../composables/useI18n.js'
import ProfileMenu from './ProfileMenu.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

export default {
  name: 'AppSidebar',
  components: { ProfileMenu, LanguageSwitcher },
  props: {
    collapsed: {
      type: Boolean,
      default: false
    }
  },
  emits: ['show-profile-details', 'show-tasks', 'toggle-collapse'],
  setup() {
    const route = useRoute()
    const { t } = useI18n()

    const navItems = [
      {
        path: '/',
        labelKey: 'nav.overview',
        icon: `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>`
      },
      {
        path: '/inventory',
        labelKey: 'nav.inventory',
        icon: `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>`
      },
      {
        path: '/orders',
        labelKey: 'nav.orders',
        icon: `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>`
      },
      {
        path: '/spending',
        labelKey: 'nav.finance',
        icon: `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>`
      },
      {
        path: '/demand',
        labelKey: 'nav.demandForecast',
        icon: `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>`
      },
      {
        path: '/reports',
        label: 'Reports',
        icon: `<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`
      },
    ]

    const isActive = (item) =>
      item.path === '/' ? route.path === '/' : route.path.startsWith(item.path)

    return { t, navItems, isActive }
  }
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  flex-shrink: 0;
  width: 240px;
  transition: width 0.2s ease;
  overflow: visible;
  z-index: 10;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-logo {
  padding: 1.25rem 1rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  display: flex;
  align-items: center;
}

.logo-text {
  flex: 1;
}

.logo-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.01em;
}

.logo-sub {
  font-size: 0.7rem;
  color: #475569;
  margin-top: 2px;
}

.sidebar-nav {
  flex: 1;
  padding: 0.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.45rem 0.75rem;
  margin: 0 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
  cursor: pointer;
}

.nav-item:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.06);
}

.nav-item.active {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.12);
}

/* Active left border indicator */
.nav-item.active::before {
  content: '';
  position: absolute;
  left: -0.5rem;
  top: 15%;
  height: 70%;
  width: 3px;
  background: #2563eb;
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.sidebar-footer {
  margin-top: auto;
  padding: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* When collapsed, center the icons */
.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.6rem;
  margin: 0 0.35rem;
}

/* Collapse button */
.collapse-btn {
  background: none;
  border: none;
  color: #475569;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: color 0.15s;
  margin-left: auto;
}
.collapse-btn:hover {
  color: #94a3b8;
}

.sidebar.collapsed :deep(.profile-name),
.sidebar.collapsed :deep(.chevron) {
  display: none;
}
</style>
