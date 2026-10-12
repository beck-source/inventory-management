<template>
  <div class="app" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <Sidebar
      :collapsed="sidebarCollapsed"
      :mobile-open="mobileSidebarOpen"
      @toggle-collapse="sidebarCollapsed = !sidebarCollapsed"
      @close-mobile="mobileSidebarOpen = false"
    />

    <div class="app-body">
      <TopHeader
        @open-mobile-sidebar="mobileSidebarOpen = true"
        @show-profile-details="showProfileDetails = true"
        @show-tasks="showTasks = true"
      />
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
import Sidebar from './components/Sidebar.vue'
import TopHeader from './components/TopHeader.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    TopHeader,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])
    const sidebarCollapsed = ref(false)
    const mobileSidebarOpen = ref(false)

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
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)
        if (isMockTask) {
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)
        if (mockTask) {
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
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
      toggleTask,
      sidebarCollapsed,
      mobileSidebarOpen
    }
  }
}
</script>

<style>
/* ============================================================
   DESIGN TOKENS — Indigo/Violet SaaS palette
   ============================================================ */
:root {
  /* Surfaces & background */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-alt: #f1f5f9;
  --color-surface-sunken: #f8fafc;

  /* Borders */
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-border-subtle: #f1f5f9;

  /* Text */
  --color-text-primary: #0f172a;
  --color-text-secondary: #334155;
  --color-text-muted: #64748b;
  --color-text-faint: #94a3b8;

  /* Brand — indigo */
  --color-primary: #6366f1;
  --color-primary-hover: #4f46e5;
  --color-primary-active: #4338ca;
  --color-primary-soft: #eef2ff;
  --color-primary-soft-strong: #e0e7ff;
  --color-primary-text: #4338ca;

  /* Accent — violet */
  --color-accent: #8b5cf6;
  --color-accent-soft: #f5f3ff;
  --color-accent-text: #6d28d9;

  /* Status */
  --color-success: #10b981;
  --color-success-soft: #ecfdf5;
  --color-success-text: #047857;

  --color-warning: #f59e0b;
  --color-warning-soft: #fffbeb;
  --color-warning-text: #b45309;

  --color-error: #ef4444;
  --color-error-soft: #fef2f2;
  --color-error-text: #b91c1c;

  --color-info: #3b82f6;
  --color-info-soft: #eff6ff;
  --color-info-text: #1d4ed8;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.06), 0 2px 4px rgba(15, 23, 42, 0.04);
  --shadow-lg: 0 12px 24px rgba(15, 23, 42, 0.08), 0 4px 8px rgba(15, 23, 42, 0.04);
  --shadow-focus: 0 0 0 3px rgba(99, 102, 241, 0.18);

  /* Layout */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 72px;
  --header-height: 64px;
}

/* ============================================================
   RESET & BASE
   ============================================================ */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-bg);
  color: var(--color-text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ============================================================
   LAYOUT
   ============================================================ */
.app {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}

.app-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  margin-left: var(--sidebar-width);
  transition: margin-left 0.25s ease;
}

.app.sidebar-collapsed .app-body {
  margin-left: var(--sidebar-width-collapsed);
}

.main-content {
  flex: 1;
  padding: var(--space-8) var(--space-8) var(--space-10);
  max-width: 1600px;
  width: 100%;
}

/* ============================================================
   PAGE HEADER
   ============================================================ */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: 0.9375rem;
  line-height: 1.5;
}

/* ============================================================
   STATS GRID
   ============================================================ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.025em;
  line-height: 1.1;
}

.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger .stat-value { color: var(--color-error); }
.stat-card.info .stat-value { color: var(--color-info); }

/* ============================================================
   CARD
   ============================================================ */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
  margin: 0;
}

/* ============================================================
   TABLE
   ============================================================ */
.table-container {
  overflow-x: auto;
  border-radius: var(--radius-md);
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--color-surface-alt);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: 0.6875rem 0.875rem;
  font-weight: 600;
  color: var(--color-text-muted);
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

td {
  padding: 0.75rem 0.875rem;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-surface-sunken);
}

tbody tr td strong {
  color: var(--color-text-primary);
  font-weight: 600;
}

/* ============================================================
   BADGES
   ============================================================ */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.1875rem 0.5625rem;
  border-radius: var(--radius-full);
  font-size: 0.6875rem;
  font-weight: 600;
  text-transform: capitalize;
  letter-spacing: 0.01em;
  line-height: 1.4;
  border: 1px solid transparent;
}

.badge.success {
  background: var(--color-success-soft);
  color: var(--color-success-text);
  border-color: #a7f3d0;
}

.badge.warning {
  background: var(--color-warning-soft);
  color: var(--color-warning-text);
  border-color: #fde68a;
}

.badge.danger {
  background: var(--color-error-soft);
  color: var(--color-error-text);
  border-color: #fecaca;
}

.badge.info {
  background: var(--color-info-soft);
  color: var(--color-info-text);
  border-color: #bfdbfe;
}

.badge.increasing {
  background: var(--color-success-soft);
  color: var(--color-success-text);
  border-color: #a7f3d0;
}

.badge.decreasing {
  background: var(--color-error-soft);
  color: var(--color-error-text);
  border-color: #fecaca;
}

.badge.stable {
  background: var(--color-primary-soft);
  color: var(--color-primary-text);
  border-color: #c7d2fe;
}

.badge.high {
  background: var(--color-error-soft);
  color: var(--color-error-text);
  border-color: #fecaca;
}

.badge.medium {
  background: var(--color-warning-soft);
  color: var(--color-warning-text);
  border-color: #fde68a;
}

.badge.low {
  background: var(--color-info-soft);
  color: var(--color-info-text);
  border-color: #bfdbfe;
}

/* ============================================================
   LOADING / ERROR
   ============================================================ */
.loading {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-muted);
  font-size: 0.9375rem;
}

.error {
  background: var(--color-error-soft);
  border: 1px solid #fecaca;
  color: var(--color-error-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: 0.9375rem;
}

/* ============================================================
   GLOBAL FORM ELEMENTS
   ============================================================ */
input,
select,
textarea {
  font-family: inherit;
}

input:focus-visible,
select:focus-visible,
textarea:focus-visible {
  outline: none;
}

/* ============================================================
   RESPONSIVE
   ============================================================ */
@media (max-width: 1024px) {
  .main-content {
    padding: var(--space-6);
  }
}

@media (max-width: 768px) {
  .app-body {
    margin-left: 0 !important;
  }

  .main-content {
    padding: var(--space-4);
  }
}
</style>
