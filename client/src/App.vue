<template>
  <div class="app">
    <header class="top-nav">
      <div class="nav-container">
        <div class="logo">
          <h1>{{ t("nav.companyName") }}</h1>
          <span class="subtitle">{{ t("nav.subtitle") }}</span>
        </div>
        <nav class="nav-tabs" :aria-label="t('nav.companyName')">
          <router-link to="/" :class="{ active: $route.path === '/' }">
            {{ t("nav.overview") }}
          </router-link>
          <router-link
            to="/inventory"
            :class="{ active: $route.path === '/inventory' }"
          >
            {{ t("nav.inventory") }}
          </router-link>
          <router-link
            to="/orders"
            :class="{ active: $route.path === '/orders' }"
          >
            {{ t("nav.orders") }}
          </router-link>
          <router-link
            to="/spending"
            :class="{ active: $route.path === '/spending' }"
          >
            {{ t("nav.finance") }}
          </router-link>
          <router-link
            to="/demand"
            :class="{ active: $route.path === '/demand' }"
          >
            {{ t("nav.demandForecast") }}
          </router-link>
          <router-link
            to="/restocking"
            :class="{ active: $route.path === '/restocking' }"
          >
            {{ t("nav.restocking") }}
          </router-link>
          <router-link
            to="/reports"
            :class="{ active: $route.path === '/reports' }"
          >
            {{ t("nav.reports") }}
          </router-link>
        </nav>
        <ThemeToggle />
        <LanguageSwitcher />
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
import { ref, onMounted, computed } from "vue";
import { api } from "./api";
import { useAuth } from "./composables/useAuth";
import { useI18n } from "./composables/useI18n";
import FilterBar from "./components/FilterBar.vue";
import ProfileMenu from "./components/ProfileMenu.vue";
import ProfileDetailsModal from "./components/ProfileDetailsModal.vue";
import TasksModal from "./components/TasksModal.vue";
import LanguageSwitcher from "./components/LanguageSwitcher.vue";
import ThemeToggle from "./components/ThemeToggle.vue";

export default {
  name: "App",
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    ThemeToggle,
  },
  setup() {
    const { currentUser } = useAuth();
    const { t } = useI18n();
    const showProfileDetails = ref(false);
    const showTasks = ref(false);
    const apiTasks = ref([]);

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value];
    });

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks();
      } catch (err) {
        console.error("Failed to load tasks:", err);
      }
    };

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData);
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask);
      } catch (err) {
        console.error("Failed to add task:", err);
      }
    };

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some((t) => t.id === taskId);

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(
            (t) => t.id === taskId,
          );
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1);
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId);
          apiTasks.value = apiTasks.value.filter((t) => t.id !== taskId);
        }
      } catch (err) {
        console.error("Failed to delete task:", err);
      }
    };

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find((t) => t.id === taskId);

        if (mockTask) {
          // Toggle mock task status
          mockTask.status =
            mockTask.status === "pending" ? "completed" : "pending";
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId);
          const index = apiTasks.value.findIndex((t) => t.id === taskId);
          if (index !== -1) {
            apiTasks.value[index] = updatedTask;
          }
        }
      } catch (err) {
        console.error("Failed to toggle task:", err);
      }
    };

    onMounted(loadTasks);

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
    };
  },
};
</script>

