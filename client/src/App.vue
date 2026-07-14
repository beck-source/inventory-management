<template>
  <div class="app">
    <!-- Mobile top bar (hamburger + brand only) -->
    <header class="mobile-topbar">
      <button class="hamburger-btn" @click="toggleDrawer" aria-label="Toggle navigation">
        <svg width="22" height="22" viewBox="0 0 20 20" fill="none">
          <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"/>
        </svg>
      </button>
      <div class="logo logo-mobile">
        <h1>{{ t('nav.companyName') }}</h1>
      </div>
    </header>

    <!-- Mobile drawer backdrop -->
    <div v-if="isDrawerOpen" class="drawer-backdrop" @click="closeDrawer"></div>

    <aside class="sidebar" :class="{ collapsed: isCollapsed, 'drawer-open': isDrawerOpen }">
      <div class="logo">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="subtitle">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :title="t('nav.overview')" @click="closeDrawer">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 10L10 3L17 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5 8.5V16C5 16.5523 5.44772 17 6 17H8.5V13C8.5 12.4477 8.94772 12 9.5 12H10.5C11.0523 12 11.5 12.4477 11.5 13V17H14C14.5523 17 15 16.5523 15 16V8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>

        <router-link to="/inventory" class="nav-item" :title="t('nav.inventory')" @click="closeDrawer">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 6L10 3L17 6L10 9L3 6Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M3 6V14L10 17M17 6V14L10 17M10 9V17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link to="/orders" class="nav-item" :title="t('nav.orders')" @click="closeDrawer">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M4 3H16V17L13 15L10 17L7 15L4 17V3Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M7 7H13M7 10.5H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.orders') }}</span>
        </router-link>

        <router-link to="/demand" class="nav-item" :title="t('nav.demandForecast')" @click="closeDrawer">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 14L7.5 9L10.5 12L17 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12 5H17V10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 17H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link to="/restocking" class="nav-item" :title="t('nav.restocking')" @click="closeDrawer">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 3V17M10 3L6 7M10 3L14 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3 17H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.restocking') }}</span>
        </router-link>

        <router-link to="/spending" class="nav-item" :title="t('nav.finance')" @click="closeDrawer">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 2V18M14 5.5C14 4.11929 12.2091 3 10 3C7.79086 3 6 4.11929 6 5.5C6 6.88071 7.79086 8 10 8C12.2091 8 14 9.11929 14 10.5C14 11.8807 12.2091 13 10 13C7.79086 13 6 11.8807 6 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.finance') }}</span>
        </router-link>

        <router-link to="/backlog" class="nav-item" :title="t('nav.backlog')" @click="closeDrawer">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3 5H17M3 10H17M3 15H12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.backlog') }}</span>
        </router-link>

        <router-link to="/reports" class="nav-item" :title="t('nav.reports')" @click="closeDrawer">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M6 3H12L16 7V17H4V3H6Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M7 10H13M7 13H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.reports') }}</span>
        </router-link>
      </nav>

      <button class="collapse-toggle" @click="toggleCollapsed" :title="isCollapsed ? 'Expand' : 'Collapse'">
        <svg class="collapse-icon" :class="{ flipped: isCollapsed }" width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M11 4L6 9L11 14" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="nav-label">Collapse</span>
      </button>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content-column">
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
import { useLayout } from './composables/useLayout'
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
    const { isCollapsed, isDrawerOpen, toggleCollapsed, closeDrawer, toggleDrawer } = useLayout()
    const route = useRoute()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Close mobile drawer whenever the route changes
    watch(() => route.path, () => {
      closeDrawer()
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
      isCollapsed,
      isDrawerOpen,
      toggleCollapsed,
      closeDrawer,
      toggleDrawer,
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
  /* spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-7: 3rem;

  /* color roles */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-border-hover: #cbd5e1;
  --color-text: #0f172a;
  --color-text-secondary: #334155;
  --color-text-muted: #64748b;

  --color-primary: #2563eb;
  --color-primary-dark: #1e40af;
  --color-primary-bg: #eff6ff;

  --color-success: #059669;
  --color-success-bg: #d1fae5;
  --color-success-text: #065f46;

  --color-warning: #ea580c;
  --color-warning-bg: #fed7aa;
  --color-warning-text: #92400e;

  --color-danger: #dc2626;
  --color-danger-bg: #fecaca;
  --color-danger-text: #991b1b;

  --color-info: #2563eb;
  --color-info-bg: #dbeafe;
  --color-info-text: #1e40af;

  /* radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;

  /* shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);

  /* sidebar */
  --sidebar-width-expanded: 240px;
  --sidebar-width-collapsed: 72px;
  --sidebar-breakpoint: 768px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-bg);
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}

