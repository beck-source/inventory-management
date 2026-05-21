<template>
  <div class="flex min-h-screen bg-sia-mist text-slate-700">
    <SidebarNav :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />

    <div class="flex-1 flex flex-col min-w-0">
      <header class="sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-sia-line">
        <div class="flex items-center gap-3 px-8 h-16">
          <button
            class="lg:hidden p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100"
            @click="toggleSidebar"
            aria-label="Toggle sidebar"
          >
            <Menu :size="20" />
          </button>

          <div class="hidden md:flex items-center gap-2 flex-1 max-w-md">
            <div class="relative w-full">
              <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search inventory, orders…"
                class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 focus:outline-none focus:border-sia-blue focus:bg-white focus:ring-2 focus:ring-sia-blue/10 transition"
              />
            </div>
          </div>

          <div class="flex-1 md:hidden" />

          <button
            class="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition"
            aria-label="Notifications"
          >
            <Bell :size="18" />
          </button>

          <div class="h-6 w-px bg-slate-200 mx-1" />

          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>

      <FilterBar />

      <main class="flex-1 px-8 py-6 overflow-x-hidden">
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
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { Menu, Bell, Search } from 'lucide-vue-next'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import SidebarNav from './components/SidebarNav.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

const SIDEBAR_KEY = 'sia.sidebar.collapsed'

export default {
  name: 'App',
  components: {
    SidebarNav,
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    Menu,
    Bell,
    Search,
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    const stored = localStorage.getItem(SIDEBAR_KEY)
    const sidebarCollapsed = ref(stored === null
      ? (typeof window !== 'undefined' && window.innerWidth < 1024)
      : stored === 'true')

    let userToggled = stored !== null

    const toggleSidebar = () => {
      userToggled = true
      sidebarCollapsed.value = !sidebarCollapsed.value
    }

    watch(sidebarCollapsed, (v) => {
      localStorage.setItem(SIDEBAR_KEY, String(v))
    })

    // Auto-collapse when user resizes down to a smaller viewport, unless they've explicitly
    // toggled in this session. This keeps the icons-only mode useful on tablet/narrow desktop.
    const onResize = () => {
      if (userToggled) return
      sidebarCollapsed.value = window.innerWidth < 1024
    }

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
          if (index !== -1) currentUser.value.tasks.splice(index, 1)
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
          if (index !== -1) apiTasks.value[index] = updatedTask
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(() => {
      loadTasks()
      window.addEventListener('resize', onResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', onResize)
    })

    return {
      t,
      sidebarCollapsed,
      toggleSidebar,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
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
  font-family: 'Sora', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #F5F7FB;
  color: #0A1633;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Page primitives kept compatible with existing views, restyled to Sia palette. */

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0A1633;
  margin-bottom: 0.25rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1.25rem 1.375rem;
  border-radius: 14px;
  border: 1px solid #E2E8F0;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: linear-gradient(90deg, #00B6F0, #DEECFC 60%, #FFEAF0);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 8px 24px -12px rgba(10, 22, 51, 0.15);
  transform: translateY(-1px);
}

.stat-card:hover::before { opacity: 1; }

.stat-label {
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0A1633;
  letter-spacing: -0.025em;
  font-feature-settings: 'tnum';
}

.stat-card.warning .stat-value { color: #ea580c; }
.stat-card.success .stat-value { color: #059669; }
.stat-card.danger  .stat-value { color: #dc2626; }
.stat-card.info    .stat-value { color: #00B6F0; }

.card {
  background: white;
  border-radius: 14px;
  padding: 1.375rem;
  border: 1px solid #E2E8F0;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 2px rgba(10, 22, 51, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid #E2E8F0;
}

.card-title {
  font-size: 1.0625rem;
  font-weight: 700;
  color: #0A1633;
  letter-spacing: -0.015em;
}

.table-container { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; }

thead {
  background: #F8FAFC;
  border-top: 1px solid #E2E8F0;
  border-bottom: 1px solid #E2E8F0;
}

th {
  text-align: left;
  padding: 0.625rem 0.75rem;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.625rem 0.75rem;
  border-top: 1px solid #F1F5F9;
  color: #334155;
  font-size: 0.875rem;
}

tbody tr { transition: background-color 0.15s ease; }
tbody tr:hover { background: #F8FAFC; }

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.badge.success    { background: #d1fae5; color: #065f46; }
.badge.warning    { background: #fed7aa; color: #92400e; }
.badge.danger     { background: #fecaca; color: #991b1b; }
.badge.info       { background: #DEECFC; color: #0a3a5e; }
.badge.increasing { background: #d1fae5; color: #065f46; }
.badge.decreasing { background: #fecaca; color: #991b1b; }
.badge.stable     { background: #e0e7ff; color: #3730a3; }
.badge.high       { background: #fecaca; color: #991b1b; }
.badge.medium     { background: #fed7aa; color: #92400e; }
.badge.low        { background: #DEECFC; color: #0a3a5e; }

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
  border-radius: 10px;
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
