<template>
  <div class="app-shell">
    <AppSidebar
      :items="navItems"
      :brand="t('nav.companyName')"
      :subtitle="t('nav.subtitle')"
      :open="mobileMenuOpen"
      @close="closeMobileMenu"
    >
      <template #footer="{ collapsed }">
        <ProfileMenu
          :compact="collapsed"
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </template>
    </AppSidebar>

    <div class="app-main">
      <header class="app-topbar">
        <button
          ref="menuButton"
          type="button"
          class="app-menu-btn"
          :aria-label="t('nav.openMenu')"
          :title="t('nav.openMenu')"
          aria-controls="app-sidebar"
          :aria-expanded="mobileMenuOpen ? 'true' : 'false'"
          @click="mobileMenuOpen = !mobileMenuOpen"
        >
          <svg
            viewBox="0 0 24 24"
            width="22"
            height="22"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            aria-hidden="true"
          >
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <h1 class="app-topbar-title">{{ pageTitle }}</h1>
        <div class="app-topbar-actions">
          <LanguageSwitcher />
        </div>
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
import { ref, onMounted, computed, watch } from 'vue'
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
    const mobileMenuOpen = ref(false)
    const menuButton = ref(null)

    // Sidebar items, in the original top-nav order. Icons are inline SVG path data
    // (24x24 viewBox, stroked by AppSidebar) so no icon dependency is needed.
    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: 'M4 4h6v7H4zM14 4h6v4h-6zM14 12h6v8h-6zM4 15h6v5H4z' },
      { to: '/inventory', label: t('nav.inventory'), icon: 'M21 8l-9-5-9 5v8l9 5 9-5zM3 8l9 5 9-5M12 13v8' },
      { to: '/orders', label: t('nav.orders'), icon: 'M9 4h6v3H9zM9 5.5H5.5A1.5 1.5 0 0 0 4 7v12.5A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5V7a1.5 1.5 0 0 0-1.5-1.5H15M8 12h8M8 16h5' },
      { to: '/spending', label: t('nav.finance'), icon: 'M4 4v16h16M8 16v-4M12 16V8M16 16v-6' },
      { to: '/demand', label: t('nav.demandForecast'), icon: 'M3 17l6-6 4 4 8-8M15 7h6v6' },
      { to: '/restocking', label: t('nav.restocking'), icon: 'M20 11a8 8 0 0 0-14.9-3M4 5v3.5h3.5M4 13a8 8 0 0 0 14.9 3M20 19v-3.5h-3.5' },
      { to: '/reports', label: t('nav.reports'), icon: 'M7 3h7l5 5v13H7zM14 3v5h5M10 13h6M10 17h6' }
    ])

    // Top bar title follows the active route's nav label
    const pageTitle = computed(() => {
      const active = navItems.value.find(item => item.to === route.path)
      return active ? active.label : t('nav.companyName')
    })

    const closeMobileMenu = (options = {}) => {
      mobileMenuOpen.value = false
      // Escape / scrim click: hand focus back to the control that opened the drawer
      if (options && options.restoreFocus && menuButton.value) {
        menuButton.value.focus()
      }
    }

    // Any navigation (including browser back/forward) closes the drawer
    watch(() => route.path, () => {
      mobileMenuOpen.value = false
    })
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
      navItems,
      pageTitle,
      mobileMenuOpen,
      menuButton,
      closeMobileMenu,
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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-app);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---- Top bar controls (layout classes live in styles/tokens.css) ---- */
.app-topbar-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.app-menu-btn {
  display: none; /* only shown below 720px, where the sidebar becomes a drawer */
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  margin-left: calc(var(--space-2) * -1);
  background: transparent;
  border: 0;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.app-menu-btn:hover {
  background: var(--bg-muted);
  color: var(--text);
}

@media (max-width: 719px) {
  .app-menu-btn {
    display: inline-flex;
  }

  .app-topbar {
    padding: 0 var(--space-4);
  }
}

/* ---- Content column ---- */
.main-content {
  flex: 1;
  max-width: var(--content-max-width);
  width: 100%;
  margin: 0 auto;
  padding: var(--space-5) var(--space-6);
}

@media (max-width: 719px) {
  .main-content {
    padding: var(--space-4);
  }
}

.page-header {
  margin-bottom: var(--space-5);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 17.5rem), 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-5);
}

.stat-card {
  background: var(--bg-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  border-color: var(--border-strong, #cbd5e1);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.02em;
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
  color: var(--accent);
}

.card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.01em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--bg-app);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 600;
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--bg-muted);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--bg-app);
}

/* Status colours are intentionally unchanged from the previous design */
.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
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
  padding: var(--space-8);
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
}
</style>
