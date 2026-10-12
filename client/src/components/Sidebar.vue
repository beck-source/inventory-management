<template>
  <aside class="sidebar">
    <div class="sidebar-logo">
      <span class="sidebar-company">{{ t('nav.companyName') }}</span>
      <span class="sidebar-subtitle">{{ t('nav.subtitle') }}</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="link in navLinks"
        :key="link.to"
        :to="link.to"
        class="sidebar-link"
        :class="{ active: isActive(link) }"
      >
        <svg
          v-html="link.icon"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="sidebar-icon"
        ></svg>
        <span>{{ link.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-bottom">
      <LanguageSwitcher />
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </aside>
</template>

<script>
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import ProfileMenu from './ProfileMenu.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

export default {
  name: 'Sidebar',
  components: {
    ProfileMenu,
    LanguageSwitcher
  },
  emits: ['show-profile-details', 'show-tasks'],
  setup() {
    const route = useRoute()
    const { t } = useI18n()

    const navLinks = [
      {
        to: '/',
        get label() { return t('nav.overview') },
        exact: true,
        icon: '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>'
      },
      {
        to: '/inventory',
        get label() { return t('nav.inventory') },
        icon: '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
      },
      {
        to: '/orders',
        get label() { return t('nav.orders') },
        icon: '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>'
      },
      {
        to: '/spending',
        get label() { return t('nav.finance') },
        icon: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>'
      },
      {
        to: '/demand',
        get label() { return t('nav.demandForecast') },
        icon: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>'
      },
      {
        to: '/reports',
        label: 'Reports',
        icon: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>'
      }
    ]

    const isActive = (link) => {
      if (link.exact || link.to === '/') {
        return route.path === '/'
      }
      return route.path.startsWith(link.to)
    }

    return { t, navLinks, isActive }
  }
}
</script>

<style scoped>
.sidebar {
  background: #0f172a;
  width: 220px;
  height: 100vh;
  position: sticky;
  top: 0;
  overflow-y: auto;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.sidebar-logo {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1.5rem 1.25rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-company {
  font-size: 1rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.015em;
}

.sidebar-subtitle {
  font-size: 0.7rem;
  color: #64748b;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 0.75rem 0.75rem;
  flex: 1;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #94a3b8;
  text-decoration: none;
  transition: background 0.15s, color 0.15s;
  margin-bottom: 0.125rem;
}

.sidebar-link:hover {
  background: rgba(255, 255, 255, 0.07);
  color: #e2e8f0;
}

.sidebar-link.active {
  background: #2563eb;
  color: #ffffff;
}

.sidebar-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.sidebar-bottom {
  padding: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: auto;
}
</style>
