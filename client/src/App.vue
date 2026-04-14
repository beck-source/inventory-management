<template>
  <!-- .sidebar-collapsed added when sidebar is collapsed; drives grid/transition -->
  <div class="app-shell" :class="{ 'sidebar-collapsed': isCollapsed }">
    <!-- ═══════════════════════════════════════════════════
         SIDEBAR
         ═══════════════════════════════════════════════════ -->
    <aside class="sidebar">
      <!-- Brand + collapse toggle -->
      <div class="sidebar-brand">
        <div class="brand-content">
          <!-- Box icon acts as logo mark -->
          <svg class="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          </svg>
          <div class="brand-text">
            <span class="brand-name">{{ t('nav.companyName') }}</span>
            <span class="brand-sub">{{ t('nav.subtitle') }}</span>
          </div>
        </div>
        <!-- Collapse toggle button -->
        <button
          class="collapse-btn"
          @click="toggleCollapse"
          :title="isCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        >
          <!-- Chevron flips via CSS when collapsed -->
          <svg class="collapse-icon" viewBox="0 0 16 16" fill="none">
            <path d="M10 4L6 8L10 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <router-link
          to="/"
          :class="['nav-item', { active: $route.path === '/' }]"
          :title="isCollapsed ? t('nav.overview') : undefined"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M2 4a2 2 0 012-2h3a2 2 0 012 2v3a2 2 0 01-2 2H4a2 2 0 01-2-2V4zm9 0a2 2 0 012-2h3a2 2 0 012 2v3a2 2 0 01-2 2h-3a2 2 0 01-2-2V4zM2 13a2 2 0 012-2h3a2 2 0 012 2v3a2 2 0 01-2 2H4a2 2 0 01-2-2v-3zm9 0a2 2 0 012-2h3a2 2 0 012 2v3a2 2 0 01-2 2h-3a2 2 0 01-2-2v-3z"/>
          </svg>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>

        <router-link
          to="/inventory"
          :class="['nav-item', { active: $route.path === '/inventory' }]"
          :title="isCollapsed ? t('nav.inventory') : undefined"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4 3a2 2 0 100 4h12a2 2 0 100-4H4z"/>
            <path fill-rule="evenodd" d="M3 8h14v7a2 2 0 01-2 2H5a2 2 0 01-2-2V8zm5 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" clip-rule="evenodd"/>
          </svg>
          <span class="nav-label">{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link
          to="/orders"
          :class="['nav-item', { active: $route.path === '/orders' }]"
          :title="isCollapsed ? t('nav.orders') : undefined"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4zm7 5a1 1 0 10-2 0v1H8a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V9z" clip-rule="evenodd"/>
          </svg>
          <span class="nav-label">{{ t('nav.orders') }}</span>
        </router-link>

        <router-link
          to="/spending"
          :class="['nav-item', { active: $route.path === '/spending' }]"
          :title="isCollapsed ? t('nav.finance') : undefined"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z"/>
            <path fill-rule="evenodd" d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z" clip-rule="evenodd"/>
          </svg>
          <span class="nav-label">{{ t('nav.finance') }}</span>
        </router-link>

        <router-link
          to="/demand"
          :class="['nav-item', { active: $route.path === '/demand' }]"
          :title="isCollapsed ? t('nav.demandForecast') : undefined"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd"/>
          </svg>
          <span class="nav-label">{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link
          to="/reports"
          :class="['nav-item', { active: $route.path === '/reports' }]"
          :title="isCollapsed ? t('nav.reports') : undefined"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm2 10a1 1 0 10-2 0v3a1 1 0 102 0v-3zm2-3a1 1 0 011 1v5a1 1 0 11-2 0v-5a1 1 0 011-1zm4-1a1 1 0 10-2 0v7a1 1 0 102 0V8z" clip-rule="evenodd"/>
          </svg>
          <span class="nav-label">{{ t('nav.reports') }}</span>
        </router-link>

        <router-link
          to="/restocking"
          :class="['nav-item', { active: $route.path === '/restocking' }]"
          :title="isCollapsed ? t('nav.restocking') : undefined"
        >
          <svg class="nav-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd"/>
          </svg>
          <span class="nav-label">{{ t('nav.restocking') }}</span>
        </router-link>
      </nav>

      <!-- Footer: polished profile card + language switcher -->
      <div class="sidebar-footer">
        <!-- Language row: compact globe button -->
        <div class="footer-lang-row">
          <LanguageSwitcher />
        </div>

        <!-- Profile card -->
        <div class="sidebar-profile-card">
          <div class="profile-card-avatar">
            {{ getInitials(currentUser.name) }}
          </div>
          <div class="profile-card-info">
            <div class="profile-card-name">{{ currentUser.name }}</div>
            <div class="profile-card-role">{{ currentUser.jobTitle }}</div>
          </div>
          <!-- Three-dot menu trigger wrapping the existing ProfileMenu dropdown -->
          <div class="profile-card-menu">
            <ProfileMenu
              @show-profile-details="showProfileDetails = true"
              @show-tasks="showTasks = true"
            />
          </div>
        </div>

        <!-- Collapsed state: just avatar centred, opens ProfileMenu on click -->
        <div class="sidebar-profile-collapsed">
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </div>
    </aside>

    <!-- ═══════════════════════════════════════════════════
         MAIN AREA
         ═══════════════════════════════════════════════════ -->
    <div class="main-area">
      <!-- Filter bar sits as a sticky top strip -->
      <div class="content-topbar">
        <FilterBar />
      </div>

      <main class="page-content">
        <router-view />
      </main>
    </div>

    <!-- Modals (unchanged) -->
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

const COLLAPSE_KEY = 'sidebar-collapsed'

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
    const { currentUser, getInitials } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Sidebar collapse state — persisted to localStorage
    const isCollapsed = ref(false)

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      localStorage.setItem(COLLAPSE_KEY, isCollapsed.value ? '1' : '0')
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
      // Restore persisted collapse state
      isCollapsed.value = localStorage.getItem(COLLAPSE_KEY) === '1'
    })

    return {
      t,
      currentUser,
      getInitials,
      isCollapsed,
      toggleCollapse,
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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--surface-bg);
  color: var(--text-primary);
  font-size: var(--text-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:root {
  /* u2500u2500 Layout u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --sidebar-width: 220px;
  --sidebar-width-collapsed: 64px;

  /* u2500u2500 Sidebar (dark variant u2014 default) u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --sidebar-bg: #0f172a;
  --sidebar-text: #94a3b8;
  --sidebar-text-hover: #e2e8f0;
  --sidebar-text-active: #ffffff;
  --sidebar-item-active-bg: rgba(59, 130, 246, 0.15);
  --sidebar-accent: #3b82f6;

  /* u2500u2500 Surface colours u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --surface-bg: #f8fafc;
  --surface-card: #ffffff;
  --surface-border: #e2e8f0;
  --surface-border-strong: #cbd5e1;
  --surface-hover: #f1f5f9;
  --surface-active: #e2e8f0;

  /* u2500u2500 Text u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --text-inverse: #ffffff;

  /* u2500u2500 Brand / accent u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --color-blue: #2563eb;
  --color-blue-bg: #eff6ff;
  --color-blue-border: #bfdbfe;

  /* u2500u2500 Status colours u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --color-success: #059669;
  --color-success-bg: #d1fae5;
  --color-success-text: #065f46;

  --color-warning: #d97706;
  --color-warning-bg: #fef3c7;
  --color-warning-text: #92400e;

  --color-danger: #dc2626;
  --color-danger-bg: #fecaca; /* kept for badge.danger; use --color-danger-surface for large areas */
  --color-danger-surface: #fef2f2;
  --color-danger-text: #991b1b;

  --color-info: #2563eb;
  --color-info-bg: #dbeafe;
  --color-info-text: #1e40af;

  /* u2500u2500 Trend badges u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --color-increasing-bg: #d1fae5;
  --color-increasing-text: #065f46;
  --color-stable-bg: #e0e7ff;
  --color-stable-text: #3730a3;
  --color-decreasing-bg: #fecaca;
  --color-decreasing-text: #991b1b;

  /* u2500u2500 Spacing u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --space-page: 1.75rem;      /* outer padding of .page-content */
  --space-card: 1.25rem;      /* .card internal padding */
  --space-gap: 1.25rem;       /* gaps between cards / grid items */
  --space-section: 1.5rem;    /* margin-bottom between sections */

  /* u2500u2500 Shape u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --radius-card: 10px;
  --radius-badge: 6px;
  --radius-btn: 8px;
  --radius-input: 6px;

  /* u2500u2500 Shadows u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-modal: 0 20px 60px rgba(0, 0, 0, 0.15);

  /* u2500u2500 Typography u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;

  --text-xs: 0.75rem;     /* 12px */
  --text-sm: 0.813rem;    /* 13px */
  --text-base: 0.875rem;  /* 14px  u2190 default body size */
  --text-md: 0.938rem;    /* 15px */
  --text-lg: 1.125rem;    /* 18px */
  --text-xl: 1.375rem;    /* 22px */
  --text-2xl: 1.875rem;   /* 30px */

  /* u2500u2500 Transitions u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
  --transition-fast: 0.15s ease;
  --transition-base: 0.2s ease;
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Shell layout
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.app-shell {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  min-height: 100vh;
  transition: grid-template-columns 0.2s ease;
}

.app-shell.sidebar-collapsed {
  grid-template-columns: var(--sidebar-width-collapsed) 1fr;
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Sidebar
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  border-right: 1px solid rgba(255, 255, 255, 0.04);
  z-index: 50;
}

/* Brand row: logo + name/subtitle + collapse button */
.sidebar-brand {
  padding: 1rem 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  flex-shrink: 0;
}

.brand-content {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  min-width: 0;
  flex: 1;
}

.brand-icon {
  width: 24px;
  height: 24px;
  color: var(--sidebar-accent);
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  min-width: 0;
  /* hide text when collapsed */
  transition: opacity 0.15s ease;
}

.brand-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-sub {
  font-size: 0.688rem;
  color: var(--sidebar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Collapse toggle button */
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: var(--sidebar-text);
  cursor: pointer;
  flex-shrink: 0;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--sidebar-text-hover);
}

.collapse-icon {
  width: 14px;
  height: 14px;
  /* flip chevron direction when expanded (pointing left) vs collapsed (pointing right) */
  transition: transform 0.2s ease;
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Nav items
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.625rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
  white-space: nowrap;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--sidebar-text-hover);
}

.nav-item.active {
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-text-active);
}

