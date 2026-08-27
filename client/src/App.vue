<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ collapsed: isSidebarCollapsed }">
      <div class="sidebar-logo">
        <div class="logo-mark">CC</div>
        <div v-if="!isSidebarCollapsed" class="logo-text">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <button
        class="sidebar-toggle"
        :title="isSidebarCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        @click="toggleSidebar"
      >
        <svg class="toggle-icon" :class="{ flipped: isSidebarCollapsed }" viewBox="0 0 20 20" fill="none">
          <path d="M12.5 4L7 10L12.5 16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-if="!isSidebarCollapsed">{{ t('nav.collapseSidebar') }}</span>
      </button>

      <nav class="sidebar-nav">
        <router-link
          to="/"
          class="nav-link"
          :class="{ active: $route.path === '/' }"
          :title="isSidebarCollapsed ? t('nav.overview') : null"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none">
            <rect x="2.5" y="2.5" width="6.5" height="6.5" rx="1.25" stroke="currentColor" stroke-width="1.5"/>
            <rect x="11" y="2.5" width="6.5" height="6.5" rx="1.25" stroke="currentColor" stroke-width="1.5"/>
            <rect x="2.5" y="11" width="6.5" height="6.5" rx="1.25" stroke="currentColor" stroke-width="1.5"/>
            <rect x="11" y="11" width="6.5" height="6.5" rx="1.25" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.overview') }}</span>
        </router-link>

        <router-link
          to="/inventory"
          class="nav-link"
          :class="{ active: $route.path === '/inventory' }"
          :title="isSidebarCollapsed ? t('nav.inventory') : null"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none">
            <path d="M3 6L10 3L17 6V14L10 17L3 14V6Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M3 6L10 9L17 6" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M10 9V17" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link
          to="/orders"
          class="nav-link"
          :class="{ active: $route.path === '/orders' }"
          :title="isSidebarCollapsed ? t('nav.orders') : null"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none">
            <path d="M6 3H14C14.5523 3 15 3.44772 15 4V16C15 16.5523 14.5523 17 14 17H6C5.44772 17 5 16.5523 5 16V4C5 3.44772 5.44772 3 6 3Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 3V2C8 1.44772 8.44772 1 9 1H11C11.5523 1 12 1.44772 12 2V3" stroke="currentColor" stroke-width="1.5"/>
            <path d="M7.5 9.5L9 11L12.5 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.orders') }}</span>
        </router-link>

        <router-link
          to="/spending"
          class="nav-link"
          :class="{ active: $route.path === '/spending' }"
          :title="isSidebarCollapsed ? t('nav.finance') : null"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none">
            <path d="M4 16V10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M10 16V4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M16 16V8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.finance') }}</span>
        </router-link>

        <router-link
          to="/demand"
          class="nav-link"
          :class="{ active: $route.path === '/demand' }"
          :title="isSidebarCollapsed ? t('nav.demandForecast') : null"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none">
            <path d="M3 13L7.5 8.5L10.5 11.5L17 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 5H17V10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link
          to="/reports"
          class="nav-link"
          :class="{ active: $route.path === '/reports' }"
          :title="isSidebarCollapsed ? t('nav.reports') : null"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none">
            <path d="M6 2H12L16 6V16C16 16.5523 15.5523 17 15 17H6C5.44772 17 5 16.5523 5 16V3C5 2.44772 5.44772 2 6 2Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M12 2V6H16" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M7.5 10.5H13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M7.5 13.5H13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span v-if="!isSidebarCollapsed">{{ t('nav.reports') }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher :collapsed="isSidebarCollapsed" />
        <ProfileMenu
          :collapsed="isSidebarCollapsed"
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

    // Sidebar collapse: auto-collapses below AUTO_COLLAPSE_QUERY width, but a
    // manual toggle (persisted to localStorage) always overrides the auto behavior.
    const AUTO_COLLAPSE_QUERY = '(max-width: 1024px)'
    const mediaQuery = window.matchMedia(AUTO_COLLAPSE_QUERY)
    const isNarrowViewport = ref(mediaQuery.matches)

    const storedPreference = localStorage.getItem('sidebarCollapsed')
    const manualCollapsed = ref(storedPreference === null ? null : storedPreference === 'true')

    const isSidebarCollapsed = computed(() => {
      return manualCollapsed.value !== null ? manualCollapsed.value : isNarrowViewport.value
    })

    const toggleSidebar = () => {
      manualCollapsed.value = !isSidebarCollapsed.value
      localStorage.setItem('sidebarCollapsed', String(manualCollapsed.value))
    }

    const handleViewportChange = (event) => {
      isNarrowViewport.value = event.matches
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
    onMounted(() => mediaQuery.addEventListener('change', handleViewportChange))
    onUnmounted(() => mediaQuery.removeEventListener('change', handleViewportChange))

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      isSidebarCollapsed,
      toggleSidebar
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

.app-shell {
  display: flex;
  min-height: 100vh;
}

/* ---------- Sidebar ---------- */

.sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 100;
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar.collapsed .sidebar-logo {
  justify-content: center;
  padding: 1.5rem 0.75rem;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: calc(100% - 1.5rem);
  margin: 0.75rem 0.75rem 0;
  padding: 0.5rem 0.75rem;
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  color: #94a3b8;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.813rem;
  font-weight: 500;
  transition: all 0.15s ease;
}

.sidebar-toggle:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.06);
}

.sidebar.collapsed .sidebar-toggle {
  justify-content: center;
  width: calc(100% - 1.5rem);
}

.toggle-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.toggle-icon.flipped {
  transform: rotate(180deg);
}

.logo-mark {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.813rem;
  letter-spacing: 0.02em;
}

.logo-text {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.logo-text h1 {
  font-size: 0.938rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subtitle {
  font-size: 0.688rem;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 1rem 0.75rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: 8px;
  color: #94a3b8;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  transition: all 0.15s ease;
  position: relative;
}

.sidebar.collapsed .nav-link {
  justify-content: center;
  padding: 0.625rem;
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.nav-link:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.06);
}

.nav-link.active {
  color: #ffffff;
  background: rgba(59, 130, 246, 0.16);
}

.nav-link.active::before {
  content: '';
  position: absolute;
  left: -0.75rem;
  top: 0.25rem;
  bottom: 0.25rem;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #3b82f6;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-footer .language-switcher,
.sidebar-footer .profile-menu {
  width: 100%;
}

.sidebar-footer .language-button,
.sidebar-footer .profile-button {
  width: 100%;
}

.sidebar.collapsed .sidebar-footer {
  padding: 1rem 0.75rem;
}

/* ---------- Content area ---------- */

.content-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
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
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
  transform: translateY(-1px);
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
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
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
  border-radius: 999px;
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
