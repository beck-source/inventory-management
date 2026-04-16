<template>
  <div class="app" :class="{ 'sidebar-collapsed': isCollapsed, 'mobile-open': isMobileOpen }">

    <!-- SIDEBAR -->
    <aside class="sidebar">

      <!-- Brand -->
      <div class="sidebar-brand">
        <div class="sidebar-brand-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <!-- Factory/Warehouse Icon -->
            <rect x="3" y="8" width="18" height="10" rx="1" stroke="#fbbf24"/>
            <path d="M8 8V4M16 8V4" stroke="#60a5fa"/>
            <path d="M3 14H1M23 14H21" stroke="#34d399"/>
            <rect x="5" y="10" width="3" height="4" fill="#f87171" opacity="0.6"/>
            <rect x="11" y="10" width="3" height="4" fill="#818cf8" opacity="0.6"/>
            <rect x="17" y="10" width="2" height="4" fill="#fbbf24" opacity="0.6"/>
          </svg>
        </div>
        <div v-if="!isCollapsed" class="sidebar-brand-text">
          <span class="sidebar-brand-name">{{ t('nav.companyName') }}</span>
          <span class="sidebar-brand-sub">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <!-- Nav links -->
      <nav class="sidebar-nav">
        <router-link to="/" :class="['sidebar-link', { active: $route.path === '/' }]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="sidebar-icon"><path d="M3 13h2v-2H3v2zm0-4h2V7H3v2zm0-4h2V3H3v2zm4 8h10v-2H7v2zm0-4h10V7H7v2zm0-4V3H7v2h10V3H7z"/></svg>
          <span v-if="!isCollapsed" class="sidebar-label">{{ t('nav.overview') }}</span>
        </router-link>

        <router-link to="/inventory" :class="['sidebar-link', { active: $route.path === '/inventory' }]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="sidebar-icon"><path d="M20 7h-4V5l-2-2h-4L8 5v2H4c-1.1 0-2 .9-2 2v5c0 .75.4 1.38 1 1.73V19c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-3.28c.6-.35 1-.98 1-1.72V9c0-1.1-.9-2-2-2zm-8-2h4v2h-4V5zM4 9h16v5h-5v-3H9v3H4V9zm9 6h-2v-2h2v2zm5 4H6v-3h3v1h6v-1h3v3z"/></svg>
          <span v-if="!isCollapsed" class="sidebar-label">{{ t('nav.inventory') }}</span>
        </router-link>

        <router-link to="/orders" :class="['sidebar-link', { active: $route.path === '/orders' }]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="sidebar-icon"><path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
          <span v-if="!isCollapsed" class="sidebar-label">{{ t('nav.orders') }}</span>
        </router-link>

        <router-link to="/spending" :class="['sidebar-link', { active: $route.path === '/spending' }]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="sidebar-icon"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>
          <span v-if="!isCollapsed" class="sidebar-label">{{ t('nav.finance') }}</span>
        </router-link>

        <router-link to="/demand" :class="['sidebar-link', { active: $route.path === '/demand' }]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="sidebar-icon"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z"/></svg>
          <span v-if="!isCollapsed" class="sidebar-label">{{ t('nav.demandForecast') }}</span>
        </router-link>

        <router-link to="/reports" :class="['sidebar-link', { active: $route.path === '/reports' }]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="sidebar-icon"><path d="M9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4zm2.5 2.1h-15V5h15v14.1zm0-16.1h-15c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h15c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>
          <span v-if="!isCollapsed" class="sidebar-label">Reports</span>
        </router-link>

        <router-link to="/restocking" :class="['sidebar-link', { active: $route.path === '/restocking' }]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="sidebar-icon"><path d="M19 8l-4 4h3c0 3.31-2.69 6-6 6-1.01 0-1.97-.25-2.8-.7l-1.46 1.46C8.97 19.54 10.43 20 12 20c4.42 0 8-3.58 8-8h3l-4-4zM6 12c0-3.31 2.69-6 6-6 1.01 0 1.97.25 2.8.7l1.46-1.46C15.03 4.46 13.57 4 12 4c-4.42 0-8 3.58-8 8H1l4 4 4-4H6z"/></svg>
          <span v-if="!isCollapsed" class="sidebar-label">Restocking</span>
        </router-link>
      </nav>

      <!-- Collapse toggle -->
      <button class="sidebar-toggle" @click="isCollapsed = !isCollapsed" :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path v-if="!isCollapsed" d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12z"/>
          <path v-else d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/>
        </svg>
      </button>

      <!-- User profile + language switcher (bottom) -->
      <div class="sidebar-footer">
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>

    </aside>

    <!-- MAIN CONTENT -->
    <main class="main-content">
      <!-- Mobile top bar — hidden on desktop via CSS -->
      <div class="mobile-header">
        <button class="mobile-menu-btn" @click="isMobileOpen = !isMobileOpen" aria-label="Toggle navigation">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <span class="mobile-brand-name">{{ t('nav.companyName') }}</span>
      </div>
      <FilterBar />
      <router-view />
    </main>

    <!-- Modals (keep exactly as-is) -->
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

    <!-- Mobile backdrop — tapping it closes the drawer -->
    <div
      class="sidebar-overlay"
      :class="{ visible: isMobileOpen }"
      @click="isMobileOpen = false"
      aria-hidden="true"
    ></div>

  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
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
    const isCollapsed = ref(false)
    const route = useRoute()
    const isMobileOpen = ref(false)

    // Close the mobile drawer whenever the user navigates to a new page
    watch(() => route.path, () => {
      isMobileOpen.value = false
    })
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
      isCollapsed,
      isMobileOpen,
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
/* ── Reset ─────────────────────────────── */
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f8fafc;
  color: #1e293b;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── App shell ──────────────────────────── */
