<template>
  <div class="app" :class="{ 'sidebar-collapsed': collapsed }">
    <!-- Slim top bar, only visible below 768px; hosts the drawer toggle -->
    <header class="mobile-bar">
      <button
        class="icon-button"
        type="button"
        :aria-label="t('nav.openNavigation')"
        :aria-expanded="drawerOpen ? 'true' : 'false'"
        aria-controls="app-sidebar"
        @click="drawerOpen = !drawerOpen"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <span class="mobile-brand">{{ t('nav.companyName') }}</span>
    </header>

    <div v-if="drawerOpen" class="backdrop" @click="drawerOpen = false"></div>

    <aside id="app-sidebar" class="sidebar" :class="{ open: drawerOpen }">
      <div class="sidebar-brand">
        <span v-if="collapsed" class="brand-mark" aria-hidden="true">{{ brandMark }}</span>
        <h1 class="brand-name" :class="{ 'visually-hidden': collapsed }">{{ t('nav.companyName') }}</h1>
        <span class="brand-subtitle" :class="{ 'visually-hidden': collapsed }">{{ t('nav.subtitle') }}</span>
      </div>

      <nav class="sidebar-nav" aria-label="Main">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
          :aria-current="$route.path === item.path ? 'page' : undefined"
          :title="collapsed ? t(item.labelKey) : undefined"
        >
          <svg class="nav-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path :d="item.icon" />
          </svg>
          <span :class="{ 'visually-hidden': collapsed }">{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>

      <div class="sidebar-toggle-row">
        <button
          class="sidebar-toggle"
          type="button"
          :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          :title="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          :aria-expanded="collapsed ? 'false' : 'true'"
          aria-controls="app-sidebar"
          @click="toggleSidebar"
        >
          <svg class="toggle-chevron" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M15 6l-6 6 6 6" />
          </svg>
        </button>
      </div>

      <div class="sidebar-footer">
        <LanguageSwitcher :compact="collapsed" />
        <ProfileMenu
          :compact="collapsed"
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content-column">
      <div class="content-inner">
        <FilterBar />
        <main class="main-content">
          <router-view />
        </main>
      </div>
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
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
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

    // Close the mobile drawer after navigating; otherwise it keeps covering the new page.
    watch(() => route.path, () => { drawerOpen.value = false })

    // Sidebar collapse. userCollapsed: null = no manual choice, follow the auto rule.
    const STORAGE_KEY = 'inventory.sidebarCollapsed'
    const readStored = () => {
      // localStorage can throw (private mode, blocked storage); fall back to auto behavior.
      try {
        const v = window.localStorage.getItem(STORAGE_KEY)
        return v === 'true' ? true : v === 'false' ? false : null
      } catch (e) {
        return null
      }
    }
    const userCollapsed = ref(readStored())
    const hasMQ = typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    const narrowQuery = hasMQ ? window.matchMedia('(max-width: 1024px)') : null
    const drawerQuery = hasMQ ? window.matchMedia('(max-width: 768px)') : null
    const autoCollapsed = ref(narrowQuery ? narrowQuery.matches : false)
    const isDrawerMode = ref(drawerQuery ? drawerQuery.matches : false)
    const onNarrowChange = (e) => { autoCollapsed.value = e.matches }
    const onDrawerChange = (e) => { isDrawerMode.value = e.matches }
    if (narrowQuery) narrowQuery.addEventListener('change', onNarrowChange)
    if (drawerQuery) drawerQuery.addEventListener('change', onDrawerChange)
    onUnmounted(() => {
      if (narrowQuery) narrowQuery.removeEventListener('change', onNarrowChange)
      if (drawerQuery) drawerQuery.removeEventListener('change', onDrawerChange)
    })

    // Off-canvas drawer (<= 768px) always shows the full sidebar, so the collapsed state is ignored there.
    // Between 769px and 1024px the rail is the default unless the user chose otherwise.
    const collapsed = computed(() => {
      if (isDrawerMode.value) return false
      return userCollapsed.value !== null ? userCollapsed.value : autoCollapsed.value
    })

    const toggleSidebar = () => {
      userCollapsed.value = !collapsed.value
      try {
        window.localStorage.setItem(STORAGE_KEY, String(userCollapsed.value))
      } catch (e) {
        // Storage unavailable: the choice still applies for this session.
      }
    }

    // Compact brand mark: initials of up to two words, or the first character for unspaced names (e.g. Japanese).
    const brandMark = computed(() => {
      const words = t('nav.companyName').trim().split(/\s+/).filter(Boolean)
      if (words.length > 1) return words.slice(0, 2).map(w => Array.from(w)[0]).join('').toUpperCase()
      return (Array.from(words[0] || '')[0] || '').toUpperCase()
    })

    // Icons are single SVG path strings so all share one stroke style.
    const navItems = [
      { path: '/', labelKey: 'nav.overview', icon: 'M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z' },
      { path: '/inventory', labelKey: 'nav.inventory', icon: 'M21 8l-9-5-9 5v8l9 5 9-5zM3 8l9 5 9-5M12 13v8' },
      { path: '/orders', labelKey: 'nav.orders', icon: 'M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01' },
      { path: '/spending', labelKey: 'nav.finance', icon: 'M12 2v20M17 6H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6' },
      { path: '/demand', labelKey: 'nav.demandForecast', icon: 'M3 17l6-6 4 4 8-8M15 7h6v6' },
      { path: '/reports', labelKey: 'nav.reports', icon: 'M14 3H6a1 1 0 00-1 1v16a1 1 0 001 1h12a1 1 0 001-1V8zM14 3v5h5M9 13h6M9 17h6' }
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
      drawerOpen,
      collapsed,
      brandMark,
      toggleSidebar,
      navItems,
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
  /* Spacing: 4px base. Only these values appear in padding, margin and gap. */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* Type */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  --text-xs: 12px;
  --text-sm: 13px;
  --text-base: 14px;
  --text-md: 16px;
  --text-lg: 20px;
  --text-xl: 24px;
  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;

  /* Shape */
  --radius-control: 6px;
  --radius-card: 10px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  /* Color: surfaces and text (current app values) */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #1e293b;
  --color-heading: #0f172a;
  --color-text-muted: #64748b;
  --color-hover: #f1f5f9;

  /* Color: accent */
  --color-accent: #2563eb;
  --color-accent-tint: #eff6ff;
  --focus-ring: 0 0 0 3px rgba(37, 99, 235, 0.25);

  /* Color: status (text/value color, tinted background, darker badge text) */
  --color-success: #059669;
  --color-success-tint: #d1fae5;
  --color-success-text: #065f46;
  --color-info: #2563eb;
  --color-info-tint: #dbeafe;
  --color-info-text: #1e40af;
  --color-warning: #ea580c;
  --color-warning-tint: #fed7aa;
  --color-warning-text: #92400e;
  --color-danger: #dc2626;
  --color-danger-tint: #fecaca;
  --color-danger-text: #991b1b;

  /* Layout */
  --sidebar-width: 240px;
  --sidebar-width-collapsed: 72px;
  --content-max: 1280px;
  --control-height: 36px;
  --mobile-bar-height: 56px;
}

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
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* ---------- Shell ---------- */
.app {
  min-height: 100vh;
}

/* Overriding the token on the root lets the sidebar, content margin and any other consumer follow. */
.app.sidebar-collapsed {
  --sidebar-width: var(--sidebar-width-collapsed);
}

/* Hidden visually but still read by assistive tech. */
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: 100; /* below dropdowns/modals (1000+) */
  transition: width 0.2s ease;
}

