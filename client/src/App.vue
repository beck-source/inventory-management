<template>
  <div
    class="app"
    :class="{ 'sidebar-collapsed': collapsed, 'sidebar-overlay': tabletOverlayOpen }"
  >
    <aside id="app-sidebar" class="sidebar" :class="{ open: drawerOpen }">
      <div class="sidebar-brand">
        <span class="brand-mark" aria-hidden="true">{{ brandInitial }}</span>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav class="sidebar-nav" aria-label="Main">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :aria-label="item.label"
          :title="collapsed ? item.label : null"
          @click="closeNav"
        >
          <component :is="item.icon" class="sidebar-icon" />
          <span class="sidebar-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
        <button
          type="button"
          class="collapse-toggle"
          :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          :aria-expanded="!collapsed"
          :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
          @click="toggleCollapsed"
        >
          <CollapseIcon class="sidebar-icon collapse-icon" />
          <span class="sidebar-label">Collapse</span>
        </button>
      </div>
    </aside>

    <div v-if="backdropVisible" class="sidebar-backdrop" @click="closeNav"></div>

    <div class="content-column">
      <div class="mobile-bar">
        <button
          type="button"
          class="drawer-toggle"
          aria-label="Open navigation menu"
          aria-controls="app-sidebar"
          :aria-expanded="drawerOpen"
          @click="drawerOpen = true"
        >
          <MenuIcon class="sidebar-icon" />
        </button>
        <span class="mobile-title">{{ t('nav.companyName') }}</span>
      </div>
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
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import {
  OverviewIcon,
  InventoryIcon,
  OrdersIcon,
  FinanceIcon,
  DemandIcon,
  RestockingIcon,
  ReportsIcon,
  MenuIcon,
  CollapseIcon
} from './components/NavIcons'

const COLLAPSE_KEY = 'sidebar-collapsed'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    MenuIcon,
    CollapseIcon
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Sidebar state: collapsed icon rail (desktop, persisted), tablet overlay and phone drawer
    // Layout tiers: phone < 640px (off-canvas drawer), tablet 640-1024px (icon rail,
    // expands as an overlay), desktop > 1024px (persisted collapse, pushes content).
    // Queries are read synchronously in setup so the first paint already uses the right layout.
    // 639.98px avoids a gap for fractional viewport widths between 639 and 640.
    const phoneQuery = window.matchMedia ? window.matchMedia('(max-width: 639.98px)') : null
    const tabletQuery = window.matchMedia
      ? window.matchMedia('(min-width: 640px) and (max-width: 1024px)')
      : null
    const isPhone = ref(!!phoneQuery && phoneQuery.matches)
    const isTablet = ref(!!tabletQuery && tabletQuery.matches)

    // Stored preference: '1' collapsed, '0' expanded, null = none (use the tier default)
    const storedPref = ref(null)
    try {
      storedPref.value = localStorage.getItem(COLLAPSE_KEY)
    } catch (e) {
      // localStorage can be unavailable (private mode); fall back to tier defaults
    }

    const drawerOpen = ref(false)
    // Tablet overlay is transient (not persisted); an explicit stored '0' opens it initially
    const tabletOpen = ref(storedPref.value === '0')

    // Icon rail shown: desktop follows the stored choice, tablet is a rail unless overlay-expanded
    const collapsed = computed(() => {
      if (isPhone.value) return false
      if (isTablet.value) return !tabletOpen.value
      return storedPref.value === '1'
    })
    const tabletOverlayOpen = computed(() => isTablet.value && tabletOpen.value)
    const backdropVisible = computed(
      () => (isPhone.value && drawerOpen.value) || tabletOverlayOpen.value
    )

    const toggleCollapsed = () => {
      if (isTablet.value) {
        tabletOpen.value = !tabletOpen.value
        return
      }
      storedPref.value = collapsed.value ? '0' : '1'
      try {
        localStorage.setItem(COLLAPSE_KEY, storedPref.value)
      } catch (e) {
        // ignore persistence failure
      }
    }

    // Close the phone drawer and the tablet overlay (backdrop, link click, Escape)
    const closeNav = () => {
      drawerOpen.value = false
      tabletOpen.value = false
    }

    const onKeydown = (event) => {
      if (event.key === 'Escape') closeNav()
    }

    // Live tier changes: reset transient state so nothing stays open across layouts
    const onTierChange = () => {
      isPhone.value = phoneQuery.matches
      isTablet.value = tabletQuery.matches
      drawerOpen.value = false
      tabletOpen.value = storedPref.value === '0'
    }

    // Same routes and labels as the previous top nav (Reports has no i18n key)
    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: OverviewIcon },
      { to: '/inventory', label: t('nav.inventory'), icon: InventoryIcon },
      { to: '/orders', label: t('nav.orders'), icon: OrdersIcon },
      { to: '/spending', label: t('nav.finance'), icon: FinanceIcon },
      { to: '/demand', label: t('nav.demandForecast'), icon: DemandIcon },
      { to: '/restocking', label: t('nav.restocking'), icon: RestockingIcon },
      { to: '/reports', label: 'Reports', icon: ReportsIcon }
    ])

    // First character of the company name, shown as the logo mark in the icon rail
    const brandInitial = computed(() => (t('nav.companyName') || '').charAt(0))

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
      window.addEventListener('keydown', onKeydown)
      if (phoneQuery) {
        phoneQuery.addEventListener('change', onTierChange)
        tabletQuery.addEventListener('change', onTierChange)
      }
    })
    onBeforeUnmount(() => {
      window.removeEventListener('keydown', onKeydown)
      if (phoneQuery) {
        phoneQuery.removeEventListener('change', onTierChange)
        tabletQuery.removeEventListener('change', onTierChange)
      }
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
      drawerOpen,
      tabletOverlayOpen,
      backdropVisible,
      closeNav,
      toggleCollapsed,
      navItems,
      brandInitial
    }
  }
}
</script>

