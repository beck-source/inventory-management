<template>
  <div class="app">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-brand">
        <h1>
          <span class="logo-full">{{ t('nav.companyName') }}</span>
          <span class="logo-mark">F</span>
        </h1>
        <span class="subtitle">{{ t('nav.subtitle') }}</span>
      </div>

      <button
        type="button"
        class="sidebar-toggle"
        :aria-label="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :disabled="isMobile"
        :title="isMobile ? 'Sidebar locked at this width' : ''"
        @click="toggle"
      >
        <svg
          v-if="isCollapsed"
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <polyline points="7 4 13 10 7 16" />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          width="18"
          height="18"
          viewBox="0 0 20 20"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <polyline points="13 4 7 10 13 16" />
        </svg>
      </button>

      <nav class="sidebar-nav">
        <router-link
          to="/"
          :title="t('nav.overview')"
          :class="{ active: $route.path === '/' }"
        >
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2.5" y="2.5" width="6" height="6" rx="1" />
              <rect x="11.5" y="2.5" width="6" height="6" rx="1" />
              <rect x="2.5" y="11.5" width="6" height="6" rx="1" />
              <rect x="11.5" y="11.5" width="6" height="6" rx="1" />
            </svg>
          </span>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>

        <router-link
          to="/inventory"
          :title="t('nav.inventory')"
          :class="{ active: $route.path === '/inventory' }"
        >
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2.5 6 10 2.5 17.5 6 10 9.5 2.5 6Z" />
              <path d="M2.5 6v8L10 17.5V9.5" />
              <path d="M17.5 6v8L10 17.5" />
            </svg>
          </span>
          <span class="nav-label">{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link
          to="/orders"
          :title="t('nav.orders')"
          :class="{ active: $route.path === '/orders' }"
        >
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <rect x="4" y="4" width="12" height="14" rx="1.5" />
              <rect x="7" y="2.5" width="6" height="3" rx="0.75" />
              <line x1="7" y1="10" x2="13" y2="10" />
              <line x1="7" y1="13" x2="13" y2="13" />
            </svg>
          </span>
          <span class="nav-label">{{ t('nav.orders') }}</span>
        </router-link>

        <router-link
          to="/restocking"
          title="Restocking"
          :class="{ active: $route.path === '/restocking' }"
        >
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16.5 6.5A7 7 0 1 0 17 12" />
              <polyline points="17 3 17 7 13 7" />
            </svg>
          </span>
          <span class="nav-label">Restocking</span>
        </router-link>

        <router-link
          to="/spending"
          :title="t('nav.finance')"
          :class="{ active: $route.path === '/spending' }"
        >
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="10" y1="2.5" x2="10" y2="17.5" />
              <path d="M13.5 5.5H8.25a2.25 2.25 0 0 0 0 4.5h3.5a2.25 2.25 0 0 1 0 4.5H6" />
            </svg>
          </span>
          <span class="nav-label">{{ t('nav.finance') }}</span>
        </router-link>

        <router-link
          to="/demand"
          :title="t('nav.demandForecast')"
          :class="{ active: $route.path === '/demand' }"
        >
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="2.5 15 7 10 10 12.5 17.5 5" />
              <polyline points="13 5 17.5 5 17.5 9.5" />
            </svg>
          </span>
          <span class="nav-label">{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link
          to="/reports"
          title="Reports"
          :class="{ active: $route.path === '/reports' }"
        >
          <span class="nav-icon" aria-hidden="true">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M4.5 2.5h7L15.5 6.5v11a0 0 0 0 1 0 0h-11a0 0 0 0 1 0 0Z" />
              <polyline points="11.5 2.5 11.5 6.5 15.5 6.5" />
              <line x1="7" y1="10.5" x2="13" y2="10.5" />
              <line x1="7" y1="13" x2="13" y2="13" />
              <line x1="7" y1="15.5" x2="11" y2="15.5" />
            </svg>
          </span>
          <span class="nav-label">Reports</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="sidebar-footer-item">
          <LanguageSwitcher />
        </div>
        <div class="sidebar-footer-item">
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </div>
    </aside>

    <div class="layout-content">
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
import { useSidebar } from './composables/useSidebar'
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
    const { isCollapsed, isMobile, toggle } = useSidebar()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

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
      isMobile,
      toggle,
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
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  transition: grid-template-columns 200ms ease;
}
.app:has(.sidebar.collapsed) { grid-template-columns: 64px 1fr; }
/* Fallback for browsers without :has — sidebar still works because of its own width transition */

.sidebar {
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  width: 240px;
  transition: width 200ms ease;
  overflow: hidden;
  position: sticky;
  top: 0;
  height: 100vh;
}
.sidebar.collapsed { width: 64px; }

.sidebar-brand {
  padding: 1.25rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  min-height: 64px;
}
.sidebar-brand h1 {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  white-space: nowrap;
}
.sidebar-brand .subtitle {
  font-size: 0.75rem;
  color: #64748b;
  white-space: nowrap;
  transition: opacity 150ms ease;
}
.sidebar.collapsed .sidebar-brand { padding: 1.25rem 0.5rem; justify-content: center; }
.sidebar.collapsed .sidebar-brand .subtitle,
.sidebar.collapsed .sidebar-brand .logo-full { display: none; }
.sidebar:not(.collapsed) .sidebar-brand .logo-mark { display: none; }

.sidebar-toggle {
  appearance: none;
  background: transparent;
  border: 1px solid #e2e8f0;
  color: #64748b;
  border-radius: 6px;
  padding: 0.375rem 0.5rem;
  margin: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 150ms ease, color 150ms ease;
}
.sidebar-toggle:hover:not(:disabled) { background: #f1f5f9; color: #0f172a; }
.sidebar-toggle:disabled { opacity: 0.5; cursor: not-allowed; }
.sidebar.collapsed .sidebar-toggle { margin: 0.75rem auto; }

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 0.5rem;
  flex: 1;
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
  transition: background 150ms ease, color 150ms ease;
  white-space: nowrap;
  overflow: hidden;
}
.sidebar-nav a:hover { background: #f1f5f9; color: #0f172a; }
.sidebar-nav a.active {
  background: #eff6ff;
  color: #2563eb;
}
.sidebar-nav .nav-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.sidebar-nav .nav-label {
  transition: opacity 150ms ease;
}
.sidebar.collapsed .sidebar-nav a { justify-content: center; padding: 0.625rem 0.5rem; }
.sidebar.collapsed .sidebar-nav .nav-label { opacity: 0; width: 0; }

.sidebar-footer {
  border-top: 1px solid #e2e8f0;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.sidebar.collapsed .sidebar-footer { padding: 0.75rem 0.25rem; }

.layout-content {
  display: flex;
  flex-direction: column;
  min-width: 0; /* allow children to overflow */
}

/* Keep main-content responsive in the new grid */
.main-content {
  flex: 1;
  width: 100%;
  max-width: none; /* was 1600px capped by old layout; now contained by the grid */
  margin: 0;
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
