<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <button
        class="collapse-btn"
        type="button"
        :title="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        aria-label="Toggle sidebar"
        @click="toggle"
      >
        <svg v-if="collapsed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link to="/" :class="{ active: $route.path === '/' }" :title="collapsed ? t('nav.overview') : ''">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
        </span>
        <span v-show="!collapsed" class="nav-label">{{ t('nav.overview') }}</span>
      </router-link>

      <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }" :title="collapsed ? t('nav.inventory') : ''">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
            <line x1="12" y1="22.08" x2="12" y2="12" />
          </svg>
        </span>
        <span v-show="!collapsed" class="nav-label">{{ t('nav.inventory') }}</span>
      </router-link>

      <router-link to="/orders" :class="{ active: $route.path === '/orders' }" :title="collapsed ? t('nav.orders') : ''">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="9" cy="21" r="1" />
            <circle cx="20" cy="21" r="1" />
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
          </svg>
        </span>
        <span v-show="!collapsed" class="nav-label">{{ t('nav.orders') }}</span>
      </router-link>

      <router-link to="/spending" :class="{ active: $route.path === '/spending' }" :title="collapsed ? t('nav.finance') : ''">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="1" x2="12" y2="23" />
            <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
        </span>
        <span v-show="!collapsed" class="nav-label">{{ t('nav.finance') }}</span>
      </router-link>

      <router-link to="/demand" :class="{ active: $route.path === '/demand' }" :title="collapsed ? t('nav.demandForecast') : ''">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 3v18h18" />
            <polyline points="19 9 13 15 9 11 5 15" />
          </svg>
        </span>
        <span v-show="!collapsed" class="nav-label">{{ t('nav.demandForecast') }}</span>
      </router-link>

      <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }" :title="collapsed ? t('nav.restocking') : ''">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10" />
            <polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
        </span>
        <span v-show="!collapsed" class="nav-label">{{ t('nav.restocking') }}</span>
      </router-link>

      <router-link to="/reports" :class="{ active: $route.path === '/reports' }" :title="collapsed ? t('nav.reports') : ''">
        <span class="nav-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </span>
        <span v-show="!collapsed" class="nav-label">{{ t('nav.reports') }}</span>
      </router-link>
    </nav>
  </aside>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from '../composables/useI18n'

const STORAGE_KEY = 'sidebar-collapsed'

export default {
  name: 'AppSidebar',
  setup() {
    const { t } = useI18n()
    const collapsed = ref(false)

    // null = user has not explicitly chosen, so we follow the responsive default.
    let userChoice = null
    let mql = null

    const readStored = () => {
      try {
        const v = localStorage.getItem(STORAGE_KEY)
        if (v === null) return null
        return v === 'true'
      } catch (e) {
        return null
      }
    }

    const writeStored = (val) => {
      try {
        localStorage.setItem(STORAGE_KEY, String(val))
      } catch (e) {
        // localStorage unavailable (private mode / disabled) - ignore.
      }
    }

    // Only applies the viewport-based default when the user hasn't made an
    // explicit choice this session (or in a previous persisted session).
    const applyResponsiveDefault = () => {
      if (userChoice !== null) return
      collapsed.value = mql ? !mql.matches : false
    }

    const toggle = () => {
      collapsed.value = !collapsed.value
      userChoice = collapsed.value
      writeStored(collapsed.value)
    }

    onMounted(() => {
      mql = window.matchMedia('(min-width: 1024px)')
      const stored = readStored()
      if (stored !== null) {
        userChoice = stored
        collapsed.value = stored
      } else {
        collapsed.value = !mql.matches
      }
      mql.addEventListener('change', applyResponsiveDefault)
    })

    onUnmounted(() => {
      if (mql) mql.removeEventListener('change', applyResponsiveDefault)
    })

    return { t, collapsed, toggle }
  }
}
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  flex-shrink: 0;
  width: 230px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  box-shadow: 1px 0 3px 0 rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  z-index: 100;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #ffffff;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  overflow-y: auto;
}

.sidebar-nav a {
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
}

.sidebar.collapsed .sidebar-nav a {
  justify-content: center;
  padding: 0.625rem;
}

.sidebar-nav a:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.sidebar-nav a.active {
  color: #2563eb;
  background: #eff6ff;
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
