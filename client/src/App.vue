<template>
  <div class="app-shell">
    <!-- Sidebar -->
    <Sidebar
      :is-open="sidebarOpen"
      :collapsed="sidebarCollapsed"
      @close="sidebarOpen = false"
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
      @toggle-collapse="toggleCollapse"
    />

    <!-- Mobile overlay: closes sidebar when clicking outside -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false"></div>

    <!-- Main content area -->
    <div class="app-content">
      <!-- Top bar: hamburger (mobile) + filter bar -->
      <header class="app-topbar">
        <button class="hamburger" @click="sidebarOpen = !sidebarOpen" aria-label="Toggle sidebar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <FilterBar />
      </header>

      <!-- Page content -->
      <main class="app-main">
        <router-view />
      </main>
    </div>

    <!-- Modals live here so they're always available regardless of active route -->
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
import { ref, computed } from 'vue'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import Sidebar from './components/Sidebar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    FilterBar,
    ProfileDetailsModal,
    TasksModal
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const sidebarOpen = ref(false)
    // Persist collapsed state across page reloads
    const sidebarCollapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')

    const toggleCollapse = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
      localStorage.setItem('sidebar-collapsed', sidebarCollapsed.value)
    }

    const tasks = computed(() => currentUser.value.tasks)

    const addTask = (taskData) => {
      const newTask = { id: Date.now(), ...taskData, status: 'pending' }
      currentUser.value.tasks.unshift(newTask)
    }

    const deleteTask = (taskId) => {
      const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
      if (index !== -1) currentUser.value.tasks.splice(index, 1)
    }

    const toggleTask = (taskId) => {
      const task = currentUser.value.tasks.find(t => t.id === taskId)
      if (task) task.status = task.status === 'pending' ? 'completed' : 'pending'
    }

    return {
      t,
      showProfileDetails,
      showTasks,
      sidebarOpen,
      sidebarCollapsed,
      toggleCollapse,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
/* ─── Design tokens — Theme 2: Light sidebar / Light content ─── */
:root {
  /* Sidebar */
  --sidebar-width:           220px;
  --sidebar-collapsed-width:  56px;
  --sidebar-bg:          #f1f5f9;
  --sidebar-text:        #64748b;
  --sidebar-text-hover:  #0f172a;
  --sidebar-active-bg:   #e2e8f0;
  --sidebar-active-text: #0f172a;
  --sidebar-border:      #e2e8f0;
  --sidebar-icon-color:  #94a3b8;

  /* Content */
  --content-bg:    #ffffff;
  --surface-bg:    #ffffff;
  --border-color:  #e2e8f0;
  --text-primary:  #0f172a;
  --text-secondary:#64748b;
  --text-muted:    #94a3b8;

  /* Accent — indigo */
  --accent:        #6366f1;
  --accent-hover:  #4f46e5;
  --accent-subtle: #eef2ff;

  /* Status */
  --status-green:  #16a34a; --status-green-bg:  #f0fdf4;
  --status-blue:   #2563eb; --status-blue-bg:   #eff6ff;
  --status-yellow: #ca8a04; --status-yellow-bg: #fefce8;
  --status-red:    #dc2626; --status-red-bg:    #fef2f2;

  /* Spacing */
  --content-padding: 1.75rem;
  --card-padding:    1.25rem;
  --gap-sm:  .5rem;
  --gap-md:  1rem;
  --gap-lg:  1.5rem;
  --gap-xl:  2rem;

  /* Radius + shadows */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Fira Code', 'Cascadia Code', monospace;
  --text-xs:   .75rem;
  --text-sm:   .875rem;
  --text-base: 1rem;
  --text-lg:   1.125rem;
  --text-xl:   1.25rem;
  --text-2xl:  1.5rem;
}

/* ─── Reset ─── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-sans);
  background: var(--content-bg);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ─── App shell: sidebar + content side by side ─── */
.app-shell {
  display: flex;
  min-height: 100vh;
}

.app-content {
  flex: 1;
  /* min-width: 0 prevents flex child from overflowing its container */
  min-width: 0;
  background: var(--content-bg);
  display: flex;
  flex-direction: column;
}

/* ─── Top bar (filter strip) ─── */
.app-topbar {
  display: flex;
  align-items: center;
  gap: var(--gap-md);
  padding: .625rem 1.5rem;
  background: var(--surface-bg);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  /* z-index keeps topbar above scrolling page content but below sidebar overlay */
  z-index: 100;
}

.hamburger {
  display: none;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-color);
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  flex-shrink: 0;
  padding: 0;
}

