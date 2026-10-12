<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <button
          class="sidebar-toggle"
          @click="toggleSidebar"
          :aria-expanded="!sidebarCollapsed"
          aria-label="Toggle sidebar"
        >
          <svg viewBox="0 0 18 18" fill="none" width="16" height="16">
            <path v-if="!sidebarCollapsed" d="M11 3L6 9L11 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path v-else d="M7 3L12 9L7 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="sidebar-link" :class="{ active: $route.path === '/' }" :title="t('nav.overview')">
          <svg class="sidebar-link-icon" viewBox="0 0 18 18" fill="none"><path d="M2 9L9 2L16 9M4 7V15C4 15.55 4.45 16 5 16H7.5V11.5C7.5 11.22 7.72 11 8 11H10C10.28 11 10.5 11.22 10.5 11.5V16H13C13.55 16 14 15.55 14 15V7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/inventory" class="sidebar-link" :class="{ active: $route.path === '/inventory' }" :title="t('nav.inventory')">
          <svg class="sidebar-link-icon" viewBox="0 0 18 18" fill="none"><path d="M2 5L9 2L16 5V13L9 16L2 13V5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M2 5L9 8L16 5M9 8V16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.inventory') }}</span>
        </router-link>
        <router-link to="/orders" class="sidebar-link" :class="{ active: $route.path === '/orders' }" :title="t('nav.orders')">
          <svg class="sidebar-link-icon" viewBox="0 0 18 18" fill="none"><path d="M5 2H13C13.55 2 14 2.45 14 3V16L9 13.5L4 16V3C4 2.45 4.45 2 5 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.orders') }}</span>
        </router-link>
        <router-link to="/spending" class="sidebar-link" :class="{ active: $route.path === '/spending' }" :title="t('nav.finance')">
          <svg class="sidebar-link-icon" viewBox="0 0 18 18" fill="none"><path d="M9 1V17M13 4.5C13 3 11.5 2 9 2C6.5 2 5 3.2 5 4.8C5 6.4 6.5 7 9 7.5C11.5 8 13 8.9 13 10.5C13 12.1 11.5 13.3 9 13.3C6.5 13.3 5 12.3 5 10.8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>{{ t('nav.finance') }}</span>
        </router-link>
        <router-link to="/demand" class="sidebar-link" :class="{ active: $route.path === '/demand' }" :title="t('nav.demandForecast')">
          <svg class="sidebar-link-icon" viewBox="0 0 18 18" fill="none"><path d="M2 14L6.5 8.5L10 11.5L16 3.5M16 3.5H11.5M16 3.5V8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>{{ t('nav.demandForecast') }}</span>
        </router-link>
        <router-link to="/reports" class="sidebar-link" :class="{ active: $route.path === '/reports' }" title="Reports">
          <svg class="sidebar-link-icon" viewBox="0 0 18 18" fill="none"><path d="M4 2H11L15 6V15C15 15.55 14.55 16 14 16H4C3.45 16 3 15.55 3 15V3C3 2.45 3.45 2 4 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.5 10H11.5M6.5 12.5H11.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>Reports</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher />
      </div>
    </aside>

    <div class="app-main">
      <header class="content-topbar">
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </header>
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
    const sidebarCollapsed = ref(false)
    const toggleSidebar = () => { sidebarCollapsed.value = !sidebarCollapsed.value }
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
      showProfileDetails,
      showTasks,
      sidebarCollapsed,
      toggleSidebar,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
:root {
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-border-subtle: #f1f5f9;
  --color-text-primary: #0f172a;
  --color-text-secondary: #334155;
  --color-text-tertiary: #475569;
  --color-text-muted: #64748b;
  --color-text-faint: #94a3b8;
  --color-brand: #2563eb;
  --color-brand-hover: #f1f5f9;
  --color-brand-light: #eff6ff;
  --color-success: #059669;
  --color-success-bg: #d1fae5;
  --color-success-text: #065f46;
  --color-warning: #ea580c;
  --color-warning-bg: #fed7aa;
  --color-warning-text: #92400e;
  --color-danger: #dc2626;
  --color-danger-bg: #fecaca;
  --color-danger-text: #991b1b;
  --color-info-bg: #dbeafe;
  --color-info-text: #1e40af;

  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;

  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);

  --sidebar-width: 260px;
  --topbar-height: 64px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app-shell {
  display: flex;
  min-height: 100vh;
}