/* ---------- Sidebar ---------- */

.sidebar {
  display: flex;
  flex-direction: column;
  width: var(--sidebar-width-expanded);
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  padding: var(--space-5) var(--space-4);
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  transition: width 0.2s ease;
  z-index: 100;
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar .logo {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  padding: 0 var(--space-2) var(--space-5);
  margin-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.sidebar.collapsed .logo {
  align-items: center;
  text-align: center;
}

.logo h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar.collapsed .logo h1 {
  font-size: 0.75rem;
}

.subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar.collapsed .subtitle {
  display: none;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: var(--radius-md);
  transition: all 0.15s ease;
  white-space: nowrap;
}

.nav-item:hover {
  color: var(--color-text);
  background: var(--color-bg);
}

.nav-item.router-link-active {
  color: var(--color-primary);
  background: var(--color-primary-bg);
}

.nav-icon {
  flex-shrink: 0;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: var(--space-3);
}

.sidebar.collapsed .nav-label {
  display: none;
}

.collapse-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  margin-top: var(--space-2);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  font-family: inherit;
  transition: all 0.15s ease;
}

.collapse-toggle:hover {
  color: var(--color-text);
  background: var(--color-bg);
  border-color: var(--color-border-hover);
}

.sidebar.collapsed .collapse-toggle {
  justify-content: center;
}

.collapse-icon {
  flex-shrink: 0;
  transition: transform 0.2s ease;
}

.collapse-icon.flipped {
  transform: rotate(180deg);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.sidebar.collapsed .sidebar-footer :deep(.profile-name),
.sidebar.collapsed .sidebar-footer :deep(.language-switcher) {
  display: none;
}

/* ---------- Mobile top bar / drawer ---------- */

.mobile-topbar {
  display: none;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-4);
  height: 56px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 110;
}

.hamburger-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  border: none;
  color: var(--color-text);
  cursor: pointer;
  padding: var(--space-2);
}

.logo-mobile h1 {
  font-size: 1.05rem;
}

.drawer-backdrop {
  display: none;
}

/* ---------- Content column ---------- */

.content-column {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.main-content {
  flex: 1;
  width: 100%;
  padding: var(--space-5) var(--space-6);
}

@media (max-width: 768px) {
  .app {
    flex-direction: column;
  }

  .mobile-topbar {
    display: flex;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: var(--sidebar-width-expanded);
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    z-index: 200;
  }

  .sidebar.drawer-open {
    transform: translateX(0);
  }

  .sidebar.collapsed {
    width: var(--sidebar-width-expanded);
  }

  .sidebar.collapsed .nav-label,
  .sidebar.collapsed .subtitle {
    display: block;
  }

  .collapse-toggle {
    display: none;
  }

  .drawer-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: 150;
  }

  .main-content {
    padding: var(--space-4);
  }
}

.page-header {
  margin-bottom: var(--space-5);
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text);
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
  margin-bottom: var(--space-5);
}

.stat-card {
  background: var(--color-surface);
  padding: 1.25rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-border-hover);
  box-shadow: var(--shadow-md);
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
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: 1.25rem;
  transition: box-shadow 0.2s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
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
  padding: 0.313rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.badge.warning {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.badge.danger {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

.badge.info {
  background: var(--color-info-bg);
  color: var(--color-info-text);
}

.badge.increasing {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.badge.decreasing {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
}

.badge.medium {
  background: var(--color-warning-bg);
  color: var(--color-warning-text);
}

.badge.low {
  background: var(--color-info-bg);
  color: var(--color-info-text);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid var(--color-danger-bg);
  color: var(--color-danger-text);
  padding: 1rem;
  border-radius: var(--radius-md);
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
