<template>
  <div
    class="flex min-h-screen bg-sia-mist text-slate-700 dark:bg-sia-ink dark:text-slate-200"
  >
    <SidebarNav :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />

    <div class="flex-1 flex flex-col min-w-0">
      <header
        class="sticky top-0 z-30 bg-white/80 backdrop-blur border-b border-sia-line dark:bg-sia-panel/80 dark:border-sia-border"
      >
        <div class="flex items-center gap-3 px-8 h-16">
          <button
            class="lg:hidden p-2 -ml-2 rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            @click="toggleSidebar"
            aria-label="Toggle sidebar"
          >
            <Menu :size="20" />
          </button>

          <div class="hidden md:flex items-center gap-2 flex-1 max-w-md">
            <div class="relative w-full">
              <Search
                :size="16"
                class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                placeholder="Search inventory, orders…"
                class="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm placeholder:text-slate-400 focus:outline-none focus:border-sia-blue focus:bg-white focus:ring-2 focus:ring-sia-blue/10 transition dark:bg-slate-800 dark:border-sia-border dark:placeholder:text-slate-500 dark:text-slate-100 dark:focus:bg-slate-800"
              />
            </div>
          </div>

          <div class="flex-1 md:hidden" />

          <!-- Light/dark toggle. Shows the icon for the mode the user will switch TO. -->
          <button
            class="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800"
            @click="toggleTheme"
            :aria-label="
              theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
            "
            :title="
              theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
            "
          >
            <Sun v-if="theme === 'dark'" :size="18" />
            <Moon v-else :size="18" />
          </button>

          <button
            class="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800"
            aria-label="Notifications"
          >
            <Bell :size="18" />
          </button>

          <div class="h-6 w-px bg-slate-200 mx-1 dark:bg-sia-border" />

          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>

      <FilterBar />

      <main class="flex-1 px-8 py-6 overflow-x-hidden">
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
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { Menu, Bell, Search, Sun, Moon } from "lucide-vue-next";
import { api } from "./api";
import { useAuth } from "./composables/useAuth";
import { useI18n } from "./composables/useI18n";
import { useTheme } from "./composables/useTheme";
import SidebarNav from "./components/SidebarNav.vue";
import FilterBar from "./components/FilterBar.vue";
import ProfileMenu from "./components/ProfileMenu.vue";
import ProfileDetailsModal from "./components/ProfileDetailsModal.vue";
import TasksModal from "./components/TasksModal.vue";
import LanguageSwitcher from "./components/LanguageSwitcher.vue";

const SIDEBAR_KEY = "sia.sidebar.collapsed";

