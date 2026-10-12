<template>
  <aside class="sidebar" :class="{ 'sidebar-collapsed': isCollapsed }">
    <nav class="sidebar-nav" role="navigation" aria-label="Main navigation">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'active': isActiveRoute(item.path) }"
        :aria-label="item.label"
        :title="isCollapsed ? item.label : ''"
        :aria-current="isActiveRoute(item.path) ? 'page' : undefined"
      >
        <component :is="item.icon" class="nav-icon" aria-hidden="true" />
        <span v-if="!isCollapsed" class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import OverviewIcon from './icons/OverviewIcon.vue'
import InventoryIcon from './icons/InventoryIcon.vue'
import OrdersIcon from './icons/OrdersIcon.vue'
import FinanceIcon from './icons/FinanceIcon.vue'
import DemandIcon from './icons/DemandIcon.vue'
import RestockingIcon from './icons/RestockingIcon.vue'
import ReportsIcon from './icons/ReportsIcon.vue'

export default {
  name: 'Sidebar',
  components: {
    OverviewIcon,
    InventoryIcon,
    OrdersIcon,
    FinanceIcon,
    DemandIcon,
    RestockingIcon,
    ReportsIcon
  },
  props: {
    isCollapsed: {
      type: Boolean,
      default: false
    }
  },
  setup() {
    const route = useRoute()
    const { t } = useI18n()

    const navItems = computed(() => [
      { path: '/', label: t('nav.overview'), icon: 'OverviewIcon' },
      { path: '/inventory', label: t('nav.inventory'), icon: 'InventoryIcon' },
      { path: '/orders', label: t('nav.orders'), icon: 'OrdersIcon' },
      { path: '/spending', label: t('nav.finance'), icon: 'FinanceIcon' },
      { path: '/demand', label: t('nav.demandForecast'), icon: 'DemandIcon' },
      { path: '/restocking', label: t('nav.restocking'), icon: 'RestockingIcon' },
      { path: '/reports', label: 'Reports', icon: 'ReportsIcon' }
    ])

    const isActiveRoute = (path) => route.path === path

    return { navItems, isActiveRoute }
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 70px;
  height: calc(100vh - 70px);
  width: 240px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 95;
  overflow: hidden;
}

.sidebar-collapsed {
  width: 70px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 1rem 0;
  gap: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  transition: all 0.2s ease;
  position: relative;
  white-space: nowrap;
}

.sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 0.75rem;
}

.nav-item:hover {
  background: #f8fafc;
  color: #0f172a;
}

.nav-item.active {
  background: #eff6ff;
  color: #2563eb;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #2563eb;
}

.nav-icon {
  flex-shrink: 0;
}

.nav-label {
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar-collapsed .nav-label {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.nav-item:focus {
  outline: 2px solid #3b82f6;
  outline-offset: -2px;
}
</style>
