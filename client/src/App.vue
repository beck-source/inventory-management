<template>
  <div class="app-shell" :class="{ 'is-collapsed': collapsed }">
    <AppSidebar
      ref="sidebar"
      :collapsed="collapsed"
      :drawer-open="drawerOpen"
      :theme="theme"
      @toggle-collapse="toggleCollapse"
      @toggle-theme="toggleTheme"
      @close-drawer="drawerOpen = false"
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
    />
    <div v-if="drawerOpen" class="sidebar-backdrop" @click="drawerOpen = false"></div>

    <div class="app-main">
      <!-- Mobile only: brand plus the button that opens the drawer -->
      <header class="app-topbar">
        <button
          ref="menuBtn"
          type="button"
          class="menu-btn"
          :aria-label="t('nav.openMenu')"
          :aria-expanded="drawerOpen"
          @click="drawerOpen = true"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
            <path d="M4 7h16" /><path d="M4 12h16" /><path d="M4 17h16" />
          </svg>
        </button>
        <span class="app-topbar-title">{{ t('nav.companyName') }}</span>
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
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import { useLayout } from './composables/useLayout'
import AppSidebar from './components/AppSidebar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import './styles/tokens.css'

// Matches the 900px drawer breakpoint in the styles below
const DRAWER_QUERY = '(max-width: 900px)'

export default {
  name: 'App',
  components: {
    AppSidebar,
    FilterBar,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const { collapsed, theme, drawerOpen, toggleCollapse, toggleTheme } = useLayout()
    const route = useRoute()
    const sidebar = ref(null)
    const menuBtn = ref(null)
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

    // Drawer behavior: close on route change so the new page is visible
    watch(() => route.path, () => {
      drawerOpen.value = false
    })

    // Lock page scroll behind the open drawer and move focus in/out for keyboard users
    watch(drawerOpen, async (open) => {
      document.body.style.overflow = open ? 'hidden' : ''
      await nextTick()
      if (open) {
        sidebar.value && sidebar.value.focusFirst()
      } else if (menuBtn.value && menuBtn.value.offsetParent !== null) {
        menuBtn.value.focus()
      }
    })

    const onKeydown = (e) => {
      if (e.key === 'Escape' && drawerOpen.value) drawerOpen.value = false
    }

    // Resizing up to desktop while the drawer is open would leave scroll locked, so close it
    let mql = null
    const onBreakpointChange = (e) => {
      if (!e.matches) drawerOpen.value = false
    }

    onMounted(() => {
      loadTasks()
      document.addEventListener('keydown', onKeydown)
      mql = window.matchMedia(DRAWER_QUERY)
      mql.addEventListener('change', onBreakpointChange)
    })

    onBeforeUnmount(() => {
      document.removeEventListener('keydown', onKeydown)
      if (mql) mql.removeEventListener('change', onBreakpointChange)
      document.body.style.overflow = ''
    })

    return {
      t,
      collapsed,
      theme,
      drawerOpen,
      toggleCollapse,
      toggleTheme,
      sidebar,
      menuBtn,
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
  font-size: var(--text-base);
  background: var(--color-bg);
  color: var(--color-text);
  /* Tabular figures keep numeric columns and stat values aligned */
  font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

button,
input,
select,
textarea {
  font-family: inherit;
}

:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* Shell: the sidebar takes its own column, so content is never hidden behind it */
.app-shell {
  display: flex;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  /* min-width: 0 lets wide tables scroll inside their container instead of stretching the page */
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-5);
}

.app-topbar,
.sidebar-backdrop {
  display: none;
}

/* 900px is the drawer breakpoint (custom properties cannot be used in media queries) */
@media (max-width: 900px) {
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgb(5 13 18 / 0.55);
    z-index: var(--z-backdrop);
  }

  .app-topbar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    height: 56px;
    padding: 0 var(--space-4);
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: var(--z-sticky);
  }

  .app-topbar-title {
    font-size: var(--text-lg);
    font-weight: var(--weight-semibold);
  }

  .menu-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 44px;
    height: 44px;
    margin-left: calc(-1 * var(--space-2));
    background: transparent;
    border: 0;
    border-radius: var(--radius-sm);
    color: var(--color-text);
    cursor: pointer;
  }

  .menu-btn:hover {
    background: var(--color-hover);
  }

  .main-content {
    padding: var(--space-4);
    /* Some views (chart grids with fixed min widths) are wider than a phone. Scroll them inside
       the content area so the page itself never gets a horizontal scrollbar. */
    overflow-x: auto;
  }
}

.page-header {
  margin-bottom: var(--space-5);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.015em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

/* Cards: 1px border, no resting shadow */
.stat-card {
  position: relative;
  overflow: hidden;
  background: var(--color-surface);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: border-color 0.15s ease;
}

/* Thin left rule in the card's status color (neutral when it has no status) */
.stat-card::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--stat-rule, var(--color-border-strong));
}

.stat-card:hover {
  border-color: var(--color-border-strong);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 2rem;
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  letter-spacing: -0.02em;
}

.stat-card.warning { --stat-rule: var(--color-warning); }
.stat-card.success { --stat-rule: var(--color-success); }
.stat-card.danger { --stat-rule: var(--color-danger); }
.stat-card.info { --stat-rule: var(--color-info); }

.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger .stat-value { color: var(--color-danger); }
.stat-card.info .stat-value { color: var(--color-info); }

.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-4);
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
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
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
  background: var(--color-surface-muted);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: var(--weight-semibold);
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-surface-muted);
}

/* Badges keep light pastel fills in both themes; dark text on a light fill stays legible */
.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success,
.badge.increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning,
.badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: #fecaca;
  color: #991b1b;
}

.badge.info,
.badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.loading {
  text-align: center;
  padding: var(--space-7);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.error {
  background: var(--color-danger-soft);
  border: 1px solid var(--color-danger);
  color: var(--color-danger);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
