<template>
  <div class="app" :class="{ 'is-collapsed': isCollapsed, 'drawer-open': isDrawerOpen }">
    <aside id="app-sidebar" class="sidebar">
      <div class="brand">
        <!-- Monogram stays visible in the icon rail, where the brand text is hidden. -->
        <span class="brand-mark" aria-hidden="true">{{ t('nav.companyName').charAt(0) }}</span>
        <div class="brand-text">
          <h1 class="brand-name">{{ t('nav.companyName') }}</h1>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <!--
          "/" is a prefix of every route, so its non-exact "active" state must not
          highlight it: active-class is empty for "/" and only exact-active-class
          applies. All other routes are flat, so exact and non-exact match together.
        -->
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-link"
          :title="item.label"
          :active-class="item.exact ? '' : 'active'"
          exact-active-class="active"
        >
          <svg
            class="nav-icon"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path v-for="d in item.icon" :key="d" :d="d" />
          </svg>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <button
        type="button"
        class="collapse-toggle"
        :aria-label="isCollapsed ? t('nav.expand') : t('nav.collapse')"
        :title="isCollapsed ? t('nav.expand') : t('nav.collapse')"
        :aria-expanded="!isCollapsed"
        @click="toggleCollapse"
      >
        <svg
          class="collapse-icon"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M15 18l-6-6 6-6" />
        </svg>
        <span class="nav-label">{{ isCollapsed ? t('nav.expand') : t('nav.collapse') }}</span>
      </button>
    </aside>

    <div v-if="isDrawerOpen" class="drawer-backdrop" @click="closeDrawer"></div>

    <div class="app-main">
      <header class="topbar">
        <div class="topbar-left">
          <button
            type="button"
            class="menu-button"
            :aria-label="t('nav.menu')"
            :title="t('nav.menu')"
            aria-controls="app-sidebar"
            :aria-expanded="isDrawerOpen"
            @click="openDrawer"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M4 6h16" />
              <path d="M4 12h16" />
              <path d="M4 18h16" />
            </svg>
          </button>
          <h2 class="page-title">{{ pageTitle }}</h2>
        </div>
        <div class="topbar-actions">
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
    const route = useRoute()
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

    // --- Sidebar state ---
    // localStorage can throw (private windows, blocked site data), so every
    // access is wrapped; without storage the sidebar just starts expanded and
    // the preference isn't remembered.
    const readCollapsed = () => {
      try {
        return localStorage.getItem('sidebar-collapsed') === 'true'
      } catch (err) {
        return false
      }
    }
    const isCollapsed = ref(readCollapsed())

    // Mobile drawer. The collapsed (icon-only) state is desktop-only: the CSS
    // ignores it below 900px so the drawer always shows full labels.
    const isDrawerOpen = ref(false)

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      try {
        localStorage.setItem('sidebar-collapsed', String(isCollapsed.value))
      } catch (err) {
        // Not persisted; the in-memory state still works for this session.
      }
    }
    const openDrawer = () => { isDrawerOpen.value = true }
    const closeDrawer = () => { isDrawerOpen.value = false }

    // Nav definition. `icon` is a list of SVG path strings (24x24, stroked).
    // Only "/" needs `exact`, because every route path starts with "/".
    const navDefs = [
      { path: '/', key: 'nav.overview', exact: true, icon: ['M3 3h7v9H3z', 'M14 3h7v5h-7z', 'M14 12h7v9h-7z', 'M3 16h7v5H3z'] },
      { path: '/inventory', key: 'nav.inventory', icon: ['M21 8l-9-5-9 5v8l9 5 9-5V8z', 'M3 8l9 5 9-5', 'M12 13v8'] },
      { path: '/orders', key: 'nav.orders', icon: ['M16 5h2a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h2', 'M9 3h6v4H9z', 'M9 12h6', 'M9 16h4'] },
      { path: '/spending', key: 'nav.finance', icon: ['M12 3v18', 'M16.5 7.5C16 6.3 14.4 5.5 12 5.5c-2.5 0-4 1-4 2.75s1.5 2.4 4 3 4 1.2 4 3S14.5 17.5 12 17.5c-2.4 0-4-.8-4.5-2'] },
      { path: '/demand', key: 'nav.demandForecast', icon: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'] },
      { path: '/reports', key: 'nav.reports', icon: ['M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z', 'M14 3v5h5', 'M9 13h6', 'M9 17h6'] }
    ]
    // Computed (not a constant) so labels re-translate when the language changes.
    const navItems = computed(() => navDefs.map(def => ({ ...def, label: t(def.key) })))

    // Page title is derived from the route: match the path against the same nav
    // entries (and so the same nav.* label keys) the sidebar uses; unknown
    // routes fall back to Overview.
    const pageTitle = computed(() => {
      const match = navItems.value.find(item => item.path === route.path)
      return (match || navItems.value[0]).label
    })

    // Never leave the drawer open after navigating.
    watch(() => route.path, closeDrawer)

    const onKeydown = (event) => {
      if (event.key === 'Escape') closeDrawer()
    }
    onMounted(() => window.addEventListener('keydown', onKeydown))
    onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      isCollapsed,
      isDrawerOpen,
      toggleCollapse,
      openDrawer,
      closeDrawer,
      navItems,
      pageTitle
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
  background: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---------- App shell ---------- */
.app {
  display: flex;
  min-height: 100vh;
}

.app-main {
  flex: 1;
  /* min-width: 0 lets this flex child shrink below its content width, so wide
     tables scroll inside .table-container instead of widening the page. */
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* ---------- Sidebar ---------- */
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  width: var(--sidebar-w);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  z-index: var(--z-sidebar);
  overflow: hidden;
  transition: width var(--transition-fast);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-5);
  height: var(--topbar-h);
  flex-shrink: 0;
  border-bottom: 1px solid var(--sidebar-divider);
  white-space: nowrap;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

/* Monogram: only shown in the icon rail, where the brand text is hidden. */
.brand-mark {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--sidebar-active-bg);
  color: var(--sidebar-active-text);
  font-weight: 700;
}

