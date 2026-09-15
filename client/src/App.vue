<template>
  <div class="app">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-header">
        <div class="logo">
          <span v-if="isCollapsed" class="logo-mark">{{ companyInitial }}</span>
          <template v-else>
            <h1>{{ t('nav.companyName') }}</h1>
            <span class="subtitle">{{ t('nav.subtitle') }}</span>
          </template>
        </div>
        <button
          class="sidebar-toggle"
          @click="toggleSidebar"
          :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-label="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        >
          <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
            <path d="M12.5 5L7.5 10L12.5 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <nav class="nav-links">
        <router-link to="/" :class="{ active: $route.path === '/' }" :title="t('nav.overview')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2.5" y="2.5" width="6" height="6" rx="1"/>
            <rect x="11.5" y="2.5" width="6" height="6" rx="1"/>
            <rect x="2.5" y="11.5" width="6" height="6" rx="1"/>
            <rect x="11.5" y="11.5" width="6" height="6" rx="1"/>
          </svg>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }" :title="t('nav.inventory')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10 2.5L17 6.25V13.75L10 17.5L3 13.75V6.25L10 2.5Z"/>
            <path d="M3 6.25L10 10L17 6.25"/>
            <path d="M10 10V17.5"/>
          </svg>
          <span class="nav-label">{{ t('nav.inventory') }}</span>
        </router-link>
        <router-link to="/orders" :class="{ active: $route.path === '/orders' }" :title="t('nav.orders')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="4" y="3.5" width="12" height="14" rx="1.5"/>
            <path d="M7.5 2.5H12.5V4.5H7.5V2.5Z"/>
            <path d="M7 9H13M7 12H13M7 15H10.5"/>
          </svg>
          <span class="nav-label">{{ t('nav.orders') }}</span>
        </router-link>
        <router-link to="/spending" :class="{ active: $route.path === '/spending' }" :title="t('nav.finance')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="10" cy="10" r="7.5"/>
            <path d="M10 5.5V14.5"/>
            <path d="M12.5 7.5C12.5 6.5 11.4 6 10 6C8.6 6 7.5 6.8 7.5 7.9C7.5 10.1 12.5 9 12.5 11.6C12.5 12.9 11.3 13.5 10 13.5C8.7 13.5 7.5 13 7.5 12"/>
          </svg>
          <span class="nav-label">{{ t('nav.finance') }}</span>
        </router-link>
        <router-link to="/demand" :class="{ active: $route.path === '/demand' }" :title="t('nav.demandForecast')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 13.5L8 8.5L11 11.5L17 5.5"/>
            <path d="M12.5 5.5H17V10"/>
          </svg>
          <span class="nav-label">{{ t('nav.demandForecast') }}</span>
        </router-link>
        <router-link to="/reports" :class="{ active: $route.path === '/reports' }" title="Reports">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 2.5H12L15.5 6V17C15.5 17.2761 15.2761 17.5 15 17.5H6C5.72386 17.5 5.5 17.2761 5.5 17V3C5.5 2.72386 5.72386 2.5 6 2.5Z"/>
            <path d="M12 2.5V6H15.5"/>
            <path d="M7.5 10H12.5M7.5 13H12.5"/>
          </svg>
          <span class="nav-label">Reports</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher :collapsed="isCollapsed" />
        <ProfileMenu
          :collapsed="isCollapsed"
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content-area" :class="{ collapsed: isCollapsed }">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Sidebar collapse/expand state
    const SIDEBAR_STORAGE_KEY = 'sidebar-collapsed'
    const SIDEBAR_BREAKPOINT = 1024

    const readStoredSidebarPreference = () => {
      try {
        const stored = window.localStorage.getItem(SIDEBAR_STORAGE_KEY)
        if (stored === 'true') return true
        if (stored === 'false') return false
      } catch (err) {
        console.error('Failed to read sidebar preference:', err)
      }
      return null
    }

    const writeStoredSidebarPreference = (value) => {
      try {
        window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(value))
      } catch (err) {
        console.error('Failed to persist sidebar preference:', err)
      }
    }

    const breakpointQuery = typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia(`(max-width: ${SIDEBAR_BREAKPOINT - 1}px)`)
      : null

    const storedSidebarPreference = readStoredSidebarPreference()
    const hasManualSidebarOverride = ref(storedSidebarPreference !== null)
    const isCollapsed = ref(
      storedSidebarPreference !== null
        ? storedSidebarPreference
        : (breakpointQuery ? breakpointQuery.matches : false)
    )

    const companyInitial = computed(() => {
      const name = t('nav.companyName') || ''
      return name.trim().charAt(0).toUpperCase() || 'I'
    })

    const handleBreakpointChange = (event) => {
      if (!hasManualSidebarOverride.value) {
        isCollapsed.value = event.matches
      }
    }

    const toggleSidebar = () => {
      isCollapsed.value = !isCollapsed.value
      hasManualSidebarOverride.value = true
      writeStoredSidebarPreference(isCollapsed.value)
    }

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(() => {
      loadTasks()

      if (breakpointQuery) {
        if (typeof breakpointQuery.addEventListener === 'function') {
          breakpointQuery.addEventListener('change', handleBreakpointChange)
        } else if (typeof breakpointQuery.addListener === 'function') {
          // Legacy fallback (older Safari)
          breakpointQuery.addListener(handleBreakpointChange)
        }
      }
    })

    onUnmounted(() => {
      if (breakpointQuery) {
        if (typeof breakpointQuery.removeEventListener === 'function') {
          breakpointQuery.removeEventListener('change', handleBreakpointChange)
        } else if (typeof breakpointQuery.removeListener === 'function') {
          breakpointQuery.removeListener(handleBreakpointChange)
        }
      }
    })

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      isCollapsed,
      toggleSidebar,
      companyInitial
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #f8fafc;
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 240px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-header {
  padding: 24px 24px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.sidebar.collapsed .sidebar-header {
  flex-direction: column;
  padding: 20px 12px 16px;
}

.logo {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  overflow: hidden;
}

.logo h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  line-height: 1.2;
  white-space: nowrap;
}

