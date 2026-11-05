---
description: Transform Vue 3 app from horizontal top nav to modern SaaS-style vertical sidebar navigation
---

# SaaS Sidebar Navigation Redesign

Transform the Factory Inventory Management System from horizontal top navigation to a modern SaaS-style vertical sidebar, similar to Linear, Notion, or Vercel dashboards.

## What This Command Does

This command delegates to **vue-expert** to:
1. Create a new collapsible Sidebar component (260px ↔ 72px)
2. Restructure App.vue from top nav to flex layout with sidebar
3. Reposition FilterBar to top of content area
4. Add compact mode to ProfileMenu and LanguageSwitcher
5. Add navigation icons (Heroicons outline style)
6. Implement mobile responsive behavior
7. Preserve all existing functionality (routing, filters, modals, i18n)

## Prerequisites

- Vue 3 with Composition API
- Vue Router configured
- Existing App.vue with horizontal top navigation
- FilterBar, ProfileMenu, and LanguageSwitcher components

## Implementation Instructions for vue-expert

### Step 1: Create Sidebar State Composable (5 min)

**File:** `client/src/composables/useSidebar.js`

```javascript
import { ref } from 'vue'

// Module-level reactive state (singleton pattern)
const isCollapsed = ref(false)
const isMobileOpen = ref(false)

export function useSidebar() {
  const toggleSidebar = () => {
    isCollapsed.value = !isCollapsed.value
  }

  const toggleMobileMenu = () => {
    isMobileOpen.value = !isMobileOpen.value
  }

  const closeMobileMenu = () => {
    isMobileOpen.value = false
  }

  return {
    isCollapsed,
    isMobileOpen,
    toggleSidebar,
    toggleMobileMenu,
    closeMobileMenu
  }
}
```

### Step 2: Create Sidebar Component (45 min)

**File:** `client/src/components/Sidebar.vue`

**Template:**
```vue
<template>
  <aside 
    class="sidebar" 
    :class="{ collapsed: isCollapsed, 'mobile-open': isMobileOpen }"
  >
    <!-- Header with Logo and Collapse Button -->
    <div class="sidebar-header">
      <div class="logo" v-if="!isCollapsed">
        <svg class="logo-icon" width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="url(#gradient)" />
          <path d="M16 8L8 12V20L16 24L24 20V12L16 8Z" stroke="white" stroke-width="2" fill="none"/>
          <defs>
            <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
              <stop offset="0%" stop-color="#2563eb" />
              <stop offset="100%" stop-color="#1e40af" />
            </linearGradient>
          </defs>
        </svg>
        <div class="logo-text">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>
      <div class="logo-compact" v-else>
        <svg class="logo-icon" width="32" height="32" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="url(#gradient-compact)" />
          <path d="M16 8L8 12V20L16 24L24 20V12L16 8Z" stroke="white" stroke-width="2" fill="none"/>
          <defs>
            <linearGradient id="gradient-compact" x1="0" y1="0" x2="32" y2="32">
              <stop offset="0%" stop-color="#2563eb" />
              <stop offset="100%" stop-color="#1e40af" />
            </linearGradient>
          </defs>
        </svg>
      </div>
      <button 
        class="collapse-toggle" 
        @click="toggleSidebar"
        :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path 
            :d="isCollapsed ? 'M8 4L14 10L8 16' : 'M12 4L6 10L12 16'" 
            stroke="currentColor" 
            stroke-width="2" 
            stroke-linecap="round" 
            stroke-linejoin="round"
          />
        </svg>
      </button>
    </div>

    <!-- Navigation Links -->
    <nav class="sidebar-nav">
      <router-link 
        v-for="item in navItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        @click="closeMobileMenu"
      >
        <component :is="item.icon" class="nav-icon" />
        <span v-if="!isCollapsed">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Footer with Language Switcher and Profile Menu -->
    <div class="sidebar-footer">
      <LanguageSwitcher :compact="isCollapsed" />
      <ProfileMenu 
        :compact="isCollapsed"
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>

  <!-- Mobile Overlay -->
  <div 
    v-if="isMobileOpen" 
    class="sidebar-overlay"
    @click="closeMobileMenu"
  ></div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

// Icons as inline SVG components
const HomeIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M3 10L10 3L17 10M5 8V17H8V13H12V17H15V8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
}

const CubeIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M10 2L3 6V14L10 18L17 14V6L10 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M3 6L10 10M10 10L17 6M10 10V18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
}

const ShoppingBagIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M6 2L3 6V16C3 17.1046 3.89543 18 5 18H15C16.1046 18 17 17.1046 17 16V6L14 2H6Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M3 6H17M13 10C13 11.6569 11.6569 13 10 13C8.34315 13 7 11.6569 7 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
}

const CurrencyDollarIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M10 2C14.4183 2 18 5.58172 18 10C18 14.4183 14.4183 18 10 18C5.58172 18 2 14.4183 2 10C2 5.58172 5.58172 2 10 2Z" stroke="currentColor" stroke-width="2"/>
      <path d="M10 6V14M13 7C13 7 12 6 10 6C8 6 8 7 8 7.5C8 8 8.5 8.5 10 8.5C11.5 8.5 12 9 12 9.5C12 10 12 11 10 11C8 11 7 10 7 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg>
  `
}

const ChartBarIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M3 17V13M10 17V7M17 17V11M3 9L9.5 3L13 6.5L17 2.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
}

const DocumentTextIcon = {
  template: `
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M4 4C4 2.89543 4.89543 2 6 2H11L16 7V16C16 17.1046 15.1046 18 14 18H6C4.89543 18 4 17.1046 4 16V4Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M11 2V7H16M7 10H13M7 13H13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
}

const { t } = useI18n()
const { isCollapsed, isMobileOpen, toggleSidebar, closeMobileMenu } = useSidebar()

defineEmits(['show-profile-details', 'show-tasks'])

const navItems = computed(() => [
  { path: '/', label: t('nav.overview'), icon: HomeIcon },
  { path: '/inventory', label: t('nav.inventory'), icon: CubeIcon },
  { path: '/orders', label: t('nav.orders'), icon: ShoppingBagIcon },
  { path: '/spending', label: t('nav.finance'), icon: CurrencyDollarIcon },
  { path: '/demand', label: t('nav.demandForecast'), icon: ChartBarIcon },
  { path: '/reports', label: 'Reports', icon: DocumentTextIcon }
])
</script>

<style scoped>
.sidebar {
  width: 260px;
  background: white;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  flex-shrink: 0;
  position: relative;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-header {
  padding: 1.25rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
}

.logo-icon {
  flex-shrink: 0;
}

.logo-text {
  flex: 1;
  min-width: 0;
}

.logo-text h1 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  line-height: 1.2;
}

.logo-text .subtitle {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
}

.logo-compact {
  flex: 1;
  display: flex;
  justify-content: center;
}

.collapse-toggle {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.collapse-toggle:hover {
  background: #f8fafc;
  color: #334155;
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0.75rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.875rem;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
  position: relative;
}

.nav-item:hover {
  background: #f8fafc;
  color: #334155;
}

.nav-item.router-link-active {
  background: #eff6ff;
  color: #2563eb;
}

.nav-item.router-link-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: #2563eb;
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  flex-shrink: 0;
}

.sidebar.collapsed .nav-item span {
  display: none;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.625rem;
}

.sidebar-footer {
  border-top: 1px solid #e2e8f0;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* Mobile Styles */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
    width: 260px;
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .sidebar.collapsed {
    width: 260px;
  }

  .sidebar-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 199;
  }
}
</style>
```

### Step 3: Modify App.vue Layout (30 min)

**Changes to make:**

1. **Import Sidebar component** (add after line 66):
```javascript
import Sidebar from './components/Sidebar.vue'
```

2. **Add Sidebar to components** (update line 70-76):
```javascript
components: {
  Sidebar,
  FilterBar,
  ProfileMenu,
  ProfileDetailsModal,
  TasksModal,
  LanguageSwitcher
}
```

3. **Replace template** (lines 1-54) with:
```vue
<template>
  <div class="app-container">
    <Sidebar 
      @show-profile-details="showProfileDetails = true"
      @show-tasks="showTasks = true"
    />
    
    <!-- Mobile Menu Button -->
    <button 
      class="mobile-menu-btn"
      @click="toggleMobileMenu"
      title="Toggle menu"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M3 10H17M3 5H17M3 15H17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div class="main-wrapper">
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
```

4. **Add useSidebar import** (line 61):
```javascript
import { useSidebar } from './composables/useSidebar'
```

5. **Add toggleMobileMenu** to setup (after line 79):
```javascript
const { toggleMobileMenu } = useSidebar()
```

6. **Update return statement** (add toggleMobileMenu):
```javascript
return {
  t,
  showProfileDetails,
  showTasks,
  tasks,
  addTask,
  deleteTask,
  toggleTask,
  toggleMobileMenu
}
```

7. **Replace all styles** (in `<style>` block) with:
```css
/* Remove old top-nav styles completely */

.app-container {
  display: flex;
  min-height: 100vh;
  background: #f8fafc;
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-content {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem;
}

.mobile-menu-btn {
  display: none;
}

@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    position: fixed;
    top: 1rem;
    left: 1rem;
    z-index: 100;
    width: 40px;
    height: 40px;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    color: #64748b;
  }

  .mobile-menu-btn:hover {
    background: #f8fafc;
  }

  .main-content {
    padding: 4rem 1rem 1rem 1rem;
  }
}

/* Keep all existing global styles below (cards, tables, badges, etc.) */
```

### Step 4: Update FilterBar Component (15 min)

**File:** `client/src/components/FilterBar.vue`

**Changes to styles** (starting at line 101):

1. Update `.filters-bar` class:
```css
.filters-bar {
  background: white;
  border-bottom: 1px solid #e2e8f0;
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 90;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.filters-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}
```

### Step 5: Add Compact Mode to ProfileMenu (20 min)

**File:** `client/src/components/ProfileMenu.vue`

**Changes:**

1. **Add compact prop** (after line 76):
```javascript
const props = defineProps({
  compact: {
    type: Boolean,
    default: false
  }
})
```

2. **Update template** for compact mode (replace lines 2-23):
```vue
<div class="profile-menu" :class="{ compact: props.compact }">
  <button
    class="profile-button"
    :class="{ 'compact-button': props.compact }"
    @click="toggleDropdown"
    @blur="handleBlur"
  >
    <div class="avatar">
      {{ getInitials(currentUser.name) }}
    </div>
    <template v-if="!props.compact">
      <span class="profile-name">{{ currentUser.name }}</span>
      <svg
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </template>
  </button>
```

3. **Update dropdown positioning** (line 171):
```css
.dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 280px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden;
}

.profile-menu.compact .dropdown-menu {
  left: calc(100% + 0.5rem);
  top: 0;
  right: auto;
}

.compact-button {
  padding: 0.5rem;
  border-radius: 8px;
  width: 100%;
  justify-content: center;
}
```

### Step 6: Add Compact Mode to LanguageSwitcher (15 min)

**File:** `client/src/components/LanguageSwitcher.vue`

**Similar changes as ProfileMenu:**

1. **Add compact prop** in script setup
2. **Hide label and chevron** when compact
3. **Adjust dropdown positioning** for sidebar (opens to right)

### Step 7: Test All Functionality (30 min)

**Manual Testing Checklist:**
- [ ] Navigate between all routes (6 routes)
- [ ] Verify active route highlighting (blue bg, left border)
- [ ] Test hover states on nav items
- [ ] Click collapse button → sidebar shrinks to 72px
- [ ] Click expand button → sidebar returns to 260px
- [ ] Verify labels hide/show on collapse/expand
- [ ] Test filter bar → filters work correctly
- [ ] Click profile menu → dropdown opens
- [ ] Click profile details → modal opens
- [ ] Click my tasks → modal opens
- [ ] Test language switcher
- [ ] Resize to mobile → menu button appears
- [ ] Click mobile menu button → sidebar slides in
- [ ] Click overlay → sidebar slides out
- [ ] Verify all modals still work

## Design Specifications

### Colors (Existing Design System)
- Primary blue: `#2563eb`
- Active background: `#eff6ff`
- Hover background: `#f8fafc`
- Border: `#e2e8f0`
- Text primary: `#0f172a`
- Text secondary: `#64748b`

### Spacing
- Sidebar expanded: 260px
- Sidebar collapsed: 72px
- Nav item height: 40px
- Nav item gap: 0.25rem
- Icon size: 20px × 20px

### Transitions
- Sidebar width: 0.3s ease
- Background/color: 0.2s ease
- Icon rotation: 0.2s ease

## Expected Outcome

After running this command, the application should have:
- ✅ Vertical sidebar on the left (collapsible 260px ↔ 72px)
- ✅ Navigation with icons + labels
- ✅ Active route highlighting with blue background and left border
- ✅ Smooth transitions on hover and collapse
- ✅ FilterBar at top of content area (white background)
- ✅ Profile and language controls in sidebar footer
- ✅ Mobile responsive overlay sidebar
- ✅ All existing functionality preserved (routing, filters, modals)

## Verification

After implementation, test:
1. **Visual**: Sidebar displays correctly, icons aligned, colors match design
2. **Navigation**: All routes work, active states update correctly
3. **Interaction**: Collapse/expand works smoothly, hover states correct
4. **Filters**: Global filters still apply to all views
5. **Modals**: Profile and tasks modals still open correctly
6. **Mobile**: Menu button shows, sidebar slides in/out with overlay
7. **i18n**: Language switching still works
