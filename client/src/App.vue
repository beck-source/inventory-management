<template>
  <div class="app">
    <!-- Sidebar: sticky vertical nav replacing the old horizontal top-nav -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <h1>{{ t('nav.companyName') }}</h1>
        <span class="subtitle">{{ t('nav.subtitle') }}</span>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/" :class="{ active: $route.path === '/' }">
          <!-- Grid / Overview icon -->
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
          </svg>
          <span>{{ t('nav.overview') }}</span>
        </router-link>

        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
          <!-- Box / package icon -->
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M21 16V8a2 2 0 0 0-1-1.73L13 2.27a2 2 0 0 0-2 0L4 6.27A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
          <span>{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
          <!-- Clipboard / orders icon -->
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/>
          </svg>
          <span>{{ t('nav.orders') }}</span>
        </router-link>

        <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
          <!-- Bar-chart / finance icon -->
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
          </svg>
          <span>{{ t('nav.finance') }}</span>
        </router-link>

        <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
          <!-- Trending-up icon -->
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>
          </svg>
          <span>{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
          <!-- Refresh / restock icon -->
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
          </svg>
          <span>{{ t('nav.restocking') }}</span>
        </router-link>

        <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
          <!-- Document / reports icon -->
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
          </svg>
          <span>Reports</span>
        </router-link>
      </nav>
    </aside>

    <!-- App body: topbar + filter bar + page content -->
    <div class="app-body">
      <header class="topbar">
        <!-- Controls group pushed to the right via margin-left:auto -->
        <div class="topbar-controls">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
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
   DESIGN TOKENS
   All hardcoded hex values and spacing throughout this file
   reference these variables so a single edit propagates everywhere.
   ============================================================ */
:root {
  /* Neutrals (slate) */
  --bg-app: #f8fafc;
  --bg-surface: #ffffff;
  --bg-subtle: #f1f5f9;
  --bg-muted: #f8fafc;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --border-faint: #f1f5f9;

  /* Text */
  --text-strong: #0f172a;
  --text-body: #334155;
  --text-muted: #64748b;
  --text-subtle: #475569;

  /* Brand / primary — INDIGO/VIOLET (replaces old blue #2563eb) */
  --primary: #4f46e5;
  --primary-hover: #4338ca;
  --primary-soft: #eef2ff;
  --primary-softer: #e0e7ff;

  /* Status */
  --success: #059669;
  --success-bg: #d1fae5;
  --success-fg: #065f46;
  --warning: #ea580c;
  --warning-bg: #fed7aa;
  --warning-fg: #92400e;
  --danger: #dc2626;
  --danger-bg: #fecaca;
  --danger-fg: #991b1b;
  /* Info retuned to indigo so it harmonizes with the new brand accent */
  --info: #4f46e5;
  --info-bg: #e0e7ff;
  --info-fg: #3730a3;

  /* Spacing — strict 8px rhythm */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;

  /* Radius */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;

  /* Elevation */
  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);

  /* Type scale */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 0.938rem;
  --text-lg: 1.125rem;
  --text-xl: 1.375rem;
  --text-2xl: 1.875rem;
  --text-3xl: 2.25rem;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

  /* Layout */
  --sidebar-w: 248px;
  --topbar-h: 64px;
  --content-max: 1440px;
}

/* ============================================================
   RESET
   ============================================================ */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-app);
  color: var(--text-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ============================================================
   APP SHELL — flex ROW so sidebar sits beside content
   ============================================================ */
.app {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}

/* ============================================================
   SIDEBAR
   sticky + height:100vh so it stays fixed while content scrolls.
   align-self:flex-start is required for position:sticky inside a
   flex row — without it the sidebar stretches to full page height
   and sticky has no room to activate.
   ============================================================ */
.sidebar {
  width: var(--sidebar-w);
  flex-shrink: 0;
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  position: sticky;
  top: 0;
  height: 100vh;
  align-self: flex-start;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* Brand block at the top of the sidebar */
.sidebar-brand {
  padding: var(--space-5);
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.sidebar-brand h1 {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-strong);
  letter-spacing: -0.025em;
  line-height: 1.2;
}

/* Subtitle sits directly below company name — no inline divider needed */
.sidebar-brand .subtitle {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 400;
}

/* Nav list inside the sidebar */
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3);
  flex: 1;
}

/* Each nav link: icon + label side-by-side */
.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--text-muted);
  text-decoration: none;
  /* position:relative is needed for the ::before accent bar */
  position: relative;
  transition: background 0.15s ease, color 0.15s ease;
}