.app {
  display: flex;
  min-height: 100vh;
}

/* ── Sidebar ────────────────────────────── */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 240px;
  height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1a1f3a 100%);
  display: flex;
  flex-direction: column;
  z-index: 50;
  transition: width 0.2s ease;
  overflow: hidden;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);
}

.app.sidebar-collapsed .sidebar {
  width: 64px;
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 12px;
  height: 72px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
  flex-shrink: 0;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
  transition: all 0.3s ease;
}

.sidebar-brand:hover {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
}

.sidebar-brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  color: white;
  font-size: 18px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  letter-spacing: -0.02em;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
  transition: all 0.3s ease;
}

.sidebar-brand:hover .sidebar-brand-icon {
  transform: scale(1.08);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.35);
}

.sidebar-brand-icon svg {
  width: 22px;
  height: 22px;
}

.sidebar-brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.sidebar-brand-name {
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.sidebar-brand-sub {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
  white-space: nowrap;
  margin-top: 2px;
  letter-spacing: 0.01em;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-nav::-webkit-scrollbar { width: 4px; }
.sidebar-nav::-webkit-scrollbar-track { background: transparent; }
.sidebar-nav::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 2px;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 11px;
  border-radius: 8px;
  font-size: 13.5px;
  font-weight: 500;
  color: #cbd5e1;
  text-decoration: none;
  margin-bottom: 3px;
  transition: all 0.2s ease;
  white-space: nowrap;
  overflow: hidden;
  position: relative;
}

.sidebar-link:hover {
  background: rgba(59, 130, 246, 0.1);
  color: #e2e8f0;
  padding-left: 13px;
}

.sidebar-link.active {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.05) 100%);
  color: #60a5fa;
  font-weight: 600;
  border-left: 3px solid #3b82f6;
  padding-left: 8px;
}

.sidebar-link.active .sidebar-icon {
  opacity: 1;
}

.sidebar-icon {
  flex-shrink: 0;
  opacity: 0.5;
  transition: all 0.2s ease;
}

.sidebar-link:hover .sidebar-icon {
  opacity: 0.85;
}

.sidebar-label {
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

/* Collapse toggle */
.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(59, 130, 246, 0.05);
  color: #94a3b8;
  cursor: pointer;
  margin: 0 0 12px 11px;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.sidebar-toggle:hover {
  background: rgba(59, 130, 246, 0.12);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.3);
}

.sidebar-toggle:active {
  transform: scale(0.96);
}

/* Footer */
.sidebar-footer {
  padding: 12px 8px 14px;
  border-top: 1px solid rgba(71, 85, 105, 0.2);
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}

/* ── Main content ───────────────────────── */
.main-content {
  margin-left: 240px;
  min-height: 100vh;
  padding: 28px 32px;
  background: #f8fafc;
  flex: 1;
  transition: margin-left 0.2s ease;
  min-width: 0;
}

.app.sidebar-collapsed .main-content {
  margin-left: 64px;
}

/* ── Page header ────────────────────────── */
.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  margin-bottom: 4px;
}

.page-header p {
  color: #64748b;
  font-size: 14px;
}

/* ── Stats grid ─────────────────────────── */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

/* ── Stat card ──────────────────────────── */
.stat-card {
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  border: 1px solid #e8edf4;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s, border-color 0.2s;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border-color: #cbd5e1;
}

