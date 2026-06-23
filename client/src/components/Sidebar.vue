<template>
  <aside class="sidebar" :class="{ open: isOpen, collapsed: collapsed }">

    <!-- Brand -->
    <div class="sidebar-brand">
      <div class="brand-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="7" height="7" rx="1"/>
          <rect x="15" y="3" width="7" height="7" rx="1"/>
          <rect x="2" y="14" width="7" height="7" rx="1"/>
          <rect x="15" y="14" width="7" height="7" rx="1"/>
        </svg>
      </div>
      <div class="brand-text">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-link"
        :class="{ 'router-link-active': isActive(item) }"
        :title="collapsed ? item.label : ''"
        @click="$emit('close')"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div class="footer-language">
        <LanguageSwitcher />
      </div>
      <div
        class="sidebar-user"
        :title="collapsed ? currentUser.name : ''"
        @click="$emit('show-tasks')"
      >
        <div class="user-avatar">{{ getInitials(currentUser.name) }}</div>
        <div class="user-info">
          <span class="user-name">{{ currentUser.name }}</span>
          <span class="user-role">{{ currentUser.jobTitle }}</span>
        </div>
        <button
          class="user-menu-btn"
          @click.stop="$emit('show-profile-details')"
          :title="t('nav.profile') || 'Profile'"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>
          </svg>
        </button>
      </div>

      <!-- Collapse toggle — desktop only -->
      <button class="collapse-btn" @click="$emit('toggle-collapse')" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'">
        <svg class="collapse-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <!-- Points left when expanded (collapse), right when collapsed (expand) -->
          <polyline v-if="!collapsed" points="15 18 9 12 15 6"/>
          <polyline v-else            points="9 18 15 12 9 6"/>
        </svg>
        <span class="collapse-label">Collapse</span>
      </button>
    </div>

  </aside>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'

export default {
  name: 'Sidebar',
  components: { LanguageSwitcher },
  props: {
    isOpen:    { type: Boolean, default: false },
    collapsed: { type: Boolean, default: false }
  },
  emits: ['close', 'show-profile-details', 'show-tasks', 'toggle-collapse'],
  setup() {
    const route = useRoute()
    const { currentUser, getInitials } = useAuth()
    const { t } = useI18n()

    const navItems = computed(() => [
      {
        path: '/',
        exact: true,
        label: t('nav.overview'),
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1"/>
          <rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/>
          <rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>`
      },
      {
        path: '/inventory',
        label: t('nav.inventory'),
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
          <line x1="12" y1="22.08" x2="12" y2="12"/>
        </svg>`
      },
      {
        path: '/orders',
        label: t('nav.orders'),
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/>
          <rect x="9" y="3" width="6" height="4" rx="1"/>
          <line x1="9" y1="12" x2="15" y2="12"/>
          <line x1="9" y1="16" x2="13" y2="16"/>
        </svg>`
      },
      {
        path: '/spending',
        label: t('nav.finance'),
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <rect x="1" y="4" width="22" height="16" rx="2"/>
          <line x1="1" y1="10" x2="23" y2="10"/>
        </svg>`
      },
      {
        path: '/demand',
        label: t('nav.demandForecast'),
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
          <polyline points="16 7 22 7 22 13"/>
        </svg>`
      },
      {
        path: '/reports',
        label: 'Reports',
        icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="20" x2="18" y2="10"/>
          <line x1="12" y1="20" x2="12" y2="4"/>
          <line x1="6" y1="20" x2="6" y2="14"/>
        </svg>`
      }
    ])

    const isActive = (item) => {
      if (item.exact) return route.path === item.path
      return route.path === item.path || route.path.startsWith(item.path + '/')
    }

    return { navItems, currentUser, getInitials, t, isActive }
  }
}
</script>

<style scoped>
/* ── Base sidebar ── */
.sidebar {
  width: var(--sidebar-width);
  min-height: 100vh;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow: hidden;           /* clip during width transition */
  /* Animate width + padding together for smooth collapse */
  transition: width .25s ease;
}

/* ── Collapsed state: icon-only strip ── */
.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: .75rem;
  padding: 1.25rem 1rem 1rem;
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
  /* clip brand text without layout jump */
  overflow: hidden;
  white-space: nowrap;
}

.brand-icon {
  width: 32px;
  height: 32px;
  background: var(--accent);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.brand-icon svg { width: 16px; height: 16px; }

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  /* fade out with the width transition */
  transition: opacity .2s ease;
}

.brand-name     { font-size: .875rem; font-weight: 700; color: var(--sidebar-text-hover); }
.brand-subtitle { font-size: .7rem;   color: var(--sidebar-text); }

