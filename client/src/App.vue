<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-logo">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="sidebar-subtitle">{{ t('nav.subtitle') }}</span>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" :class="{ active: $route.path === '/' }" :title="isCollapsed ? t('nav.overview') : ''">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="nav-icon" aria-hidden="true">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
          </svg>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }" :title="isCollapsed ? t('nav.inventory') : ''">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="nav-icon" aria-hidden="true">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
          <span class="nav-label">{{ t('nav.inventory') }}</span>
        </router-link>
        <router-link to="/orders" :class="{ active: $route.path === '/orders' }" :title="isCollapsed ? t('nav.orders') : ''">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="nav-icon" aria-hidden="true">
            <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>
            <rect x="9" y="3" width="6" height="4" rx="1"/>
            <line x1="9" y1="12" x2="15" y2="12"/>
            <line x1="9" y1="16" x2="13" y2="16"/>
          </svg>
          <span class="nav-label">{{ t('nav.orders') }}</span>
        </router-link>
        <router-link to="/spending" :class="{ active: $route.path === '/spending' }" :title="isCollapsed ? t('nav.finance') : ''">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="nav-icon" aria-hidden="true">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
            <polyline points="17 6 23 6 23 12"/>
          </svg>
          <span class="nav-label">{{ t('nav.finance') }}</span>
        </router-link>
        <router-link to="/demand" :class="{ active: $route.path === '/demand' }" :title="isCollapsed ? t('nav.demandForecast') : ''">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="nav-icon" aria-hidden="true">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
          <span class="nav-label">{{ t('nav.demandForecast') }}</span>
        </router-link>
        <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }" :title="isCollapsed ? t('nav.restocking') : ''">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="nav-icon" aria-hidden="true">
            <polyline points="1 4 1 10 7 10"/>
            <path d="M3.51 15a9 9 0 1 0 .49-3.5"/>
          </svg>
          <span class="nav-label">{{ t('nav.restocking') }}</span>
        </router-link>
        <router-link to="/reports" :class="{ active: $route.path === '/reports' }" :title="isCollapsed ? 'Reports' : ''">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="nav-icon" aria-hidden="true">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          <span class="nav-label">Reports</span>
        </router-link>
        <button class="sidebar-toggle" @click="toggleSidebar" :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline v-if="!isCollapsed" points="15 18 9 12 15 6"/>
            <polyline v-else points="9 18 15 12 9 6"/>
          </svg>
        </button>
      </nav>
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="app-body" :class="{ collapsed: isCollapsed }">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal :is-open="showProfileDetails" @close="showProfileDetails = false" />
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
    const apiTasks = ref(api.getTasks())
    const isCollapsed = ref(false)

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const addTask = (taskData) => {
      const newTask = api.createTask(taskData)
      apiTasks.value.unshift(newTask)
    }

    const deleteTask = (taskId) => {
      const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)
      if (isMockTask) {
        const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
        if (index !== -1) currentUser.value.tasks.splice(index, 1)
      } else {
        api.deleteTask(taskId)
        apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
      }
    }

    const toggleTask = (taskId) => {
      const mockTask = currentUser.value.tasks.find(t => t.id === taskId)
      if (mockTask) {
        mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
      } else {
        const updatedTask = api.toggleTask(taskId)
        const index = apiTasks.value.findIndex(t => t.id === taskId)
        if (index !== -1) apiTasks.value[index] = updatedTask
      }
    }

    const toggleSidebar = () => {
      isCollapsed.value = !isCollapsed.value
    }

    onMounted(() => {
      if (window.innerWidth <= 768) isCollapsed.value = true
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

/* ── Sidebar ── */
.sidebar {
  width: 240px;
  min-height: 100vh;
  background: #0f172a;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar.collapsed .sidebar-logo h1,
.sidebar.collapsed .sidebar-subtitle,
.sidebar.collapsed .nav-label {
  display: none;
}

.sidebar.collapsed .sidebar-logo {
  padding: 1.125rem 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.sidebar-logo {
  padding: 1.5rem 1.25rem 1.125rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.sidebar-logo h1 {
  font-size: 1rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-subtitle {
  display: block;
  font-size: 0.7rem;
  color: #475569;
  margin-top: 0.2rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  padding: 0.875rem 0.625rem;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.563rem 0.875rem;
  color: #94a3b8;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 6px;
  border-left: 3px solid transparent;
  transition: color 0.15s ease, background 0.15s ease;
}

.sidebar-nav a:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.06);
}

.sidebar-nav a.active {
  color: #f8fafc;
  background: rgba(37, 99, 235, 0.18);
  border-left-color: #2563eb;
  font-weight: 600;
}

.nav-icon {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
}

/* Center icons when collapsed */
.sidebar.collapsed .sidebar-nav a {
  justify-content: center;
  padding: 0.563rem;
  position: relative;
}

/* Styled tooltip via CSS — shows the title attribute value to the right of the icon */
.sidebar.collapsed .sidebar-nav a[title]:hover::after {
  content: attr(title);
  position: absolute;
  left: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%);
  background: #1e293b;
  color: #f8fafc;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
  padding: 0.35rem 0.65rem;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  pointer-events: none;
  z-index: 200;
}

.sidebar.collapsed .sidebar-toggle {
  justify-content: center;
  padding: 0.563rem;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  width: 100%;
  padding: 0.563rem 0.875rem;
  background: none;
  border: none;
  border-radius: 6px;
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease;
  margin-top: 0.5rem;
}

.sidebar-toggle:hover {
  color: #f1f5f9;
  background: rgba(255, 255, 255, 0.06);
}

.sidebar-footer {
  padding: 0.875rem 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* ── App body ── */
.app-layout {
  display: flex;
  min-height: 100vh;
}

.app-body {
  margin-left: 240px;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f8fafc;
  transition: margin-left 0.2s ease;
}

.app-body.collapsed {
  margin-left: 60px;
}

.main-content {
  flex: 1;
  padding: 1.75rem 2rem;
  max-width: 1400px;
  width: 100%;
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
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid #e2e8f0;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
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
