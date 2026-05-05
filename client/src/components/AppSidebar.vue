<template>
  <aside class="app-sidebar">
    <div class="sidebar-logo">
      <h1>{{ t('nav.companyName') }}</h1>
      <p>{{ t('nav.subtitle') }}</p>
    </div>

    <nav class="sidebar-nav">
      <router-link to="/" :class="{ active: $route.path === '/' }">
        <!-- layout-dashboard -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="9" rx="1"/>
          <rect x="14" y="3" width="7" height="5" rx="1"/>
          <rect x="14" y="12" width="7" height="9" rx="1"/>
          <rect x="3" y="16" width="7" height="5" rx="1"/>
        </svg>
        {{ t('nav.overview') }}
      </router-link>

      <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
        <!-- package -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="m7.5 4.27 9 5.15"/>
          <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
          <path d="m3.3 7 8.7 5 8.7-5"/>
          <path d="M12 22V12"/>
        </svg>
        {{ t('nav.inventory') }}
      </router-link>

      <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
        <!-- shopping-cart -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="8" cy="21" r="1"/>
          <circle cx="19" cy="21" r="1"/>
          <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>
        </svg>
        {{ t('nav.orders') }}
      </router-link>

      <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
        <!-- dollar-sign -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="2" x2="12" y2="22"/>
          <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
        </svg>
        {{ t('nav.finance') }}
      </router-link>

      <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
        <!-- trending-up -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
          <polyline points="16 7 22 7 22 13"/>
        </svg>
        {{ t('nav.demandForecast') }}
      </router-link>

      <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
        <!-- rotate-cw -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/>
          <path d="M21 3v5h-5"/>
        </svg>
        {{ t('nav.restocking') }}
      </router-link>

      <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
        <!-- bar-chart-3 -->
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 3v18h18"/>
          <path d="M18 17V9"/>
          <path d="M13 17V5"/>
          <path d="M8 17v-3"/>
        </svg>
        {{ t('nav.reports') }}
      </router-link>
    </nav>

    <div class="sidebar-spacer"></div>

    <div class="sidebar-footer">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script>
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

export default {
  name: 'AppSidebar',
  components: {
    LanguageSwitcher,
    ProfileMenu
  },
  emits: ['show-profile-details', 'show-tasks'],
  setup() {
    const { t } = useI18n()
    return { t }
  }
}
</script>

<style scoped>
.app-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  padding: var(--space-5) var(--space-3);
  z-index: 100;
}
.sidebar-logo { padding: 0 var(--space-3) var(--space-5); }
.sidebar-logo h1 {
  color: var(--text-on-dark);
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.sidebar-logo p {
  margin-top: 2px;
  color: var(--text-on-dark-muted);
  font-size: var(--text-xs);
}
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: var(--space-2);
}
.sidebar-nav a {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--text-on-dark-muted);
  text-decoration: none;
  font-size: var(--text-sm);
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
  position: relative;
}
.sidebar-nav a:hover {
  background: var(--bg-sidebar-hover);
  color: var(--text-on-dark);
}
.sidebar-nav a.active {
  background: var(--bg-sidebar-active);
  color: var(--text-on-dark);
}
/* Active indicator bar on left edge */
.sidebar-nav a.active::before {
  content: '';
  position: absolute;
  left: calc(-1 * var(--space-3));
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
}
.sidebar-nav svg { flex-shrink: 0; }
.sidebar-spacer { flex: 1; }
.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--bg-sidebar-active);
}
</style>
