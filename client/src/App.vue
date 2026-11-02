<template>
  <div class="app">
    <Sidebar>
      <template #brand>
        <div class="brand-mark">
          <div class="brand-name">{{ t('nav.companyName') }}</div>
          <div class="brand-sub">{{ t('nav.subtitle') }}</div>
        </div>
      </template>

      <template #nav>
        <NavItem to="/" :label="t('nav.overview')" />
        <NavItem to="/inventory" :label="t('nav.inventory')" />
        <NavItem to="/orders" :label="t('nav.orders')" />
        <NavItem to="/spending" :label="t('nav.finance')" />
        <NavItem to="/demand" :label="t('nav.demandForecast')" />
        <NavItem to="/reports" label="Reports" />
      </template>

      <template #footer>
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </template>
    </Sidebar>

    <main class="main-content">
      <router-view />
    </main>

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
import Sidebar from './components/ui/Sidebar.vue'
import NavItem from './components/ui/NavItem.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    NavItem,
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
      toggleTask
    }
  }
}
</script>

<style>
:root {
  /* Color tokens */
  --surface-bg: #f8fafc;
  --surface-card: #ffffff;
  --surface-muted: #f1f5f9;
  --surface-nav: #0f172a;
  --ink-primary: #0f172a;
  --ink-secondary: #334155;
  --ink-muted: #64748b;
  --ink-inverse: #f8fafc;
  --line: #e2e8f0;
  --line-strong: #cbd5e1;
  --accent: #3b82f6;
  --accent-2: #8b5cf6;
  --success: #10b981;
  --warn: #f59e0b;
  --danger: #ef4444;

  /* Spacing scale */
  --sp-1: 4px;
  --sp-2: 8px;
  --sp-3: 12px;
  --sp-4: 16px;
  --sp-5: 20px;
  --sp-6: 24px;
  --sp-7: 32px;
  --sp-8: 40px;
  --sp-9: 48px;
  --sp-10: 64px;

  /* Radius */
  --r-sm: 6px;
  --r-md: 10px;
  --r-lg: 14px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--surface-bg);
  color: var(--ink-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-size: 14px;
  line-height: 1.5;
}

.app {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  padding: 32px 40px 48px;
  min-width: 0;
}

/* Brand mark */
.brand-mark {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.brand-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-inverse);
  letter-spacing: -0.01em;
}

.brand-sub {
  font-size: 11px;
  color: var(--ink-muted);
  font-weight: 400;
}

/* Global table styles */
table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-bg);
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

th {
  text-align: left;
  padding: 8px 12px;
  font-weight: 600;
  color: var(--ink-muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

td {
  padding: 12px 12px;
  border-top: 1px solid var(--surface-muted);
  color: var(--ink-secondary);
  font-size: 13px;
  height: 44px;
}

tbody tr {
  transition: background-color 0.1s ease;
}

tbody tr:hover {
  background: var(--surface-muted);
}

/* Loading / error global */
.loading {
  text-align: center;
  padding: 48px;
  color: var(--ink-muted);
  font-size: 14px;
}

.error {
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: var(--danger);
  padding: 16px;
  border-radius: var(--r-md);
  margin: 16px 0;
  font-size: 14px;
}

/* Table container */
.table-container {
  overflow-x: auto;
}
</style>
