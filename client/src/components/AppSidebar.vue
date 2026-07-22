<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': isCollapsed }">

    <!-- Header: logo icon + company name -->
    <div class="sidebar-header">
      <div class="sidebar-logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>
        </svg>
      </div>
      <span class="sidebar-company-name">{{ t('nav.companyName') }}</span>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :class="{ active: isItemActive(item) }"
        :title="isCollapsed ? item.label : undefined"
        :aria-current="isItemActive(item) ? 'page' : undefined"
      >
        <!-- eslint-disable-next-line vue/no-v-html -->
        <svg
          class="nav-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          v-html="item.iconHtml"
        ></svg>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>

      <!-- Collapse toggle -->
      <button
        class="sidebar-collapse-btn"
        @click="toggleCollapse"
        :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
      >
        <svg
          class="collapse-icon"
          :class="{ 'collapse-icon--rotated': isCollapsed }"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>
    </nav>

    <!-- Brainrot Mode toggle -->
    <div class="brainrot-section" :class="{ 'brainrot-on': brainrotEnabled }">
      <button
        class="brainrot-btn"
        @click="toggle"
        :title="isCollapsed ? 'Brainrot Mode' : undefined"
      >
        <span class="brainrot-icon">⚡</span>
        <span class="brainrot-label">Brainrot Mode</span>
        <div class="toggle-track" :class="{ on: brainrotEnabled }">
          <div class="toggle-thumb"></div>
        </div>
      </button>
    </div>

    <!-- Compliance footer -->
    <div class="compliance-footer" v-show="!isCollapsed">
      <div class="cf-data-region">Data stored in EU-West-1 (Frankfurt)</div>
      <div class="cf-badges-row">
        <span class="cf-gdpr-badge">
          <span class="cf-green-dot"></span>GDPR Compliant
        </span>
      </div>
      <div class="cf-links-row">
        <button class="cf-link" @click="openPrivacyPolicy">Privacy Policy</button>
        <span class="cf-dot-sep">·</span>
        <button class="cf-link" @click="openWhistleblower">Report a Concern</button>
      </div>
    </div>

    <!-- Footer: user profile + tools -->
    <div class="sidebar-footer">
      <button
        class="footer-user"
        @click="handleProfileClick"
        :title="isCollapsed ? currentUser.name : undefined"
      >
        <div class="footer-avatar">{{ getInitials(currentUser.name) }}</div>
        <span class="footer-user-name">{{ currentUser.name }}</span>
      </button>

      <div class="footer-tools">
        <button
          class="footer-tasks-btn"
          @click="handleTasksClick"
          title="Tasks"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M15 3H3C2.44772 3 2 3.44772 2 4V14C2 14.5523 2.44772 15 3 15H15C15.5523 15 16 14.5523 16 14V4C16 3.44772 15.5523 3 15 3Z"/>
            <path d="M6 7L8 9L12 5"/>
          </svg>
        </button>
        <LanguageSwitcher />
      </div>
    </div>

  </aside>
</template>

<script>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'
import { useBrainrot } from '../composables/useBrainrot'
import LanguageSwitcher from './LanguageSwitcher.vue'