.brand-name {
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--sidebar-active-text);
  letter-spacing: -0.025em;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: var(--sidebar-text);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
}

.nav-link,
.collapse-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  font-family: inherit;
  font-size: 0.9375rem;
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.nav-link:hover,
.collapse-toggle:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-hover);
}

.nav-link:focus-visible,
.collapse-toggle:focus-visible,
.menu-button:focus-visible {
  outline: 2px solid var(--sidebar-accent);
  outline-offset: 2px;
}

.nav-link.active {
  background: var(--sidebar-active-bg);
  color: var(--sidebar-active-text);
}

/* 3px accent bar on the left edge of the active link */
.nav-link.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: var(--space-2);
  bottom: var(--space-2);
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--sidebar-accent);
}

.nav-icon,
.collapse-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.collapse-toggle {
  margin: var(--space-3);
  margin-top: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.collapse-icon {
  transition: transform var(--transition-fast);
}

.app.is-collapsed .collapse-icon {
  transform: rotate(180deg);
}

/*
 * Responsive sidebar, three tiers:
 *   >= 1024px     full sidebar with labels; the toggle switches to the icon
 *                 rail (.is-collapsed, persisted in localStorage).
 *   640 - 1023px  always the icon rail, whatever the saved collapsed state,
 *                 and the toggle is hidden (the rail is forced, not a choice).
 *   < 640px       off-canvas drawer with full labels (collapsed state ignored).
 * The rail rules below are therefore wrapped in min-width: 640px so that the
 * drawer never inherits them, and need no "undo" rules.
 */

/* Icon rail, user-chosen (>= 640px; the toggle only exists >= 1024px) */
@media (min-width: 640px) {
  .app.is-collapsed .sidebar {
    width: var(--sidebar-w-collapsed);
  }

  .app.is-collapsed .nav-label,
  .app.is-collapsed .brand-text {
    display: none;
  }

  .app.is-collapsed .brand-mark {
    display: flex;
  }

  .app.is-collapsed .brand {
    justify-content: center;
    padding: 0;
  }

  .app.is-collapsed .nav-link,
  .app.is-collapsed .collapse-toggle {
    justify-content: center;
  }
}

/* Icon rail, forced (640 - 1023px): same look as above, regardless of state */
@media (min-width: 640px) and (max-width: 1023px) {
  .app .sidebar {
    width: var(--sidebar-w-collapsed);
  }

  .app .nav-label,
  .app .brand-text {
    display: none;
  }

  .app .brand-mark {
    display: flex;
  }

  .app .brand {
    justify-content: center;
    padding: 0;
  }

  .app .nav-link,
  .app .collapse-toggle {
    justify-content: center;
  }

  .app .collapse-toggle {
    display: none;
  }
}

/* ---------- Topbar ---------- */
.topbar {
  position: sticky;
  top: 0;
  height: var(--topbar-h);
  z-index: var(--z-topbar);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: 0 var(--space-6);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.topbar-left,
.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.page-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.menu-button {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-muted);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.menu-button:hover {
  background: var(--color-subtle);
  color: var(--color-text);
}

.menu-button svg {
  width: 20px;
  height: 20px;
}

.drawer-backdrop {
  display: none;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-w);
  padding: var(--space-6);
}

/* ---------- Mobile (< 640px): off-canvas drawer ---------- */
@media (max-width: 639px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    /* Drawer is always full width with labels: the collapsed state is ignored
       (the rail rules above only apply from 640px up). z-index stays at
       --z-sidebar, which is above --z-drawer-backdrop. */
    width: var(--sidebar-w);
    transform: translateX(-100%);
    transition: transform var(--transition-fast);
  }

  .app.drawer-open .sidebar {
    transform: translateX(0);
  }

  .collapse-toggle {
    display: none;
  }

  .drawer-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: var(--z-drawer-backdrop);
    background: rgba(15, 23, 42, 0.5);
  }

  .menu-button {
    display: inline-flex;
  }

  .topbar {
    padding: 0 var(--space-4);
  }

  .main-content {
    padding: var(--space-4);
  }
}

/* ---------- Page header ---------- */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-muted);
  font-size: 0.9375rem;
}

/* ---------- Stat cards ---------- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--color-muted);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 2rem;
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
  color: var(--color-primary);
}

/* ---------- Cards ---------- */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1.0625rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

/* ---------- Tables ---------- */
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
  padding: var(--space-3) var(--space-4);
  font-weight: 600;
  color: var(--color-muted);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--color-subtle);
  color: var(--color-text-soft);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--color-bg);
}

/* ---------- Badges ---------- */
.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success,
.badge.increasing {
  background: var(--color-success-soft);
  color: #065f46;
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-soft);
  color: #92400e;
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-soft);
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

/* ---------- States ---------- */
.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-muted);
  font-size: 0.9375rem;
}

.error {
  background: #fef2f2;
  border: 1px solid var(--color-danger-soft);
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: 0.9375rem;
}
</style>
