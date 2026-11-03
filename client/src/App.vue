<template>
  <div class="app" :class="{ 'drawer-open': drawerOpen, 'rail': rail }">
    <div class="sidebar-backdrop" @click="closeDrawer"></div>
    <aside id="app-sidebar" class="sidebar">
      <div class="brand">
        <div class="brand-text">
          <h1 class="brand-name">{{ t('nav.companyName') }}</h1>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <button
          type="button"
          class="collapse-toggle"
          :aria-label="rail ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="rail ? 'false' : 'true'"
          aria-controls="app-sidebar"
          @click="toggleRail"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path v-if="rail" d="M9 6l6 6-6 6" />
            <path v-else d="M15 6l-6 6 6 6" />
          </svg>
        </button>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: $route.path === item.to }"
          :title="rail ? item.label : null"
        >
          <span class="nav-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path v-for="d in item.icon" :key="d" :d="d" />
            </svg>
          </span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <button
          type="button"
          class="menu-button"
          aria-label="Toggle navigation menu"
          aria-controls="app-sidebar"
          :aria-expanded="drawerOpen ? 'true' : 'false'"
          @click="drawerOpen = !drawerOpen"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
        <FilterBar />
      </header>
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
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
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
    const drawerOpen = ref(false)
    const route = useRoute()
    const closeDrawer = () => { drawerOpen.value = false }
    watch(() => route.path, closeDrawer)

    // Sidebar collapse: desktop persists, tablet defaults to rail (not persisted)
    const STORAGE_KEY = 'sidebar-collapsed'
    const readStored = () => {
      try { return localStorage.getItem(STORAGE_KEY) === 'true' } catch (e) { return false }
    }
    const collapsedPref = ref(readStored())
    const tabletExpanded = ref(false)
    const viewport = ref('desktop')
    const rail = computed(() => {
      if (viewport.value === 'desktop') return collapsedPref.value
      if (viewport.value === 'tablet') return !tabletExpanded.value
      return false
    })
    const toggleRail = () => {
      if (viewport.value === 'desktop') {
        collapsedPref.value = !collapsedPref.value
        try { localStorage.setItem(STORAGE_KEY, String(collapsedPref.value)) } catch (e) { /* ignore */ }
      } else if (viewport.value === 'tablet') {
        tabletExpanded.value = !tabletExpanded.value
      }
    }
    const desktopMq = window.matchMedia('(min-width: 1024px)')
    const tabletMq = window.matchMedia('(min-width: 768px)')
    const updateViewport = () => {
      const next = desktopMq.matches ? 'desktop' : tabletMq.matches ? 'tablet' : 'phone'
      if (next === 'tablet' && viewport.value !== 'tablet') tabletExpanded.value = false
      viewport.value = next
    }
    updateViewport()
    desktopMq.addEventListener('change', updateViewport)
    tabletMq.addEventListener('change', updateViewport)
    onBeforeUnmount(() => {
      desktopMq.removeEventListener('change', updateViewport)
      tabletMq.removeEventListener('change', updateViewport)
    })

    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: ['M4 4h6v6H4z', 'M14 4h6v6h-6z', 'M4 14h6v6H4z', 'M14 14h6v6h-6z'] },
      { to: '/inventory', label: t('nav.inventory'), icon: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'] },
      { to: '/orders', label: t('nav.orders'), icon: ['M9 3h6v4H9z', 'M9 5H6a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-3', 'M9 12h6', 'M9 16h4'] },
      { to: '/spending', label: t('nav.finance'), icon: ['M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z', 'M14.5 9.5C14 8.5 13 8 12 8c-1.4 0-2.5.8-2.5 2s1.1 1.7 2.5 2 2.5.8 2.5 2-1.1 2-2.5 2c-1 0-2-.5-2.5-1.5', 'M12 6v2', 'M12 16v2'] },
      { to: '/demand', label: t('nav.demandForecast'), icon: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'] },
      { to: '/restocking', label: t('nav.restocking'), icon: ['M20 11a8 8 0 0 0-14.5-4.5L4 8', 'M4 4v4h4', 'M4 13a8 8 0 0 0 14.5 4.5L20 16', 'M20 20v-4h-4'] },
      { to: '/reports', label: 'Reports', icon: ['M6 4a1 1 0 0 1 1-1h7l4 4v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1z', 'M14 3v4h4', 'M9 13h6', 'M9 17h6'] }
    ])

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
      drawerOpen,
      closeDrawer,
      rail,
      toggleRail,
      navItems,
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
  --color-ink: #0f172a;
  --color-muted: #64748b;
  --color-border: #e2e8f0;
  --color-bg: #f8fafc;
  --color-accent: #2563eb;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --font-title: 24px;
  --font-heading: 16px;
  --font-body: 14px;
  --font-caption: 12px;
  --sidebar-width: 240px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-size: var(--font-body);
  background: var(--color-bg);
  color: var(--color-ink);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.app {
  --rail-width: 64px;
  display: grid;
  grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
  min-height: 100vh;
  transition: grid-template-columns 0.2s ease;
}

