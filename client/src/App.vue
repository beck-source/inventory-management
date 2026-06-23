<template>
  <div class="app">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-header">
        <div class="logo">
          <h1 v-if="!isCollapsed">{{ t('nav.companyName') }}</h1>
          <h1 v-else class="logo-mark">{{ t('nav.companyName').charAt(0) }}</h1>
          <span v-if="!isCollapsed" class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <button
          class="collapse-toggle"
          type="button"
          :aria-label="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="toggleCollapsed"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" :class="{ flipped: isCollapsed }">
            <path d="M11 4L6 9L11 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link
          to="/"
          class="nav-item"
          :class="{ active: $route.path === '/' }"
          :data-tooltip="t('nav.overview')"
        >
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <rect x="2.5" y="2.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="11.5" y="2.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="2.5" y="11.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="11.5" y="11.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>

        <router-link
          to="/inventory"
          class="nav-item"
          :class="{ active: $route.path === '/inventory' }"
          :data-tooltip="t('nav.inventory')"
        >
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M2.5 6L10 2.5L17.5 6V14L10 17.5L2.5 14V6Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M2.5 6L10 9.5L17.5 6" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M10 9.5V17.5" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span class="nav-label">{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link
          to="/orders"
          class="nav-item"
          :class="{ active: $route.path === '/orders' }"
          :data-tooltip="t('nav.orders')"
        >
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <rect x="4" y="3.5" width="12" height="14" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M7.5 2.5H12.5V4.5H7.5V2.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M7 9H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M7 12.5H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.orders') }}</span>
        </router-link>

        <router-link
          to="/spending"
          class="nav-item"
          :class="{ active: $route.path === '/spending' }"
          :data-tooltip="t('nav.finance')"
        >
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 1.5V18.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M13.75 4.5H8.25C6.73122 4.5 5.5 5.73122 5.5 7.25C5.5 8.76878 6.73122 10 8.25 10H11.75C13.2688 10 14.5 11.2312 14.5 12.75C14.5 14.2688 13.2688 15.5 11.75 15.5H5.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.finance') }}</span>
        </router-link>

        <router-link
          to="/demand"
          class="nav-item"
          :class="{ active: $route.path === '/demand' }"
          :data-tooltip="t('nav.demandForecast')"
        >
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 17V3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M3 17H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M3 13L7.5 8.5L11 12L17 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link
          to="/restocking"
          class="nav-item"
          :class="{ active: $route.path === '/restocking' }"
          :data-tooltip="t('nav.restocking')"
        >
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M16.5 10C16.5 13.5899 13.5899 16.5 10 16.5C6.41015 16.5 4 13.5 4 13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3.5 10C3.5 6.41015 6.41015 3.5 10 3.5C13.5899 3.5 16 6.5 16 6.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M16 3.5V6.5H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M4 16.5V13.5H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.restocking') }}</span>
        </router-link>

        <router-link
          to="/reports"
          class="nav-item"
          :class="{ active: $route.path === '/reports' }"
          data-tooltip="Reports"
        >
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M5.5 2.5H12L15.5 6V16C15.5 16.5523 15.0523 17 14.5 17H5.5C4.94772 17 4.5 16.5523 4.5 16V3.5C4.5 2.94772 4.94772 2.5 5.5 2.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M7 10H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M7 13H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M7 7H10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">Reports</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content-area">
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
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

// Key used to persist the sidebar collapsed state across reloads.
const SIDEBAR_COLLAPSED_KEY = 'sidebar-collapsed'

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

    // Restore the sidebar collapsed state from localStorage on load.
    const isCollapsed = ref(localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === 'true')

    const toggleCollapsed = () => {
      isCollapsed.value = !isCollapsed.value
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(isCollapsed.value))
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

    onMounted(loadTasks)

    return {
      t,
      isCollapsed,
      toggleCollapsed,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
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

/* Sidebar shell */
.sidebar {
  display: flex;
  flex-direction: column;
  width: 16.25rem;
  flex-shrink: 0;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  height: 100vh;
  position: sticky;
  top: 0;
  transition: width 0.2s ease;
  overflow-x: hidden;
}

.sidebar.collapsed {
  width: 4.5rem;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 1.25rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  min-height: 4.5rem;
}

.sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 1.25rem 0.5rem;
}

.logo {
  display: flex;
  align-items: baseline;
  gap: 0.625rem;
  min-width: 0;
  overflow: hidden;
}

.logo h1 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  white-space: nowrap;
}

.logo h1.logo-mark {
  font-size: 1.25rem;
  text-align: center;
}

.subtitle {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
  white-space: nowrap;
}

.collapse-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.75rem;
  height: 1.75rem;
  flex-shrink: 0;
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s ease;
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

/* Sidebar navigation */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem 0.75rem;
  overflow-y: auto;
}

.sidebar.collapsed .sidebar-nav {
  padding: 1rem 0.5rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: 6px;
  transition: all 0.15s ease;
  position: relative;
  white-space: nowrap;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.625rem;
}

.nav-icon {
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.nav-item.active {
  color: #2563eb;
  background: #eff6ff;
}

/* Tooltip shown when sidebar is collapsed and a nav item is hovered. */
.sidebar.collapsed .nav-item[data-tooltip]:hover::after {
  content: attr(data-tooltip);
  position: absolute;
  left: calc(100% + 0.5rem);
  top: 50%;
  transform: translateY(-50%);
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0.375rem 0.625rem;
  font-size: 0.813rem;
  font-weight: 500;
  color: #0f172a;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  z-index: 200;
  pointer-events: none;
}

/* Sidebar footer */
.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding: 1rem 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.sidebar.collapsed .sidebar-footer {
  padding: 1rem 0.5rem;
  align-items: center;
}

.sidebar.collapsed .sidebar-footer > * {
  width: 2.25rem;
  overflow: hidden;
}

/* Content area */
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
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
  transition: all 0.2s ease;
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
