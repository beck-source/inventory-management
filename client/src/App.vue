<template>
  <div class="app">
    <header class="top-nav">
      <div class="nav-container">
        <div class="logo">
          <h1>{{ t('nav.companyName') }}<span>IMS</span></h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <nav class="nav-tabs">
          <router-link to="/" :class="{ active: $route.path === '/' }">
            {{ t('nav.overview') }}
          </router-link>
          <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
            {{ t('nav.inventory') }}
          </router-link>
          <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
            {{ t('nav.orders') }}
          </router-link>
          <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
            {{ t('nav.finance') }}
          </router-link>
          <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
            {{ t('nav.demandForecast') }}
          </router-link>
          <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
            Reports
          </router-link>
        </nav>
        <LanguageSwitcher />
        <button class="theme-toggle" @click="toggleTheme" :aria-label="isDark ? 'Switch to light theme' : 'Switch to dark theme'" :title="isDark ? 'Switch to light theme' : 'Switch to dark theme'">
          <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
          </svg>
        </button>
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
import { useTheme } from './composables/useTheme'
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
    const { isDark, toggleTheme } = useTheme()
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
      isDark,
      toggleTheme,
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
*, *::before, *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* Smooth theme transitions on the properties that change between themes */
html {
  transition:
    background-color 0.2s ease,
    color            0.2s ease;
}

body,
.top-nav,
.filters-bar,
.card,
.stat-card,
.modal-container,
.dropdown-menu {
  transition:
    background-color 0.2s ease,
    color            0.2s ease,
    border-color     0.2s ease;
}

body {
  font-family: var(--uui-font);
  font-size: var(--uui-text-m-size);
  line-height: var(--uui-text-m-lh);
  background: var(--uui-surface-app);
  color: var(--uui-text-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-nav {
  background: var(--uui-surface-main);
  border-bottom: 1px solid var(--uui-border);
  box-shadow: var(--uui-shadow-100);
  position: sticky;
  top: 0;
  z-index: var(--uui-z-sticky);
}

.nav-container {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 0 var(--uui-space-24);
  height: 60px;
}

.nav-container > .nav-tabs {
  margin-left: auto;
  margin-right: var(--uui-space-12);
}

.nav-container > .language-switcher {
  margin-right: var(--uui-space-12);
}

.logo {
  display: flex;
  align-items: baseline;
  gap: var(--uui-space-6);
}

.logo h1 {
  font-size: var(--uui-h4-size);
  font-weight: var(--uui-fw-bold);
  color: var(--uui-text-secondary);
  letter-spacing: -0.02em;
}

.logo h1 span {
  color: var(--uui-primary);
  font-weight: var(--uui-fw-bold);
  letter-spacing: 0.04em;
}

.subtitle {
  font-size: var(--uui-text-xs-size);
  color: var(--uui-text-tertiary);
  font-weight: var(--uui-fw-regular);
  padding-left: var(--uui-space-12);
  border-left: 1px solid var(--uui-border);
}

.nav-tabs {
  display: flex;
  gap: var(--uui-space-3);
}

.nav-tabs a {
  padding: 0 var(--uui-space-12);
  height: var(--uui-size-36);
  display: inline-flex;
  align-items: center;
  color: var(--uui-text-secondary);
  text-decoration: none;
  font-weight: var(--uui-fw-semibold);
  font-size: var(--uui-text-s-size);
  border-radius: var(--uui-radius-6);
  transition: all 0.12s ease;
  position: relative;
}

.nav-tabs a:hover {
  color: var(--uui-text-primary);
  background: var(--uui-night-100);
}

.nav-tabs a.active {
  color: var(--uui-blue-80);
  background: var(--uui-primary-subtle);
}

.nav-tabs a.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--uui-primary);
}

.main-content {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: var(--uui-space-24) var(--uui-space-30);
}

.page-header {
  margin-bottom: var(--uui-space-18);
}

.page-header h2 {
  font-size: var(--uui-h2-size);
  font-weight: var(--uui-h2-fw);
  line-height: var(--uui-h2-lh);
  color: var(--uui-text-primary);
  margin-bottom: var(--uui-space-3);
}

.page-header p {
  color: var(--uui-text-secondary);
  font-size: var(--uui-text-m-size);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--uui-space-18);
  margin-bottom: var(--uui-space-18);
}