.app.rail {
  grid-template-columns: var(--rail-width) minmax(0, 1fr);
}

.sidebar {
  background: var(--color-ink);
  color: #e2e8f0;
  height: 100vh;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: var(--space-5) var(--space-4);
  border-bottom: 1px solid rgba(226, 232, 240, 0.12);
}

.brand-name {
  font-size: var(--font-heading);
  font-weight: 600;
  color: #ffffff;
  letter-spacing: -0.01em;
}

.brand-subtitle {
  display: block;
  margin-top: var(--space-1);
  font-size: var(--font-caption);
  color: #94a3b8;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
}

.brand-text {
  min-width: 0;
}

.collapse-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  background: transparent;
  border: 1px solid rgba(226, 232, 240, 0.18);
  border-radius: 6px;
  color: #cbd5e1;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.collapse-toggle:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  flex-shrink: 0;
  margin-right: var(--space-3);
}

.nav-label {
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 40px;
  padding: var(--space-2) var(--space-3) var(--space-2) var(--space-4);
  color: #cbd5e1;
  text-decoration: none;
  font-size: var(--font-body);
  font-weight: 500;
  border-radius: 6px;
  transition: background 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.nav-item.active {
  background: rgba(37, 99, 235, 0.18);
  color: #ffffff;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: var(--space-2);
  bottom: var(--space-2);
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: #3b82f6;
}

.sidebar .nav-item:focus-visible,
.sidebar button:focus-visible {
  outline-color: #93c5fd;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid rgba(226, 232, 240, 0.12);
}

/* Icon rail mode (desktop and tablet only; never set on phones) */
.app.rail .sidebar {
  overflow: visible;
}

.app.rail .brand {
  justify-content: center;
  padding: var(--space-5) var(--space-2);
}

.app.rail .brand-text {
  display: none;
}

.app.rail .sidebar-nav,
.app.rail .sidebar-footer {
  padding-left: var(--space-2);
  padding-right: var(--space-2);
}

.app.rail .nav-item {
  justify-content: center;
  padding: var(--space-2);
}

.app.rail .nav-icon {
  margin-right: 0;
}

/* Visually hidden but kept in the accessibility tree */
.app.rail .nav-label,
.app.rail .language-label,
.app.rail .profile-name {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.app.rail .chevron {
  display: none;
}

.app.rail .language-button,
.app.rail .profile-button {
  justify-content: center;
  padding-left: 0;
  padding-right: 0;
}

.app.rail .language-button {
  height: 40px;
}

.app.rail .profile-button {
  gap: 0;
}

.app.rail .language-switcher .dropdown-menu,
.app.rail .profile-menu .dropdown-menu {
  left: calc(100% + var(--space-2));
  right: auto;
  bottom: 0;
  min-width: 180px;
}

.app.rail .profile-menu .dropdown-menu {
  min-width: 264px;
}

.app.rail .nav-item::after {
  content: attr(title);
  position: absolute;
  left: calc(100% + var(--space-2));
  top: 50%;
  transform: translateY(-50%);
  padding: var(--space-1) var(--space-2);
  background: var(--color-ink);
  color: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.18);
  border-radius: 6px;
  font-size: var(--font-caption);
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  z-index: 300;
}

.app.rail .nav-item:hover::after,
.app.rail .nav-item:focus-visible::after {
  opacity: 1;
  visibility: visible;
}

.workspace {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 56px;
  padding: var(--space-2) var(--space-5);
  background: #ffffff;
  border-bottom: 1px solid var(--color-border);
}

.menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  background: #ffffff;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-ink);
  cursor: pointer;
}

.menu-button:hover {
  background: var(--color-bg);
}

.sidebar-backdrop {
  display: none;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: var(--space-5);
}

@media (prefers-reduced-motion: reduce) {
  .app,
  .nav-item,
  .collapse-toggle {
    transition: none;
  }
}

@media (max-width: 767px) {
  .app {
    grid-template-columns: minmax(0, 1fr);
  }

  .collapse-toggle {
    display: none;
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: var(--sidebar-width);
    max-width: 85vw;
    z-index: 200;
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform 0.2s ease, visibility 0.2s;
  }

  .app.drawer-open .sidebar {
    transform: translateX(0);
    visibility: visible;
  }

  .app.drawer-open .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 150;
    background: rgba(15, 23, 42, 0.5);
  }

  .menu-button {
    display: inline-flex;
  }

  .topbar {
    padding: var(--space-2) var(--space-4);
  }

  .main-content {
    padding: var(--space-4);
  }
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.stat-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: #0f172a;
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
  color: #2563eb;
}

.card {
  background: white;
  border-radius: 10px;
  padding: 1.25rem;
  border: 1px solid #e2e8f0;
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
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
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
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
  background: #f8fafc;
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
  color: #64748b;
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
