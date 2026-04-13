<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-sub">{{ t('nav.subtitle') }}</span>
      </div>
      <nav class="sidebar-nav">
        <router-link class="nav-item" to="/"><span class="nav-icon">&#9638;</span><span class="nav-label">{{ t('nav.overview') }}</span></router-link>
        <router-link class="nav-item" to="/inventory"><span class="nav-icon">&#9635;</span><span class="nav-label">{{ t('nav.inventory') }}</span></router-link>
        <router-link class="nav-item" to="/orders"><span class="nav-icon">&#9636;</span><span class="nav-label">{{ t('nav.orders') }}</span></router-link>
        <router-link class="nav-item" to="/spending"><span class="nav-icon">$</span><span class="nav-label">{{ t('nav.finance') }}</span></router-link>
        <router-link class="nav-item" to="/demand"><span class="nav-icon">&#9650;</span><span class="nav-label">{{ t('nav.demandForecast') }}</span></router-link>
        <router-link class="nav-item" to="/reports"><span class="nav-icon">&#9637;</span><span class="nav-label">Reports</span></router-link>
      </nav>
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu @show-profile-details="showProfileDetails = true" @show-tasks="showTasks = true" />
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <h1 class="page-title">{{ $route.name }}</h1>
        <div class="topbar-actions"></div>
      </header>
      <div class="filter-row"><FilterBar /></div>
      <main class="content"><router-view /></main>
    </div>

    <ProfileDetailsModal :is-open="showProfileDetails" @close="showProfileDetails = false" />
    <TasksModal :is-open="showTasks" :tasks="tasks" @close="showTasks = false" @add-task="addTask" @delete-task="deleteTask" @toggle-task="toggleTask" />
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
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --sidebar-w: 240px;
  --topbar-h: 60px;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-5: 24px; --space-6: 32px; --space-7: 48px;
  --surface-0: #ffffff; --surface-1: #f8fafc; --surface-3: #e2e8f0;
  --sidebar-bg: #0f172a; --sidebar-text: #cbd5e1; --sidebar-text-muted: #64748b; --sidebar-hover: #1e293b; --sidebar-border: #1e293b;
  --border: #e2e8f0;
  --text-1: #0f172a; --text-2: #64748b; --text-3: #94a3b8;
  --accent: #6366f1; --accent-soft: #eef2ff; --accent-contrast: #ffffff;
  --success: #10b981; --warning: #f59e0b; --danger: #ef4444; --info: #6366f1;
  --radius-sm: 4px; --radius-md: 6px; --radius-lg: 10px;
  --shadow-sm: 0 1px 2px rgba(15,23,42,0.04); --shadow-md: 0 4px 12px rgba(15,23,42,0.08);
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --text-xs: 0.75rem; --text-sm: 0.875rem; --text-md: 0.9375rem; --text-lg: 1.125rem; --text-xl: 1.375rem;
}
body { font-family: var(--font-sans); background: var(--surface-1); color: var(--text-1); -webkit-font-smoothing: antialiased; }

