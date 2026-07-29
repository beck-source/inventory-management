<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <h1 class="sidebar-logo">{{ isCollapsed ? 'IM' : t('nav.companyName') }}</h1>
      <span v-if="!isCollapsed" class="sidebar-subtitle">{{ t('nav.subtitle') }}</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        to="/"
        class="nav-item"
        :class="{ active: $route.path === '/' }"
        :data-tooltip="t('nav.overview')"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor">
          <rect x="3" y="3" width="6" height="6" rx="1" stroke-width="1.5"/>
          <rect x="11" y="3" width="6" height="6" rx="1" stroke-width="1.5"/>
          <rect x="3" y="11" width="6" height="6" rx="1" stroke-width="1.5"/>
          <rect x="11" y="11" width="6" height="6" rx="1" stroke-width="1.5"/>
        </svg>
        <span>{{ t('nav.overview') }}</span>
      </router-link>

      <router-link
        to="/inventory"
        class="nav-item"
        :data-tooltip="t('nav.inventory')"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor">
          <path d="M4 6L10 3L16 6M4 6L10 9M4 6V14L10 17M10 9L16 6M10 9V17M16 6V14L10 17" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>{{ t('nav.inventory') }}</span>
      </router-link>

      <router-link
        to="/orders"
        class="nav-item"
        :data-tooltip="t('nav.orders')"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor">
          <path d="M4 4H16C16.5523 4 17 4.44772 17 5V15C17 15.5523 16.5523 16 16 16H4C3.44772 16 3 15.5523 3 15V5C3 4.44772 3.44772 4 4 4Z" stroke-width="1.5"/>
          <path d="M6 8H14M6 11H14" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ t('nav.orders') }}</span>
      </router-link>

      <router-link
        to="/spending"
        class="nav-item"
        :data-tooltip="t('nav.finance')"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor">
          <circle cx="10" cy="10" r="7" stroke-width="1.5"/>
          <path d="M10 6V10L13 13" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M12 7C12 7 11.5 6 10 6C8.5 6 7.5 7 7.5 8.5C7.5 10 9 10.5 10 11C11 11.5 12.5 12 12.5 13.5C12.5 15 11.5 16 10 16C8.5 16 8 15 8 15" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>{{ t('nav.finance') }}</span>
      </router-link>

      <router-link
        to="/demand"
        class="nav-item"
        :data-tooltip="t('nav.demandForecast')"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor">
          <path d="M4 14L8 10L12 13L16 6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M16 6V10M16 6H12" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>{{ t('nav.demandForecast') }}</span>
      </router-link>

      <router-link
        to="/reports"
        class="nav-item"
        data-tooltip="Reports"
      >
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor">
          <path d="M5 4H15C15.5523 4 16 4.44772 16 5V15C16 15.5523 15.5523 16 15 16H5C4.44772 16 4 15.5523 4 15V5C4 4.44772 4.44772 4 5 4Z" stroke-width="1.5"/>
          <path d="M7 8H13M7 11H13M7 14H10" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <span>Reports</span>
      </router-link>
    </nav>

    <div v-if="!isCollapsed" class="sidebar-section">
      <button
        class="section-header"
        @click="toggleFilters"
      >
        <span>Filters</span>
        <svg
          class="chevron"
          :class="{ 'chevron-open': filtersOpen }"
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
        >
          <path d="M3 5L6 8L9 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>
      <div v-if="filtersOpen" class="filters-content">
        <SidebarFilters />
      </div>
    </div>

    <div class="sidebar-spacer"></div>

    <button
      class="sidebar-toggle"
      @click="toggleSidebar"
      :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
    >
      <svg class="chevron-icon" viewBox="0 0 16 16" fill="none">
        <path
          v-if="!isCollapsed"
          d="M10 4L6 8L10 12"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <path
          v-else
          d="M6 4L10 8L6 12"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>

    <div class="sidebar-footer">
      <LanguageSwitcher variant="sidebar" :collapsed="isCollapsed" />
      <ProfileMenu
        variant="sidebar"
        :collapsed="isCollapsed"
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from '../composables/useI18n'
import SidebarFilters from './SidebarFilters.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

const { t } = useI18n()

const filtersOpen = ref(true)
const isCollapsed = ref(false)

const emit = defineEmits(['show-profile-details', 'show-tasks', 'sidebar-collapsed'])

const toggleFilters = () => {
  filtersOpen.value = !filtersOpen.value
}

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('sidebar-collapsed', isCollapsed.value)
  emit('sidebar-collapsed', isCollapsed.value)
}

