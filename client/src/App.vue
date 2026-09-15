<template>
  <div class="app-shell" :class="{ 'is-collapsed': sidebarCollapsed }">
    <a class="skip-link" href="#main-content">{{ t('nav.skipToContent') }}</a>
    <AppSidebar
      ref="sidebar"
      :collapsed="sidebarCollapsed"
      :mobile-open="mobileNavOpen"
      @close-mobile="mobileNavOpen = false"
    />

    <div
      class="nav-scrim"
      :class="{ 'is-visible': mobileNavOpen }"
      @click="mobileNavOpen = false"
    ></div>

    <div class="app-main">
      <header class="topbar">
        <div class="topbar-inner">
          <button
            ref="navToggle"
            type="button"
            class="icon-button nav-toggle"
            aria-controls="app-sidebar"
            :aria-expanded="navExpanded"
            :aria-label="toggleLabel"
            :title="toggleLabel"
            @click="toggleNav"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
              <template v-if="isMobile && mobileNavOpen">
                <path d="M18 6L6 18" />
                <path d="M6 6l12 12" />
              </template>
              <template v-else>
                <path d="M3 6h18" />
                <path d="M3 12h18" />
                <path d="M3 18h18" />
              </template>
            </svg>
          </button>

          <nav class="breadcrumb" aria-label="Breadcrumb">
            <span class="breadcrumb-root">{{ t('nav.companyName') }}</span>
            <template v-if="currentPageLabel">
              <span class="breadcrumb-sep" aria-hidden="true">/</span>
              <span class="breadcrumb-current" aria-current="page">{{ currentPageLabel }}</span>
            </template>
          </nav>

          <div class="topbar-actions">
            <LanguageSwitcher />
            <span class="topbar-divider" aria-hidden="true"></span>
            <ProfileMenu
              @show-profile-details="showProfileDetails = true"
              @show-tasks="showTasks = true"
            />
          </div>
        </div>
      </header>

      <FilterBar />

      <main id="main-content" class="main-content">
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
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import AppSidebar from './components/AppSidebar.vue'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

const SIDEBAR_STORAGE_KEY = 'app-sidebar-collapsed'
const MOBILE_BREAKPOINT = '(max-width: 1024px)'

const PAGE_LABEL_KEYS = {
  '/': 'nav.overview',
  '/inventory': 'nav.inventory',
  '/orders': 'nav.orders',
  '/spending': 'nav.finance',
  '/restocking': 'nav.restocking',
  '/demand': 'nav.demandForecast',
  '/reports': 'nav.reports'
}

export default {
  name: 'App',
  components: {
    AppSidebar,
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

    const sidebarCollapsed = ref(
      localStorage.getItem(SIDEBAR_STORAGE_KEY) === 'true'
    )
    const mobileNavOpen = ref(false)
    const navToggle = ref(null)
    const sidebar = ref(null)

    // Tracked reactively so the toggle can describe whichever state it
    // actually controls at the current viewport.
    const isMobile = ref(
      typeof window !== 'undefined' &&
      window.matchMedia(MOBILE_BREAKPOINT).matches
    )

    let mediaQuery = null

    const handleViewportChange = (event) => {
      isMobile.value = event.matches
      if (!event.matches) {
        mobileNavOpen.value = false
      }
    }

    const handleKeydown = (event) => {
      if (event.key === 'Escape' && mobileNavOpen.value) {
        mobileNavOpen.value = false
      }
    }

    const toggleNav = () => {
      if (isMobile.value) {
        mobileNavOpen.value = !mobileNavOpen.value
        return
      }
      sidebarCollapsed.value = !sidebarCollapsed.value
      localStorage.setItem(SIDEBAR_STORAGE_KEY, String(sidebarCollapsed.value))
    }

    // On mobile the button opens/closes a drawer; on desktop it collapses
    // the rail. The label and aria-expanded must follow whichever applies.
    const navExpanded = computed(() =>
      isMobile.value ? mobileNavOpen.value : !sidebarCollapsed.value
    )

    const toggleLabel = computed(() => {
      if (isMobile.value) {
        return mobileNavOpen.value ? t('nav.closeMenu') : t('nav.openMenu')
      }
      return sidebarCollapsed.value ? t('nav.expandSidebar') : t('nav.collapseSidebar')
    })

    const currentPageLabel = computed(() => {
      const key = PAGE_LABEL_KEYS[route.path]
      return key ? t(key) : ''
    })

    // Move focus into the drawer on open and back to the toggle on close —
    // the sidebar precedes the topbar in DOM order, so Tab alone won't reach it.
    watch(mobileNavOpen, async (open) => {
      await nextTick()
      if (open) {
        sidebar.value?.focusFirst?.()
      } else if (isMobile.value) {
        navToggle.value?.focus()
      }
    })

    // Close the mobile drawer whenever navigation happens.
    watch(() => route.path, () => {
      mobileNavOpen.value = false
    })

    onMounted(() => {
      mediaQuery = window.matchMedia(MOBILE_BREAKPOINT)
      isMobile.value = mediaQuery.matches
      mediaQuery.addEventListener('change', handleViewportChange)
      document.addEventListener('keydown', handleKeydown)
    })

    onUnmounted(() => {
      mediaQuery?.removeEventListener('change', handleViewportChange)
      document.removeEventListener('keydown', handleKeydown)
    })

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
      mobileNavOpen,
      isMobile,
      navToggle,
      sidebar,
      toggleNav,
      navExpanded,
      toggleLabel,
      currentPageLabel
    }
  }
}
</script>

