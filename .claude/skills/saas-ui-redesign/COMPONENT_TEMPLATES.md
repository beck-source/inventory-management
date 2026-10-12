# SaaS UI Redesign - Component Templates

Ready-to-use Vue 3 components for modern SaaS interfaces. Copy and customize for your project.

## Sidebar Navigation Component

**File: `src/components/Sidebar.vue`**

```vue
<template>
  <aside class="sidebar" :class="{ collapsed }">
    <!-- Logo / Brand -->
    <div class="sidebar-header">
      <router-link to="/" class="logo-link">
        <span class="logo-icon">🏭</span>
        <span class="logo-text">{{ appName }}</span>
      </router-link>
      <button
        v-if="isMobile"
        class="close-btn"
        @click="toggleCollapse"
        aria-label="Close sidebar"
      >
        ✕
      </button>
    </div>

    <!-- Main Navigation -->
    <nav class="sidebar-nav">
      <div class="nav-section">
        <div class="section-title">Main</div>
        <router-link
          v-for="item in mainItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :title="item.label"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </div>

      <div class="nav-section">
        <div class="section-title">Analytics</div>
        <router-link
          v-for="item in analyticsItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :title="item.label"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </div>
    </nav>

    <!-- Footer Info -->
    <div class="sidebar-footer">
      <p class="version-text">v{{ appVersion }}</p>
    </div>
  </aside>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'Sidebar',
  props: {
    appName: {
      type: String,
      default: 'Inventory'
    },
    appVersion: {
      type: String,
      default: '1.0.0'
    }
  },
  setup() {
    const collapsed = ref(false)
    const isMobile = ref(window.innerWidth < 768)

    const mainItems = [
      { path: '/', label: 'Dashboard', icon: '📊' },
      { path: '/inventory', label: 'Inventory', icon: '📦' },
      { path: '/orders', label: 'Orders', icon: '📋' },
      { path: '/demand', label: 'Demand', icon: '📈' },
      { path: '/backlog', label: 'Backlog', icon: '⚠️' }
    ]

    const analyticsItems = [
      { path: '/spending', label: 'Spending', icon: '💰' },
      { path: '/reports', label: 'Reports', icon: '📑' }
    ]

    const toggleCollapse = () => {
      collapsed.value = !collapsed.value
    }

    return {
      collapsed,
      isMobile,
      mainItems,
      analyticsItems,
      toggleCollapse
    }
  }
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 240px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  z-index: 1000;
  overflow-y: auto;
  transition: transform 0.3s ease;
}

.sidebar.collapsed {
  transform: translateX(-100%);
}

/* Sidebar Header */
.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: #0f172a;
  font-weight: bold;
  font-size: 1rem;
  flex: 1;
  min-width: 0;
}

.logo-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.logo-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.close-btn {
  display: none;
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 4px;
  color: #64748b;
}

.close-btn:hover {
  color: #0f172a;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-title {
  padding: 8px 16px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #94a3b8;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 0;
  border-radius: 6px;
  color: #475569;
  text-decoration: none;
  font-size: 0.9375rem;
  transition: all 0.2s ease;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.nav-item.router-link-active {
  background: #dbeafe;
  color: #0369a1;
  font-weight: 600;
}

.nav-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Sidebar Footer */
.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  text-align: center;
}

.version-text {
  font-size: 0.75rem;
  color: #94a3b8;
  margin: 0;
}

/* Scrollbar styling */
.sidebar-nav::-webkit-scrollbar {
  width: 6px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.sidebar-nav::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Mobile Responsive */
@media (max-width: 768px) {
  .sidebar {
    width: 100%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .close-btn {
    display: block;
  }

  .sidebar.collapsed {
    transform: translateX(-100%);
  }
}
</style>
```

## Top Header Component

**File: `src/components/TopHeader.vue`**

