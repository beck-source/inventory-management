<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-logo">
        <div class="logo-mark">
          <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" width="32" height="32">
            <rect width="32" height="32" rx="8" fill="var(--color-accent-dim)"/>
            <rect x="7" y="7" width="8" height="8" rx="1.5" fill="#00d4ff"/>
            <rect x="17" y="7" width="8" height="8" rx="1.5" fill="rgba(0,212,255,0.4)"/>
            <rect x="7" y="17" width="8" height="8" rx="1.5" fill="rgba(0,212,255,0.4)"/>
            <rect x="17" y="17" width="8" height="8" rx="1.5" fill="#00d4ff"/>
          </svg>
        </div>
        <div class="logo-text">
          <span class="logo-name">{{ t('nav.companyName') }}</span>
          <span class="logo-sub">{{ t('nav.subtitle') }}</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          :data-label="item.label"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu @show-profile-details="showProfileDetails = true" @show-tasks="showTasks = true" />
        <button class="sidebar-toggle" @click="toggleSidebar" :title="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5"/>
          </svg>
        </button>
      </div>
    </aside>
    <div class="main-area" :class="{ 'main-area--collapsed': sidebarCollapsed }">
      <div class="topbar"><FilterBar /></div>
      <main class="main-content"><router-view /></main>
    </div>

    <ProfileDetailsModal :is-open="showProfileDetails" @close="showProfileDetails = false" />
    <TasksModal :is-open="showTasks" :tasks="tasks" @close="showTasks = false" @add-task="addTask" @delete-task="deleteTask" @toggle-task="toggleTask" />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

const svgGrid = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`

const svgBox = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"/></svg>`

const svgClipboard = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/></svg>`

const svgChart = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/></svg>`

const svgTrend = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941"/></svg>`