<style>
/* ---------- Design tokens ---------- */
:root {
  /* spacing, 4px base */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* type */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.25rem;
  --text-xl: 1.5rem;

  /* color: slate palette */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-muted: #f1f5f9;
  --color-border: #e2e8f0;
  --color-border-strong: #cbd5e1;
  --color-text: #0f172a;
  --color-text-secondary: #334155;
  --color-text-muted: #64748b;
  --color-accent: #2563eb;
  --color-accent-soft: #eff6ff;

  /* status */
  --color-success: #059669;
  --color-info: #2563eb;
  --color-warning: #d97706;
  --color-danger: #dc2626;

  /* sidebar */
  --color-sidebar-bg: #0f172a;
  --color-sidebar-text: #cbd5e1;
  --color-sidebar-muted: #94a3b8;
  --color-sidebar-hover: rgba(255, 255, 255, 0.06);
  --color-sidebar-active: rgba(255, 255, 255, 0.12);
  --sidebar-width: 248px;
  --sidebar-width-collapsed: 68px;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 4px 12px rgba(15, 23, 42, 0.08);

  --content-max-width: 1440px;

  /* Offset used by sticky bars that live inside the content column.
     0 on desktop (sidebar is beside the content); the mobile bar height below 640px. */
  --mobile-bar-height: 56px;
  --sticky-top: 0px;

  --control-height: 36px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: var(--color-bg);
  color: var(--color-text-secondary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

/* ---------- App shell ---------- */
.app {
  display: flex;
  min-height: 100vh;
}

.content-column {
  flex: 1;
  /* min-width: 0 stops wide tables from stretching the flex column */
  min-width: 0;
  margin-left: var(--sidebar-width);
  transition: margin-left 0.2s ease;
}

.sidebar-collapsed .content-column {
  margin-left: var(--sidebar-width-collapsed);
}

.main-content {
  max-width: var(--content-max-width);
  width: 100%;
  margin: 0 auto;
  padding: var(--space-6) var(--space-8) var(--space-12);
}

/* ---------- Sidebar ---------- */
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-3);
  background: var(--color-sidebar-bg);
  color: var(--color-sidebar-text);
  transition: width 0.2s ease, transform 0.2s ease;
  /* above sticky filter bar (90); below modals (1000/2000) */
  z-index: 100;
}

