<template>
  <div class="sidebar-layout">
    <div
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      @click="closeSidebar"
    ></div>

    <aside
      class="sidebar"
      :class="{ 'sidebar-open': sidebarOpen, collapsed: effectiveCollapsed }"
    >
      <div class="sidebar-brand">
        <div class="brand-text">
          <h1 class="brand-name">{{ t('nav.companyName') }}</h1>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <span class="brand-mark" aria-hidden="true">{{ companyInitials }}</span>

        <button
          class="collapse-toggle"
          type="button"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="!collapsed"
          :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="toggleCollapse"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            :class="{ flipped: collapsed }"
          >
            <path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav" aria-label="Primary">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          :title="effectiveCollapsed ? item.label : null"
          @click="closeSidebar"
        >
          <span class="nav-icon" aria-hidden="true">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <div class="content-area" :class="{ collapsed: effectiveCollapsed }">
      <header class="top-header">
        <button
          class="menu-toggle"
          type="button"
          aria-label="Toggle navigation menu"
          @click="toggleSidebar"
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path d="M3 6h16M3 11h16M3 16h16" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" />
          </svg>
        </button>

        <div class="header-title">
          <h2>{{ currentPageTitle }}</h2>
        </div>

        <div class="header-actions">
          <slot name="header-actions" />
        </div>
      </header>

      <div v-if="$slots.filters" class="filters-row">
        <slot name="filters" />
      </div>

      <main class="main-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'

const COLLAPSE_STORAGE_KEY = 'sidebar-collapsed'
// Screens in this range keep the sidebar visible (not the mobile overlay)
// but default to icons-only mode to save horizontal space.
const AUTO_COLLAPSE_MIN_WIDTH = 1024
const AUTO_COLLAPSE_MAX_WIDTH = 1279

const route = useRoute()
const { t } = useI18n()

const sidebarOpen = ref(false)

const navItems = computed(() => [
  { path: '/', label: t('nav.overview'), icon: '📊' },
  { path: '/inventory', label: t('nav.inventory'), icon: '📦' },
  { path: '/orders', label: t('nav.orders'), icon: '📋' },
  { path: '/spending', label: t('nav.finance'), icon: '💰' },
  { path: '/demand', label: t('nav.demandForecast'), icon: '📈' },
  { path: '/restocking', label: t('nav.restocking'), icon: '🔄' },
  { path: '/reports', label: 'Reports', icon: '📄' }
])

const isActive = (path) => route.path === path

const currentPageTitle = computed(() => {
  const match = navItems.value.find(item => item.path === route.path)
  return match ? match.label : ''
})

const companyInitials = computed(() => {
  const name = t('nav.companyName') || ''
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map(word => word[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
})

// --- Mobile overlay sidebar (< 1024px) ---
const toggleSidebar = () => {
  sidebarOpen.value = !sidebarOpen.value
}

const closeSidebar = () => {
  sidebarOpen.value = false
}

watch(() => route.path, closeSidebar)

// --- Collapsible icons-only sidebar (>= 1024px) ---
const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1280)
const isDesktop = computed(() => windowWidth.value >= AUTO_COLLAPSE_MIN_WIDTH)
const isMediumScreen = computed(
  () => windowWidth.value >= AUTO_COLLAPSE_MIN_WIDTH && windowWidth.value <= AUTO_COLLAPSE_MAX_WIDTH
)

const storedPreference = typeof localStorage !== 'undefined' ? localStorage.getItem(COLLAPSE_STORAGE_KEY) : null
// Once the user manually toggles the sidebar, stop auto-collapsing based on viewport width
const userOverridden = ref(storedPreference !== null)
const collapsed = ref(storedPreference !== null ? storedPreference === 'true' : isMediumScreen.value)

// Collapsed mode only applies on desktop widths; mobile always uses the full-label overlay
const effectiveCollapsed = computed(() => isDesktop.value && collapsed.value)

const toggleCollapse = () => {
  collapsed.value = !collapsed.value
  userOverridden.value = true
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(COLLAPSE_STORAGE_KEY, String(collapsed.value))
  }
}

const handleResize = () => {
  windowWidth.value = window.innerWidth
  if (!userOverridden.value) {
    collapsed.value = isMediumScreen.value
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.sidebar-layout {
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  width: 256px;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 110;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, width 0.2s ease;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-brand {
  position: relative;
  height: 64px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.brand-text {
  min-width: 0;
  overflow: hidden;
}

.brand-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  line-height: 1.2;
  white-space: nowrap;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
  white-space: nowrap;
}

.brand-mark {
  display: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #2563eb;
  color: #ffffff;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.025em;
  align-items: center;
  justify-content: center;
}

.collapse-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-left: auto;
  flex-shrink: 0;
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapse-toggle:hover {
  background: #f1f5f9;
  color: #0f172a;
  border-color: #cbd5e1;
}

.collapse-toggle svg {
  transition: transform 0.2s ease;
}

.collapse-toggle svg.flipped {
  transform: rotate(180deg);
}

/* Collapsed (icons-only) sidebar */
.sidebar.collapsed .sidebar-brand {
  padding: 0;
  justify-content: center;
}

.sidebar.collapsed .brand-text {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sidebar.collapsed .brand-mark {
  display: flex;
}

.sidebar.collapsed .collapse-toggle {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 1rem 0.75rem;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.875rem;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  border-left: 3px solid transparent;
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.nav-item.active {
  background: #eff6ff;
  color: #2563eb;
  border-left-color: #2563eb;
  font-weight: 600;
}

.nav-item:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.nav-icon {
  font-size: 1.125rem;
  line-height: 1;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
}

/* Collapsed (icons-only) nav items */
.sidebar.collapsed .sidebar-nav {
  padding: 1rem 0.5rem;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.625rem;
}

.sidebar.collapsed .nav-label {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Backdrop for mobile */
.sidebar-backdrop {
  display: none;
}

/* Content area */
.content-area {
  flex: 1;
  min-width: 0;
  margin-left: 256px;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.2s ease;
}

.content-area.collapsed {
  margin-left: 72px;
}

.top-header {
  height: 64px;
  flex-shrink: 0;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0 1.5rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.menu-toggle {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #334155;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.menu-toggle:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.header-title {
  min-width: 0;
}

.header-title h2 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  letter-spacing: 0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.filters-row {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  padding: 0.75rem 1.5rem;
  position: sticky;
  top: 64px;
  z-index: 90;
}

.main-content {
  flex: 1;
  width: 100%;
  padding: 1.5rem;
}

/* Mobile: collapse sidebar, show hamburger */
@media (max-width: 1023px) {
  .sidebar {
    transform: translateX(-100%);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  }

  .sidebar.sidebar-open {
    transform: translateX(0);
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: 105;
  }

  .content-area,
  .content-area.collapsed {
    margin-left: 0;
  }

  .menu-toggle {
    display: flex;
  }

  .collapse-toggle {
    display: none;
  }
}

@media (max-width: 639px) {
  .top-header {
    padding: 0 1rem;
  }

  .filters-row {
    padding: 0.625rem 1rem;
  }

  .main-content {
    padding: 1rem;
  }

  .header-title h2 {
    max-width: 40vw;
  }
}
</style>
