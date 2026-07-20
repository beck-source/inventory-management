<template>
  <div class="app-shell">
    <AppSidebar />

    <div class="main">
      <header class="topbar">
        <h2 class="topbar-title">{{ pageTitle }}</h2>
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>

      <FilterBar />

      <main class="content">
        <div class="content-inner">
          <router-view />
        </div>
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
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import AppSidebar from './components/AppSidebar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const route = useRoute()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    const pageTitles = {
      '/': () => t('nav.overview'),
      '/inventory': () => t('nav.inventory'),
      '/orders': () => t('nav.orders'),
      '/restocking': () => 'Restocking',
      '/spending': () => t('nav.finance'),
      '/demand': () => t('nav.demandForecast'),
      '/reports': () => 'Reports'
    }

    const pageTitle = computed(() => {
      const resolver = pageTitles[route.path]
      return resolver ? resolver() : ''
    })

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
      pageTitle,
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
:root {
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-2: #f1f5f9;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-secondary: #334155;
  --color-text-muted: #64748b;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-weak: #eff6ff;
  --color-success: #059669;
  --color-success-weak: #d1fae5;
  --color-warning: #ea580c;
  --color-warning-weak: #fed7aa;
  --color-danger: #dc2626;
  --color-danger-weak: #fecaca;
  --color-info: #2563eb;
  --color-info-weak: #dbeafe;

  /* dark sidebar */
  --sidebar-bg: #0f172a;
  --sidebar-brand: #f8fafc;
  --sidebar-text: #94a3b8;
  --sidebar-text-hover: #f8fafc;
  --sidebar-hover-bg: rgba(255, 255, 255, .06);
  --sidebar-active-bg: rgba(37, 99, 235, .18);
  --sidebar-active-text: #ffffff;
  --sidebar-border: rgba(255, 255, 255, .08);

  /* spacing / radius / shadow / type */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, .04), 0 1px 3px rgba(15, 23, 42, .06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, .08);
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --sidebar-width: 248px;
  --topbar-height: 64px;
  --content-max-width: 1400px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

a:focus-visible,
button:focus-visible,
input:focus-visible,
select:focus-visible,
[tabindex]:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.app-shell {
  display: flex;
  min-height: 100vh;
}

.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: var(--topbar-height);
  flex-shrink: 0;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-5);
  position: sticky;
  top: 0;
  z-index: 100;
}

.topbar-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: var(--space-5);
}

.content-inner {
  max-width: var(--content-max-width);
  margin: 0 auto;
}

.page-header {
  margin-bottom: var(--space-5);
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-1);
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
  margin-bottom: var(--space-5);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
  min-width: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
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
  background: var(--color-surface-2);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 600;
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

th.numeric,
td.numeric {
  text-align: right;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-surface-2);
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--color-success-weak);
  color: #065f46;
}

.badge.warning {
  background: var(--color-warning-weak);
  color: #92400e;
}

.badge.danger {
  background: var(--color-danger-weak);
  color: #991b1b;
}

.badge.info {
  background: var(--color-info-weak);
  color: #1e40af;
}

.badge.increasing {
  background: var(--color-success-weak);
  color: #065f46;
}

.badge.decreasing {
  background: var(--color-danger-weak);
  color: #991b1b;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: var(--color-danger-weak);
  color: #991b1b;
}

.badge.medium {
  background: var(--color-warning-weak);
  color: #92400e;
}

.badge.low {
  background: var(--color-info-weak);
  color: #1e40af;
}

.loading {
  text-align: center;
  padding: var(--space-7);
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.error {
  background: var(--color-danger-weak);
  border: 1px solid var(--color-danger-weak);
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  margin: var(--space-4) 0;
  font-size: 0.938rem;
}

@media (max-width: 900px) {
  .topbar {
    padding: 0 var(--space-4);
  }

  .content {
    padding: var(--space-4);
  }
}
</style>
