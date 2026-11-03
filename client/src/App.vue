<template>
  <div class="shell" :class="{ collapsed }">
    <div v-if="mobileOpen" class="backdrop" @click="closeMobile"></div>

    <aside class="sidebar" :class="{ open: mobileOpen }">
      <div class="sidebar-head">
        <div class="brand-mark" aria-hidden="true">{{ t('nav.companyName').charAt(0) }}</div>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-sub">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav class="sidebar-nav" aria-label="Main">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          exact-active-class="active"
          :title="collapsed ? item.label : null"
          :aria-label="item.label"
          @click="closeMobile"
        >
          <NavIcon :name="item.icon" class="nav-icon" />
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-foot">
        <button
          class="collapse-btn"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="toggle"
        >
          <NavIcon name="collapse" class="nav-icon collapse-icon" />
          <span class="nav-label">Collapse</span>
        </button>
      </div>
    </aside>

    <div class="main-col">
      <header class="topbar">
        <button class="menu-btn" aria-label="Open navigation" @click="openMobile">
          <NavIcon name="menu" class="nav-icon" />
        </button>
        <FilterBar />
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>

      <main class="content">
        <div class="content-inner">
          <router-view />
        </div>
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
import NavIcon from './components/NavIcon.vue'
import { useSidebar } from './composables/useSidebar'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    NavIcon
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const { collapsed, mobileOpen, toggle, openMobile, closeMobile } = useSidebar()

    // Reports label is not in the locale files (was hardcoded English); keep it as is
    const navItems = computed(() => [
      { to: '/', icon: 'overview', label: t('nav.overview') },
      { to: '/inventory', icon: 'inventory', label: t('nav.inventory') },
      { to: '/orders', icon: 'orders', label: t('nav.orders') },
      { to: '/spending', icon: 'finance', label: t('nav.finance') },
      { to: '/demand', icon: 'demand', label: t('nav.demandForecast') },
      { to: '/restocking', icon: 'restocking', label: t('nav.restocking') },
      { to: '/reports', icon: 'reports', label: 'Reports' }
    ])
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

    return {
      t,
      navItems,
      collapsed,
      mobileOpen,
      toggle,
      openMobile,
      closeMobile,
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
  font-family: var(--font);
  font-size: var(--text-base);
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ---------- App shell ---------- */
/* Shell is exactly viewport height; only .content scrolls, so there is no double scrollbar */
.shell {
  display: flex;
  height: 100vh;
  background: var(--bg);
}

.sidebar {
  width: var(--sidebar-w);
  flex: none;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  transition: width var(--ease);
  z-index: var(--z-sidebar);
}

.collapsed .sidebar { width: var(--sidebar-w-collapsed); }

.sidebar-head {
  height: var(--topbar-h);
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--border);
  overflow: hidden;
}

.brand-mark {
  width: 32px;
  height: 32px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: #fff;
  font-weight: 700;
  font-size: var(--text-lg);
}

.brand-text { display: flex; flex-direction: column; min-width: 0; line-height: 1.2; }

.brand-name {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-sub {
  font-size: var(--text-xs);
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-link,
.collapse-btn {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  width: 100%;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-md);
  background: none;
  color: var(--text-muted);
  text-decoration: none;
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: background var(--ease), color var(--ease);
}

.nav-link:hover,
.collapse-btn:hover { background: var(--surface-muted); color: var(--text); }

.nav-link.active { background: var(--accent-soft); color: var(--accent); }

.nav-link:focus-visible,
.collapse-btn:focus-visible,
.menu-btn:focus-visible { outline: none; box-shadow: var(--focus-ring); }

.nav-icon { width: 20px; height: 20px; flex: none; }
.collapse-icon { transition: transform var(--ease); }
.collapsed .collapse-icon { transform: rotate(180deg); }

.collapsed .nav-label,
.collapsed .brand-text { display: none; }
.collapsed .nav-link,
.collapsed .collapse-btn { justify-content: center; padding: 0; }
.collapsed .sidebar-head { justify-content: center; padding: 0; }

.sidebar-foot {
  flex: none;
  padding: var(--space-3);
  border-top: 1px solid var(--border);
}

.main-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  min-height: var(--topbar-h);
  flex: none;
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-8);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: relative;
  z-index: var(--z-topbar);
}