.stat-card {
  background: var(--uui-surface-main);
  padding: var(--uui-space-18);
  border-radius: var(--uui-radius-12);
  border: 1px solid var(--uui-border);
  transition: all 0.12s ease;
}

.stat-card:hover {
  border-color: var(--uui-border-strong);
  box-shadow: var(--uui-shadow-200);
}

.stat-label {
  color: var(--uui-text-secondary);
  font-size: var(--uui-text-xs-size);
  font-weight: var(--uui-fw-semibold);
  text-transform: uppercase;
  letter-spacing: var(--uui-overline-tracking);
  margin-bottom: var(--uui-space-6);
}

.stat-value {
  font-size: 34px;
  font-weight: var(--uui-fw-bold);
  color: var(--uui-text-primary);
  line-height: 1;
}

.stat-card.warning .stat-value {
  color: var(--uui-warning);
}

.stat-card.success .stat-value {
  color: var(--uui-success);
}

.stat-card.danger .stat-value {
  color: var(--uui-error);
}

.stat-card.info .stat-value {
  color: var(--uui-info);
}

.card {
  background: var(--uui-surface-main);
  border-radius: var(--uui-radius-12);
  padding: var(--uui-space-18);
  border: 1px solid var(--uui-border);
  margin-bottom: var(--uui-space-18);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--uui-space-12);
  padding-bottom: var(--uui-space-12);
  border-bottom: 1px solid var(--uui-divider);
}

.card-title {
  font-size: var(--uui-h4-size);
  font-weight: var(--uui-h4-fw);
  line-height: var(--uui-h4-lh);
  color: var(--uui-text-primary);
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--uui-surface-lowest);
  border-top: 1px solid var(--uui-divider);
  border-bottom: 1px solid var(--uui-divider);
}

th {
  text-align: left;
  padding: 10px var(--uui-space-18);
  font-weight: var(--uui-fw-semibold);
  color: var(--uui-text-tertiary);
  font-size: var(--uui-text-xs-size);
  text-transform: uppercase;
  letter-spacing: var(--uui-overline-tracking);
}

td {
  padding: 14px var(--uui-space-18);
  border-top: 1px solid var(--uui-divider);
  color: var(--uui-text-primary);
  font-size: var(--uui-text-s-size);
}

tbody tr {
  transition: background-color 0.12s ease;
}

tbody tr:hover {
  background: var(--uui-night-50);
}

/* Badge component — mirrors UUI Badge */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 24px;
  padding: 0 9px;
  border-radius: var(--uui-radius-full);
  font-size: var(--uui-text-xs-size);
  font-weight: var(--uui-fw-semibold);
}

.badge::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.badge.success {
  background: var(--uui-success-subtle);
  color: var(--uui-green-70);
}

.badge.warning {
  background: var(--uui-warning-subtle);
  color: var(--uui-amber-70);
}

.badge.danger {
  background: var(--uui-error-subtle);
  color: var(--uui-fire-70);
}

.badge.info {
  background: var(--uui-info-subtle);
  color: var(--uui-cyan-70);
}

.badge.increasing {
  background: var(--uui-success-subtle);
  color: var(--uui-green-70);
}

.badge.decreasing {
  background: var(--uui-error-subtle);
  color: var(--uui-fire-70);
}

.badge.stable {
  background: var(--uui-accent-subtle);
  color: var(--uui-violet-70);
}

.badge.high {
  background: var(--uui-error-subtle);
  color: var(--uui-fire-70);
}

.badge.medium {
  background: var(--uui-warning-subtle);
  color: var(--uui-amber-70);
}

.badge.low {
  background: var(--uui-info-subtle);
  color: var(--uui-cyan-70);
}

.theme-toggle {
  width: var(--uui-size-36);
  height: var(--uui-size-36);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--uui-radius-6);
  background: transparent;
  color: var(--uui-icon);
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
  margin-right: var(--uui-space-6);
  flex-shrink: 0;
}

.theme-toggle:hover {
  background: var(--uui-night-100);
  color: var(--uui-icon-active);
}

.loading {
  text-align: center;
  padding: var(--uui-space-48);
  color: var(--uui-text-secondary);
  font-size: var(--uui-text-s-size);
}

.error {
  background: var(--uui-error-subtle);
  border: 1px solid var(--uui-fire-30);
  color: var(--uui-fire-70);
  padding: var(--uui-space-12);
  border-radius: var(--uui-radius-6);
  margin: var(--uui-space-12) 0;
  font-size: var(--uui-text-s-size);
}
</style>