.hamburger svg { width: 18px; height: 18px; }

/* Mobile overlay dims content when sidebar is open */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.35);
  /* z-index above content (100) but below sidebar (200) */
  z-index: 150;
}

/* ─── Main page area ─── */
.app-main {
  flex: 1;
  padding: var(--content-padding);
}

/* ─── Global utility classes ─── */

/* Page header */
.page-header   { margin-bottom: var(--gap-xl); }
.page-title    { font-size: var(--text-2xl); font-weight: 700; color: var(--text-primary); line-height: 1.2; letter-spacing: -.025em; }
.page-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin-top: .25rem; }

/* Cards */
.card        { background: var(--surface-bg); border: 1px solid var(--border-color); border-radius: var(--radius-md); box-shadow: var(--shadow-sm); margin-bottom: var(--gap-lg); }
.card-header { padding: 1rem var(--card-padding); border-bottom: 1px solid var(--border-color); display: flex; align-items: center; justify-content: space-between; }
.card-title  { font-size: var(--text-base); font-weight: 700; color: var(--text-primary); letter-spacing: -.025em; }

/* Tables */
.table-container { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; }

thead { background: #f8fafc; border-top: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); }

th {
  text-align: left;
  padding: .5rem .75rem;
  font-weight: 600;
  color: #475569;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: .05em;
}

td {
  padding: .5rem .75rem;
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: var(--text-sm);
}

tbody tr { transition: background-color .15s ease; }
tbody tr:hover { background: #f8fafc; }

/* Badges */
.badge {
  display: inline-block;
  padding: .3rem .75rem;
  border-radius: 6px;
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .025em;
}

.badge.success   { background: #d1fae5; color: #065f46; }
.badge.warning   { background: #fed7aa; color: #92400e; }
.badge.danger    { background: #fecaca; color: #991b1b; }
.badge.info      { background: #dbeafe; color: #1e40af; }
.badge.increasing{ background: #d1fae5; color: #065f46; }
.badge.decreasing{ background: #fecaca; color: #991b1b; }
.badge.stable    { background: #e0e7ff; color: #3730a3; }
.badge.high      { background: #fecaca; color: #991b1b; }
.badge.medium    { background: #fed7aa; color: #92400e; }
.badge.low       { background: #dbeafe; color: #1e40af; }

/* Stat cards (kept for backward compat with views using .stat-card) */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--gap-md);
  margin-bottom: var(--gap-lg);
}

.stat-card {
  background: var(--surface-bg);
  padding: var(--card-padding);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  transition: box-shadow .2s ease, border-color .2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-md);
}

.stat-label { color: var(--text-secondary); font-size: var(--text-sm); font-weight: 600; text-transform: uppercase; letter-spacing: .5px; margin-bottom: .625rem; }
.stat-value { font-size: 2.25rem; font-weight: 700; color: var(--text-primary); letter-spacing: -.025em; }
.stat-card.warning .stat-value { color: #ea580c; }
.stat-card.success .stat-value { color: #059669; }
.stat-card.danger  .stat-value { color: #dc2626; }
.stat-card.info    .stat-value { color: #2563eb; }

/* Loading / error states */
.loading { text-align: center; padding: 3rem; color: var(--text-secondary); font-size: var(--text-sm); }
.error   { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; padding: 1rem; border-radius: 8px; margin: 1rem 0; font-size: var(--text-sm); }

/* ─── Responsive: show hamburger, hide desktop sidebar on mobile ─── */
@media (max-width: 768px) {
  .hamburger        { display: flex; }
  .sidebar-overlay  { display: block; }
  .app-main         { padding: 1rem; }
}
</style>