<style>
/* Keyboard users would otherwise tab the whole sidebar on every route change. */
.skip-link {
  position: absolute;
  left: 0.5rem;
  top: -3rem;
  z-index: 300;
  padding: 0.5rem 0.875rem;
  background: #ffffff;
  color: #1d4ed8;
  border: 1px solid #1d4ed8;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  text-decoration: none;
  transition: top 0.15s ease;
}

.skip-link:focus {
  top: 0.5rem;
}

/* ==========================================================================
   Design tokens
   ========================================================================== */

:root {
  /* Spacing scale — 4px base */
  --space-1: 0.25rem;  /*  4px */
  --space-2: 0.5rem;   /*  8px */
  --space-3: 0.75rem;  /* 12px */
  --space-4: 1rem;     /* 16px */
  --space-5: 1.25rem;  /* 20px */
  --space-6: 1.5rem;   /* 24px */
  --space-8: 2rem;     /* 32px */
  --space-10: 2.5rem;  /* 40px */

  /* Shell geometry */
  --sidebar-width: 260px;
  --sidebar-width-collapsed: 72px;
  --topbar-height: 64px;
  --content-max-width: 1600px;

  /* Surfaces & lines */
  --surface: #ffffff;
  --surface-muted: #f8fafc;
  --surface-sunken: #f1f5f9;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;

  /* Text */
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #64748b;

  /* Accent */
  --accent: #2563eb;
  --accent-strong: #1d4ed8;
  --accent-soft: #eff6ff;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 999px;

  /* Elevation */
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 12px 32px rgba(15, 23, 42, 0.12);

  --transition: 180ms cubic-bezier(0.4, 0, 0.2, 1);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--surface-muted);
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ==========================================================================
   App shell — fixed left sidebar + offset content column
   ========================================================================== */

.app-shell {
  --shell-sidebar-width: var(--sidebar-width);
  min-height: 100vh;
}

.app-shell.is-collapsed {
  --shell-sidebar-width: var(--sidebar-width-collapsed);
}

.app-main {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin-left: var(--shell-sidebar-width);
  transition: margin-left var(--transition);
}

.nav-scrim {
  position: fixed;
  inset: 0;
  z-index: 150;
  background: rgba(15, 23, 42, 0.45);
  opacity: 0;
  visibility: hidden;
  transition: opacity var(--transition), visibility var(--transition);
}

/* ==========================================================================
   Topbar
   ========================================================================== */

/* Above .nav-scrim (150) so the toggle stays clickable while the mobile
   drawer is open; the sidebar itself (200) still sits above both. */
.topbar {
  position: sticky;
  top: 0;
  z-index: 160;
  height: var(--topbar-height);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar-inner {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: 0 var(--space-8);
}

.icon-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  padding: 0;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  cursor: pointer;
  transition: background var(--transition), color var(--transition), border-color var(--transition);
}

.icon-button:hover {
  background: var(--surface-sunken);
  color: var(--text-primary);
}

.icon-button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.icon-button svg {
  width: 20px;
  height: 20px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  font-size: 0.875rem;
}

.breadcrumb-root {
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.breadcrumb-sep {
  color: var(--border-strong);
}

.breadcrumb-current {
  color: var(--text-primary);
  font-weight: 600;
  white-space: nowrap;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
}

.topbar-divider {
  width: 1px;
  height: 24px;
  background: var(--border);
}

/* ==========================================================================
   Content
   ========================================================================== */

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--space-8);
}

.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-5);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-xs);
  transition: border-color var(--transition), box-shadow var(--transition);
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-sm);
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.03em;
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
  color: var(--accent);
}

.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-xs);
  margin-bottom: var(--space-5);
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
  font-size: 1.063rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-muted);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-2) var(--space-3);
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-2) var(--space-3);
  border-top: 1px solid var(--surface-sunken);
  color: #334155;
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--surface-muted);
}

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
  padding: var(--space-10);
  color: var(--text-muted);
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: 0.938rem;
}

/* ==========================================================================
   Responsive
   ========================================================================== */

@media (max-width: 1024px) {
  .app-main {
    margin-left: 0;
  }

  .nav-scrim.is-visible {
    opacity: 1;
    visibility: visible;
  }
}

@media (max-width: 768px) {
  .topbar-inner {
    padding: 0 var(--space-4);
  }

  .breadcrumb-root,
  .breadcrumb-sep {
    display: none;
  }

  .main-content {
    padding: var(--space-5) var(--space-4);
  }
}
</style>
