<template>
  <div
    class="app app-shell"
    :class="{ 'is-collapsed': collapsed, 'is-mobile-open': mobileOpen }"
  >
    <div class="cosmos-horizon" aria-hidden="true"></div>

    <aside id="primary-sidebar" class="sidebar" :aria-label="t('nav.primary')">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true"></span>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-sub">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <div>
        <div class="nav-section-label">{{ t('nav.sectionLabel') }}</div>
        <nav class="side-nav">
          <router-link
            v-for="(item, i) in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-item"
            exact-active-class="is-active"
            :title="item.label"
            @click="mobileOpen = false"
          >
            <span v-html="item.icon" aria-hidden="true" class="nav-icon"></span>
            <span class="nav-label">{{ item.label }}</span>
            <span class="nav-index" aria-hidden="true">{{ String(i + 1).padStart(2, '0') }}</span>
          </router-link>
        </nav>
      </div>

      <div class="sidebar-footer">
        <div class="system-status" role="status" :title="t('nav.systemStatus')">
          <span class="status-dot" aria-hidden="true"></span>
          <span class="status-text">{{ t('nav.systemStatus') }}</span>
        </div>
        <button
          class="collapse-btn"
          type="button"
          :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          :aria-expanded="!collapsed"
          @click="toggleCollapsed"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6l-6 6 6 6"/></svg>
          <span class="nav-label">{{ t('nav.collapse') }}</span>
        </button>
      </div>
    </aside>

    <div
      v-if="mobileOpen"
      class="sidebar-scrim"
      :aria-label="t('nav.closeNavigation')"
      @click="mobileOpen = false"
    ></div>

    <div class="shell-main">
      <header class="topbar">
        <button
          class="btn btn-icon btn-ghost menu-toggle"
          type="button"
          :aria-label="t('nav.openNavigation')"
          aria-controls="primary-sidebar"
          :aria-expanded="mobileOpen"
          @click="mobileOpen = true"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10"/></svg>
        </button>
        <div class="topbar-filters">
          <FilterBar />
        </div>
        <div class="topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
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
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

// Static, app-controlled SVG strings (safe for v-html). Stroke = currentColor.
const svg = (d) => `<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`
const ICONS = {
  overview: svg('<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8" stroke-dasharray="3 3"/><path d="M12 1v3M12 20v3M1 12h3M20 12h3"/>'),
  inventory: svg('<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/>'),
  orders: svg('<path d="M4 4h16v16H4z"/><path d="M8 9h8M8 13h8M8 17h5"/>'),
  finance: svg('<path d="M3 17l5-5 4 4 8-8"/><path d="M15 8h5v5"/>'),
  demand: svg('<path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/>'),
  reports: svg('<circle cx="12" cy="12" r="9"/><path d="M12 3v9l6.5 6.5"/>')
}

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

    // Sidebar shell state
    const collapsed = ref(localStorage.getItem('sidebar-collapsed') === '1')
    const mobileOpen = ref(false)
    const toggleCollapsed = () => {
      collapsed.value = !collapsed.value
      localStorage.setItem('sidebar-collapsed', collapsed.value ? '1' : '0')
    }

    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: ICONS.overview },
      { to: '/inventory', label: t('nav.inventory'), icon: ICONS.inventory },
      { to: '/orders', label: t('nav.orders'), icon: ICONS.orders },
      { to: '/spending', label: t('nav.finance'), icon: ICONS.finance },
      { to: '/demand', label: t('nav.demandForecast'), icon: ICONS.demand },
      { to: '/reports', label: t('nav.reports'), icon: ICONS.reports }
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
      collapsed,
      mobileOpen,
      toggleCollapsed,
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
/*
  Global layer on top of styles/theme.css (Orbital Command design system).
  theme.css owns tokens, shell, cards, tables, badges, controls and states.
  Only rules that views depend on and that theme.css does not provide live here.
*/
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Icon wrapper for v-html nav icons: let the inner svg be the flex child */
.nav-icon {
  display: contents;
}

/*
  theme.css declares .menu-toggle { display: none } before .btn { display: inline-flex },
  so .btn wins at equal specificity. Re-assert with higher specificity.
*/
.topbar .menu-toggle {
  display: none;
  flex-shrink: 0;
}

@media (max-width: 760px) {
  .topbar .menu-toggle {
    display: inline-flex;
  }

  .topbar .topbar-actions {
    margin-left: auto;
  }

  /* Filters drop to their own full-width row under the toggle and actions */
  .topbar .topbar-filters {
    order: 3;
    flex-basis: 100%;
  }
}

/* Translated status text keeps the telemetry look */
.system-status .status-text {
  text-transform: uppercase;
}

.brand-name {
  letter-spacing: 0.08em;
}

.brand-sub {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* theme.css restores the drawer brand with display: revert, which drops its flex column */
@media (max-width: 760px) {
  .app-shell.is-mobile-open .brand-text {
    display: flex;
  }
}

/*
  Views place kicker / title / subtitle directly inside .page-header (no wrapper div),
  so give each its own row of the wrapping flex container.
*/
.page-header > .page-kicker,
.page-header > .page-title,
.page-header > h2,
.page-header > p {
  flex-basis: 100%;
}

.page-header > h2,
.page-header > p {
  margin-top: 0;
}

.page-header > .page-kicker {
  margin-bottom: 0;
}

/* Vertical rhythm the views rely on (they stack siblings without gaps) */
.page-header {
  margin-bottom: var(--space-8);
  row-gap: var(--space-2);
}

.stats-grid {
  margin-bottom: var(--space-8);
  /* 220px (theme) wraps 4 KPIs to 3 + 1 on the 1024px icon-rail layout */
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.card {
  margin-bottom: var(--space-5);
}

/* Status variants not covered by theme.css */
.stat-card.info .stat-value {
  background: none;
  color: var(--info);
}

.badge.increasing {
  color: var(--success);
  background: var(--success-bg);
}

.badge.decreasing {
  color: var(--danger);
  background: var(--danger-bg);
}

.badge.stable {
  color: var(--neutral);
  background: var(--neutral-bg);
}

.badge.low {
  color: var(--info);
  background: var(--info-bg);
}

.error {
  margin: var(--space-4) 0;
}

/* Flex-column modals would otherwise shrink theme.css's 2px aurora top edge to 0 */
.modal::before,
.modal-content::before {
  flex-shrink: 0;
}
</style>
