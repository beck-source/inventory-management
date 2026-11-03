<template>
  <div class="app" :class="{ 'drawer-open': drawerOpen, 'sidebar-collapsed': collapsed }">
    <header class="mobile-bar">
      <button
        type="button"
        class="icon-btn"
        :aria-expanded="drawerOpen"
        aria-controls="app-sidebar"
        :aria-label="t('nav.openMenu')"
        @click="drawerOpen = true"
      >
        <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <span class="brand-name">{{ t('nav.companyName') }}</span>
    </header>

    <div class="backdrop" aria-hidden="true" @click="drawerOpen = false"></div>

    <aside id="app-sidebar" class="sidebar">
      <div class="sidebar-brand">
        <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-sub">{{ t('nav.subtitle') }}</span>
        </div>
        <button
          type="button"
          class="icon-btn drawer-close"
          :aria-label="t('nav.closeMenu')"
          @click="drawerOpen = false"
        >
          <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav" :aria-label="t('nav.primary')">
        <div v-for="group in navGroups" :key="group.key" class="nav-group">
          <div class="nav-group-label">{{ t(group.labelKey) }}</div>
          <router-link
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="nav-link"
            :title="collapsed ? t(item.labelKey) : null"
            :aria-label="t(item.labelKey)"
            :active-class="item.exact ? '' : 'is-active'"
            exact-active-class="is-active"
          >
            <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path v-for="d in item.icon" :key="d" :d="d" />
            </svg>
            <span class="nav-label">{{ t(item.labelKey) }}</span>
          </router-link>
        </div>
      </nav>

      <div class="sidebar-footer">
        <button
          type="button"
          class="nav-link sidebar-toggle"
          :aria-expanded="!collapsed"
          :aria-label="toggleLabel"
          :title="toggleLabel"
          @click="toggleSidebar"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path v-for="d in toggleIcon" :key="d" :d="d" />
          </svg>
          <span class="nav-label">{{ toggleLabel }}</span>
        </button>
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="content">
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
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import { useSidebar } from './composables/useSidebar'
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
    const { collapsed, toggleSidebar } = useSidebar()
    const drawerOpen = ref(false)
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

    const navGroups = [
      {
        key: 'operations',
        labelKey: 'nav.groupOperations',
        items: [
          {
            to: '/',
            labelKey: 'nav.overview',
            exact: true,
            icon: ['M3 3h7v9H3z', 'M14 3h7v5h-7z', 'M14 12h7v9h-7z', 'M3 16h7v5H3z']
          },
          {
            to: '/inventory',
            labelKey: 'nav.inventory',
            icon: [
              'M16.5 9.4 7.5 4.21',
              'M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z',
              'm3.3 7 8.7 5 8.7-5',
              'M12 22V12'
            ]
          },
          {
            to: '/orders',
            labelKey: 'nav.orders',
            icon: [
              'M8 2h8v4H8z',
              'M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2',
              'M12 11h4',
              'M12 16h4',
              'M8 11h.01',
              'M8 16h.01'
            ]
          },
          {
            to: '/restocking',
            labelKey: 'nav.restocking',
            icon: [
              'M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8',
              'M21 3v5h-5',
              'M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16',
              'M8 16H3v5'
            ]
          }
        ]
      },
      {
        key: 'insights',
        labelKey: 'nav.groupInsights',
        items: [
          {
            to: '/spending',
            labelKey: 'nav.finance',
            icon: ['M12 2v20', 'M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6']
          },
          {
            to: '/demand',
            labelKey: 'nav.demandForecast',
            icon: ['M22 7 13.5 15.5 8.5 10.5 2 17', 'M16 7h6v6']
          },
          {
            to: '/reports',
            labelKey: 'nav.reports',
            icon: [
              'M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z',
              'M14 2v4a2 2 0 0 0 2 2h4',
              'M10 9H8',
              'M16 13H8',
              'M16 17H8'
            ]
          }
        ]
      }
    ]

    const toggleLabel = computed(() =>
      collapsed.value ? t('nav.expandSidebar') : t('nav.collapseSidebar')
    )
    const toggleIcon = computed(() =>
      collapsed.value
        ? ['m6 17 5-5-5-5', 'm13 17 5-5-5-5']
        : ['m11 17-5-5 5-5', 'm18 17-5-5 5-5']
    )

    const brandInitial = computed(() => t('nav.companyName').charAt(0))

    const onKeydown = (event) => {
      if (event.key === 'Escape') drawerOpen.value = false
    }

    watch(() => route.fullPath, () => {
      drawerOpen.value = false
    })

    onMounted(() => {
      loadTasks()
      window.addEventListener('keydown', onKeydown)
    })

    onUnmounted(() => {
      window.removeEventListener('keydown', onKeydown)
    })

    return {
      t,
      drawerOpen,
      collapsed,
      toggleSidebar,
      toggleLabel,
      toggleIcon,
      navGroups,
      brandInitial,
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
  /* Spacing: 4px base scale */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* Layout */
  --sidebar-width: 256px;
  --sidebar-width-collapsed: 64px;
  --topbar-height: 56px;
  --content-max-width: 1440px;

  /* Surfaces and text */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-muted: #f1f5f9;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-secondary: #475569;
  --color-text-muted: #64748b;

  /* Brand / interactive */
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-primary-soft: #eff6ff;
  --color-focus-ring: rgba(37, 99, 235, 0.4);

  /* Sidebar */
  --sidebar-bg: var(--color-surface);
  --sidebar-border: var(--color-border);
  --sidebar-text: var(--color-text-secondary);
  --sidebar-text-active: var(--color-primary);
  --sidebar-item-hover: var(--color-surface-muted);
  --sidebar-item-active: var(--color-primary-soft);

  /* Semantic status */
  --color-success: #059669;
  --color-success-soft: #d1fae5;
  --color-success-text: #065f46;
  --color-info: #2563eb;
  --color-info-soft: #dbeafe;
  --color-info-text: #1e40af;
  --color-warning: #d97706;
  --color-warning-soft: #fef3c7;
  --color-warning-text: #92400e;
  --color-danger: #dc2626;
  --color-danger-soft: #fee2e2;
  --color-danger-text: #991b1b;

  /* Type */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 2rem;

  /* Shape and depth */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);
  --shadow-overlay: 0 20px 40px rgba(15, 23, 42, 0.18);

  /* Motion */
  --transition-fast: 120ms ease;
  --transition-base: 200ms ease;

  /* Stacking (modals use their own z-index of 1000+ and sit above all of these) */
  --z-sidebar: 100;
  --z-topbar: 90;
  --z-backdrop: 110;
  --z-modal: 200;
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --transition-fast: 0ms;
    --transition-base: 0ms;
  }
}

:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
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

/* App shell */
.app {
  min-height: 100vh;
}

.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  z-index: var(--z-sidebar);
  transition: width var(--transition-base);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-shrink: 0;
  height: var(--topbar-height);
  padding: 0 var(--space-5);
  border-bottom: 1px solid var(--sidebar-border);
}

.brand-mark {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: #fff;
  font-size: var(--text-sm);
  font-weight: 700;
}

.brand-text {
  min-width: 0;
}

.brand-name {
  display: block;
  font-size: var(--text-base);
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: 1.2;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-sub {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-group-label {
  padding: 0 var(--space-3) var(--space-1);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.nav-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--sidebar-text);
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  transition: background var(--transition-fast), color var(--transition-fast);
}

button.nav-link {
  width: 100%;
  border: 0;
  background: transparent;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
}

.nav-link:hover {
  background: var(--sidebar-item-hover);
  color: var(--color-text);
}

.nav-link.is-active {
  background: var(--sidebar-item-active);
  color: var(--sidebar-text-active);
}

.nav-link.is-active::before {
  content: '';
  position: absolute;
  left: calc(var(--space-3) * -1);
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: var(--color-primary);
}

.nav-label {
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-icon,
.icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  flex-shrink: 0;
  padding: var(--space-3);
  border-top: 1px solid var(--sidebar-border);
}

.icon-btn {
  display: inline-grid;
  place-items: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.icon-btn:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.content {
  margin-left: var(--sidebar-width);
  transition: margin-left var(--transition-base);
  min-width: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-8);
}

.mobile-bar,
.backdrop,
.drawer-close {
  display: none;
}

/* Icon-only sidebar (user toggle or narrow viewport default; drawer mode below 768px ignores it) */
@media (min-width: 768px) {
  .sidebar-collapsed .sidebar {
    width: var(--sidebar-width-collapsed);
  }

  .sidebar-collapsed .content {
    margin-left: var(--sidebar-width-collapsed);
  }

  .sidebar-collapsed .brand-text,
  .sidebar-collapsed .nav-label,
  .sidebar-collapsed .nav-group-label {
    display: none;
  }

  .sidebar-collapsed .sidebar-brand {
    justify-content: center;
    padding: 0;
  }

  .sidebar-collapsed .nav-link {
    justify-content: center;
    padding: 0;
  }

  .sidebar-collapsed .nav-group + .nav-group {
    padding-top: var(--space-5);
    border-top: 1px solid var(--color-border);
  }
}

/* Off-canvas drawer */
@media (max-width: 767px) {
  .sidebar {
    width: var(--sidebar-width);
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform var(--transition-base), visibility var(--transition-base);
    z-index: calc(var(--z-backdrop) + 1);
  }

  .brand-text {
    flex: 1;
  }

  .sidebar-brand {
    padding: 0 var(--space-4) 0 var(--space-5);
  }

  .sidebar-toggle {
    display: none;
  }

  .drawer-close {
    display: inline-grid;
  }

  .drawer-open .sidebar {
    transform: none;
    visibility: visible;
    box-shadow: var(--shadow-overlay);
  }

  .drawer-open .backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: var(--z-backdrop);
  }

  .content {
    margin-left: 0;
  }

  .mobile-bar {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    height: var(--topbar-height);
    padding: 0 var(--space-4);
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: var(--z-topbar);
  }

  .main-content {
    padding: var(--space-4);
  }
}

