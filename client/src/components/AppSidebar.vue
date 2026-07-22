<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div class="brand" v-show="!collapsed">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="subtitle">{{ t('nav.subtitle') }}</span>
      </div>
      <button type="button" class="toggle-btn" @click="$emit('toggle')" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <ChevronLeft v-if="!collapsed" :size="18" />
        <ChevronRight v-else :size="18" />
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="link in navLinks"
        :key="link.path"
        :to="link.path"
        :class="{ active: $route.path === link.path }"
        :title="collapsed ? link.label : ''"
      >
        <component :is="link.icon" :size="20" />
        <span class="nav-label" v-show="!collapsed">{{ link.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script>
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  DollarSign,
  TrendingUp,
  RefreshCw,
  FileText,
  ChevronLeft,
  ChevronRight
} from 'lucide-vue-next'
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

export default {
  name: 'AppSidebar',
  components: {
    LayoutDashboard,
    Package,
    ShoppingCart,
    DollarSign,
    TrendingUp,
    RefreshCw,
    FileText,
    ChevronLeft,
    ChevronRight,
    LanguageSwitcher,
    ProfileMenu
  },
  props: {
    collapsed: {
      type: Boolean,
      required: true
    }
  },
  emits: ['toggle', 'show-profile-details', 'show-tasks'],
  setup() {
    const { t } = useI18n()

    const navLinks = [
      { path: '/',           label: 'Overview',         icon: 'LayoutDashboard' },
      { path: '/inventory',  label: 'Inventory',        icon: 'Package' },
      { path: '/orders',     label: 'Orders',           icon: 'ShoppingCart' },
      { path: '/spending',   label: 'Finance',          icon: 'DollarSign' },
      { path: '/demand',     label: 'Demand Forecast',  icon: 'TrendingUp' },
      { path: '/restocking', label: 'Restocking',       icon: 'RefreshCw' },
      { path: '/reports',    label: 'Reports',          icon: 'FileText' }
    ]

    return { t, navLinks }
  }
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
  overflow: visible;
  position: sticky;
  top: 0;
}

.sidebar.collapsed {
  width: 64px;
}

/* ---- Header ---- */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  min-height: 70px;
  gap: 0.5rem;
  overflow: hidden;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
}

.brand {
  overflow: hidden;
  white-space: nowrap;
}

.brand h1 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.brand .subtitle {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
}

.toggle-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fafc;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

/* ---- Nav ---- */
.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-nav a:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.sidebar-nav a.active {
  color: #2563eb;
  background: #eff6ff;
}

.sidebar.collapsed .sidebar-nav a {
  justify-content: center;
  padding: 0.625rem;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ---- Footer ---- */
.sidebar-footer {
  padding: 0.75rem 0.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
</style>