.topbar-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: none;
}

.menu-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text-body);
  cursor: pointer;
}

.backdrop { display: none; }

.content { flex: 1; overflow-y: auto; }

.content-inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6) var(--space-8);
}

@media (max-width: 768px) {
  /* Sidebar becomes an off-canvas drawer; collapse state is ignored here */
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    width: var(--sidebar-w);
    transform: translateX(-100%);
    transition: transform var(--ease);
  }
  .collapsed .sidebar { width: var(--sidebar-w); }
  .collapsed .nav-label { display: inline; }
  .collapsed .brand-text { display: flex; }
  .collapsed .nav-link,
  .collapsed .collapse-btn { justify-content: flex-start; padding: 0 var(--space-3); }
  .collapsed .sidebar-head { justify-content: flex-start; padding: 0 var(--space-4); }
  .collapsed .collapse-icon { transform: none; }
  .sidebar-foot { display: none; }
  .sidebar.open { transform: none; box-shadow: var(--shadow-lg); }
  .backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    z-index: var(--z-backdrop);
  }
  .menu-btn { display: inline-flex; }
  .topbar { flex-wrap: wrap; padding: var(--space-2) var(--space-4); }
  .content-inner { padding: var(--space-4); }
}

/* ---------- Shared page patterns ---------- */
.page-header { margin-bottom: var(--space-6); }

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: var(--text-base);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: border-color var(--ease), box-shadow var(--ease);
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value { color: #ea580c; }
.stat-card.success .stat-value { color: #059669; }
.stat-card.danger .stat-value { color: var(--danger); }
.stat-card.info .stat-value { color: var(--info); }

.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-6);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text);
}

.table-container { overflow-x: auto; }

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-muted);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 600;
  color: var(--text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border);
  color: var(--text-body);
  font-size: var(--text-base);
}

/* Keep IDs (SKU, order numbers) on one line */
td strong { white-space: nowrap; }

tbody tr { transition: background-color var(--ease); }
tbody tr:hover { background: var(--surface-muted); }

.badge {
  display: inline-block;
  padding: 2px var(--space-3);
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: 500;
  text-transform: capitalize;
  white-space: nowrap;
}

.badge.success, .badge.increasing { background: #d1fae5; color: #065f46; }
.badge.warning, .badge.medium { background: #fef3c7; color: #92400e; }
.badge.danger, .badge.decreasing, .badge.high { background: #fee2e2; color: #991b1b; }
.badge.info, .badge.low { background: #dbeafe; color: #1e40af; }
.badge.stable { background: var(--surface-muted); color: var(--text-body); }

.loading {
  text-align: center;
  padding: 48px var(--space-4);
  color: var(--text-muted);
  font-size: var(--text-base);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-base);
}

/* Shared primary / secondary buttons for views and modals */
.btn-primary, .btn-secondary {
  height: 36px;
  padding: 0 var(--space-4);
  border-radius: var(--radius-md);
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: background var(--ease), border-color var(--ease), box-shadow var(--ease);
}
.btn-primary { background: var(--accent); border: 1px solid var(--accent); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--accent-hover); border-color: var(--accent-hover); }
.btn-secondary { background: var(--surface); border: 1px solid var(--border); color: var(--text-body); }
.btn-secondary:hover:not(:disabled) { background: var(--surface-muted); }
.btn-primary:focus-visible, .btn-secondary:focus-visible { outline: none; box-shadow: var(--focus-ring); }
.btn-primary:disabled, .btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
