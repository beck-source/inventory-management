<template>
  <div class="app">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="sidebar-brand">
        <div class="sidebar-brand-text">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <!-- Manual toggle only makes sense above the 1024px breakpoint; below it,
             collapse is forced by isNarrow so the button would be a no-op -->
        <button
          v-if="!isNarrow"
          class="sidebar-toggle"
          type="button"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="!collapsed"
          @click="toggleSidebar"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <path
              v-if="collapsed"
              d="M6.5 4L11.5 9L6.5 14"
              stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"
            />
            <path
              v-else
              d="M11.5 4L6.5 9L11.5 14"
              stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"
            />
          </svg>
        </button>
      </div>

      <nav class="sidebar-nav">
        <!-- aria-current announces the active route to assistive tech; :class binding unchanged.
             :title / :aria-label expose the label via native tooltip + a11y tree when collapsed. -->
        <router-link to="/" :class="{ active: $route.path === '/' }"
                     :aria-current="$route.path === '/' ? 'page' : null"
                     :title="t('nav.overview')" :aria-label="t('nav.overview')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <rect x="3" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="11" y="3" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="3" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <rect x="11" y="11" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span class="label">{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }"
                     :aria-current="$route.path === '/inventory' ? 'page' : null"
                     :title="t('nav.inventory')" :aria-label="t('nav.inventory')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M3 6.5L10 3L17 6.5L10 10L3 6.5Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M3 6.5V13.5L10 17L17 13.5V6.5" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            <path d="M10 10V17" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span class="label">{{ t('nav.inventory') }}</span>
        </router-link>
        <router-link to="/orders" :class="{ active: $route.path === '/orders' }"
                     :aria-current="$route.path === '/orders' ? 'page' : null"
                     :title="t('nav.orders')" :aria-label="t('nav.orders')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <rect x="5" y="3" width="10" height="14" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M7.5 3V2.5C7.5 2 8 1.5 8.5 1.5H11.5C12 1.5 12.5 2 12.5 2.5V3" stroke="currentColor" stroke-width="1.5"/>
            <path d="M7.5 9H12.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M7.5 12H12.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="label">{{ t('nav.orders') }}</span>
        </router-link>
        <router-link to="/spending" :class="{ active: $route.path === '/spending' }"
                     :aria-current="$route.path === '/spending' ? 'page' : null"
                     :title="t('nav.finance')" :aria-label="t('nav.finance')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M10 2.5V17.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M13.5 5.5H8.5C7.4 5.5 6.5 6.4 6.5 7.5C6.5 8.6 7.4 9.5 8.5 9.5H11.5C12.6 9.5 13.5 10.4 13.5 11.5C13.5 12.6 12.6 13.5 11.5 13.5H6.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="label">{{ t('nav.finance') }}</span>
        </router-link>
        <router-link to="/demand" :class="{ active: $route.path === '/demand' }"
                     :aria-current="$route.path === '/demand' ? 'page' : null"
                     :title="t('nav.demandForecast')" :aria-label="t('nav.demandForecast')">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M3 14L7.5 9.5L11 12.5L17 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M12.5 6H17V10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="label">{{ t('nav.demandForecast') }}</span>
        </router-link>
        <router-link to="/reports" :class="{ active: $route.path === '/reports' }"
                     :aria-current="$route.path === '/reports' ? 'page' : null"
                     title="Reports" aria-label="Reports">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <rect x="3" y="10" width="3.5" height="7" rx="0.5" stroke="currentColor" stroke-width="1.5"/>
            <rect x="8.25" y="6" width="3.5" height="11" rx="0.5" stroke="currentColor" stroke-width="1.5"/>
            <rect x="13.5" y="3" width="3.5" height="14" rx="0.5" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span class="label">Reports</span>
        </router-link>
      </nav>

      <!-- Footer dropdowns (LanguageSwitcher, ProfileMenu) open upward - see their scoped styles -->
      <div class="sidebar-footer">
        <LanguageSwitcher :collapsed="collapsed" />
        <ProfileMenu
          :collapsed="collapsed"
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </aside>

    <div class="main">
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <!-- Modals stay mounted at .app root so they layer above the sidebar via --z-modal -->
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
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
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

    // Sidebar collapse state.
    // `collapsed` is deliberately ONE derived boolean (userCollapsed || isNarrow) rather
    // than two independent flags, so every consumer (CSS via .collapsed class, and the
    // `collapsed` prop passed to LanguageSwitcher/ProfileMenu) reacts identically whether
    // the user manually toggled the rail or the viewport shrank below 1024px. This avoids
    // divergent styling/prop states between "manually collapsed" and "forced narrow".
    const userCollapsed = ref(localStorage.getItem('sidebarCollapsed') === 'true')
    const narrowQuery = window.matchMedia('(max-width: 1024px)')
    const isNarrow = ref(narrowQuery.matches)
    const collapsed = computed(() => userCollapsed.value || isNarrow.value)

    const handleNarrowChange = (e) => {
      isNarrow.value = e.matches
    }

    const toggleSidebar = () => {
      userCollapsed.value = !userCollapsed.value
      localStorage.setItem('sidebarCollapsed', String(userCollapsed.value))
    }

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

    onMounted(() => {
      loadTasks()
      narrowQuery.addEventListener('change', handleNarrowChange)
    })

    onBeforeUnmount(() => {
      narrowQuery.removeEventListener('change', handleNarrowChange)
    })

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      collapsed,
      toggleSidebar,
      isNarrow
    }
  }
}
</script>

<style>
/* ==== Design tokens ====
   Single source of truth for color/spacing/radius/shadow/z-index. Palette values are
   lifted 1:1 from the previous hardcoded literals below - no new colors introduced. */
