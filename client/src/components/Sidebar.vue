<template>
  <aside class="sidebar" :class="{ collapsed: effectiveCollapsed }">
    <button
      v-if="!isSmallScreen"
      class="toggle-btn"
      type="button"
      :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
      @click="collapsed = !collapsed"
    >
      <svg
        class="toggle-icon"
        :class="{ flipped: collapsed }"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </button>

    <nav class="nav-links">
      <router-link
        to="/"
        :class="{ active: $route.path === '/' }"
        :title="t('nav.overview')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 11l9-8 9 8" />
          <path d="M5 10v10a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1V10" />
        </svg>
        <span v-if="!effectiveCollapsed" class="nav-label">{{ t('nav.overview') }}</span>
      </router-link>

      <router-link
        to="/inventory"
        :class="{ active: $route.path === '/inventory' }"
        :title="t('nav.inventory')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 8l-9-5-9 5 9 5 9-5z" />
          <path d="M3 8v8l9 5 9-5V8" />
          <path d="M12 13v8" />
        </svg>
        <span v-if="!effectiveCollapsed" class="nav-label">{{ t('nav.inventory') }}</span>
      </router-link>

      <router-link
        to="/orders"
        :class="{ active: $route.path === '/orders' }"
        :title="t('nav.orders')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="6" y="4" width="12" height="17" rx="1" />
          <path d="M9 3h6a1 1 0 0 1 1 1v1H8V4a1 1 0 0 1 1-1z" />
          <line x1="9" y1="10" x2="15" y2="10" />
          <line x1="9" y1="14" x2="15" y2="14" />
          <line x1="9" y1="18" x2="13" y2="18" />
        </svg>
        <span v-if="!effectiveCollapsed" class="nav-label">{{ t('nav.orders') }}</span>
      </router-link>

      <router-link
        to="/spending"
        :class="{ active: $route.path === '/spending' }"
        :title="t('nav.finance')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 7v10" />
          <path d="M14.5 9.5c0-1-1-1.5-2.5-1.5s-2.5.7-2.5 1.8c0 2.4 5 1 5 3.4 0 1.1-1 1.8-2.5 1.8s-2.5-.5-2.5-1.5" />
        </svg>
        <span v-if="!effectiveCollapsed" class="nav-label">{{ t('nav.finance') }}</span>
      </router-link>

      <router-link
        to="/demand"
        :class="{ active: $route.path === '/demand' }"
        :title="t('nav.demandForecast')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 17 9 11 13 15 21 6" />
          <polyline points="15 6 21 6 21 12" />
        </svg>
        <span v-if="!effectiveCollapsed" class="nav-label">{{ t('nav.demandForecast') }}</span>
      </router-link>

      <router-link
        to="/restocking"
        :class="{ active: $route.path === '/restocking' }"
        :title="t('nav.restocking')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12a9 9 0 1 1-3.2-6.9" />
          <polyline points="21 3 21 8 16 8" />
        </svg>
        <span v-if="!effectiveCollapsed" class="nav-label">{{ t('nav.restocking') }}</span>
      </router-link>

      <router-link
        to="/reports"
        :class="{ active: $route.path === '/reports' }"
        :title="t('nav.reports')"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="3" width="16" height="18" rx="1" />
          <line x1="8" y1="8" x2="16" y2="8" />
          <line x1="8" y1="12" x2="16" y2="12" />
          <line x1="8" y1="16" x2="12" y2="16" />
        </svg>
        <span v-if="!effectiveCollapsed" class="nav-label">{{ t('nav.reports') }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Sidebar',
  setup() {
    const { t } = useI18n()

    // User's manual collapse preference for this page load only (no persistence)
    const collapsed = ref(false)

    // Track viewport width so the sidebar can auto-collapse on small screens
    const windowWidth = ref(window.innerWidth)
    const handleResize = () => {
      windowWidth.value = window.innerWidth
    }

    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })

    const isSmallScreen = computed(() => windowWidth.value <= 768)

    // Below the breakpoint the sidebar is always icons-only, regardless of the manual toggle
    const effectiveCollapsed = computed(() => isSmallScreen.value || collapsed.value)

    return {
      t,
      collapsed,
      isSmallScreen,
      effectiveCollapsed
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  padding: 1rem 0.75rem;
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: 64px;
  padding: 1rem 0.5rem;
  align-items: center;
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin-bottom: 1rem;
  margin-left: auto;
  background: transparent;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sidebar.collapsed .toggle-btn {
  margin-left: 0;
}

.toggle-btn:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.toggle-icon {
  width: 16px;
  height: 16px;
  transition: transform 0.2s ease;
}

.toggle-icon.flipped {
  transform: rotate(180deg);
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
}

.nav-links a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar.collapsed .nav-links a {
  justify-content: center;
  padding: 0.625rem;
  width: 100%;
}

.nav-links a:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.nav-links a.active {
  color: #2563eb;
  background: #eff6ff;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