```vue
<template>
  <header class="top-header">
    <!-- Left side: Menu toggle + Breadcrumbs -->
    <div class="header-left">
      <button
        class="menu-toggle"
        @click="$emit('toggle-menu')"
        aria-label="Toggle sidebar"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <line x1="3" y1="6" x2="21" y2="6" stroke-width="2"></line>
          <line x1="3" y1="12" x2="21" y2="12" stroke-width="2"></line>
          <line x1="3" y1="18" x2="21" y2="18" stroke-width="2"></line>
        </svg>
      </button>

      <!-- Optional Breadcrumbs -->
      <nav class="breadcrumbs" v-if="breadcrumbs.length">
        <span v-for="(crumb, i) in breadcrumbs" :key="i" class="breadcrumb-item">
          <router-link v-if="crumb.path" :to="crumb.path">
            {{ crumb.label }}
          </router-link>
          <span v-else>{{ crumb.label }}</span>
          <span v-if="i < breadcrumbs.length - 1" class="separator">/</span>
        </span>
      </nav>
    </div>

    <!-- Right side: Actions + Profile -->
    <div class="header-right">
      <!-- Search (optional) -->
      <div class="search-box" v-if="showSearch">
        <input
          type="text"
          placeholder="Search..."
          class="search-input"
          @focus="searchFocus = true"
          @blur="searchFocus = false"
        />
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <circle cx="11" cy="11" r="8"></circle>
          <path d="m21 21-4.35-4.35"></path>
        </svg>
      </div>

      <!-- Notifications -->
      <button class="header-icon-btn" title="Notifications">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
        </svg>
        <span class="notification-badge">3</span>
      </button>

      <!-- Language Switcher -->
      <button class="header-icon-btn" title="Language" @click="cycleLanguage">
        {{ currentLanguage }}
      </button>

      <!-- Divider -->
      <div class="divider"></div>

      <!-- Profile Menu -->
      <div class="profile-menu" v-click-outside="closeProfile">
        <button class="profile-btn" @click="toggleProfile">
          <img :src="userAvatar" :alt="userName" class="avatar" />
          <span class="user-name">{{ userName }}</span>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            :class="{ rotated: profileOpen }"
          >
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>

        <!-- Dropdown Menu -->
        <div class="dropdown" v-show="profileOpen">
          <button class="dropdown-item">
            <span>👤</span> Profile
          </button>
          <button class="dropdown-item">
            <span>⚙️</span> Settings
          </button>
          <button class="dropdown-item">
            <span>📚</span> Help
          </button>
          <hr class="dropdown-divider" />
          <button class="dropdown-item logout">
            <span>🚪</span> Logout
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'TopHeader',
  props: {
    breadcrumbs: {
      type: Array,
      default: () => []
    },
    userName: {
      type: String,
      default: 'John Doe'
    },
    userAvatar: {
      type: String,
      default: 'https://api.dicebear.com/7.x/avataaars/svg?seed=John'
    },
    showSearch: {
      type: Boolean,
      default: false
    }
  },
  emits: ['toggle-menu', 'logout'],
  setup(props, { emit }) {
    const profileOpen = ref(false)
    const searchFocus = ref(false)
    const currentLanguage = ref('EN')

    const toggleProfile = () => {
      profileOpen.value = !profileOpen.value
    }

    const closeProfile = () => {
      profileOpen.value = false
    }

    const cycleLanguage = () => {
      currentLanguage.value = currentLanguage.value === 'EN' ? 'JP' : 'EN'
    }

    return {
      profileOpen,
      searchFocus,
      currentLanguage,
      toggleProfile,
      closeProfile,
      cycleLanguage
    }
  }
}
</script>

<style scoped>
.top-header {
  position: sticky;
  top: 0;
  left: 240px;
  height: 64px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  z-index: 100;
  gap: 24px;
  transition: left 0.3s ease;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.menu-toggle {
  display: none;
  background: none;
  border: none;
  color: #475569;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.menu-toggle:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.875rem;
  color: #64748b;
  min-width: 0;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.breadcrumb-item a {
  color: #3b82f6;
  text-decoration: none;
}

.breadcrumb-item a:hover {
  text-decoration: underline;
}

.separator {
  color: #cbd5e1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  position: relative;
  width: 200px;
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 36px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-box svg {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  pointer-events: none;
}

.header-icon-btn {
  position: relative;
  background: none;
  border: none;
  color: #475569;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.header-icon-btn:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: white;
  font-size: 0.65rem;
  padding: 2px 4px;
  border-radius: 10px;
  font-weight: bold;
}

.divider {
  width: 1px;
  height: 32px;
  background: #e2e8f0;
}

.profile-menu {
  position: relative;
}

.profile-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
  color: #0f172a;
  font-size: 0.875rem;
}

.profile-btn:hover {
  background: #f1f5f9;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e2e8f0;
}

.user-name {
  font-weight: 500;
}

.profile-btn svg {
  transition: transform 0.2s;
}

.profile-btn svg.rotated {
  transform: rotate(180deg);
}

.dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  min-width: 180px;
  z-index: 1000;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  background: none;
  border: none;
  color: #475569;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
  text-align: left;
}

.dropdown-item:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.dropdown-item.logout {
  color: #ef4444;
}

.dropdown-item.logout:hover {
  background: #fee2e2;
}

.dropdown-divider {
  margin: 4px 0;
  border: none;
  border-top: 1px solid #e2e8f0;
}

@media (max-width: 768px) {
  .top-header {
    left: 0;
  }

  .menu-toggle {
    display: block;
  }

  .breadcrumbs {
    display: none;
  }

  .search-box {
    display: none;
  }

  .user-name {
    display: none;
  }
}
</style>

<!-- Add this to your main.js for the click-outside directive -->
<script>
// Define v-click-outside directive
const vClickOutside = {
  mounted(el, binding) {
    el.clickOutsideEvent = function (event) {
      if (!(el == event.target || el.contains(event.target))) {
        binding.value(event)
      }
    }
    document.addEventListener('click', el.clickOutsideEvent)
  },
  unmounted(el) {
    document.removeEventListener('click', el.clickOutsideEvent)
  }
}
</script>
```

