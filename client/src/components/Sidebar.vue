<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <h1 v-if="!isCollapsed" class="sidebar-logo">{{ t('nav.companyName') }}</h1>
      <button
        class="collapse-btn"
        type="button"
        @click="toggleCollapse"
        :aria-label="collapseLabel"
      >
        <ChevronsLeft v-if="!isCollapsed" :size="18" />
        <ChevronsRight v-else :size="18" />
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.route"
        :to="item.route"
        active-class="active"
        exact-active-class="active-exact"
        class="nav-item"
      >
        <component :is="iconMap[item.icon]" class="nav-icon" :size="20" />
        <span v-if="!isCollapsed" class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
      <LanguageSwitcher />
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import {
  Home,
  Box,
  Truck,
  DollarSign,
  TrendingUp,
  Repeat,
  FileText,
  Archive,
  ChevronsLeft,
  ChevronsRight
} from '@lucide/vue'
import { useI18n } from '../composables/useI18n'
import ProfileMenu from './ProfileMenu.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

const props = defineProps({
  navItems: {
    type: Array,
    required: true
  },
  isCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle-collapse', 'show-profile-details', 'show-tasks'])

const { t } = useI18n()

const iconMap = {
  home: Home,
  box: Box,
  truck: Truck,
  'dollar-sign': DollarSign,
  'trending-up': TrendingUp,
  repeat: Repeat,
  'file-text': FileText,
  archive: Archive
}

const toggleCollapse = () => {
  emit('toggle-collapse')
}

const collapseLabel = computed(() =>
  props.isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'
)
</script>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  width: var(--sidebar-width-expanded);
  height: 100vh;
  background: var(--color-neutral-0);
  border-right: 1px solid var(--color-neutral-200);
  transition: width var(--sidebar-transition);
  position: sticky;
  top: 0;
  z-index: 100;
  overflow-y: auto;
}

.sidebar.collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-neutral-200);
  height: 70px;
  flex-shrink: 0;
}

.sidebar-logo {
  font-size: 1.125rem;
  font-weight: 700;
  font-family: var(--font-display);
  color: var(--color-primary);
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapse-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-2);
  color: var(--color-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: var(--color-neutral-100);
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--space-3) var(--space-2);
  gap: var(--space-1);
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-3);
  height: var(--sidebar-item-height);
  color: var(--color-text-muted);
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s;
  font-weight: 500;
  font-size: 0.938rem;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--color-neutral-100);
  color: var(--color-primary);
}

.nav-item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.nav-item.active-exact,
.nav-item.active {
  background: var(--color-primary);
  color: white;
}

.nav-icon {
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .sidebar-header {
  flex-direction: column-reverse;
  height: auto;
  padding: var(--space-3);
  gap: var(--space-2);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  border-top: 1px solid var(--color-neutral-200);
  background: var(--color-neutral-100);
  flex-shrink: 0;
}

.sidebar.collapsed .sidebar-footer :deep(.profile-name),
.sidebar.collapsed .sidebar-footer :deep(.language-label),
.sidebar.collapsed .sidebar-footer :deep(.chevron) {
  display: none;
}

.sidebar.collapsed .sidebar-footer :deep(.profile-button),
.sidebar.collapsed .sidebar-footer :deep(.language-button) {
  justify-content: center;
  padding: var(--space-2);
}

.sidebar.collapsed .sidebar-footer :deep(.dropdown-menu) {
  left: calc(100% + var(--space-2));
  right: auto;
  top: 0;
}

@media (max-width: 1024px) {
  .sidebar {
    width: var(--sidebar-width-collapsed);
  }

  .sidebar .sidebar-logo,
  .sidebar .nav-label {
    display: none;
  }

  .sidebar .nav-item {
    justify-content: center;
    padding: 0;
  }

  .sidebar .sidebar-footer :deep(.profile-name),
  .sidebar .sidebar-footer :deep(.language-label),
  .sidebar .sidebar-footer :deep(.chevron) {
    display: none;
  }

  .sidebar .sidebar-footer :deep(.profile-button),
  .sidebar .sidebar-footer :deep(.language-button) {
    justify-content: center;
    padding: var(--space-2);
  }
}
</style>