/* Shell layout */
.app-shell { display: grid; grid-template-columns: var(--sidebar-w) 1fr; height: 100vh; }
.sidebar { background: var(--sidebar-bg); display: flex; flex-direction: column; padding: var(--space-5) var(--space-3); gap: var(--space-1); overflow-y: auto; height: 100vh; }
.sidebar-brand { padding: 0 var(--space-3) var(--space-5); border-bottom: 1px solid var(--sidebar-border); margin-bottom: var(--space-4); }
.brand-name { display: block; color: #fff; font-weight: 600; font-size: var(--text-lg); letter-spacing: -0.01em; }
.brand-sub { display: block; color: var(--sidebar-text-muted); font-size: var(--text-xs); margin-top: 2px; }
.sidebar-nav { display: flex; flex-direction: column; gap: var(--space-1); }
.nav-item { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3); border-radius: var(--radius-md); color: var(--sidebar-text); font-size: var(--text-sm); font-weight: 500; text-decoration: none; transition: background 120ms ease, color 120ms ease; }
.nav-item:hover { background: var(--sidebar-hover); color: #fff; }
.nav-item.router-link-exact-active { background: var(--accent); color: var(--accent-contrast); }
.nav-icon { display: inline-flex; width: 18px; justify-content: center; font-size: var(--text-sm); opacity: 0.9; }
.sidebar-footer { margin-top: auto; padding-top: var(--space-4); border-top: 1px solid var(--sidebar-border); display: flex; flex-direction: column; gap: var(--space-3); }
.main { display: flex; flex-direction: column; min-width: 0; background: var(--surface-1); height: 100vh; overflow: hidden; }
.topbar { height: var(--topbar-h); flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: 0 var(--space-6); border-bottom: 1px solid var(--border); background: var(--surface-0); }
.page-title { font-size: var(--text-xl); font-weight: 600; letter-spacing: -0.01em; }
.topbar-actions { display: flex; align-items: center; gap: var(--space-3); }
.filter-row { flex-shrink: 0; padding: var(--space-3) var(--space-6); border-bottom: 1px solid var(--border); background: var(--surface-0); overflow-x: auto; }
.content { flex: 1; overflow-y: auto; padding: var(--space-6); }

/* Responsive — collapse to icon rail below 960px */
@media (max-width: 960px) {
  :root { --sidebar-w: 64px; }
  .sidebar { padding: var(--space-5) var(--space-2); }
  .brand-sub, .nav-label { display: none; }
  .sidebar-brand { display: none; }
  .nav-item { justify-content: center; padding: var(--space-3) 0; }
  .sidebar-footer { align-items: center; }
}

/* Global component classes */
.page-header { margin-bottom: var(--space-5); }
.page-header h2 { font-size: var(--text-lg); font-weight: 600; color: var(--text-1); margin-bottom: var(--space-1); }
.page-header p { color: var(--text-2); font-size: var(--text-sm); }

.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: var(--space-5); margin-bottom: var(--space-5); }
.stat-card { background: var(--surface-0); padding: var(--space-5); border-radius: var(--radius-lg); border: 1px solid var(--border); box-shadow: var(--shadow-sm); transition: box-shadow 120ms ease, border-color 120ms ease; }
.stat-card:hover { border-color: #cbd5e1; box-shadow: var(--shadow-md); }
.stat-label { color: var(--text-2); font-size: var(--text-xs); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: var(--space-2); }
.stat-value { font-size: 2rem; font-weight: 700; color: var(--text-1); letter-spacing: -0.02em; }
.stat-card.warning .stat-value { color: var(--warning); }
.stat-card.success .stat-value { color: var(--success); }
.stat-card.danger .stat-value { color: var(--danger); }
.stat-card.info .stat-value { color: var(--info); }

.card { background: var(--surface-0); border-radius: var(--radius-lg); padding: var(--space-5); border: 1px solid var(--border); box-shadow: var(--shadow-sm); margin-bottom: var(--space-5); }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-4); padding-bottom: var(--space-3); border-bottom: 1px solid var(--border); }
.card-title { font-size: var(--text-lg); font-weight: 600; color: var(--text-1); }

.table-container { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead { background: var(--surface-1); border-bottom: 1px solid var(--border); }
th { text-align: left; padding: var(--space-2) var(--space-3); font-weight: 600; color: var(--text-2); font-size: var(--text-xs); text-transform: uppercase; letter-spacing: 0.05em; }
td { padding: var(--space-3); border-top: 1px solid var(--border); color: var(--text-1); font-size: var(--text-sm); }
tbody tr { transition: background 120ms ease; }
tbody tr:hover { background: var(--surface-1); }

.badge { display: inline-block; padding: 2px var(--space-2); border-radius: 999px; font-size: var(--text-xs); font-weight: 500; }
.badge.success, .badge.increasing { background: #d1fae5; color: #065f46; }
.badge.warning, .badge.medium { background: #fef3c7; color: #92400e; }
.badge.danger, .badge.decreasing, .badge.high { background: #fee2e2; color: #991b1b; }
.badge.info, .badge.stable, .badge.low { background: var(--accent-soft); color: var(--accent); }

.loading { text-align: center; padding: var(--space-7); color: var(--text-2); font-size: var(--text-sm); }
.error { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: var(--space-4); border-radius: var(--radius-md); margin: var(--space-4) 0; font-size: var(--text-sm); }

button { font-family: inherit; cursor: pointer; }
select, input { font-family: inherit; border: 1px solid var(--border); border-radius: var(--radius-md); padding: var(--space-2) var(--space-3); font-size: var(--text-sm); background: var(--surface-0); color: var(--text-1); transition: box-shadow 120ms ease, border-color 120ms ease; }
select:focus, input:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
</style>
