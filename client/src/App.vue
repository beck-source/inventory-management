<template>
  <div class="app">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- Brand -->
      <div class="sidebar-brand">
        <div class="brand-monogram">CC</div>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <!-- Nav -->
      <nav class="sidebar-nav">
        <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
          <!-- Overview: grid of 4 dots -->
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="3" width="6" height="6" rx="1.5" fill="currentColor"/>
            <rect x="11" y="3" width="6" height="6" rx="1.5" fill="currentColor"/>
            <rect x="3" y="11" width="6" height="6" rx="1.5" fill="currentColor"/>
            <rect x="11" y="11" width="6" height="6" rx="1.5" fill="currentColor"/>
          </svg>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>

        <router-link to="/inventory" class="nav-item" :class="{ active: $route.path === '/inventory' }">
          <!-- Inventory: stacked boxes -->
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="10" width="14" height="7" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
            <rect x="5" y="6" width="10" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="7" y="3" width="6" height="4" rx="1" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span class="nav-label">{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link to="/orders" class="nav-item" :class="{ active: $route.path === '/orders' }">
          <!-- Orders: clipboard with lines -->
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="3" width="12" height="14" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M7 8h6M7 11h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <rect x="8" y="2" width="4" height="2.5" rx="1" fill="currentColor"/>
          </svg>
          <span class="nav-label">{{ t('nav.orders') }}</span>
        </router-link>

        <router-link to="/restocking" class="nav-item" :class="{ active: $route.path === '/restocking' }">
          <!-- Restocking: refresh arrow circle -->
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 10a6 6 0 016-6 6 6 0 014.24 1.76L16 7.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M16 10a6 6 0 01-6 6 6 6 0 01-4.24-1.76L4 12.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <polyline points="14,5 16,7.5 13.5,8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="6,15 4,12.5 6.5,12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.restocking') }}</span>
        </router-link>

        <router-link to="/spending" class="nav-item" :class="{ active: $route.path === '/spending' }">
          <!-- Spending: dollar sign in circle -->
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 6v8M8 8.5c0-.83.67-1.5 1.5-1.5h1c.83 0 1.5.67 1.5 1.5S11.33 10 10.5 10h-1C8.67 10 8 10.67 8 11.5S8.67 13 9.5 13h1c.83 0 1.5-.67 1.5-1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.finance') }}</span>
        </router-link>

        <router-link to="/demand" class="nav-item" :class="{ active: $route.path === '/demand' }">
          <!-- Demand: trending up arrow -->
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="3,14 8,9 11,12 17,6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="13,6 17,6 17,10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link to="/backlog" class="nav-item" :class="{ active: $route.path === '/backlog' }">
          <!-- Backlog: hourglass (delayed queue) -->
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5 3h10M5 17h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M6 3c0 4 3 5 4 7-1 2-4 3-4 7M14 3c0 4-3 5-4 7 1 2 4 3 4 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">{{ t('nav.backlog') }}</span>
        </router-link>

        <router-link to="/reports" class="nav-item" :class="{ active: $route.path === '/reports' }">
          <!-- Reports: bar chart -->
          <svg class="nav-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="3" y="11" width="3.5" height="6" rx="1" fill="currentColor"/>
            <rect x="8.25" y="7" width="3.5" height="10" rx="1" fill="currentColor"/>
            <rect x="13.5" y="3" width="3.5" height="14" rx="1" fill="currentColor"/>
          </svg>
          <span class="nav-label">{{ t('nav.reports') }}</span>
        </router-link>
      </nav>

      <!-- Footer -->
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
        <button class="collapse-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
          <svg
            class="chevron-icon"
            :class="{ rotated: sidebarCollapsed }"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M13 15l-5-5 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="nav-label">Collapse</span>
        </button>
      </div>
    </aside>

    <!-- Main column -->
    <div class="main-column">
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
import { ref, watch, computed } from 'vue'
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

    // Sidebar collapse state persisted to localStorage
    const sidebarCollapsed = ref(localStorage.getItem('sidebarCollapsed') === 'true')

    watch(sidebarCollapsed, (v) => {
      localStorage.setItem('sidebarCollapsed', String(v))
    })

    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }

    const tasks = computed(() => currentUser.value.tasks)

    const addTask = (taskData) => {
      const newTask = {
        id: `task-${Date.now()}`,
        status: 'pending',
        ...taskData
      }
      currentUser.value.tasks.unshift(newTask)
    }

    const deleteTask = (taskId) => {
      const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
      if (index !== -1) {
        currentUser.value.tasks.splice(index, 1)
      }
    }

    const toggleTask = (taskId) => {
      const task = currentUser.value.tasks.find(t => t.id === taskId)
      if (task) {
        task.status = task.status === 'pending' ? 'completed' : 'pending'
      }
    }

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      sidebarCollapsed,
      toggleSidebar
    }
  }
}
</script>

