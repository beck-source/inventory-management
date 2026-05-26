<template>
  <div :class="['app-shell', { 'sidebar-collapsed': collapsed }]">
    <!-- LEFT SIDEBAR -->
    <aside :class="['sidebar', { collapsed }]">
      <div class="sidebar-header">
        <div class="sidebar-brand" v-show="!collapsed">
          <div class="logo-name">{{ t('nav.companyName') }}</div>
          <div class="logo-subtitle">{{ t('nav.subtitle') }}</div>
        </div>
        <button class="sidebar-toggle" @click="toggleSidebar" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
          <span class="toggle-icon">{{ collapsed ? '›' : '‹' }}</span>
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="['nav-item', { active: $route.path === item.path }]"
          :title="collapsed ? t(item.labelKey) : ''"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label" v-show="!collapsed">{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>

      <div class="sidebar-spacer"></div>

      <div :class="['sidebar-footer', { collapsed }]">
        <LanguageSwitcher v-show="!collapsed" />
        <button
          class="dark-mode-toggle"
          @click="toggleDark"
          :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        >{{ isDark ? '☀' : '☾' }}</button>
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <!-- RIGHT CONTENT -->
    <div class="content-area">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- MODALS (unchanged) -->
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
import { useDarkMode } from './composables/useDarkMode'

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
    const { isDark, toggleDark } = useDarkMode()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Collapsed state — auto-collapse on viewports narrower than 1024px
    const collapsed = ref(false)

    const toggleSidebar = () => {
      collapsed.value = !collapsed.value
    }

    // Auto-collapse on small screens and keep in sync on resize
    const mq = window.matchMedia('(max-width: 1024px)')
    const handleMq = (e) => { collapsed.value = e.matches }
    collapsed.value = mq.matches

    onUnmounted(() => mq.removeEventListener('change', handleMq))
    // register listener — done after collapsed.value is set so no double-trigger on mount
    mq.addEventListener('change', handleMq)

    const navItems = [
      { path: '/',            labelKey: 'nav.overview',       icon: '◈' },
      { path: '/inventory',   labelKey: 'nav.inventory',      icon: '▤' },
      { path: '/orders',      labelKey: 'nav.orders',         icon: '◎' },
      { path: '/spending',    labelKey: 'nav.finance',        icon: '◇' },
      { path: '/demand',      labelKey: 'nav.demandForecast', icon: '↗' },
      { path: '/reports',     labelKey: 'nav.reports',        icon: '▦' },
      { path: '/restocking',  labelKey: 'nav.restocking',     icon: '↺' },
    ]

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
      navItems,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      collapsed,
      toggleSidebar,
      isDark,
      toggleDark,
    }
  }
}
</script>

<style>
:root {
  --color-bg: #f8fafc;
  --color-sidebar-bg: #ffffff;
  --color-sidebar-border: #e2e8f0;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-text-primary: #0f172a;
  --color-text-muted: #64748b;
  --color-accent: #2563eb;
  --color-accent-hover: #1d4ed8;
  --color-accent-subtle: rgba(37, 99, 235, 0.08);
  --color-nav-hover: rgba(37, 99, 235, 0.05);
  --sidebar-width: 240px;
  --sidebar-width-collapsed: 56px;
  --sidebar-transition: 0.22s ease;
  --content-padding: 1.5rem 2rem;
  --border-radius: 10px;
}

[data-theme="dark"] {
  --color-bg: #0f172a;
  --color-sidebar-bg: #1e293b;
  --color-sidebar-border: #334155;
  --color-surface: #1e293b;
  --color-border: #334155;
  --color-text-primary: #f1f5f9;
  --color-text-muted: #94a3b8;
  --color-accent: #60a5fa;
  --color-accent-hover: #93c5fd;
  --color-accent-subtle: rgba(96, 165, 250, 0.12);
  --color-nav-hover: rgba(96, 165, 250, 0.08);
}

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
  transition: background-color 0.2s ease, color 0.2s ease;
}

.page-header {
  margin-bottom: 1.5rem;
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
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--color-surface);
  padding: 1.25rem;
  border-radius: var(--border-radius);
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
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
  color: var(--color-accent);
}

.card {
  background: var(--color-surface);
  border-radius: var(--border-radius);
  padding: 1.25rem;
  border: 1px solid var(--color-border);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
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
  background: var(--color-bg);
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
  color: var(--color-text-muted);
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

<style scoped>
.app-shell {
  display: grid;
  grid-template-columns: auto 1fr;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  background: var(--color-sidebar-bg);
  border-right: 1px solid var(--color-sidebar-border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;         /* clips labels during collapse animation */
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  transition: width var(--sidebar-transition), min-width var(--sidebar-transition);
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
  min-width: var(--sidebar-width-collapsed);
}

.sidebar-header {
  padding: 0.875rem 0.75rem;
  border-bottom: 1px solid var(--color-sidebar-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  min-height: 56px;
}

.sidebar-brand {
  overflow: hidden;
  flex: 1;
  min-width: 0;
}

.logo-name {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.logo-subtitle {
  font-size: 0.6875rem;
  color: var(--color-text-muted);
  margin-top: 3px;
}

.sidebar-toggle {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  padding: 0;
}

.sidebar-toggle:hover {
  background: var(--color-nav-hover);
  color: var(--color-text-primary);
  border-color: var(--color-accent);
}

.toggle-icon {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1;
  /* shift slightly right when showing › to keep optical center */
  margin-left: 1px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--color-nav-hover);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-weight: 600;
}

.nav-icon {
  font-size: 0.9375rem;
  width: 1.125rem;
  text-align: center;
  flex-shrink: 0;
  opacity: 0.8;
}

.nav-item.active .nav-icon {
  opacity: 1;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.5rem;
}

.sidebar.collapsed .nav-icon {
  width: auto;
  font-size: 1.125rem;
  opacity: 0.7;
}

.sidebar.collapsed .nav-item.active .nav-icon {
  opacity: 1;
}

.sidebar-spacer {
  flex: 1;
}

.sidebar-footer {
  padding: 0.875rem 0.75rem;
  border-top: 1px solid var(--color-sidebar-border);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sidebar-footer.collapsed {
  justify-content: center;
  padding: 0.875rem 0;
}

.dark-mode-toggle {
  background: none;
  border: 1px solid var(--color-sidebar-border);
  border-radius: 6px;
  padding: 0.375rem 0.5rem;
  cursor: pointer;
  font-size: 1rem;
  color: var(--color-text-muted);
  transition: all 0.15s ease;
  line-height: 1;
  flex-shrink: 0;
}
.dark-mode-toggle:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.content-area {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--content-padding);
  background: var(--color-bg);
}
</style>