export default {
  name: 'AppSidebar',
  components: { LanguageSwitcher },
  emits: ['profile-click', 'tasks-click'],
  setup(props, { emit }) {
    const route = useRoute()
    const { currentUser, getInitials } = useAuth()
    const { t } = useI18n()

    const { brainrotEnabled, toggle } = useBrainrot()

    const isCollapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      localStorage.setItem('sidebar-collapsed', String(isCollapsed.value))
    }

    const navItems = computed(() => [
      {
        to: '/',
        label: t('nav.overview'),
        exact: true,
        iconHtml: '<path d="M3 3h7v7H3zm11 0h7v7h-7zM3 14h7v7H3zm11 0h7v7h-7z"/>'
      },
      {
        to: '/inventory',
        label: t('nav.inventory'),
        iconHtml: '<path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/>'
      },
      {
        to: '/orders',
        label: t('nav.orders'),
        iconHtml: '<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 000 4h6a2 2 0 000-4M9 5a2 2 0 012-2h2a2 2 0 012 2"/>'
      },
      {
        to: '/spending',
        label: t('nav.finance'),
        iconHtml: '<path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/>'
      },
      {
        to: '/demand',
        label: t('nav.demandForecast'),
        iconHtml: '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>'
      },
      {
        to: '/reports',
        label: t('nav.reports'),
        iconHtml: '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>'
      },
      {
        to: '/restocking',
        label: t('nav.restocking'),
        iconHtml: '<polyline points="1 4 1 10 7 10"/><polyline points="23 20 23 14 17 14"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10M23 14l-4.64 4.36A9 9 0 013.51 15"/>'
      }
    ])

    const isItemActive = (item) => {
      if (item.exact) {
        return route.path === item.to
      }
      return route.path.startsWith(item.to)
    }

    const handleProfileClick = () => {
      emit('profile-click')
    }

    const handleTasksClick = () => {
      emit('tasks-click')
    }

    const openPrivacyPolicy = () => {
      alert('Privacy Policy: 40,000 words. Summary: we use your data to run this app.')
    }

    const openWhistleblower = () => {
      alert('Your report has been received anonymously. Thank you for your courage.')
    }

    return {
      isCollapsed,
      toggleCollapse,
      navItems,
      isItemActive,
      currentUser,
      getInitials,
      t,
      handleProfileClick,
      handleTasksClick,
      brainrotEnabled,
      toggle,
      openPrivacyPolicy,
      openWhistleblower
    }
  }
}
</script>

<style scoped>
:global(:root) {
  --sidebar-width: 240px;
  --sidebar-collapsed-width: 56px;
  --sidebar-bg: #f7f8fa;
  --sidebar-border: #e8ecf0;
  --sidebar-text: #37352f;
  --sidebar-muted: #9b9b9b;
  --sidebar-active-bg: #e8ecf0;
  --sidebar-hover-bg: #eff1f4;
}

/* ─── Sidebar shell ─────────────────────────────────────────────────── */
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  position: sticky;
  top: 0;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  flex-shrink: 0;
  /* overflow intentionally omitted so footer dropdown is not clipped */
}

.sidebar--collapsed {
  width: var(--sidebar-collapsed-width);
}

/* ─── Header ────────────────────────────────────────────────────────── */
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 12px 12px;
  min-height: 56px;
  overflow: hidden;
  white-space: nowrap;
  flex-shrink: 0;
}

.sidebar-logo-icon {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: white;
}

.sidebar-logo-icon svg {
  width: 16px;
  height: 16px;
}

.sidebar-company-name {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--sidebar-text);
  letter-spacing: -0.01em;
  white-space: nowrap;
}

/* ─── Nav ───────────────────────────────────────────────────────────── */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-top: 4px;
  overflow: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  border-radius: 6px;
  margin: 1px 8px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: 13.5px;
  font-weight: 500;
  white-space: nowrap;
  transition: background 0.15s;
}

.nav-item:hover {
  background: var(--sidebar-hover-bg);
}

.nav-item.active {
  background: var(--sidebar-active-bg);
}

.nav-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Collapse button (bottom of nav) */
.sidebar-collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 4px 8px 8px;
  padding: 7px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  color: var(--sidebar-muted);
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}

.sidebar-collapse-btn:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text);
}