.logo-mark {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: #2563eb;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: -0.025em;
  flex-shrink: 0;
}

.subtitle {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
  white-space: nowrap;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.sidebar-toggle:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #0f172a;
}

.sidebar-toggle svg {
  transition: transform 0.2s ease;
}

.sidebar.collapsed .sidebar-toggle svg {
  transform: rotate(180deg);
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 16px;
  flex: 1;
}

.sidebar.collapsed .nav-links {
  padding: 8px 12px;
  align-items: center;
}

.nav-links a {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 0.75rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: 8px;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
}

.sidebar.collapsed .nav-links a {
  justify-content: center;
  padding: 0.625rem;
  width: 48px;
}

.nav-icon {
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar.collapsed .nav-label {
  display: none;
}

.nav-links a:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.nav-links a.active {
  color: #2563eb;
  background: #eff6ff;
  border-left-color: #2563eb;
  font-weight: 600;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 24px 24px;
  border-top: 1px solid #e2e8f0;
}

.sidebar.collapsed .sidebar-footer {
  padding: 16px 12px 20px;
  align-items: center;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin-left: 240px;
  width: calc(100% - 240px);
  transition: margin-left 0.2s ease, width 0.2s ease;
}

.content-area.collapsed {
  margin-left: 72px;
  width: calc(100% - 72px);
}

.main-content {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.stat-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: #ea580c;
}

.stat-card.success .stat-value {
  color: #059669;
}

.stat-card.danger .stat-value {
  color: #dc2626;
}

.stat-card.info .stat-value {
  color: #2563eb;
}

.card {
  background: white;
  border-radius: 10px;
  padding: 1.25rem;
  border: 1px solid #e2e8f0;
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: #f8fafc;
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning {
  background: #fed7aa;
  color: #92400e;
}

.badge.danger {
  background: #fecaca;
  color: #991b1b;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.decreasing {
  background: #fecaca;
  color: #991b1b;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: #fecaca;
  color: #991b1b;
}

.badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
