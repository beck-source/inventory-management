<template>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-logo">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="sidebar-subtitle">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" :class="{ active: $route.path === '/' }">
          {{ t('nav.overview') }}
        </router-link>
        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
          {{ t('nav.inventory') }}
        </router-link>
        <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
          {{ t('nav.orders') }}
        </router-link>
        <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
          {{ t('nav.finance') }}
        </router-link>
        <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
          {{ t('nav.demandForecast') }}
        </router-link>
        <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
          {{ t('nav.restocking') }}
        </router-link>
        <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
          {{ t('nav.reports') }}
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
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* ============================================================
   CSS Custom Properties
   ============================================================ */
:root {
  --accent: #2563eb;
  --accent-light: #eff6ff;
  --accent-hover: #1d4ed8;
  --sidebar-width: 220px;
  --border: #e2e8f0;
  --surface: #ffffff;
  --bg: #f8fafc;
  --text-primary: #0f172a;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -1px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.04);
}

/* ============================================================
   Reset & Base
   ============================================================ */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--bg);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ============================================================
   App Layout
   ============================================================ */
.app {
  display: flex;
  min-height: 100vh;
}

/* ============================================================
   Sidebar
   ============================================================ */
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 100;
}

.sidebar-logo {
  padding: 1.5rem 1.25rem 1.25rem;
  border-bottom: 1px solid var(--border);
}

.sidebar-logo h1 {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.sidebar-subtitle {
  display: block;
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 400;
  margin-top: 0.25rem;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 1rem 0.75rem;
  overflow-y: auto;
}

.sidebar-nav a {
  display: block;
  padding: 0.625rem 0.75rem;
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.sidebar-nav a:hover {
  color: var(--text-primary);
  background: #f1f5f9;
}

.sidebar-nav a.active {
  color: var(--accent);
  background: var(--accent-light);
}

.sidebar-footer {
  padding: 0.75rem 1.25rem;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

/* ============================================================
   Content Area
   ============================================================ */
.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-content {
  flex: 1;
  padding: 1.5rem 2rem;
}

/* ============================================================
   Mobile: collapse sidebar to top strip
   ============================================================ */
@media (max-width: 768px) {
  .app {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: auto;
    position: static;
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    gap: 0;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }

  .sidebar-logo {
    border-bottom: none;
    border-right: 1px solid var(--border);
    padding: 0.75rem 1rem;
  }

  .sidebar-nav {
    flex-direction: row;
    flex-wrap: wrap;
    flex: 1;
    padding: 0.5rem 0.75rem;
    gap: 0.125rem;
    overflow-y: visible;
  }

  .sidebar-footer {
    border-top: none;
    border-left: 1px solid var(--border);
    padding: 0.75rem 1rem;
  }
}

/* ============================================================
   Filter Bar
   ============================================================ */
.filters-bar {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0.75rem 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

/* ============================================================
   Page Header
   ============================================================ */
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.page-header p {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

/* ============================================================
   Stats Grid
   ============================================================ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

/* ============================================================
   Stat Card
   ============================================================ */
.stat-card {
  background: var(--surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: 1.25rem 1.5rem;
  border: 1px solid var(--border);
  border-top: 3px solid var(--accent);
}

.stat-card.success { border-top-color: #10b981; }
.stat-card.warning { border-top-color: #f59e0b; }
.stat-card.danger  { border-top-color: #ef4444; }
.stat-card.info    { border-top-color: #3b82f6; }

.stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
  margin-top: 0.375rem;
  letter-spacing: -0.025em;
}

/* ============================================================
   Card
   ============================================================ */
.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: 1.5rem;
  border: 1px solid rgba(226, 232, 240, 0.6);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.card-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

/* ============================================================
   Section Title
   ============================================================ */
.section-title {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
  margin-bottom: 1rem;
}

/* ============================================================
   Table System
   ============================================================ */
.table-container {
  overflow-x: auto;
  border-radius: var(--radius-md);
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

thead th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  background: var(--bg);
  border-bottom: 1px solid var(--border);
}

tbody td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  color: var(--text-primary);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--bg);
}

tbody tr:last-child td {
  border-bottom: none;
}

/* ============================================================
   Badge System
   ============================================================ */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.badge.success    { background: #dcfce7; color: #16a34a; }
.badge.info       { background: #dbeafe; color: #2563eb; }
.badge.warning    { background: #fef9c3; color: #ca8a04; }
.badge.danger     { background: #fee2e2; color: #dc2626; }
.badge.increasing { background: #dcfce7; color: #16a34a; }
.badge.stable     { background: #dbeafe; color: #2563eb; }
.badge.decreasing { background: #fee2e2; color: #dc2626; }
.badge.high       { background: #fee2e2; color: #dc2626; }
.badge.medium     { background: #fef9c3; color: #ca8a04; }
.badge.low        { background: #dbeafe; color: #2563eb; }

/* ============================================================
   Loading & Error States
   ============================================================ */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.error {
  background: #fee2e2;
  color: #dc2626;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  border: 1px solid #fecaca;
}
</style>