.collapse-icon {
  width: 16px;
  height: 16px;
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.collapse-icon--rotated {
  transform: rotate(180deg);
}

/* ─── Brainrot toggle ───────────────────────────────────── */
.brainrot-section {
  margin: 4px 8px;
  border-radius: 8px;
  flex-shrink: 0;
}

.brainrot-section.brainrot-on {
  background: rgba(59, 130, 246, 0.08);
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.brainrot-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 8px;
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  transition: background 0.15s;
  font-family: inherit;
}

.brainrot-btn:hover {
  background: var(--sidebar-hover-bg);
}

.brainrot-icon {
  font-size: 15px;
  flex-shrink: 0;
  width: 18px;
  text-align: center;
}

.brainrot-label {
  font-size: 13.5px;
  font-weight: 500;
  color: var(--sidebar-text);
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Toggle switch */
.toggle-track {
  width: 30px;
  height: 17px;
  border-radius: 9px;
  background: #d1d5db;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}

.toggle-track.on {
  background: #3b82f6;
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: white;
  transition: transform 0.2s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.toggle-track.on .toggle-thumb {
  transform: translateX(13px);
}

.sidebar--collapsed .brainrot-btn {
  justify-content: center;
  padding: 7px;
}

/* ─── Compliance Footer ─────────────────────────────────────────────── */
.compliance-footer {
  padding: 6px 12px 4px;
  border-top: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.cf-data-region {
  font-size: 10px;
  color: var(--sidebar-muted);
  line-height: 1.4;
  margin-bottom: 4px;
}

.cf-badges-row {
  margin-bottom: 4px;
}

.cf-gdpr-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: var(--sidebar-muted);
  font-weight: 500;
}

.cf-green-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  flex-shrink: 0;
}

.cf-links-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cf-link {
  background: transparent;
  border: none;
  color: var(--sidebar-muted);
  font-size: 10px;
  cursor: pointer;
  padding: 0;
  font-family: inherit;
  transition: color 0.15s;
  text-decoration: underline;
  text-decoration-color: transparent;
  transition: color 0.15s, text-decoration-color 0.15s;
}

.cf-link:hover {
  color: var(--sidebar-text);
  text-decoration-color: currentColor;
}

.cf-dot-sep {
  font-size: 10px;
  color: var(--sidebar-muted);
  opacity: 0.6;
}

/* ─── Footer ────────────────────────────────────────────────────────── */
.sidebar-footer {
  border-top: 1px solid var(--sidebar-border);
  padding: 8px;
  flex-shrink: 0;
  position: relative;
}

.footer-user {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 7px 8px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  transition: background 0.15s;
  margin-bottom: 4px;
  font-family: inherit;
}

.footer-user:hover {
  background: var(--sidebar-hover-bg);
}

.footer-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.footer-user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--sidebar-text);
  overflow: hidden;
  text-overflow: ellipsis;
}

.footer-tools {
  display: flex;
  align-items: center;
  gap: 2px;
}

.footer-tasks-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: var(--sidebar-muted);
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
}

.footer-tasks-btn:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text);
}

/* ─── LanguageSwitcher overrides inside sidebar ─────────────────────── */
.sidebar-footer :deep(.language-switcher) {
  flex: 1;
  position: relative;
}

.sidebar-footer :deep(.language-button) {
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--sidebar-muted);
  padding: 6px 8px;
  font-size: 12px;
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: flex-start;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.sidebar-footer :deep(.language-button):hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text);
}

.sidebar-footer :deep(.globe-icon) {
  color: inherit;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.sidebar-footer :deep(.language-label) {
  font-size: 12px;
  font-weight: 500;
}

.sidebar-footer :deep(.language-button .chevron) {
  margin-left: auto;
}

/* Dropdown opens upward from footer */
.sidebar-footer :deep(.dropdown-menu) {
  bottom: calc(100% + 0.5rem);
  top: auto;
  right: 0;
  left: 0;
  min-width: 140px;
}

/* ─── Collapsed-state overrides ─────────────────────────────────────── */

/* Hide all text labels purely via CSS — no v-show, no Vue re-render flicker */
.sidebar--collapsed .sidebar-company-name,
.sidebar--collapsed .nav-label,
.sidebar--collapsed .footer-user-name,
.sidebar--collapsed .brainrot-label,
.sidebar--collapsed .toggle-track {
  display: none;
}

.sidebar--collapsed .footer-user {
  justify-content: center;
  padding: 7px;
}

.sidebar--collapsed .footer-tools {
  justify-content: center;
}

.sidebar--collapsed .footer-tasks-btn {
  flex: 0 0 auto;
}

.sidebar--collapsed .sidebar-footer :deep(.language-switcher) {
  flex: 0 0 auto;
}

.sidebar--collapsed .sidebar-footer :deep(.language-label),
.sidebar--collapsed .sidebar-footer :deep(.language-button .chevron) {
  display: none;
}

.sidebar--collapsed .sidebar-footer :deep(.language-button) {
  padding: 6px;
  justify-content: center;
  width: auto;
}
</style>