<style>
:root {
  color-scheme: light;
  --bg: #f8fafc;
  --surface: #ffffff;
  --surface-muted: #f8fafc;
  --surface-sunken: #f1f5f9;
  --border: #e2e8f0;
  --border-strong: #cbd5e1;
  --border-subtle: #f1f5f9;
  --text-strong: #0f172a;
  --text: #1e293b;
  --text-secondary: #475569;
  --text-muted: #64748b;
  --text-subtle: #94a3b8;
  --on-accent: #ffffff;
  --accent: #2563eb;
  --accent-solid: #2563eb;
  --accent-soft: #eff6ff;
  --accent-ring: rgba(59, 130, 246, 0.3);
  --accent-ring-soft: rgba(59, 130, 246, 0.1);
  --brand-1: #667eea;
  --brand-2: #764ba2;
  --green: #10b981;
  --green-solid: #059669;
  --success-fg: #059669;
  --green-soft: #d1fae5;
  --green-bg: #f0fdf4;
  --green-border: #a7f3d0;
  --green-text: #065f46;
  --red: #ef4444;
  --red-solid: #dc2626;
  --danger-fg: #dc2626;
  --red-soft: #fecaca;
  --red-bg: #fef2f2;
  --red-text: #991b1b;
  --yellow: #f59e0b;
  --yellow-solid: #d97706;
  --orange: #ea580c;
  --warning-fg: #d97706;
  --yellow-soft: #fef3c7;
  --yellow-bg: #fffbeb;
  --yellow-border: #fcd34d;
  --orange-soft: #fed7aa;
  --orange-text: #92400e;
  --blue: #3b82f6;
  --blue-soft: #dbeafe;
  --blue-border: #bfdbfe;
  --blue-light: #60a5fa;
  --blue-text: #1e40af;
  --indigo-soft: #e0e7ff;
  --indigo-text: #3730a3;
  --purple: #8b5cf6;
  --purple-bg: #f5f3ff;
  --purple-border: #c4b5fd;
  --shadow-a: rgba(0, 0, 0, 0.08);
  --shadow-b: rgba(0, 0, 0, 0.15);
  --overlay: rgba(0, 0, 0, 0.5);
  --strong-bg: #0f172a;
  --strong-bg-hover: #1e293b;
}

:root[data-theme="dark"] {
  color-scheme: dark;
  --bg: #0b1220;
  --surface: #151f32;
  --surface-muted: #1a2539;
  --surface-sunken: #243049;
  --border: #2d3b52;
  --border-strong: #475569;
  --border-subtle: #222e45;
  --text-strong: #f8fafc;
  --text: #e2e8f0;
  --text-secondary: #cbd5e1;
  --text-muted: #9fb0c6;
  --text-subtle: #8394ac;
  --on-accent: #ffffff;
  --accent: #60a5fa;
  --accent-solid: #2563eb;
  --accent-soft: rgba(96, 165, 250, 0.16);
  --accent-ring: rgba(96, 165, 250, 0.4);
  --accent-ring-soft: rgba(96, 165, 250, 0.18);
  --green-soft: rgba(16, 185, 129, 0.2);
  --success-fg: #34d399;
  --green-bg: rgba(16, 185, 129, 0.1);
  --green-border: rgba(52, 211, 153, 0.35);
  --green-text: #6ee7b7;
  --danger-fg: #f87171;
  --red-soft: rgba(239, 68, 68, 0.22);
  --red-bg: rgba(239, 68, 68, 0.1);
  --red-text: #fca5a5;
  --warning-fg: #fbbf24;
  --yellow-soft: rgba(245, 158, 11, 0.2);
  --yellow-bg: rgba(245, 158, 11, 0.1);
  --yellow-border: rgba(251, 191, 36, 0.4);
  --orange-soft: rgba(245, 158, 11, 0.22);
  --orange-text: #fcd34d;
  --blue-soft: rgba(59, 130, 246, 0.22);
  --blue-border: rgba(96, 165, 250, 0.4);
  --blue-text: #93c5fd;
  --indigo-soft: rgba(99, 102, 241, 0.25);
  --indigo-text: #c7d2fe;
  --purple-bg: rgba(139, 92, 246, 0.12);
  --purple-border: rgba(167, 139, 250, 0.45);
  --shadow-a: rgba(0, 0, 0, 0.35);
  --shadow-b: rgba(0, 0, 0, 0.55);
  --overlay: rgba(0, 0, 0, 0.65);
  --strong-bg: #334155;
  --strong-bg-hover: #475569;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

a:focus-visible,
button:focus-visible,
[role="button"]:focus-visible,
[tabindex="0"]:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

/* Text-style button used inside clickable table rows for keyboard access */
.row-link {
  background: none;
  border: none;
  padding: 0;
  margin: 0;
  font: inherit;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.row-link:hover {
  color: var(--accent);
}

body {
  font-family:
    "Inter",
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    Roboto,
    Oxygen,
    Ubuntu,
    Cantarell,
    sans-serif;
  background: var(--surface-muted);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-nav {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 3px 0 var(--shadow-a);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 0 2rem;
  height: 70px;
}

.nav-container > .nav-tabs {
  margin-left: auto;
  margin-right: 1rem;
}

.nav-container > .theme-toggle {
  margin-right: 0.5rem;
}

.nav-container > .language-switcher {
  margin-right: 1rem;
}

.logo {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.logo h1 {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--text-strong);
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.813rem;
  color: var(--text-muted);
  font-weight: 400;
  padding-left: 0.75rem;
  border-left: 1px solid var(--border);
}

.nav-tabs {
  display: flex;
  gap: 0.25rem;
}

.nav-tabs a {
  white-space: nowrap;
}

.nav-tabs a {
  padding: 0.625rem 1.25rem;
  color: var(--text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: 6px;
  transition: all 0.2s ease;
  position: relative;
}

.nav-tabs a:hover {
  color: var(--text-strong);
  background: var(--surface-sunken);
}

.nav-tabs a.active {
  color: var(--accent);
  background: var(--accent-soft);
}

.nav-tabs a.active::after {
  content: "";
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-solid);
}

.main-content {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text-strong);
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--surface);
  padding: 1.25rem;
  border-radius: 10px;
  border: 1px solid var(--border);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--border-strong);
  box-shadow: 0 4px 12px var(--shadow-a);
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text-strong);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: var(--orange);
}