onMounted(() => {
  const stored = localStorage.getItem('sidebar-collapsed')
  if (stored !== null) {
    isCollapsed.value = stored === 'true'
    emit('sidebar-collapsed', isCollapsed.value)
  }
})
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--sidebar-border);
  z-index: 100;
  overflow-y: auto;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-header {
  padding: 1.25rem 1rem;
  border-bottom: 1px solid var(--sidebar-border);
  transition: padding 0.3s ease;
}

.sidebar.collapsed .sidebar-header {
  padding: 1.25rem 0.5rem;
  text-align: center;
}

.sidebar-logo {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--sidebar-text);
  margin: 0 0 0.25rem 0;
  letter-spacing: -0.025em;
  transition: font-size 0.3s ease;
}

.sidebar.collapsed .sidebar-logo {
  font-size: 0.875rem;
  margin: 0;
}

.sidebar-subtitle {
  font-size: 0.75rem;
  color: var(--sidebar-text-muted);
  font-weight: 400;
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar-nav {
  padding: 1rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sidebar.collapsed .sidebar-nav {
  padding: 1rem 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 1rem;
  border-radius: 6px;
  color: var(--sidebar-text-muted);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s;
  position: relative;
}

.sidebar.collapsed .nav-item {
  padding: 0.625rem;
  justify-content: center;
}

.nav-item:hover {
  background: var(--sidebar-hover);
  color: var(--sidebar-text);
}

.nav-item.router-link-active,
.nav-item.active {
  background: var(--sidebar-active);
  color: var(--accent-primary);
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-item span {
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar.collapsed .nav-item span {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

/* Tooltips for collapsed state */
.sidebar.collapsed .nav-item::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  margin-left: 12px;
  padding: 6px 12px;
  background: #1e293b;
  color: white;
  border-radius: 6px;
  font-size: 0.875rem;
  white-space: nowrap;
  z-index: 1000;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.sidebar.collapsed .nav-item:hover::after {
  opacity: 1;
}

.sidebar-section {
  padding: 0 0.75rem;
  border-top: 1px solid var(--sidebar-border);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 1rem 0.25rem;
  background: none;
  border: none;
  color: var(--sidebar-text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  cursor: pointer;
  font-family: inherit;
  transition: color 0.15s;
}

.section-header:hover {
  color: var(--sidebar-text);
}

.chevron {
  transition: transform 0.2s ease;
  color: var(--sidebar-text-muted);
}

.chevron-open {
  transform: rotate(180deg);
}

.filters-content {
  padding: 0.5rem 0.25rem 1rem;
}

.sidebar-spacer {
  flex-grow: 1;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  margin: 0.5rem auto;
  background: var(--sidebar-hover);
  border: 1px solid var(--sidebar-border);
  border-radius: 50%;
  color: var(--sidebar-text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.sidebar-toggle:hover {
  background: var(--sidebar-active);
  color: var(--sidebar-text);
  border-color: var(--accent-primary);
}

.chevron-icon {
  width: 16px;
  height: 16px;
}

.sidebar-footer {
  padding: 1rem 0.75rem;
  border-top: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sidebar.collapsed .sidebar-footer {
  padding: 1rem 0.5rem;
}

/* Auto-collapse on small screens */
@media (max-width: 1024px) {
  .sidebar {
    width: var(--sidebar-collapsed-width);
  }

  .sidebar-logo {
    font-size: 0.875rem;
    margin: 0;
  }

  .sidebar-subtitle {
    opacity: 0;
  }

  .sidebar-header {
    padding: 1.25rem 0.5rem;
    text-align: center;
  }

  .sidebar-nav {
    padding: 1rem 0.5rem;
  }

  .nav-item {
    padding: 0.625rem;
    justify-content: center;
  }

  .nav-item span {
    opacity: 0;
    width: 0;
    overflow: hidden;
  }

  .nav-item::after {
    content: attr(data-tooltip);
    position: absolute;
    left: 100%;
    top: 50%;
    transform: translateY(-50%);
    margin-left: 12px;
    padding: 6px 12px;
    background: #1e293b;
    color: white;
    border-radius: 6px;
    font-size: 0.875rem;
    white-space: nowrap;
    z-index: 1000;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s ease;
  }

  .nav-item:hover::after {
    opacity: 1;
  }

  .sidebar-section {
    display: none;
  }

  .sidebar-footer {
    padding: 1rem 0.5rem;
  }
}
</style>