.sidebar-collapsed .sidebar {
  width: var(--sidebar-width-collapsed);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2);
  min-height: 48px;
}

.brand-mark {
  width: 36px;
  height: 36px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: #fff;
  font-weight: 700;
  font-size: var(--text-base);
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* Wrap whole words instead of truncating with an ellipsis */
.brand-name {
  color: #fff;
  font-size: var(--text-base);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.01em;
  white-space: normal;
  word-break: normal;
  overflow-wrap: normal;
}

.brand-subtitle {
  color: var(--color-sidebar-muted);
  font-size: var(--text-xs);
  line-height: 1.3;
  margin-top: 2px;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
  overflow-y: auto;
  padding-top: var(--space-2);
}

.sidebar-link,
.collapse-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-3);
  height: 40px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--color-sidebar-text);
  text-decoration: none;
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.sidebar-link:hover,
.collapse-toggle:hover {
  background: var(--color-sidebar-hover);
  color: #fff;
}

/* Root link "/" must be exact-active only; other links also match nested paths */
.sidebar-link.router-link-active:not([href="/"]),
.sidebar-link.router-link-exact-active {
  background: var(--color-sidebar-active);
  color: #fff;
  box-shadow: inset 3px 0 0 var(--color-accent);
}

.sidebar .sidebar-link:focus-visible,
.sidebar .collapse-toggle:focus-visible {
  outline: 2px solid #93c5fd;
  outline-offset: -2px;
}

.sidebar-icon {
  width: 20px;
  height: 20px;
  flex: none;
}

.sidebar-label {
  white-space: nowrap;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.collapse-icon {
  transition: transform 0.2s ease;
}

.sidebar-collapsed .collapse-icon {
  transform: rotate(180deg);
}

/* Re-skin the language switcher and profile button for the dark sidebar */
.sidebar .language-switcher,
.sidebar .profile-menu {
  width: 100%;
}

.sidebar .language-button,
.sidebar .profile-button {
  width: 100%;
  height: 44px;
  background: var(--color-sidebar-hover);
  border-color: rgba(255, 255, 255, 0.12);
  color: var(--color-sidebar-text);
}

.sidebar .language-button:hover,
.sidebar .profile-button:hover {
  background: var(--color-sidebar-active);
  border-color: rgba(255, 255, 255, 0.2);
}

.sidebar .language-button .globe-icon,
.sidebar .language-button .chevron,
.sidebar .profile-button .chevron {
  color: var(--color-sidebar-muted);
}

.sidebar .profile-name {
  color: #fff;
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar .language-label {
  flex: 1;
  text-align: left;
}

/* Dropdowns open upward from the footer and stay inside the sidebar's width,
   so they are neither clipped by the viewport bottom nor pushed off-screen left. */
.sidebar .sidebar-footer .dropdown-menu {
  top: auto;
  bottom: calc(100% + var(--space-2));
  left: 0;
  right: auto;
  width: max(100%, 220px);
  min-width: 0;
}

.sidebar .sidebar-footer .profile-menu .dropdown-menu {
  width: 280px;
}

.sidebar .sidebar-footer .dropdown-menu .user-name,
.sidebar .sidebar-footer .dropdown-menu .dropdown-item {
  color: #0f172a;
}

.sidebar .sidebar-footer .dropdown-menu .dropdown-item.logout {
  color: #dc2626;
}

.sidebar .sidebar-footer .dropdown-menu .dropdown-item.active {
  color: #2563eb;
}

/* Icon rail: hide text, centre icons */
.sidebar-collapsed .sidebar-brand {
  justify-content: center;
  padding-left: 0;
  padding-right: 0;
}

.sidebar-collapsed .brand-text,
.sidebar-collapsed .sidebar-label,
.sidebar-collapsed .language-label,
.sidebar-collapsed .profile-name,
.sidebar-collapsed .sidebar .chevron {
  display: none;
}

.sidebar-collapsed .sidebar-link,
.sidebar-collapsed .collapse-toggle {
  justify-content: center;
  padding: 0;
}

.sidebar-collapsed .sidebar .language-button,
.sidebar-collapsed .sidebar .profile-button {
  justify-content: center;
  padding: 0;
}

.mobile-bar {
  display: none;
}

/* Rendered only while the phone drawer or tablet overlay is open (v-if) */
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  z-index: 150;
}

/* ---------- Tablet: expanded sidebar overlays the content ---------- */
/* Content keeps the rail-width margin while the full sidebar floats over it */
.sidebar-overlay .content-column {
  margin-left: var(--sidebar-width-collapsed);
}

.sidebar-overlay .sidebar {
  /* above the backdrop (150), below modals */
  z-index: 200;
  box-shadow: var(--shadow-md);
}

/* ---------- Mobile: drawer ---------- */
@media (max-width: 639.98px) {
  :root {
    --sticky-top: var(--mobile-bar-height);
  }

  .sidebar {
    width: var(--sidebar-width);
    transform: translateX(-100%);
    visibility: hidden;
    transition: transform 0.2s ease, visibility 0s linear 0.2s;
    z-index: 200;
  }

  .sidebar.open {
    transform: none;
    visibility: visible;
    transition: transform 0.2s ease;
    box-shadow: var(--shadow-md);
  }

    .collapse-toggle {
    display: none;
  }

  .content-column {
    margin-left: 0;
  }

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
    z-index: 95;
  }

  .drawer-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: var(--control-height);
    height: var(--control-height);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-surface);
    color: var(--color-text);
    cursor: pointer;
  }

  .mobile-title {
    font-weight: 700;
    color: var(--color-text);
  }

  .main-content {
    padding: var(--space-4) var(--space-4) var(--space-8);
  }
}