.sidebar-brand {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-6) var(--space-4) var(--space-4);
}

.brand-name {
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  color: var(--color-heading);
  letter-spacing: -0.025em;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  margin: 0 auto;
  border-radius: var(--radius-card);
  background: var(--color-heading);
  color: var(--color-surface);
  font-size: var(--text-base);
  font-weight: var(--weight-bold);
  letter-spacing: 0.025em;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--control-height);
  padding: 0 var(--space-3);
  border-radius: var(--radius-control);
  color: var(--color-text-muted);
  font-weight: var(--weight-medium);
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-item:hover {
  background: var(--color-hover);
  color: var(--color-heading);
}

.nav-item.active {
  background: var(--color-accent-tint);
  color: var(--color-accent);
}

.nav-icon {
  flex-shrink: 0;
}

.sidebar-collapsed .sidebar-brand {
  padding: var(--space-6) var(--space-2) var(--space-4);
}

.sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

/* Stronger active cue in the rail, where there is no label to rely on. */
.sidebar-collapsed .nav-item.active {
  box-shadow: inset 3px 0 0 var(--color-accent);
}

.sidebar-toggle-row {
  display: flex;
  padding: var(--space-2) var(--space-3);
}

.sidebar-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  margin-left: auto;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-control);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.sidebar-toggle:hover {
  background: var(--color-hover);
  color: var(--color-heading);
}