<style>
/* ============================================================
   Design tokens
   ============================================================ */
:root {
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-alt: #f1f5f9;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-muted: #64748b;
  --color-text-subtle: #94a3b8;
  --color-accent: #2563eb;
  --color-accent-bg: #eff6ff;
  --color-success: #059669;
  --color-success-bg: #d1fae5;
  --color-warning: #ea580c;
  --color-warning-bg: #fed7aa;
  --color-danger: #dc2626;
  --color-danger-bg: #fecaca;
  --color-info: #2563eb;
  --color-info-bg: #dbeafe;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.06);
  --shadow-lg: 0 10px 24px rgba(15, 23, 42, 0.08);
  --sidebar-width: 260px;
  --sidebar-width-collapsed: 64px;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
}

/* ============================================================
   Reset & base
   ============================================================ */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ============================================================
   App shell
   ============================================================ */
.app {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}

/* ============================================================
   Sidebar
   ============================================================ */
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  z-index: 100;
  transition: width 0.2s ease, min-width 0.2s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
  min-width: var(--sidebar-width-collapsed);
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-4);
  border-bottom: 1px solid var(--color-border);
  min-height: 70px;
  overflow: hidden;
}

.brand-monogram {
  width: 36px;
  height: 36px;
  min-width: 36px;
  border-radius: var(--radius-sm);
  background: linear-gradient(135deg, var(--color-accent) 0%, #1e40af 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.75rem;
  letter-spacing: 0.025em;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
  white-space: nowrap;
}

.brand-name {
  font-size: 0.938rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.015em;
  line-height: 1.2;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-weight: 400;
  line-height: 1.2;
}

.sidebar.collapsed .brand-text {
  display: none;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  color: var(--color-text);
  background: var(--color-surface-alt);
}

.nav-item.active {
  color: var(--color-accent);
  background: var(--color-accent-bg);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 4px;
  border-radius: 0 2px 2px 0;
  background: var(--color-accent);
}

.nav-icon {
  width: 18px;
  height: 18px;
  min-width: 18px;
  color: currentColor;
}

.nav-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar.collapsed .nav-label {
  display: none;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: var(--space-2);
}

/* Footer */
.sidebar-footer {
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* Collapse toggle */
.collapse-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  width: 100%;
  text-align: left;
  transition: all 0.15s ease;
  white-space: nowrap;
  overflow: hidden;
}

.collapse-toggle:hover {
  color: var(--color-text);
  background: var(--color-surface-alt);
}

.chevron-icon {
  width: 18px;
  height: 18px;
  min-width: 18px;
  transition: transform 0.2s ease;
}

.chevron-icon.rotated {
  transform: rotate(180deg);
}

.sidebar.collapsed .collapse-toggle {
  justify-content: center;
  padding: var(--space-2);
}

/* ============================================================
   Main column
   ============================================================ */
.main-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  padding: var(--space-6) var(--space-8);
}

/* ============================================================
   Page header
   ============================================================ */
.page-header {
  margin-bottom: var(--space-6);
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

/* ============================================================
   Stats grid
   ============================================================ */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

/* ============================================================
   Stat card
   ============================================================ */
.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-border-strong);
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

/* ============================================================
   Card
   ============================================================ */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
  transition: box-shadow 0.2s ease;
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

/* ============================================================
   Tables
   ============================================================ */
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
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--color-surface-alt);
  color: #334155;
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-bg);
}

/* ============================================================
   Badges
   ============================================================ */
.badge {
  display: inline-block;
  padding: 0.313rem var(--space-3);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--color-success-bg);
  color: #065f46;
}

.badge.warning {
  background: var(--color-warning-bg);
  color: #92400e;
}

.badge.danger {
  background: var(--color-danger-bg);
  color: #991b1b;
}

.badge.info {
  background: var(--color-info-bg);
  color: #1e40af;
}

.badge.increasing {
  background: var(--color-success-bg);
  color: #065f46;
}

.badge.decreasing {
  background: var(--color-danger-bg);
  color: #991b1b;
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: var(--color-danger-bg);
  color: #991b1b;
}

.badge.medium {
  background: var(--color-warning-bg);
  color: #92400e;
}

.badge.low {
  background: var(--color-info-bg);
  color: #1e40af;
}

/* ============================================================
   Loading / Error states
   ============================================================ */
.loading {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid var(--color-danger-bg);
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  margin: var(--space-4) 0;
  font-size: 0.938rem;
}
</style>