## Updated App.vue Layout

**File: `src/App.vue`**

```vue
<template>
  <div class="app">
    <Sidebar ref="sidebarRef" />

    <div class="main-layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <TopHeader
        @toggle-menu="toggleSidebar"
        :breadcrumbs="currentBreadcrumbs"
      />

      <FilterBar v-if="showFilters" />

      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import Sidebar from './components/Sidebar.vue'
import TopHeader from './components/TopHeader.vue'
import FilterBar from './components/FilterBar.vue'

export default {
  name: 'App',
  components: {
    Sidebar,
    TopHeader,
    FilterBar
  },
  setup() {
    const sidebarRef = ref(null)
    const sidebarCollapsed = ref(false)
    const route = useRoute()

    const showFilters = computed(() => {
      return !['/'].includes(route.path)
    })

    const currentBreadcrumbs = computed(() => {
      const breadcrumbs = [{ label: 'Home', path: '/' }]

      if (route.path !== '/') {
        const label = route.path.slice(1).charAt(0).toUpperCase() + route.path.slice(2)
        breadcrumbs.push({ label })
      }

      return breadcrumbs
    })

    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
      if (sidebarRef.value) {
        sidebarRef.value.$el.classList.toggle('collapsed')
      }
    }

    return {
      sidebarRef,
      sidebarCollapsed,
      showFilters,
      currentBreadcrumbs,
      toggleSidebar
    }
  }
}
</script>

<style scoped>
.app {
  display: flex;
  min-height: 100vh;
  background: #f9fafb;
}

.main-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 240px;
  transition: margin-left 0.3s ease;
}

.main-layout.sidebar-collapsed {
  margin-left: 0;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .main-layout {
    margin-left: 0;
  }
}
</style>
```

## Card Component (Reusable)

**File: `src/components/Card.vue`**

```vue
<template>
  <div class="card" :class="{ hoverable, elevated }">
    <div v-if="$slots.header" class="card-header">
      <slot name="header"></slot>
    </div>

    <div class="card-content">
      <slot></slot>
    </div>

    <div v-if="$slots.footer" class="card-footer">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Card',
  props: {
    hoverable: Boolean,
    elevated: Boolean
  }
}
</script>

<style scoped>
.card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.card.hoverable:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
  border-color: #cbd5e1;
}

.card.elevated {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.card-content {
  padding: 20px 24px;
}

.card-footer {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}
</style>
```

---

**Pro Tips:**
1. Copy these components into your project as-is
2. Customize colors using CSS variables
3. Update icon sets to match your design
4. Test on mobile devices before shipping
5. Use the components together for best results

All components follow the SaaS design system and spacing guidelines from the main skill documentation.