.sidebar-nav a svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-nav a:hover {
  background: var(--bg-subtle);
  color: var(--text-strong);
}

/* Active state: indigo soft background + left accent bar */
.sidebar-nav a.active {
  background: var(--primary-soft);
  color: var(--primary);
}

/* Left accent bar replaces the old bottom ::after underline.
   inset-inline-start (logical property) keeps it at the left edge.
   Vertical inset (top/bottom 6px) gives it a "pill" look rather
   than spanning the full height of the row. */
.sidebar-nav a.active::before {
  content: '';
  position: absolute;
  inset-inline-start: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  background: var(--primary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

/* ============================================================
   APP BODY — flex column containing topbar, filter bar, main
   min-width:0 prevents flex children from overflowing the row
   when content is wider than available space.
   ============================================================ */
.app-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* ============================================================
   TOPBAR
   sticky so it stays at the top of the scroll viewport.
   The offset is 0 (not --topbar-h) because the sidebar is the
   sibling of .app-body, not an ancestor — the topbar is the
   first element that needs to stick.
   ============================================================ */
.topbar {
  height: var(--topbar-h);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  padding: 0 var(--space-6);
  gap: var(--space-4);
}

/* Push LanguageSwitcher + ProfileMenu to the right */
.topbar-controls {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

/* ============================================================
   MAIN CONTENT AREA
   max-width keeps lines readable on ultra-wide displays.
   margin:0 auto centers content within the remaining width once
   the sidebar is accounted for.
   ============================================================ */
.main-content {
  flex: 1;
  max-width: var(--content-max);
  width: 100%;
  margin: 0 auto;
  padding: var(--space-5) var(--space-6);
}

/* ============================================================
   GLOBAL PRIMITIVES — refactored to design tokens
   These classes are used by every view; class names are unchanged.
   ============================================================ */

/* Page header */
.page-header {
  margin-bottom: var(--space-5);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-strong);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-base);
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-5);
}

/* Stat card */
.stat-card {
  background: var(--bg-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-3xl);
  font-weight: 700;
  color: var(--text-strong);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: var(--warning);
}

.stat-card.success .stat-value {
  color: var(--success);
}

.stat-card.danger .stat-value {
  color: var(--danger);
}

/* Info stat value uses indigo brand token (retuned from old blue) */
.stat-card.info .stat-value {
  color: var(--info);
}

/* Card */
.card {
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--border);
  margin-bottom: var(--space-5);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
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
  font-weight: 700;
  color: var(--text-strong);
  letter-spacing: -0.025em;
}

/* Table */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--bg-subtle);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: var(--text-subtle);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  /* faint border between rows rather than strong dividers */
  border-top: 1px solid var(--border-faint);
  color: var(--text-body);
  font-size: var(--text-sm);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--bg-muted);
}

/* Badges */
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
  background: var(--success-bg);
  color: var(--success-fg);
}

.badge.warning {
  background: var(--warning-bg);
  color: var(--warning-fg);
}

.badge.danger {
  background: var(--danger-bg);
  color: var(--danger-fg);
}

/* Info badge retuned to indigo to harmonize with brand */
.badge.info {
  background: var(--info-bg);
  color: var(--info-fg);
}

.badge.increasing {
  background: var(--success-bg);
  color: var(--success-fg);
}

.badge.decreasing {
  background: var(--danger-bg);
  color: var(--danger-fg);
}

/* Stable badge uses indigo info tokens (was already e0e7ff/3730a3) */
.badge.stable {
  background: var(--info-bg);
  color: var(--info-fg);
}

.badge.high {
  background: var(--danger-bg);
  color: var(--danger-fg);
}

.badge.medium {
  background: var(--warning-bg);
  color: var(--warning-fg);
}

/* Low badge kept as indigo info — matches old dbeafe/1e40af intent */
.badge.low {
  background: var(--info-bg);
  color: var(--info-fg);
}

/* Loading / error states */
.loading {
  text-align: center;
  padding: var(--space-8);
  color: var(--text-muted);
  font-size: var(--text-base);
}

.error {
  background: var(--danger-bg);
  border: 1px solid var(--danger-bg);
  color: var(--danger-fg);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}

/* Primary button — used by individual views */
.btn-primary {
  background: var(--primary);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-sm);
  padding: var(--space-2) var(--space-5);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-primary:hover {
  background: var(--primary-hover);
}
</style>