.stat-card.success .stat-value {
  color: var(--success-fg);
}

.stat-card.danger .stat-value {
  color: var(--danger-fg);
}

.stat-card.info .stat-value {
  color: var(--accent);
}

.card {
  background: var(--surface);
  border-radius: 10px;
  padding: 1.25rem;
  border: 1px solid var(--border);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-strong);
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
  background: var(--surface-muted);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--border-subtle);
  color: var(--text);
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
  padding: 0.313rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: var(--green-soft);
  color: var(--green-text);
}

.badge.warning {
  background: var(--orange-soft);
  color: var(--orange-text);
}

.badge.danger {
  background: var(--red-soft);
  color: var(--red-text);
}

.badge.info {
  background: var(--blue-soft);
  color: var(--blue-text);
}

.badge.increasing {
  background: var(--green-soft);
  color: var(--green-text);
}

.badge.decreasing {
  background: var(--red-soft);
  color: var(--red-text);
}

.badge.stable {
  background: var(--indigo-soft);
  color: var(--indigo-text);
}

.badge.high {
  background: var(--red-soft);
  color: var(--red-text);
}

.badge.medium {
  background: var(--orange-soft);
  color: var(--orange-text);
}

.badge.low {
  background: var(--blue-soft);
  color: var(--blue-text);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
  font-size: 0.938rem;
}

.error {
  background: var(--red-bg);
  border: 1px solid var(--red-soft);
  color: var(--red-text);
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

@media (max-width: 1024px) {
  .nav-container {
    flex-wrap: wrap;
    height: auto;
    padding: 0.5rem 1rem;
    row-gap: 0.5rem;
  }

  .nav-container > .nav-tabs {
    order: 3;
    flex: 0 0 100%;
    margin: 0;
    overflow-x: auto;
    padding-bottom: 0.25rem;
  }

  .nav-container > .language-switcher {
    margin-left: auto;
  }

  .main-content {
    padding: 1.25rem 1rem;
  }
}

@media (max-width: 640px) {
  .subtitle {
    display: none;
  }

  .logo h1 {
    font-size: 1.125rem;
  }

  .page-header h2 {
    font-size: 1.5rem;
  }

  .nav-tabs a {
    padding: 0.5rem 0.875rem;
  }

  .main-content {
    padding: 1rem 0.75rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-value {
    font-size: 1.75rem;
  }
}
</style>
