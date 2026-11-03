<template>
  <div class="app-shell">
    <AppSidebar
      :brand-name="t('nav.companyName')"
      :brand-tagline="t('nav.subtitle')"
      :items="navItems"
    />

    <div class="app-main">
      <AppTopbar :title="pageTitle">
        <template #actions>
          <LanguageSwitcher />
        </template>
        <template #account>
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </template>
      </AppTopbar>

      <FilterBar />

      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- Modals stay at the shell root so they layer above the sidebar and top bar (--z-modal). -->
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
import AppTopbar from './components/AppTopbar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    AppTopbar,
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

    // One entry per route. Computed so labels follow the active locale.
    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: 'dashboard' },
      { to: '/inventory', label: t('nav.inventory'), icon: 'box' },
      { to: '/orders', label: t('nav.orders'), icon: 'cart' },
      { to: '/spending', label: t('nav.finance'), icon: 'dollar' },
      { to: '/demand', label: t('nav.demandForecast'), icon: 'trending' },
      { to: '/reports', label: t('nav.reports'), icon: 'file' }
    ])

    // Top bar title follows the active route so it always matches the sidebar label.
    // Routes are flat, so an exact path match is enough (and avoids "/" matching everything).
    const pageTitle = computed(() => {
      const match = navItems.value.find(item => item.to === route.path)
      return match ? match.label : ''
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
      navItems,
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
/*
 * Global styles. Design tokens (colors, spacing, type, radii, z-index) come from
 * styles/tokens.css, which is imported first in main.js. Class names below are
 * relied on by the views and modals, so keep them stable.
 */

/* Legacy reset: views were written assuming zero default margins/padding. */
* {
  margin: 0;
  padding: 0;
}

/* ---------- Shell layout ---------- */
.app-shell {
  display: flex;
  min-height: 100vh;
  background: var(--color-bg);
}

.app-main {
  flex: 1;
  /* Without min-width: 0 a wide table would stretch this flex child and push the whole page sideways. */
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-8) var(--content-padding) var(--space-12);
}

@media (max-width: 1023px) {
  .main-content {
    padding: var(--space-4) var(--space-4) var(--space-10);
  }
}

/* ---------- Page header ---------- */
.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: var(--weight-semibold);
  line-height: var(--leading-tight);
  letter-spacing: -0.01em;
  color: var(--color-text);
}

.page-header p {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

/* ---------- KPI tiles ---------- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
}

.stat-value {
  margin-top: var(--space-2);
  font-size: var(--text-2xl);
  font-weight: var(--weight-semibold);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

/* Status colors are reserved for tiles that really are alerts. */
.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger .stat-value { color: var(--color-danger); }
.stat-card.info .stat-value { color: var(--color-info); }

/* ---------- Cards ---------- */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-xs);
  margin-bottom: var(--space-6);
}

.card:last-child {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

@media (max-width: 639px) {
  .card { padding: var(--space-4); }
}

/* ---------- Tables ---------- */
.table-container {
  overflow-x: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

/* Inside a card the card's own border frames the table, so don't double up. */
.card .table-container {
  border: 0;
  border-radius: 0;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-base);
}

thead {
  background: var(--color-surface-muted);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-subtle);
  white-space: nowrap;
  border-bottom: 1px solid var(--color-border);
}

td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
  font-size: var(--text-base);
  font-variant-numeric: tabular-nums;
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr {
  transition: background-color var(--duration-fast) var(--ease);
}

tbody tr:hover {
  background: var(--color-surface-hover);
}

/* Right-aligned numeric columns: add class "num" to both th and td. */
th.num,
td.num {
  text-align: right;
}

/* ---------- Badges ---------- */
/* Every modifier maps to one of four intents plus neutral, so old class names keep working. */
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  height: 22px;
  padding: 0 var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  text-transform: capitalize;
  white-space: nowrap;
  background: var(--color-surface-muted);
  color: var(--color-text-muted);
}

.badge.success,
.badge.increasing {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.badge.info,
.badge.low {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.badge.stable {
  background: var(--color-accent-soft);
  color: var(--color-accent-text);
}

/* ---------- Buttons ---------- */
/* Base is shared by every variant so a bare .btn-secondary (as the modals use) works without .btn. */
.btn,
.btn-primary,
.btn-secondary,
.btn-ghost,
.btn-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-4);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  white-space: nowrap;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease), border-color var(--duration-fast) var(--ease), color var(--duration-fast) var(--ease);
}

.btn-primary {
  background: var(--color-accent);
  color: var(--color-on-accent);
}
.btn-primary:hover:not(:disabled) { background: var(--color-accent-hover); }

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text);
  border-color: var(--color-border-strong);
}
.btn-secondary:hover:not(:disabled) { background: var(--color-surface-hover); }

.btn-ghost {
  background: transparent;
  color: var(--color-text-muted);
}
.btn-ghost:hover:not(:disabled) {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.btn-danger {
  background: var(--color-danger);
  /* Dark theme lightens --color-danger, so on-accent (white) text would be low contrast; use the canvas color. */
  color: var(--color-bg);
}
.btn-danger:hover:not(:disabled) { filter: brightness(0.92); }

.btn:disabled,
.btn-primary:disabled,
.btn-secondary:disabled,
.btn-ghost:disabled,
.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Square 36px icon-only button (close, delete, etc.). */
.icon-btn,
.close-button {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease), color var(--duration-fast) var(--ease);
}
.icon-btn:hover,
.close-button:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

/* The global :focus-visible rule rounds to --radius-sm; keep buttons at --radius-md. */
.btn:focus-visible,
.btn-primary:focus-visible,
.btn-secondary:focus-visible,
.btn-ghost:focus-visible,
.btn-danger:focus-visible,
.icon-btn:focus-visible,
.close-button:focus-visible {
  border-radius: var(--radius-md);
}

/* ---------- Form controls (opt-in via class) ---------- */
.input,
select.input,
textarea.input {
  height: 36px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  font: inherit;
  font-size: var(--text-base);
  transition: border-color var(--duration-fast) var(--ease), box-shadow var(--duration-fast) var(--ease);
}
textarea.input {
  height: auto;
  padding: var(--space-2) var(--space-3);
}
.input::placeholder { color: var(--color-text-subtle); }
.input:focus,
.input:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
  border-radius: var(--radius-md);
}

.field-label {
  display: block;
  margin-bottom: var(--space-1);
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text-muted);
}

/* ---------- Modals (shared shell for the *Modal.vue components) ---------- */
/* --z-modal sits above --z-sidebar and --z-backdrop, so dialogs cover the sidebar and drawer. */
.modal-overlay {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: var(--space-4);
  background: var(--overlay);
  z-index: var(--z-modal);
}

.modal-container {
  width: 100%;
  max-width: 560px;
  max-height: calc(100vh - var(--space-8));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.modal-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-semibold);
  color: var(--color-text);
}

.modal-body {
  padding: var(--space-6);
  overflow-y: auto;
  min-height: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

/* ---------- States ---------- */
.loading,
.empty-state {
  text-align: center;
  padding: var(--space-12) var(--space-6);
  color: var(--color-text-subtle);
  font-size: var(--text-base);
}

.error {
  background: var(--color-danger-soft);
  border: 1px solid color-mix(in srgb, var(--color-danger) 30%, transparent);
  color: var(--color-danger);
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