:root {
  /* ---- Neutrals (slate) ---- */
  --color-bg:            #f8fafc;  /* app background, subtle surfaces */
  --color-surface:       #ffffff;  /* cards, sidebar, nav */
  --color-border:        #e2e8f0;  /* default borders / dividers */
  --color-border-strong: #cbd5e1;  /* hover borders */
  --color-text:          #334155;  /* body text */
  --color-text-strong:   #0f172a;  /* headings */
  --color-text-muted:    #64748b;  /* secondary / labels */
  --color-text-subtle:   #475569;  /* table headers */

  /* ---- Brand ---- */
  --color-primary:       #2563eb;
  --color-primary-dark:  #1e40af;
  --color-primary-soft:  #eff6ff;  /* active nav background */
  --color-focus-ring:    rgba(59, 130, 246, 0.1);

  /* ---- Semantic (text on tinted bg) ---- */
  --color-success:     #059669;  --color-success-bg:  #d1fae5;  --color-success-ink: #065f46;
  --color-warning:     #ea580c;  --color-warning-bg:  #fed7aa;  --color-warning-ink: #92400e;
  --color-danger:      #dc2626;  --color-danger-bg:   #fecaca;  --color-danger-ink:  #991b1b;
  --color-info:        #2563eb;  --color-info-bg:     #dbeafe;  --color-info-ink:    #1e40af;

  /* ---- Spacing scale (4px base, 8px rhythm) ---- */
  --space-1: 0.25rem;  /*  4px */
  --space-2: 0.5rem;   /*  8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-12: 3rem;    /* 48px */

  /* ---- Radius ---- */
  --radius-sm: 6px;    /* buttons, inputs, badges */
  --radius-md: 10px;   /* cards, panels */
  --radius-full: 9999px;

  /* ---- Shadows ---- */
  --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 25px rgba(0, 0, 0, 0.1);

  /* ---- Typography ---- */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
               Ubuntu, Cantarell, sans-serif;

  /* ---- Layout ---- */
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 68px;
  --content-max: 1440px;

  /* ---- Z-index scale ---- */
  --z-sidebar: 50;
  --z-filterbar: 40;
  --z-dropdown: 200;
  --z-modal: 1000;
}

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

.app {
  display: flex;
  min-height: 100vh;
}

/* ---- Sidebar ---- */
.sidebar {
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
  width: var(--sidebar-width);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: var(--z-sidebar);
  transition: width 0.2s ease;
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar-brand {
  padding: var(--space-6) var(--space-5);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.sidebar-brand-text {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
  overflow: hidden;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-left: auto;
  flex-shrink: 0;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.sidebar-toggle:hover {
  background: var(--color-bg);
  color: var(--color-text-strong);
  border-color: var(--color-border-strong);
}

.sidebar-toggle:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Collapsed rail: hide brand text, center the toggle */
.sidebar.collapsed .sidebar-brand {
  padding: var(--space-6) var(--space-3);
  justify-content: center;
}

.sidebar.collapsed .sidebar-brand-text {
  display: none;
}

.sidebar-brand h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-strong);
  letter-spacing: -0.025em;
}

.sidebar-brand .subtitle {
  display: block;
  font-size: 0.813rem;
  color: var(--color-text-muted);
  font-weight: 400;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
  flex: 1;
  overflow-y: auto;
}

.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  transition: all 0.15s ease;
}

.sidebar-nav a:hover {
  color: var(--color-text-strong);
  background: var(--color-bg);
}

.sidebar-nav a.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
  font-weight: 600;
}

.nav-icon {
  flex-shrink: 0;
}

/* Collapsed rail: hide text labels, center icons, keep tap target size */
.sidebar.collapsed .sidebar-nav a {
  justify-content: center;
  padding: var(--space-3);
}

.sidebar.collapsed .sidebar-nav .label {
  display: none;
}

.sidebar-nav a:focus-visible,
.sidebar-footer button:focus-visible,
.reset-filters-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid var(--color-border);
}

.sidebar.collapsed .sidebar-footer {
  align-items: center;
}

/* ---- Main column ---- */
.main {
  flex: 1;
  min-width: 0;              /* prevents flex overflow of wide tables */
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text-strong);
  margin-bottom: var(--space-2);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
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
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--color-text-strong);
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

.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text-strong);
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
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: var(--color-text-subtle);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--color-border);
  color: var(--color-text);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-bg);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--color-success-bg);
  color: var(--color-success-ink);
}

.badge.warning {
  background: var(--color-warning-bg);
  color: var(--color-warning-ink);
}

.badge.danger {
  background: var(--color-danger-bg);
  color: var(--color-danger-ink);
}

.badge.info {
  background: var(--color-info-bg);
  color: var(--color-info-ink);
}

.badge.increasing {
  background: var(--color-success-bg);
  color: var(--color-success-ink);
}

.badge.decreasing {
  background: var(--color-danger-bg);
  color: var(--color-danger-ink);
}

.badge.stable {
  background: #e0e7ff;
  color: #3730a3;
}

.badge.high {
  background: var(--color-danger-bg);
  color: var(--color-danger-ink);
}

.badge.medium {
  background: var(--color-warning-bg);
  color: var(--color-warning-ink);
}

.badge.low {
  background: var(--color-info-bg);
  color: var(--color-info-ink);
}

.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid var(--color-danger-bg);
  color: var(--color-danger-ink);
  padding: var(--space-4);
  border-radius: var(--radius-sm);
  margin: var(--space-4) 0;
  font-size: 0.938rem;
}
</style>