/* Respect reduced motion for width / transform / margin transitions */
@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar.open,
  .content-column,
  .collapse-icon {
    transition: none !important;
  }
}

/* ---------- Page header ---------- */
.page-header {
  margin-bottom: var(--space-6);
}

.page-header h2 {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.02em;
}

.page-header p {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

/* ---------- Stat cards ---------- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-surface);
  padding: var(--space-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-md);
}

.stat-label {
  color: var(--color-text-muted);
  font-size: var(--text-xs);
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
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value { color: #ea580c; }
.stat-card.success .stat-value { color: var(--color-success); }
.stat-card.danger .stat-value { color: var(--color-danger); }
.stat-card.info .stat-value { color: var(--color-info); }

/* ---------- Cards ---------- */
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
  gap: var(--space-4);
  flex-wrap: wrap;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.card-title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.01em;
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
  padding: var(--space-3) var(--space-3);
  font-weight: 600;
  color: var(--color-text-muted);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-3);
  border-top: 1px solid var(--color-surface-muted);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--color-bg);
}

/* ---------- Badges ---------- */
.badge {
  display: inline-block;
  padding: 2px var(--space-2);
  border-radius: 9999px;
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.badge.success { background: #d1fae5; color: #065f46; }
.badge.warning { background: #fef3c7; color: #92400e; }
.badge.danger { background: #fee2e2; color: #991b1b; }
.badge.info { background: #dbeafe; color: #1e40af; }
.badge.increasing { background: #d1fae5; color: #065f46; }
.badge.decreasing { background: #fee2e2; color: #991b1b; }
.badge.stable { background: #dbeafe; color: #1e40af; }
.badge.high { background: #fee2e2; color: #991b1b; }
.badge.medium { background: #fef3c7; color: #92400e; }
.badge.low { background: #dbeafe; color: #1e40af; }

/* ---------- States ---------- */
.loading {
  text-align: center;
  padding: var(--space-12);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin: var(--space-4) 0;
  font-size: var(--text-sm);
}
</style>
