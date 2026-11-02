<template>
  <div class="app">
    <!-- Backdrop only exists visually below the drawer breakpoint (see CSS) -->
    <div
      v-if="sidebarOpen"
      class="sidebar-backdrop"
      @click="sidebarOpen = false"
    ></div>

    <aside id="app-sidebar" class="sidebar" :class="{ open: sidebarOpen }">
      <div class="logo">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="subtitle">{{ t('nav.subtitle') }}</span>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          exact-active-class="active"
        >
          {{ t(item.labelKey) }}
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

    <div class="content">
      <button
        type="button"
        class="menu-button"
        :aria-label="t('nav.menu')"
        aria-controls="app-sidebar"
        :aria-expanded="sidebarOpen ? 'true' : 'false'"
        @click="sidebarOpen = !sidebarOpen"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
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
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
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
    const sidebarOpen = ref(false)
    const route = useRoute()

    // Single source of truth for the sidebar; order matches the router config.
    const navItems = [
      { path: '/', labelKey: 'nav.overview' },
      { path: '/inventory', labelKey: 'nav.inventory' },
      { path: '/orders', labelKey: 'nav.orders' },
      { path: '/spending', labelKey: 'nav.finance' },
      { path: '/demand', labelKey: 'nav.demandForecast' },
      { path: '/reports', labelKey: 'nav.reports' }
    ]

    // Close the mobile drawer after navigating so it doesn't cover the new page
    watch(() => route.path, () => { sidebarOpen.value = false })
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
      sidebarOpen,
      navItems,
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
  min-height: 100vh;
}

/*
 * Stacking: backdrop (sidebar - 1) < sidebar < dropdowns (1000) < modals (2000).
 * The sidebar must stay below dropdowns/modals so they can overlay it.
 */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
}

.logo {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-5) var(--space-4) var(--space-4);
}

.logo h1 {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--color-text-strong);
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  font-weight: 400;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
}

.nav-item {
  display: block;
  position: relative;
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: var(--text-base);
  border-radius: var(--radius-md);
  transition: background-color 0.2s ease, color 0.2s ease;
}

.nav-item:hover {
  color: var(--color-text-strong);
  background: var(--color-surface-muted);
}

/* "active" is applied via exact-active-class: '/' would prefix-match every route otherwise */
.nav-item.active {
  color: var(--color-accent);
  background: var(--color-accent-soft);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: var(--space-2);
  bottom: var(--space-2);
  width: 3px;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.content {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  max-width: var(--content-max-width);
  width: 100%;
  margin: 0 auto;
  padding: var(--space-5) var(--space-6);
}

.menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  align-self: flex-start;
  margin: var(--space-3) var(--space-4) 0;
  padding: var(--space-2);
  background: var(--color-surface);
  color: var(--color-text-strong);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.menu-button:hover {
  background: var(--color-surface-muted);
}

.sidebar-backdrop {
  display: none;
}

/* 900px: below this the fixed 248px rail leaves too little room for tables, so it becomes a drawer */
@media (max-width: 900px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    box-shadow: var(--shadow-md);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .content {
    margin-left: 0;
  }

  .menu-button {
    display: inline-flex;
  }

  /* One below the sidebar so the drawer sits above it, still far below dropdowns/modals */
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: var(--color-overlay);
    z-index: calc(var(--z-sidebar) - 1);
  }
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
