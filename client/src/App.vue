<template>
  <div class="app-shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <!-- Mobile backdrop -->
    <div v-if="!sidebarCollapsed" class="sidebar-backdrop" @click="toggleSidebar"></div>

    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">FI</div>
        <div class="brand-text nav-label">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-sub">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }" :title="sidebarCollapsed ? t('nav.overview') : undefined" @click="closeSidebarOnMobile">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/inventory" class="nav-item" :class="{ active: $route.path === '/inventory' }" :title="sidebarCollapsed ? t('nav.inventory') : undefined" @click="closeSidebarOnMobile">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/></svg>
          <span class="nav-label">{{ t('nav.inventory') }}</span>
        </router-link>
        <router-link to="/orders" class="nav-item" :class="{ active: $route.path === '/orders' }" :title="sidebarCollapsed ? t('nav.orders') : undefined" @click="closeSidebarOnMobile">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>
          <span class="nav-label">{{ t('nav.orders') }}</span>
        </router-link>
        <router-link to="/restocking" class="nav-item" :class="{ active: $route.path === '/restocking' }" :title="sidebarCollapsed ? 'Restocking' : undefined" @click="closeSidebarOnMobile">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          <span class="nav-label">Restocking</span>
        </router-link>

        <div class="nav-section-divider"></div>

        <router-link to="/spending" class="nav-item" :class="{ active: $route.path === '/spending' }" :title="sidebarCollapsed ? t('nav.finance') : undefined" @click="closeSidebarOnMobile">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
          <span class="nav-label">{{ t('nav.finance') }}</span>
        </router-link>
        <router-link to="/demand" class="nav-item" :class="{ active: $route.path === '/demand' }" :title="sidebarCollapsed ? t('nav.demandForecast') : undefined" @click="closeSidebarOnMobile">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          <span class="nav-label">{{ t('nav.demandForecast') }}</span>
        </router-link>
        <router-link to="/reports" class="nav-item" :class="{ active: $route.path === '/reports' }" :title="sidebarCollapsed ? 'Reports' : undefined" @click="closeSidebarOnMobile">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          <span class="nav-label">Reports</span>
        </router-link>
      </nav>

      <button class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path v-if="sidebarCollapsed" d="M9 5l7 7-7 7"/>
          <path v-else d="M15 19l-7-7 7-7"/>
        </svg>
        <span class="nav-label">Collapse</span>
      </button>

      <div class="sidebar-footer">
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
        <LanguageSwitcher />
      </div>
    </aside>

    <div class="main-area">
      <div class="topbar">
        <button class="mobile-menu-btn" @click="toggleSidebar" aria-label="Toggle menu">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
        <FilterBar />
      </div>
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

    const sidebarCollapsed = ref(typeof window !== 'undefined' && window.innerWidth < 768)
    const toggleSidebar = () => { sidebarCollapsed.value = !sidebarCollapsed.value }
    const closeSidebarOnMobile = () => { if (window.innerWidth < 768) sidebarCollapsed.value = true }

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
      toggleTask,
      sidebarCollapsed,
      toggleSidebar,
      closeSidebarOnMobile
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

:root {
  --sidebar-width: 220px;
  --sidebar-bg: #0f172a;
  --sidebar-text: #94a3b8;
  --sidebar-text-active: #f1f5f9;
  --sidebar-accent: #3b82f6;
  --sidebar-hover-bg: rgba(255,255,255,0.06);
  --sidebar-active-bg: rgba(59,130,246,0.12);

  --bg-page: #f1f5f9;
  --bg-card: #ffffff;
  --border: #e2e8f0;
  --border-subtle: #f1f5f9;

  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 12px;

  --shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-page);
  color: var(--text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Shell ─────────────────────────────── */
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ── Sidebar ───────────────────────────── */
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  transition: width 0.22s ease;
  overflow: hidden;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 1.125rem 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  min-height: 60px;
}

.brand-icon {
  width: 32px;
  height: 32px;
  background: var(--sidebar-accent);
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  font-weight: 800;
  color: white;
  letter-spacing: 0.03em;
  flex-shrink: 0;
}

.brand-name {
  display: block;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--sidebar-text-active);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.brand-sub {
  display: block;
  font-size: 0.6875rem;
  color: var(--sidebar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.625rem;
  display: flex;
  flex-direction: column;
  gap: 1px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--sidebar-text);
  text-decoration: none;
  transition: background 0.12s, color 0.12s;
  border-left: 2px solid transparent;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.nav-item.active {
  background: var(--sidebar-active-bg);
  color: var(--sidebar-accent);
  border-left-color: var(--sidebar-accent);
}

.nav-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.nav-label {
  transition: opacity 0.15s ease;
  overflow: hidden;
  white-space: nowrap;
}

.nav-section-divider {
  height: 1px;
  background: rgba(255,255,255,0.07);
  margin: 0.5rem 0.25rem;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  width: calc(100% - 1.25rem);
  margin: 0 0.625rem 0.5rem;
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--sidebar-text);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-toggle:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.sidebar-toggle svg {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 0.5rem 0.625rem;
  border-top: 1px solid rgba(255,255,255,0.07);
  display: flex;
  align-items: center;
  gap: 0.375rem;
  min-height: 52px;
}

/* ── Main area ─────────────────────────── */
.main-area {
  margin-left: var(--sidebar-width);
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  min-width: 0;
  transition: margin-left 0.22s ease;
}

.topbar {
  flex-shrink: 0;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 2.5rem;
}

/* ── Page header ───────────────────────── */
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--text-secondary);
  font-size: 0.875rem;
}