.sidebar-toggle:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
}

.toggle-chevron {
  transition: transform 0.2s ease;
}

.sidebar-collapsed .sidebar-toggle {
  margin: 0 auto;
}

.sidebar-collapsed .toggle-chevron {
  transform: rotate(180deg);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
  /* Visible so the upward dropdowns can extend past the narrow rail; only .sidebar-nav scrolls. */
  overflow: visible;
}

.content-column {
  margin-left: var(--sidebar-width);
  transition: margin-left 0.2s ease;
  min-width: 0;
}

.content-inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8) var(--space-8);
}

.main-content {
  margin-top: var(--space-6);
}

.mobile-bar,
.backdrop {
  display: none;
}

.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-control);
  color: var(--color-heading);
  cursor: pointer;
}

.icon-button:hover {
  background: var(--color-hover);
}

.mobile-brand {
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  color: var(--color-heading);
}

@media (max-width: 768px) {
  .mobile-bar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    height: var(--mobile-bar-height);
    padding: 0 var(--space-4);
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: 90;
  }

  /* Off-canvas drawer. visibility keeps hidden links out of the tab order. */
  .sidebar {
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform 0.2s ease, visibility 0.2s;
    box-shadow: var(--shadow-md);
  }

  .sidebar.open {
    transform: translateX(0);
    visibility: visible;
  }

  .backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: 99;
  }

  .content-column {
    margin-left: 0;
  }

  /* Drawer mode has its own toggle; the collapse control does not apply. */
  .sidebar-toggle-row {
    display: none;
  }

  .content-inner {
    padding: var(--space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .content-column,
  .sidebar-toggle,
  .toggle-chevron,
  .nav-item,
  .stat-card,
  tbody tr {
    transition: none;
  }
}

/* ---------- Shared classes for views ---------- */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-heading);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-card);
  border: 1px solid var(--color-border);
  transition: border-color 0.15s ease;
}

.stat-card:hover {
  border-color: var(--color-border-strong);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-heading);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger .stat-value { color: var(--color-danger); }
.stat-card.info .stat-value { color: var(--color-info); }

.card {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-4);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--text-md);
  font-weight: var(--weight-semibold);
  color: var(--color-heading);
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
  background: var(--color-bg);
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
  padding: var(--space-3);
  border-top: 1px solid var(--color-hover);
  color: var(--color-text);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-bg);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-control);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success,
.badge.increasing {
  background: var(--color-success-tint);
  color: var(--color-success-text);
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-tint);
  color: var(--color-warning-text);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-tint);
  color: var(--color-danger-text);
}

.badge.info,
.badge.low {
  background: var(--color-info-tint);
  color: var(--color-info-text);
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: var(--text-base);
}

.error {
  background: #fef2f2;
  border: 1px solid var(--color-danger-tint);
  color: var(--color-danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-control);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}
</style>