.nav-item.active .nav-icon {
  color: var(--sidebar-accent);
  opacity: 1;
}

.nav-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  opacity: 0.8;
}

/* Nav label: hides when collapsed */
.nav-label {
  transition: opacity 0.15s ease;
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Sidebar footer — profile card
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.sidebar-footer {
  padding: 0.75rem 0.625rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex-shrink: 0;
}

/* Language row: compact, shown when expanded */
.footer-lang-row {
  transition: opacity 0.15s ease;
}

/* Profile card: visible when expanded */
.sidebar-profile-card {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 0.5rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 8px;
  transition: background var(--transition-fast), opacity 0.15s ease;
}

.sidebar-profile-card:hover {
  background: rgba(255, 255, 255, 0.07);
}

/* Avatar circle in profile card */
.profile-card-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.7rem;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.profile-card-info {
  flex: 1;
  min-width: 0;
  transition: opacity 0.15s ease;
}

.profile-card-name {
  font-size: 0.813rem;
  font-weight: 600;
  color: var(--sidebar-text-hover);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.profile-card-role {
  font-size: 0.688rem;
  color: var(--sidebar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 0.1rem;
}

/* The three-dot trigger area housing ProfileMenu */
.profile-card-menu {
  flex-shrink: 0;
  transition: opacity 0.15s ease;
}

/* Collapsed-only avatar: hidden when expanded */
.sidebar-profile-collapsed {
  display: none;
  justify-content: center;
  transition: opacity 0.15s ease;
}

/* Style the ProfileMenu button in the card context (dark sidebar) */
.sidebar-profile-card .profile-button,
.sidebar-profile-collapsed .profile-button {
  background: transparent;
  border: none;
  padding: 0.25rem;
  color: var(--sidebar-text);
}

.sidebar-profile-card .profile-button:hover,
.sidebar-profile-collapsed .profile-button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--sidebar-text-hover);
}

/* Hide name+chevron inside profile-card-menu; show only avatar as trigger */
.profile-card-menu .profile-name,
.profile-card-menu .chevron {
  display: none;
}

/* Profile dropdown opens upward so it doesn't clip out of viewport */
.profile-card-menu .dropdown-menu {
  top: auto;
  bottom: calc(100% + 0.5rem);
  right: 0;
  left: auto;
}

/* Collapsed: profile avatar dropdown opens to the right */
.sidebar-profile-collapsed .dropdown-menu {
  top: auto;
  bottom: calc(100% + 0.5rem);
  left: calc(100% + 0.5rem);
  right: auto;
}

/* Force light text on footer language switcher in dark sidebar */
.sidebar-footer .language-switcher .language-button {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: var(--sidebar-text);
  width: 100%;
  justify-content: flex-start;
}

.sidebar-footer .language-switcher .language-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--sidebar-text-hover);
  border-color: rgba(255, 255, 255, 0.15);
}