.collapsed .brand-text { opacity: 0; pointer-events: none; }

/* Nav */
.sidebar-nav {
  flex: 1;
  padding: .75rem .5rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: .75rem;
  padding: .6rem .75rem;
  border-radius: 7px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: .875rem;
  font-weight: 500;
  white-space: nowrap;
  transition: background .15s, color .15s;
}

.nav-link:hover               { background: var(--sidebar-active-bg); color: var(--sidebar-text-hover); }
.nav-link.router-link-active  { background: var(--sidebar-active-bg); color: var(--sidebar-active-text); }

/* When collapsed, center the icon inside the narrower strip */
.collapsed .nav-link {
  padding: .6rem 0;
  justify-content: center;
  gap: 0;
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  color: var(--sidebar-icon-color);
  transition: color .15s;
}

.nav-icon svg { width: 18px; height: 18px; }

.nav-link:hover .nav-icon,
.nav-link.router-link-active .nav-icon { color: var(--accent); }

.nav-label {
  transition: opacity .2s ease;
}

.collapsed .nav-label { opacity: 0; width: 0; overflow: hidden; }

/* Footer */
.sidebar-footer {
  padding: .5rem;
  border-top: 1px solid var(--sidebar-border);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* Hide language switcher when collapsed — too wide for icon strip */
.footer-language { transition: opacity .2s ease; }
.collapsed .footer-language { opacity: 0; height: 0; overflow: hidden; pointer-events: none; }

.sidebar-user {
  display: flex;
  align-items: center;
  gap: .6rem;
  padding: .6rem .75rem;
  border-radius: 7px;
  cursor: pointer;
  white-space: nowrap;
  transition: background .15s;
  overflow: hidden;
}

.sidebar-user:hover { background: var(--sidebar-active-bg); }

.collapsed .sidebar-user { padding: .6rem 0; justify-content: center; gap: 0; }

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--accent-subtle);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: .7rem;
  font-weight: 700;
  flex-shrink: 0;
  border: 1.5px solid var(--accent);
}

.user-info, .user-menu-btn {
  transition: opacity .2s ease;
}

.user-name  { font-size: .8rem; font-weight: 600; color: var(--sidebar-text-hover); }
.user-role  { font-size: .7rem; color: var(--sidebar-text); }

.user-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.collapsed .user-info     { opacity: 0; width: 0; overflow: hidden; }
.collapsed .user-menu-btn { opacity: 0; width: 0; overflow: hidden; pointer-events: none; }

.user-menu-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: var(--sidebar-icon-color);
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  padding: 0;
  transition: background .15s, color .15s, opacity .2s ease;
}

.user-menu-btn:hover { background: var(--sidebar-border); color: var(--sidebar-text-hover); }
.user-menu-btn svg   { width: 14px; height: 14px; }

/* Collapse toggle button */
.collapse-btn {
  display: flex;
  align-items: center;
  gap: .75rem;
  width: 100%;
  padding: .55rem .75rem;
  border: none;
  background: transparent;
  color: var(--sidebar-text);
  font-size: .875rem;
  font-weight: 500;
  border-radius: 7px;
  cursor: pointer;
  white-space: nowrap;
  transition: background .15s, color .15s;
}

.collapse-btn:hover { background: var(--sidebar-active-bg); color: var(--sidebar-text-hover); }

.collapse-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  transition: color .15s;
}

.collapse-label { transition: opacity .2s ease; }

.collapsed .collapse-btn  { padding: .55rem 0; justify-content: center; gap: 0; }
.collapsed .collapse-label { opacity: 0; width: 0; overflow: hidden; }

/* ── Mobile: slide-in overlay, no collapse mode ── */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: -100%;
    /* z-index above content overlay so it covers the dim layer */
    z-index: 200;
    width: var(--sidebar-width) !important; /* always full width on mobile */
    transition: left .25s ease;
    box-shadow: 4px 0 24px rgba(0,0,0,.12);
  }

  .sidebar.open { left: 0; }

  /* Never show collapsed state on mobile */
  .collapsed .brand-text,
  .collapsed .nav-label,
  .collapsed .footer-language,
  .collapsed .user-info,
  .collapsed .user-menu-btn,
  .collapsed .collapse-label { opacity: 1; width: auto; height: auto; overflow: visible; pointer-events: auto; }

  .collapsed .nav-link,
  .collapsed .sidebar-user,
  .collapsed .collapse-btn { padding: .6rem .75rem; justify-content: flex-start; gap: .75rem; }
}
</style>
