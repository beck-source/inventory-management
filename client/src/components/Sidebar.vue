<template>
  <!-- Mobile overlay -->
  <div
    v-if="mobileOpen"
    class="sidebar-overlay"
    @click="$emit('close-mobile')"
  ></div>

  <aside
    class="sidebar"
    :class="{
      'sidebar-collapsed': collapsed,
      'sidebar-mobile-open': mobileOpen
    }"
  >
    <!-- Logo / Branding -->
    <div class="sidebar-header">
      <div class="logo-mark" aria-hidden="true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <defs>
            <linearGradient id="logoGrad" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
              <stop offset="0" stop-color="#6366f1"/>
              <stop offset="1" stop-color="#8b5cf6"/>
            </linearGradient>
          </defs>
          <rect x="2" y="2" width="20" height="20" rx="5" fill="url(#logoGrad)"/>
          <path d="M7.5 12.5L10.5 15.5L16.5 9" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div v-if="!collapsed" class="logo-text">
        <span class="logo-name">{{ t('nav.companyName') }}</span>
        <span class="logo-sub">{{ t('nav.subtitle') }}</span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <div class="nav-section">
        <span v-if="!collapsed" class="nav-section-label">Main</span>
        <SidebarItem
          to="/"
          :label="t('nav.overview')"
          :collapsed="collapsed"
          :exact="true"
        >
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <rect x="2.5" y="2.5" width="6.5" height="6.5" rx="1.5" stroke="currentColor" stroke-width="1.6"/>
              <rect x="11" y="2.5" width="6.5" height="6.5" rx="1.5" stroke="currentColor" stroke-width="1.6"/>
              <rect x="2.5" y="11" width="6.5" height="6.5" rx="1.5" stroke="currentColor" stroke-width="1.6"/>
              <rect x="11" y="11" width="6.5" height="6.5" rx="1.5" stroke="currentColor" stroke-width="1.6"/>
            </svg>
          </template>
        </SidebarItem>
        <SidebarItem
          to="/inventory"
          :label="t('nav.inventory')"
          :collapsed="collapsed"
        >
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path d="M3 6.5L10 3L17 6.5V13.5L10 17L3 13.5V6.5Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
              <path d="M3 6.5L10 10M10 10L17 6.5M10 10V17" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
            </svg>
          </template>
        </SidebarItem>
        <SidebarItem
          to="/orders"
          :label="t('nav.orders')"
          :collapsed="collapsed"
        >
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path d="M5 3H13L16 6V16C16 16.5523 15.5523 17 15 17H5C4.44772 17 4 16.5523 4 16V4C4 3.44772 4.44772 3 5 3Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
              <path d="M13 3V6H16" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
              <path d="M7 10H13M7 13H11" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </template>
        </SidebarItem>
        <SidebarItem
          to="/spending"
          :label="t('nav.finance')"
          :collapsed="collapsed"
        >
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.6"/>
              <path d="M10 5.5V14.5M12.5 7.5C12.5 6.67 11.38 6 10 6C8.62 6 7.5 6.67 7.5 7.5C7.5 8.33 8.62 9 10 9C11.38 9 12.5 9.67 12.5 10.5C12.5 11.33 11.38 12 10 12C8.62 12 7.5 11.33 7.5 10.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
            </svg>
          </template>
        </SidebarItem>
        <SidebarItem
          to="/reports"
          :label="t('nav.analytics')"
          :collapsed="collapsed"
        >
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path d="M3 17V11M8 17V7M13 17V13M18 17V4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
          </template>
        </SidebarItem>
        <SidebarItem
          to="/demand"
          :label="t('nav.demandForecast')"
          :collapsed="collapsed"
        >
          <template #icon>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <path d="M3 13L7 9L11 11L17 5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M13 5H17V9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </template>
        </SidebarItem>
      </div>
    </nav>

    <!-- Footer: collapse toggle + version -->
    <div class="sidebar-footer">
      <button
        class="collapse-btn"
        @click="$emit('toggle-collapse')"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            :d="collapsed ? 'M6 4L10 8L6 12' : 'M10 4L6 8L10 12'"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span v-if="!collapsed" class="collapse-btn-label">Collapse</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { useI18n } from '../composables/useI18n'
import SidebarItem from './SidebarItem.vue'

defineProps({
  collapsed: {
    type: Boolean,
    default: false
  },
  mobileOpen: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle-collapse', 'close-mobile'])

const { t } = useI18n()
</script>

<style scoped>
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(2px);
  z-index: 199;
  display: none;
}

.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  z-index: 200;
  transition: width 0.25s ease;
  overflow: hidden;
}

.sidebar-collapsed {
  width: var(--sidebar-width-collapsed);
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.125rem 1rem;
  height: var(--header-height);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.logo-mark {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  margin-left: 2px;
}

.logo-text {
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

.logo-name {
  display: block;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.015em;
  line-height: 1.2;
}

.logo-sub {
  display: block;
  font-size: 0.6875rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
  font-weight: 500;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 1rem 0.625rem;
  scrollbar-width: thin;
  scrollbar-color: var(--color-border-strong) transparent;
}

.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}

.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-nav::-webkit-scrollbar-thumb {
  background: var(--color-border-strong);
  border-radius: 4px;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}

.nav-section-label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 0 0.75rem;
  margin-bottom: 0.5rem;
  display: block;
}

.sidebar-collapsed .nav-section-label {
  display: none;
}

/* Footer */
.sidebar-footer {
  padding: 0.625rem;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
}

.collapse-btn {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
}

.collapse-btn:hover {
  background: var(--color-surface-alt);
  color: var(--color-text-primary);
}

.sidebar-collapsed .collapse-btn {
  justify-content: center;
  padding: 0.5rem;
}

.collapse-btn-label {
  white-space: nowrap;
}

/* Mobile */
@media (max-width: 768px) {
  .sidebar-overlay {
    display: block;
  }

  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease, width 0.25s ease;
    width: var(--sidebar-width) !important;
    box-shadow: var(--shadow-lg);
  }

  .sidebar-mobile-open {
    transform: translateX(0);
  }
}
</style>