export default {
  name: "App",
  components: {
    SidebarNav,
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    Menu,
    Bell,
    Search,
    Sun,
    Moon,
  },
  setup() {
    const { currentUser } = useAuth();
    const { t } = useI18n();
    // Dark mode toggle wiring. The composable already applied the initial
    // theme at module load, so all we need here is the reactive ref + handler.
    const { theme, toggleTheme } = useTheme();
    const showProfileDetails = ref(false);
    const showTasks = ref(false);
    const apiTasks = ref([]);

    const stored = localStorage.getItem(SIDEBAR_KEY);
    const sidebarCollapsed = ref(
      stored === null
        ? typeof window !== "undefined" && window.innerWidth < 1024
        : stored === "true",
    );

    let userToggled = stored !== null;

    const toggleSidebar = () => {
      userToggled = true;
      sidebarCollapsed.value = !sidebarCollapsed.value;
    };

    watch(sidebarCollapsed, (v) => {
      localStorage.setItem(SIDEBAR_KEY, String(v));
    });

    // Auto-collapse when user resizes down to a smaller viewport, unless they've explicitly
    // toggled in this session. This keeps the icons-only mode useful on tablet/narrow desktop.
    const onResize = () => {
      if (userToggled) return;
      sidebarCollapsed.value = window.innerWidth < 1024;
    };

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
        apiTasks.value.unshift(newTask);
      } catch (err) {
        console.error("Failed to add task:", err);
      }
    };

    const deleteTask = async (taskId) => {
      try {
        const isMockTask = currentUser.value.tasks.some((t) => t.id === taskId);
        if (isMockTask) {
          const index = currentUser.value.tasks.findIndex(
            (t) => t.id === taskId,
          );
          if (index !== -1) currentUser.value.tasks.splice(index, 1);
        } else {
          await api.deleteTask(taskId);
          apiTasks.value = apiTasks.value.filter((t) => t.id !== taskId);
        }
      } catch (err) {
        console.error("Failed to delete task:", err);
      }
    };

    const toggleTask = async (taskId) => {
      try {
        const mockTask = currentUser.value.tasks.find((t) => t.id === taskId);
        if (mockTask) {
          mockTask.status =
            mockTask.status === "pending" ? "completed" : "pending";
        } else {
          const updatedTask = await api.toggleTask(taskId);
          const index = apiTasks.value.findIndex((t) => t.id === taskId);
          if (index !== -1) apiTasks.value[index] = updatedTask;
        }
      } catch (err) {
        console.error("Failed to toggle task:", err);
      }
    };

    onMounted(() => {
      loadTasks();
      window.addEventListener("resize", onResize);
    });

    onUnmounted(() => {
      window.removeEventListener("resize", onResize);
    });

    return {
      t,
      sidebarCollapsed,
      toggleSidebar,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask,
      theme,
      toggleTheme,
    };
  },
};
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family:
    "Sora",
    "Inter",
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    Roboto,
    sans-serif;
  background: #f5f7fb;
  color: #0a1633;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Page primitives kept compatible with existing views, restyled to Sia palette. */

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0a1633;
  margin-bottom: 0.25rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: #64748b;
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1.25rem 1.375rem;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: linear-gradient(90deg, #00b6f0, #deecfc 60%, #ffeaf0);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 8px 24px -12px rgba(10, 22, 51, 0.15);
  transform: translateY(-1px);
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-label {
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0a1633;
  letter-spacing: -0.025em;
  font-feature-settings: "tnum";
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
  color: #00b6f0;
}

.card {
  background: white;
  border-radius: 14px;
  padding: 1.375rem;
  border: 1px solid #e2e8f0;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 2px rgba(10, 22, 51, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 1.0625rem;
  font-weight: 700;
  color: #0a1633;
  letter-spacing: -0.015em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

th {
  text-align: left;
  padding: 0.625rem 0.75rem;
  font-weight: 600;
  color: #475569;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.625rem 0.75rem;
  border-top: 1px solid #f1f5f9;
  color: #334155;
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}
tbody tr:hover {
  background: #f8fafc;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
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
  background: #deecfc;
  color: #0a3a5e;
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
  background: #deecfc;
  color: #0a3a5e;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 1rem;
  border-radius: 10px;
  margin: 1rem 0;
  font-size: 0.938rem;
}

/* -------------------------------------------------------------------------
 * Dark mode overrides
 * -------------------------------------------------------------------------
 * The global selectors above use hardcoded hex colors (legacy from the
 * pre-Tailwind shell), so Tailwind's `dark:` utilities can't override them
 * inline. We re-state the affected rules under `:root.dark` instead. The
 * `dark` class is toggled by `useTheme.js` on <html>. Scope: page wrappers,
 * cards, status badges, table chrome. Charts/SVG keep their own colors.
 */
:root.dark body {
  background: #0b1220;
  color: #e5e7eb;
}

:root.dark .page-header h2 {
  color: #f1f5f9;
}
:root.dark .page-header p {
  color: #94a3b8;
}

:root.dark .stat-card {
  background: #111a2e;
  border-color: #1e2a4a;
}
:root.dark .stat-label {
  color: #94a3b8;
}
:root.dark .stat-value {
  color: #f1f5f9;
}
:root.dark .stat-sub {
  color: #94a3b8;
}

:root.dark .card {
  background: #111a2e;
  border-color: #1e2a4a;
}
:root.dark .card-header {
  border-color: #1e2a4a;
}
:root.dark .card-title {
  color: #f1f5f9;
}

:root.dark .table-container,
:root.dark table {
  background: transparent;
}
:root.dark th {
  background: #0e1426;
  color: #94a3b8;
  border-color: #1e2a4a;
}
:root.dark td {
  color: #e5e7eb;
  border-color: #1e2a4a;
}
:root.dark tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}

:root.dark .loading,
:root.dark .error {
  color: #94a3b8;
}

/* Filter bar (the FilterBar.vue background is hardcoded white). */
:root.dark .filter-bar,
:root.dark .filter-container {
  background: #0e1426;
  border-color: #1e2a4a;
}
:root.dark .filter-bar select,
:root.dark .filter-container select {
  background: #111a2e;
  color: #e5e7eb;
  border-color: #1e2a4a;
}
:root.dark .filter-bar label {
  color: #94a3b8;
}

/* -------------------------------------------------------------------------
 * Per-view dark-mode surface overrides
 * -------------------------------------------------------------------------
 * Each view (Restocking, Demand, Spending, etc.) defines its own semantic
 * classes (.budget-panel, .trend-card, .kpi-card, ...) inside <style scoped>,
 * with hardcoded light backgrounds. Scoped CSS adds a [data-v-X] attribute
 * selector — specificity 0,2,0. Our `:root.dark .foo` selectors are 0,2,1
 * and win in dark mode.
 *
 * Strategy: cover the surface classes (panels, cards, stat tiles, inputs)
 * with a uniform dark palette. Text colors flow from the body's `color`
 * cascade where possible; we only override where the scoped rule pinned
 * a specific text color.
 */

/* Surface panels — anything white or near-white */
:root.dark .budget-panel,
:root.dark .kpi-card,
:root.dark .trend-card,
:root.dark .metric-card,
:root.dark .chart-card,
:root.dark .table-card,
:root.dark .donut-chart-card,
:root.dark .forecast-card {
  background: #111a2e;
  border-color: #1e2a4a;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}

/* Soft-tint inner tiles (the #f8fafc sub-surfaces) */
:root.dark .summary-stat,
:root.dark .stat-tile,
:root.dark .insight-tile,
:root.dark .breakdown-row,
:root.dark .sub-card {
  background: #0e1426;
  border-color: #1e2a4a;
}

/* Headings/values that were pinned to slate-900 */
:root.dark .budget-value,
:root.dark .summary-value,
:root.dark .metric-value,
:root.dark .kpi-value,
:root.dark .trend-value {
  color: #f1f5f9;
}

/* Muted labels pinned to slate-500 */
:root.dark .budget-label,
:root.dark .summary-label,
:root.dark .metric-label,
:root.dark .kpi-label,
:root.dark .trend-label,
:root.dark .hint {
  color: #94a3b8;
}

/* Form inputs (qty input, search boxes inside views) */
:root.dark .qty-input,
:root.dark .text-input,
:root.dark input[type="number"],
:root.dark input[type="text"]:not([data-keep-light]),
:root.dark select:not([data-keep-light]) {
  background: #0e1426;
  color: #f1f5f9;
  border-color: #1e2a4a;
}
:root.dark .qty-input:hover {
  border-color: #2a3a66;
}
:root.dark .qty-input:focus {
  border-color: var(--sia-blue, #00b6f0);
  box-shadow: 0 0 0 3px rgba(0, 182, 240, 0.15);
}

/* Banners (success/error toast). Keep semantic hue but darken background. */
:root.dark .banner-success {
  background: rgba(16, 185, 129, 0.12);
  color: #6ee7b7;
  border-color: rgba(16, 185, 129, 0.3);
}
:root.dark .banner-error {
  background: rgba(220, 38, 38, 0.12);
  color: #fca5a5;
  border-color: rgba(220, 38, 38, 0.3);
}

/* Dividers (the #f1f5f9 hairlines inside panels) */
:root.dark .budget-controls,
:root.dark .actions {
  border-color: #1e2a4a;
}

/* Negative-budget warning text stays red — no override needed */

/* Primary action buttons across views — slate-900 → keep dark but lighten on hover for visibility */
:root.dark .btn-primary {
  background: #1e2a4a;
}
:root.dark .btn-primary:hover:not(:disabled) {
  background: #2a3a66;
}
:root.dark .btn-primary:disabled {
  background: #1e2a4a;
  color: #475569;
}
</style>