/* ── Cards ─────────────────────────────── */
.card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-card);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border-subtle);
}

.card-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

/* ── Stat cards ────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.stat-card {
  background: var(--bg-card);
  padding: 1.125rem 1.25rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-card);
  transition: box-shadow 0.15s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  line-height: 1;
}

.stat-card.warning .stat-value { color: #ea580c; }
.stat-card.success .stat-value { color: #059669; }
.stat-card.danger  .stat-value { color: #dc2626; }
.stat-card.info    .stat-value { color: #2563eb; }

/* ── Tables ────────────────────────────── */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8fafc;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: 0.5rem 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

td {
  padding: 0.625rem 0.875rem;
  border-top: 1px solid var(--border-subtle);
  color: #334155;
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.12s;
}

tbody tr:hover {
  background: #f8fafc;
}

/* ── Badges ────────────────────────────── */
.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 5px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.badge.success    { background: #d1fae5; color: #065f46; }
.badge.warning    { background: #fed7aa; color: #92400e; }
.badge.danger     { background: #fecaca; color: #991b1b; }
.badge.info       { background: #dbeafe; color: #1e40af; }
.badge.increasing { background: #d1fae5; color: #065f46; }
.badge.decreasing { background: #fecaca; color: #991b1b; }
.badge.stable     { background: #e0e7ff; color: #3730a3; }
.badge.high       { background: #fecaca; color: #991b1b; }
.badge.medium     { background: #fed7aa; color: #92400e; }
.badge.low        { background: #dbeafe; color: #1e40af; }

/* ── Loading / Error ───────────────────── */
.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 1rem;
  border-radius: var(--radius-sm);
  margin: 1rem 0;
  font-size: 0.875rem;
}

/* ── Collapsed sidebar (desktop: icons-only) ── */
.app-shell.sidebar-collapsed .sidebar {
  width: 56px;
}

.app-shell.sidebar-collapsed .main-area {
  margin-left: 56px;
}

.app-shell.sidebar-collapsed .nav-label,
.app-shell.sidebar-collapsed .brand-text {
  opacity: 0;
  width: 0;
  max-width: 0;
  pointer-events: none;
}

.app-shell.sidebar-collapsed .sidebar-brand {
  justify-content: center;
  padding: 1.125rem 0;
}

.app-shell.sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 0.5rem 0;
  border-left-color: transparent !important;
}

.app-shell.sidebar-collapsed .nav-item.active {
  border-left-color: transparent !important;
  background: var(--sidebar-active-bg);
}

.app-shell.sidebar-collapsed .nav-item.active .nav-icon {
  color: var(--sidebar-accent);
}

.app-shell.sidebar-collapsed .sidebar-toggle {
  justify-content: center;
  padding: 0.4rem 0;
  width: calc(100% - 0.75rem);
  margin: 0 0.375rem 0.5rem;
}

.app-shell.sidebar-collapsed .sidebar-footer {
  justify-content: center;
  padding: 0.5rem 0;
}

.app-shell.sidebar-collapsed .profile-button {
  justify-content: center;
  padding: 0.5rem 0;
}

.app-shell.sidebar-collapsed .nav-section-divider {
  margin: 0.5rem 0.75rem;
}

/* ── Mobile menu button (hidden on desktop) ── */
.mobile-menu-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin-left: 0.75rem;
}

.mobile-menu-btn:hover {
  background: #f1f5f9;
  color: var(--text-primary);
}

.mobile-menu-btn svg {
  width: 18px;
  height: 18px;
}

/* ── Mobile overlay backdrop ──────────────── */
.sidebar-backdrop {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  z-index: 99;
}

/* ── Mobile breakpoint ────────────────────── */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(0);
    transition: transform 0.22s ease, width 0.22s ease;
    width: 220px !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.25);
  }

  /* Collapsed on mobile = hidden off-screen */
  .app-shell.sidebar-collapsed .sidebar {
    width: 220px !important;
    transform: translateX(-100%);
  }

  /* Labels always visible on mobile (not icons-only) */
  .app-shell.sidebar-collapsed .nav-label,
  .app-shell.sidebar-collapsed .brand-text {
    opacity: 1;
    width: auto;
    max-width: none;
    pointer-events: auto;
  }

  .app-shell.sidebar-collapsed .sidebar-brand {
    justify-content: flex-start;
    padding: 1.125rem 1rem;
  }

  .app-shell.sidebar-collapsed .nav-item {
    justify-content: flex-start;
    padding: 0.5rem 0.75rem;
  }

  .app-shell.sidebar-collapsed .sidebar-toggle {
    justify-content: flex-start;
    padding: 0.4rem 0.75rem;
    width: calc(100% - 1.25rem);
    margin: 0 0.625rem 0.5rem;
  }

  .app-shell.sidebar-collapsed .sidebar-footer {
    justify-content: flex-start;
    padding: 0.5rem 0.625rem;
  }

  .app-shell.sidebar-collapsed .profile-button {
    justify-content: flex-start;
    padding: 0.5rem 0.75rem;
  }

  /* Main area always full width on mobile */
  .main-area,
  .app-shell.sidebar-collapsed .main-area {
    margin-left: 0 !important;
  }

  /* Show backdrop when sidebar is open */
  .sidebar-backdrop {
    display: block;
  }

  /* Show hamburger on mobile */
  .mobile-menu-btn {
    display: flex;
  }

  /* Hide the in-sidebar toggle on mobile */
  .sidebar-toggle {
    display: none;
  }
}
</style>