/* Page header */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: -0.02em;
  color: var(--color-text);
  margin-bottom: var(--space-1);
}

.page-header p {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* KPI cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  margin-bottom: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
}

.stat-value {
  font-size: var(--text-3xl);
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
}

.stat-card.success .stat-value {
  color: var(--color-success);
}

.stat-card.warning .stat-value {
  color: var(--color-warning);
}

.stat-card.danger .stat-value {
  color: var(--color-danger);
}

.stat-card.info .stat-value {
  color: var(--color-info);
}

/* Cards */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--color-text);
}

/* Tables */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-variant-numeric: tabular-nums;
}

thead {
  background: var(--color-surface-muted);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
}

td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-surface-muted);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--color-bg);
}

th.num,
td.num,
.text-right {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Badges */
.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
  line-height: 1.25;
  white-space: nowrap;
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
}

.badge.success,
.badge.increasing {
  background: var(--color-success-soft);
  color: var(--color-success-text);
}

.badge.warning,
.badge.medium {
  background: var(--color-warning-soft);
  color: var(--color-warning-text);
}

.badge.danger,
.badge.decreasing,
.badge.high {
  background: var(--color-danger-soft);
  color: var(--color-danger-text);
}

.badge.info,
.badge.low {
  background: var(--color-info-soft);
  color: var(--color-info-text);
}

.badge.stable {
  background: var(--color-surface-muted);
  color: var(--color-text-secondary);
}

/* Buttons */
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
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  line-height: 1;
  white-space: nowrap;
  text-decoration: none;
  cursor: pointer;
  transition: background var(--transition-fast), border-color var(--transition-fast), color var(--transition-fast);
}

.btn:disabled,
.btn-primary:disabled,
.btn-secondary:disabled,
.btn-ghost:disabled,
.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-primary);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-secondary {
  background: var(--color-surface);
  border-color: var(--color-border-strong);
  color: var(--color-text);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-surface-muted);
}

.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.btn-danger {
  background: var(--color-danger);
  color: #fff;
}

.btn-danger:hover:not(:disabled) {
  background: var(--color-danger-text);
}

/* Form controls */
.input {
  height: 36px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  font-family: inherit;
  font-size: var(--text-sm);
  color: var(--color-text);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-focus-ring);
}

.input:disabled {
  background: var(--color-surface-muted);
  cursor: not-allowed;
}

/* States */
.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.error {
  background: var(--color-danger-soft);
  border: 1px solid color-mix(in srgb, var(--color-danger) 30%, transparent);
  color: var(--color-danger-text);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-12) var(--space-6);
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}
</style>
