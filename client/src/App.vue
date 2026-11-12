<template>
  <div class="app-shell">
    <AppSidebar
      :items="navItems"
      :mobile-open="drawerOpen"
      :collapse-label="t('nav.collapseSidebar')"
      :expand-label="t('nav.expandSidebar')"
      @close="drawerOpen = false"
    >
      <template #brand>
        <div class="brand">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </template>
      <template #brand-mini>
        <span class="brand-monogram" role="img" :aria-label="t('nav.companyName')">{{ monogram }}</span>
      </template>
    </AppSidebar>

    <div class="app-main">
      <header class="app-topbar">
        <button
          type="button"
          class="app-menu-button"
          aria-controls="app-sidebar"
          :aria-expanded="drawerOpen"
          :aria-label="t('nav.openMenu')"
          @click="drawerOpen = true"
        >
          <svg class="menu-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path :d="icons.menu" />
          </svg>
        </button>
        <div class="app-topbar-title">{{ pageTitle }}</div>
        <div class="app-topbar-actions">
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>
      <div class="app-toolbar">
        <FilterBar />
      </div>
      <main class="app-content">
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
import { useRoute } from 'vue-router'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import AppSidebar from './components/AppSidebar.vue'
import { icons } from './components/icons.js'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    AppSidebar
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const drawerOpen = ref(false)
    const route = useRoute()

    const navItems = computed(() => [
      { to: '/', label: t('nav.overview'), icon: 'dashboard' },
      { to: '/inventory', label: t('nav.inventory'), icon: 'box' },
      { to: '/orders', label: t('nav.orders'), icon: 'clipboard' },
      { to: '/backlog', label: t('nav.backlog'), icon: 'layers' },
      { to: '/spending', label: t('nav.finance'), icon: 'dollar' },
      { to: '/demand', label: t('nav.demandForecast'), icon: 'trendingUp' },
      { to: '/reports', label: t('nav.reports'), icon: 'fileText' }
    ])

    const pageTitle = computed(() => {
      const item = navItems.value.find(i => i.to === route.path)
      return item ? item.label : ''
    })

    // Short brand mark for the collapsed sidebar: initials of the first two words
    const monogram = computed(() => {
      const words = t('nav.companyName').trim().split(/\s+/)
      return words.slice(0, 2).map(w => Array.from(w)[0]).join('').toUpperCase()
    })
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
      showProfileDetails,
      showTasks,
      drawerOpen,
      navItems,
      pageTitle,
      monogram,
      icons,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style scoped>
.brand {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: var(--leading-tight);
}

.brand-name,
.brand-subtitle {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-name {
  font-size: var(--text-md);
  font-weight: var(--weight-bold);
  color: var(--sidebar-item-active-text);
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--sidebar-text);
}

.brand-monogram {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-item-active-text);
  font-size: var(--text-base);
  font-weight: var(--weight-bold);
}

.menu-icon {
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

@media (min-width: 901px) {
  .app-toolbar {
    position: sticky;
    top: var(--topbar-height);
    /* Below the topbar so its dropdowns paint over the toolbar */
    z-index: calc(var(--z-topbar) - 1);
  }
}
</style>