.sidebar-footer .language-switcher .globe-icon,
.sidebar-footer .language-switcher .chevron {
  color: var(--sidebar-text);
}

/* Language dropdown positions upward in sidebar footer */
.sidebar-footer .language-switcher .dropdown-menu {
  top: auto;
  bottom: calc(100% + 0.5rem);
  left: 0;
  right: auto;
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   COLLAPSED STATE overrides
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */

/* When collapsed: centre brand icon + keep collapse btn visible */
.sidebar-collapsed .sidebar-brand {
  padding: 0.875rem 0.5rem;
  justify-content: center;
  gap: 0.25rem;
}

.sidebar-collapsed .brand-content {
  justify-content: center;
  flex: none;
}

.sidebar-collapsed .brand-text {
  opacity: 0;
  width: 0;
  overflow: hidden;
  /* collapse text width without shifting icon */
}

/* Flip the chevron to point right when collapsed */
.sidebar-collapsed .collapse-icon {
  transform: rotate(180deg);
}

/* Nav items centred in icon-only mode */
.sidebar-collapsed .sidebar-nav {
  padding: 0.75rem 0.5rem;
}

.sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 0.625rem;
}

.sidebar-collapsed .nav-label {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

/* Footer: hide lang row and expanded profile card; show collapsed avatar */
.sidebar-collapsed .footer-lang-row {
  opacity: 0;
  height: 0;
  overflow: hidden;
  pointer-events: none;
}

.sidebar-collapsed .sidebar-profile-card {
  opacity: 0;
  height: 0;
  padding: 0;
  margin: 0;
  overflow: hidden;
  pointer-events: none;
  border: none;
}

.sidebar-collapsed .sidebar-profile-collapsed {
  display: flex;
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Main area
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.main-area {
  display: flex;
  flex-direction: column;
  background: var(--surface-bg);
  min-height: 100vh;
  overflow-x: hidden;
}

.content-topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--surface-bg);
  border-bottom: 1px solid var(--surface-border);
  padding: 0.5rem 1.5rem;
}