/* ---------- Sidebar ---------- */

.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  z-index: 100;
  transition: width 0.2s ease;
}

.sidebar-header {
  padding: var(--space-6) var(--space-5) var(--space-5);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
}

.logo {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.logo h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 400;
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  overflow-y: auto;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0.625rem var(--space-4);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: var(--radius-sm);
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
}

.sidebar-link-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.sidebar-link:hover {
  color: var(--color-text-primary);
  background: var(--color-border-subtle);
}

.sidebar-link.active {
  color: var(--color-brand);
  background: var(--color-brand-light);
  border-left-color: var(--color-brand);
  font-weight: 600;
}

.sidebar-footer {
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid var(--color-border);
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.sidebar-toggle:hover {
  background: var(--color-border-subtle);
  color: var(--color-text-primary);
}

/* Manual collapse (any viewport width) */
.sidebar.collapsed {
  width: 72px;
}

.sidebar.collapsed .sidebar-header {
  padding: var(--space-5) var(--space-3);
  flex-direction: column;
  gap: var(--space-3);
}

.sidebar.collapsed .logo {
  display: none;
}

.sidebar.collapsed .sidebar-link {
  justify-content: center;
  padding: 0.625rem;
}

.sidebar.collapsed .sidebar-link span {
  display: none;
}

.sidebar.collapsed .sidebar-footer {
  display: flex;
  justify-content: center;
}

/* Automatic icons-only mode on narrower screens, independent of manual toggle */
@media (max-width: 1024px) {
  .sidebar:not(.collapsed) {
    width: 72px;
  }

  .sidebar:not(.collapsed) .sidebar-header {
    padding: var(--space-5) var(--space-3);
    flex-direction: column;
    gap: var(--space-3);
  }

  .sidebar:not(.collapsed) .logo {
    display: none;
  }

  .sidebar:not(.collapsed) .sidebar-link {
    justify-content: center;
    padding: 0.625rem;
  }

  .sidebar:not(.collapsed) .sidebar-link span {
    display: none;
  }

  .sidebar:not(.collapsed) .sidebar-footer {
    display: flex;
    justify-content: center;
  }
}

/* ---------- Content column ---------- */

.app-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.content-topbar {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  height: var(--topbar-height);
  padding: 0 var(--space-6);
}

.main-content {
  flex: 1;
  width: 100%;
  padding: var(--space-6);
}

/* ---------- Shared page/content classes (tokenized, same layout as before) ---------- */

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.stat-card:hover {
  border-color: var(--color-border-strong);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger .stat-value { color: var(--color-danger); }
.stat-card.info .stat-value { color: var(--color-brand); }

.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-5);
  transition: box-shadow 0.2s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text-primary);
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
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: var(--color-text-tertiary);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-bg);
}

.badge {
  display: inline-block;
  padding: 0.313rem var(--space-3);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success, .badge.increasing { background: var(--color-success-bg); color: var(--color-success-text); }
.badge.warning { background: var(--color-warning-bg); color: var(--color-warning-text); }
.badge.danger, .badge.decreasing, .badge.high { background: var(--color-danger-bg); color: var(--color-danger-text); }
.badge.info, .badge.low { background: var(--color-info-bg); color: var(--color-info-text); }
.badge.medium { background: var(--color-warning-bg); color: var(--color-warning-text); }
.badge.stable { background: #e0e7ff; color: #3730a3; }

.loading {
  text-align: center;
  padding: var(--space-8);
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid var(--color-danger-bg);
  color: var(--color-danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: 0.938rem;
}
</style>