const svgFile = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/></svg>`

const svgRefresh = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/></svg>`

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
    const route = useRoute()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    const isActive = (path) => {
      if (path === '/') return route.path === '/'
      return route.path.startsWith(path)
    }

    const navItems = [
      { path: '/',           label: t('nav.overview'),       icon: svgGrid },
      { path: '/inventory',  label: t('nav.inventory'),      icon: svgBox },
      { path: '/orders',     label: t('nav.orders'),         icon: svgClipboard },
      { path: '/spending',   label: t('nav.finance'),        icon: svgChart },
      { path: '/demand',     label: t('nav.demandForecast'), icon: svgTrend },
      { path: '/reports',    label: 'Reports',               icon: svgFile },
      { path: '/restocking', label: t('nav.restocking'),     icon: svgRefresh },
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
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
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
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    // Sidebar collapse state — restore from localStorage, auto-collapse on small screens
    const BREAKPOINT = 1024
    const sidebarCollapsed = ref(
      window.innerWidth <= BREAKPOINT ? true : localStorage.getItem('sidebar-collapsed') === 'true'
    )

    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
      localStorage.setItem('sidebar-collapsed', String(sidebarCollapsed.value))
    }

    // Auto-collapse when window resizes below breakpoint
    const handleResize = () => {
      if (window.innerWidth <= BREAKPOINT) {
        sidebarCollapsed.value = true
      }
    }

    onMounted(() => {
      window.addEventListener('resize', handleResize)
      loadTasks()
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
    })

    return {
      t,
      route,
      isActive,
      navItems,
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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

:root {
  /* Core surfaces */
  --color-bg-base: #0d1117;
  --color-bg-surface: #161b22;
  --color-bg-elevated: #1c2128;
  --color-bg-overlay: #21262d;

  /* Borders */
  --color-border: #30363d;
  --color-border-subtle: #21262d;

  /* Text */
  --color-text-primary: #e6edf3;
  --color-text-secondary: #8b949e;
  --color-text-muted: #484f58;

  /* Accent */
  --color-accent: #00d4ff;
  --color-accent-dim: rgba(0, 212, 255, 0.1);
  --color-accent-glow: rgba(0, 212, 255, 0.25);

  /* Status */
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-info: #58a6ff;

  /* Layout */
  --sidebar-width: 240px;
  --sidebar-collapsed-width: 56px;
  --sidebar-transition: 0.2s ease;
  --sidebar-bg: #161b22;
  --sidebar-border: #30363d;
  --sidebar-text: #8b949e;
  --sidebar-text-active: #e6edf3;
  --sidebar-active-bg: rgba(0, 212, 255, 0.08);
  --sidebar-active-border: #00d4ff;
  --topbar-bg: #161b22;
  --topbar-border: #30363d;
  --topbar-height: 52px;
  --content-bg: #0d1117;
  --content-padding: 1.5rem 1.75rem;

  /* Typography */
  --font-sans: 'IBM Plex Sans', ui-sans-serif, sans-serif;
  --font-mono: 'IBM Plex Mono', 'JetBrains Mono', monospace;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: var(--font-sans);
  background: var(--color-bg-base);
  color: var(--color-text-primary);
  -webkit-font-smoothing: antialiased;
}

/* ── Layout ── */

.app-layout {
  display: flex;
  min-height: 100vh;
  font-family: var(--font-sans);
  background: var(--color-bg-base);
}

.sidebar {
  position: fixed;
  top: 0; left: 0;
  width: var(--sidebar-width);
  height: 100vh;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  z-index: 40;
  overflow: hidden;
  transition: width var(--sidebar-transition);
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-logo {
  height: 56px; padding: 0 1rem;
  display: flex; align-items: center; gap: 0.75rem;
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.logo-mark {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.logo-text {
  overflow: hidden;
  min-width: 0;
  transition: opacity 0.15s ease, width 0.2s ease;
}

.logo-name {
  display: block; font-family: var(--font-mono);
  font-size: 0.8125rem; font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  letter-spacing: 0.02em; text-transform: uppercase;
}

.logo-sub {
  display: block; font-family: var(--font-mono);
  font-size: 0.65rem; color: var(--color-text-muted);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  letter-spacing: 0.04em;
}

.sidebar-nav {
  flex: 1; padding: 0.75rem 0.625rem;
  overflow-y: auto; display: flex; flex-direction: column; gap: 1px;
}

.nav-item {
  position: relative;
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.5rem 0.75rem; border-radius: 5px;
  color: var(--sidebar-text); text-decoration: none;
  font-size: 0.8125rem; font-weight: 500;
  transition: background 0.1s, color 0.1s;
  border-left: 2px solid transparent;
  letter-spacing: 0.01em;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--sidebar-active-bg);
  color: var(--sidebar-text-active);
  border-left-color: var(--sidebar-active-border);
}

.nav-icon { width: 16px; flex-shrink: 0; opacity: 0.7; }
.nav-icon svg { width: 16px; height: 16px; display: block; }
.nav-item.active .nav-icon { opacity: 1; }

.nav-label {
  transition: opacity 0.15s ease, width 0.2s ease;
}

.sidebar-footer {
  padding: 0.75rem 0.875rem;
  border-top: 1px solid var(--sidebar-border);
  display: flex; align-items: center; gap: 0.5rem;
  flex-shrink: 0; min-width: 0;
}

/* ── Collapsed sidebar states ── */

.sidebar.collapsed .logo-text,
.sidebar.collapsed .nav-label {
  opacity: 0;
  width: 0;
  overflow: hidden;
  pointer-events: none;
  transition: opacity 0.15s ease, width 0.2s ease;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.5rem;
  border-left-color: transparent;
}

.sidebar.collapsed .nav-item.active {
  border-left-color: var(--sidebar-active-border);
  padding-left: 0.375rem;
}

.sidebar.collapsed .nav-icon {
  margin: 0;
}

.sidebar.collapsed .sidebar-logo {
  justify-content: center;
  padding: 0 0.5rem;
}

.sidebar.collapsed .sidebar-footer {
  justify-content: center;
  padding: 0.75rem 0.375rem;
}

.sidebar.collapsed .sidebar-footer > :not(.sidebar-toggle) {
  display: none;
}

/* ── Tooltip for collapsed nav items ── */

.sidebar.collapsed .nav-item::after {
  content: attr(data-label);
  position: absolute;
  left: calc(100% + 12px);
  top: 50%;
  transform: translateY(-50%);
  background: var(--color-bg-overlay);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-family: var(--font-sans);
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.375rem 0.625rem;
  border-radius: 4px;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s ease;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.sidebar.collapsed .nav-item:hover::after {
  opacity: 1;
}

/* ── Toggle button ── */

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, transform 0.2s ease;
  flex-shrink: 0;
  padding: 0;
}

.sidebar-toggle:hover {
  color: var(--color-accent);
  border-color: var(--color-accent);
}

.sidebar-toggle svg {
  width: 14px;
  height: 14px;
  display: block;
  transition: transform 0.2s ease;
}

.sidebar.collapsed .sidebar-toggle svg {
  transform: rotate(180deg);
}

/* ── Main area ── */

.main-area {
  margin-left: var(--sidebar-width);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left var(--sidebar-transition);
}

.main-area--collapsed {
  margin-left: var(--sidebar-collapsed-width);
}

.topbar {
  position: sticky; top: 0; z-index: 50;
  background: var(--topbar-bg);
  border-bottom: 1px solid var(--topbar-border);
  min-height: var(--topbar-height);
}

.main-content {
  flex: 1; padding: var(--content-padding);
  background: var(--color-bg-base);
}

/* ── Global utility classes — DO NOT REMOVE ── */

/* Page header */
.page-header { margin-bottom: 1.25rem; }
.page-header h2 {
  font-size: 1.25rem; font-weight: 700;
  color: var(--color-text-primary); margin-bottom: 0.25rem;
  letter-spacing: -0.01em; font-family: var(--font-sans);
}
.page-header p { color: var(--color-text-secondary); font-size: 0.8125rem; }

/* Stats grid */
.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1px; margin-bottom: 1rem;
  background: var(--color-border); border-radius: 6px;
  overflow: hidden; border: 1px solid var(--color-border);
}
.stat-card {
  background: var(--color-bg-surface);
  padding: 1rem 1.25rem;
  border-radius: 0; border: none;
  transition: background 0.15s;
}
.stat-card:hover { background: var(--color-bg-elevated); }
.stat-label {
  font-family: var(--font-mono); font-size: 0.65rem; font-weight: 500;
  color: var(--color-text-secondary); text-transform: uppercase;
  letter-spacing: 0.1em; margin-bottom: 0.5rem;
}
.stat-value {
  font-family: var(--font-mono); font-size: 1.75rem; font-weight: 600;
  color: var(--color-text-primary); letter-spacing: -0.03em; line-height: 1;
}
.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger  .stat-value { color: var(--color-danger); }
.stat-card.info    .stat-value { color: var(--color-info); }

/* Card */
.card {
  background: var(--color-bg-surface);
  border-radius: 6px; padding: 0;
  border: 1px solid var(--color-border);
  margin-bottom: 1rem; overflow: hidden;
}
.card-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.75rem 1rem; border-bottom: 1px solid var(--color-border);
}
.card-title {
  font-family: var(--font-mono); font-size: 0.7rem; font-weight: 600;
  color: var(--color-text-secondary); letter-spacing: 0.08em;
  text-transform: uppercase;
}

/* Table */
.table-container { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
thead {
  background: var(--color-bg-base);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}
th {
  text-align: left; padding: 0.4rem 0.75rem;
  font-family: var(--font-mono); font-weight: 500;
  color: var(--color-text-secondary); font-size: 0.65rem;
  text-transform: uppercase; letter-spacing: 0.1em; white-space: nowrap;
}
td {
  padding: 0.425rem 0.75rem;
  border-top: 1px solid var(--color-border-subtle);
  color: var(--color-text-primary); font-size: 0.8125rem; line-height: 1.4;
}
tbody tr { transition: background 0.1s; }
tbody tr:hover { background: var(--color-bg-elevated); }

/* Badges */
.badge {
  display: inline-block; padding: 0.2rem 0.5rem;
  border-radius: 4px; font-family: var(--font-mono);
  font-size: 0.65rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.06em;
  border: 1px solid transparent;
}
.badge.success    { background: rgba(63,185,80,0.12); color: #3fb950; border-color: rgba(63,185,80,0.25); }
.badge.warning    { background: rgba(210,153,34,0.12); color: #d29922; border-color: rgba(210,153,34,0.25); }
.badge.danger     { background: rgba(248,81,73,0.12); color: #f85149; border-color: rgba(248,81,73,0.25); }
.badge.info       { background: rgba(88,166,255,0.12); color: #58a6ff; border-color: rgba(88,166,255,0.25); }
.badge.increasing { background: rgba(63,185,80,0.12); color: #3fb950; border-color: rgba(63,185,80,0.25); }
.badge.decreasing { background: rgba(248,81,73,0.12); color: #f85149; border-color: rgba(248,81,73,0.25); }
.badge.stable     { background: rgba(88,166,255,0.12); color: #58a6ff; border-color: rgba(88,166,255,0.25); }
.badge.high       { background: rgba(248,81,73,0.12); color: #f85149; border-color: rgba(248,81,73,0.25); }
.badge.medium     { background: rgba(210,153,34,0.12); color: #d29922; border-color: rgba(210,153,34,0.25); }
.badge.low        { background: rgba(88,166,255,0.12); color: #58a6ff; border-color: rgba(88,166,255,0.25); }

/* Loading / Error */
.loading { text-align: center; padding: 3rem; color: var(--color-text-secondary); font-size: 0.8125rem; font-family: var(--font-mono); }
.error {
  background: rgba(248,81,73,0.08); border: 1px solid rgba(248,81,73,0.25);
  color: var(--color-danger); padding: 0.875rem 1rem; border-radius: 6px;
  margin: 1rem 0; font-size: 0.8125rem;
}
</style>