.page-content {
  flex: 1;
  padding: var(--space-page);
  width: 100%;
  max-width: 1400px;
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Page header
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.page-header {
  margin-bottom: var(--space-section);
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-md);
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Stats grid + stat card
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-gap);
  margin-bottom: var(--space-section);
}

.stat-card {
  background: var(--surface-card);
  padding: var(--space-card);
  border-radius: var(--radius-card);
  border: 1px solid var(--surface-border);
  box-shadow: var(--shadow-card);
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
}

.stat-card:hover {
  border-color: var(--surface-border-strong);
  box-shadow: var(--shadow-card-hover);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: var(--color-warning); }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger  .stat-value { color: var(--color-danger);  }
.stat-card.info    .stat-value { color: var(--color-info);    }

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Card
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.card {
  background: var(--surface-card);
  border-radius: var(--radius-card);
  padding: var(--space-card);
  border: 1px solid var(--surface-border);
  box-shadow: var(--shadow-card);
  margin-bottom: var(--space-gap);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--surface-border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Table
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-bg);
  border-top: 1px solid var(--surface-border);
  border-bottom: 1px solid var(--surface-border);
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--surface-hover);
  color: var(--text-secondary);
  font-size: var(--text-base);
}

tbody tr {
  transition: background-color var(--transition-fast);
}

tbody tr:hover {
  background: var(--surface-hover);
}

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Badges
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: var(--radius-badge);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success    { background: var(--color-success-bg);    color: var(--color-success-text);    }
.badge.warning    { background: var(--color-warning-bg);    color: var(--color-warning-text);    }
.badge.danger     { background: var(--color-danger-bg);     color: var(--color-danger-text);     }
.badge.info       { background: var(--color-info-bg);       color: var(--color-info-text);       }
.badge.increasing { background: var(--color-increasing-bg); color: var(--color-increasing-text); }
.badge.stable     { background: var(--color-stable-bg);     color: var(--color-stable-text);     }
.badge.decreasing { background: var(--color-decreasing-bg); color: var(--color-decreasing-text); }
.badge.high       { background: var(--color-danger-bg);     color: var(--color-danger-text);     }
.badge.medium     { background: var(--color-warning-bg);    color: var(--color-warning-text);    }
.badge.low        { background: var(--color-info-bg);       color: var(--color-info-text);       }

/* u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500
   Loading and error states
   u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500u2500 */
.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-size: var(--text-md);
}

.error {
  background: var(--color-danger-surface);
  border: 1px solid var(--color-danger-bg);
  color: var(--color-danger-text);
  padding: 1rem;
  border-radius: var(--radius-input);
  margin: 1rem 0;
  font-size: var(--text-md);
}
</style>