.stat-label {
  color: #64748b;
  font-size: 11.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.stat-card.warning .stat-value { color: #ea580c; }
.stat-card.success .stat-value { color: #059669; }
.stat-card.danger  .stat-value { color: #dc2626; }
.stat-card.info    .stat-value { color: #2563eb; }

/* ── Card ───────────────────────────────── */
.card {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  border: 1px solid #e8edf4;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f1f5f9;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

/* ── Table ──────────────────────────────── */
.table-container { overflow-x: auto; }

table { width: 100%; border-collapse: collapse; }

thead {
  background: #f8fafc;
  border-top: 1px solid #f1f5f9;
  border-bottom: 1px solid #f1f5f9;
}

th {
  text-align: left;
  padding: 8px 12px;
  font-weight: 600;
  color: #64748b;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

td {
  padding: 10px 12px;
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: 13.5px;
}

tbody tr { transition: background-color 0.1s; }
tbody tr:hover { background: #f8fafc; }

/* ── Badges ─────────────────────────────── */
.badge {
  display: inline-block;
  padding: 3px 9px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.badge.success    { background: #d1fae5; color: #065f46; }
.badge.warning    { background: #fef3c7; color: #92400e; }
.badge.danger     { background: #fee2e2; color: #991b1b; }
.badge.info       { background: #dbeafe; color: #1e40af; }
.badge.increasing { background: #d1fae5; color: #065f46; }
.badge.decreasing { background: #fee2e2; color: #991b1b; }
.badge.stable     { background: #e0e7ff; color: #3730a3; }
.badge.high       { background: #fee2e2; color: #991b1b; }
.badge.medium     { background: #fef3c7; color: #92400e; }
.badge.low        { background: #dbeafe; color: #1e40af; }

/* ── States ─────────────────────────────── */
.loading {
  text-align: center;
  padding: 48px;
  color: #94a3b8;
  font-size: 14px;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 14px 16px;
  border-radius: 10px;
  margin: 16px 0;
  font-size: 14px;
}

/* ── Overlay (mobile drawer backdrop) ──────── */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 49; /* behind sidebar (z-index 50), above content */
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.25s ease;
}

/* ── Mobile top bar ─────────────────────────── */
.mobile-header {
  display: none; /* hidden on desktop */
}

/* ── Medium screens: auto icon-only rail ──────
   768px–1024px: sidebar auto-collapses to 64px,
   labels hidden via CSS (JS isCollapsed state is
   ignored at this breakpoint via !important)      */
@media (max-width: 1024px) and (min-width: 768px) {
  .sidebar {
    width: 64px !important;
  }
  .app.sidebar-collapsed .sidebar,
  .app:not(.sidebar-collapsed) .sidebar {
    width: 64px;
  }
  .main-content {
    margin-left: 64px !important;
  }
  .app.sidebar-collapsed .main-content,
  .app:not(.sidebar-collapsed) .main-content {
    margin-left: 64px;
  }
  /* Hide text, show icon-only */
  .sidebar-brand-text { display: none; }
  .sidebar-label      { display: none; }
  .sidebar-toggle     { display: none; } /* no manual toggle at this width */
  /* Center icons in their links */
  .sidebar-link {
    justify-content: center;
    padding: 10px 8px;
  }
  .sidebar-brand {
    justify-content: center;
    padding: 0 16px;
  }
}

/* ── Small screens: off-canvas drawer ─────────
   < 768px: sidebar slides in from the left as
   a full-width overlay drawer                    */
@media (max-width: 767px) {
  /* Show the mobile top bar */
  .mobile-header {
    display: flex;
    align-items: center;
    gap: 12px;
    position: sticky;
    top: 0;
    z-index: 91; /* above FilterBar (z-index 90) */
    background: #0f172a;
    padding: 0 16px;
    height: 52px;
    flex-shrink: 0;
    margin: -28px -32px 0; /* break out of main-content padding */
    width: calc(100% + 64px); /* re-fill the full width */
  }

  .mobile-menu-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 7px;
    border: none;
    background: transparent;
    color: #94a3b8;
    cursor: pointer;
    flex-shrink: 0;
    transition: background 0.15s, color 0.15s;
  }

  .mobile-menu-btn:hover {
    background: #1e293b;
    color: #e2e8f0;
  }

  .mobile-brand-name {
    font-size: 14px;
    font-weight: 700;
    color: #f1f5f9;
    letter-spacing: -0.02em;
  }

  /* FilterBar sticks below the mobile header */
  .filters-bar {
    top: 52px;
  }

  /* Sidebar: off-screen by default, slides in */
  .sidebar {
    width: 240px !important;
    transform: translateX(-100%);
    transition: transform 0.25s ease, width 0.2s ease;
    z-index: 50;
  }

  /* When mobile drawer is open */
  .app.mobile-open .sidebar {
    transform: translateX(0);
  }

  /* Always show full labels in mobile drawer */
  .app.mobile-open .sidebar-brand-text { display: flex !important; }
  .app.mobile-open .sidebar-label      { display: block !important; }
  .app.mobile-open .sidebar-link       { justify-content: flex-start; }
  .app.mobile-open .sidebar-brand      { justify-content: flex-start; }

  /* Main content: full width, no left margin */
  .main-content {
    margin-left: 0 !important;
    padding: 0 16px 24px;
  }

  /* Show the backdrop overlay */
  .sidebar-overlay {
    display: block;
  }

  .sidebar-overlay.visible {
    opacity: 1;
    pointer-events: auto;
  }
}
</style>
