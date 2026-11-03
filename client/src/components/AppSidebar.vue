<template>
  <aside
    ref="sidebarEl"
    class="sidebar"
    :class="{ 'is-open': drawerOpen }"
    :aria-label="t('nav.primaryNav')"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" class="brand-glyph">
          <path d="M21 8l-9-5-9 5 9 5 9-5z" />
          <path d="M3 8v8l9 5 9-5V8" />
        </svg>
      </span>
      <span class="brand-text">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-sub">{{ t('nav.subtitle') }}</span>
      </span>
      <button
        type="button"
        class="icon-btn drawer-close"
        :aria-label="t('nav.closeMenu')"
        @click="$emit('close-drawer')"
      >
        <svg viewBox="0 0 24 24" class="icon" aria-hidden="true"><path d="M6 6l12 12" /><path d="M18 6L6 18" /></svg>
      </button>
    </div>

    <nav class="sidebar-nav">
      <div v-for="section in sections" :key="section.labelKey" class="sidebar-section">
        <div class="sidebar-section-label">{{ t(section.labelKey) }}</div>
        <router-link
          v-for="item in section.items"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :active-class="item.to === '/' ? '' : 'is-active'"
          exact-active-class="is-active"
          :title="collapsed ? t(item.labelKey) : null"
        >
          <svg viewBox="0 0 24 24" class="icon" aria-hidden="true">
            <path v-for="d in icons[item.icon]" :key="d" :d="d" />
          </svg>
          <span class="sidebar-label">{{ t(item.labelKey) }}</span>
        </router-link>
      </div>
    </nav>

    <div class="sidebar-footer">
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
      <LanguageSwitcher />
      <div class="footer-actions">
        <button
          type="button"
          class="icon-btn"
          :aria-label="theme === 'dark' ? t('nav.switchToLight') : t('nav.switchToDark')"
          :title="theme === 'dark' ? t('nav.switchToLight') : t('nav.switchToDark')"
          @click="$emit('toggle-theme')"
        >
          <svg viewBox="0 0 24 24" class="icon" aria-hidden="true">
            <template v-if="theme === 'dark'">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2" /><path d="M12 20v2" /><path d="M4.9 4.9l1.4 1.4" /><path d="M17.7 17.7l1.4 1.4" />
              <path d="M2 12h2" /><path d="M20 12h2" /><path d="M4.9 19.1l1.4-1.4" /><path d="M17.7 6.3l1.4-1.4" />
            </template>
            <path v-else d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" />
          </svg>
        </button>
        <button
          type="button"
          class="icon-btn collapse-btn"
          :aria-label="collapsed ? t('nav.expand') : t('nav.collapse')"
          :title="collapsed ? t('nav.expand') : t('nav.collapse')"
          :aria-expanded="!collapsed"
          @click="$emit('toggle-collapse')"
        >
          <svg viewBox="0 0 24 24" class="icon" :class="{ flipped: collapsed }" aria-hidden="true">
            <path d="M11 17l-5-5 5-5" /><path d="M18 17l-5-5 5-5" />
          </svg>
        </button>
      </div>
    </div>
  </aside>
</template>

<script>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

// Stroke paths on a 24x24 grid, rendered inline so no icon package is needed
const icons = {
  home: ['M3 11l9-8 9 8', 'M5 10v10h14V10'],
  box: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'],
  list: ['M8 6h13', 'M8 12h13', 'M8 18h13', 'M3 6h.01', 'M3 12h.01', 'M3 18h.01'],
  trend: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'],
  coin: ['M12 2v20', 'M17 6H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6'],
  report: ['M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z', 'M14 3v5h5', 'M9 13h6', 'M9 17h6']
}

// Data-driven so adding a route is one line
const sections = [
  { labelKey: 'nav.sectionOverview', items: [{ to: '/', icon: 'home', labelKey: 'nav.overview' }] },
  {
    labelKey: 'nav.sectionOperations',
    items: [
      { to: '/inventory', icon: 'box', labelKey: 'nav.inventory' },
      { to: '/orders', icon: 'list', labelKey: 'nav.orders' },
      { to: '/demand', icon: 'trend', labelKey: 'nav.demandForecast' }
    ]
  },
  {
    labelKey: 'nav.sectionFinance',
    items: [
      { to: '/spending', icon: 'coin', labelKey: 'nav.finance' },
      { to: '/reports', icon: 'report', labelKey: 'nav.reports' }
    ]
  }
]

export default {
  name: 'AppSidebar',
  components: { LanguageSwitcher, ProfileMenu },
  props: {
    collapsed: { type: Boolean, default: false },
    drawerOpen: { type: Boolean, default: false },
    theme: { type: String, default: 'light' }
  },
  emits: [
    'toggle-collapse',
    'toggle-theme',
    'close-drawer',
    'show-profile-details',
    'show-tasks'
  ],
  setup() {
    const { t } = useI18n()
    const sidebarEl = ref(null)

    // Called by the shell when the drawer opens so keyboard users land inside it
    const focusFirst = () => {
      const target = sidebarEl.value && sidebarEl.value.querySelector('.sidebar-link')
      if (target) target.focus()
    }

    return { t, sections, icons, sidebarEl, focusFirst }
  }
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  border-right: 1px solid var(--sidebar-border);
  z-index: var(--z-sidebar);
  transition: width 0.2s ease;
  /* overflow stays visible so footer popovers can open upward and sideways; only .sidebar-nav scrolls */
}

.icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.icon.flipped {
  transform: rotate(180deg);
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 64px;
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--sidebar-marker);
  color: #04202a;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.brand-glyph {
  width: 22px;
  height: 22px;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.brand-name {
  color: var(--sidebar-text-active);
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-sub {
  font-size: var(--text-xs);
  color: var(--sidebar-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-2) 0 var(--space-4);
}

.sidebar-section-label {
  padding: var(--space-4) var(--space-5) var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--weight-medium);
  color: var(--sidebar-text-muted);
}

.sidebar-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  margin: 2px var(--space-3);
  padding: 0 var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  white-space: nowrap;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.sidebar-link:hover {
  background: var(--sidebar-item-hover);
  color: var(--sidebar-text-active);
}

.sidebar-link.is-active {
  background: var(--sidebar-item-active);
  color: var(--sidebar-text-active);
}

/* Cyan marker flush with the sidebar edge: the one branded element */
.sidebar-link.is-active::before {
  content: '';
  position: absolute;
  left: calc(-1 * var(--space-3));
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--sidebar-marker);
}

.sidebar-link.is-active .icon {
  color: var(--sidebar-marker);
}

.sidebar a:focus-visible,
.sidebar button:focus-visible {
  outline: 2px solid var(--sidebar-marker);
  outline-offset: 2px;
}

/* Footer */
.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  border-top: 1px solid var(--sidebar-border);
  flex-shrink: 0;
}

.footer-actions {
  display: flex;
  gap: var(--space-2);
}

.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  min-width: 36px;
  flex: 1;
  background: transparent;
  border: 1px solid var(--sidebar-border);
  border-radius: var(--radius-sm);
  color: var(--sidebar-text);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.icon-btn:hover {
  background: var(--sidebar-item-hover);
  color: var(--sidebar-text-active);
}

.drawer-close {
  display: none;
  flex: 0 0 auto;
}

/* Footer controls keep their own markup; restyle them for the dark sidebar.
   The extra .sidebar class outranks the children's own scoped rules. */
.sidebar .sidebar-footer :deep(.profile-button),
.sidebar .sidebar-footer :deep(.language-button) {
  width: 100%;
  background: transparent;
  border-color: var(--sidebar-border);
  color: var(--sidebar-text);
}

.sidebar .sidebar-footer :deep(.profile-button:hover),
.sidebar .sidebar-footer :deep(.language-button:hover) {
  background: var(--sidebar-item-hover);
  border-color: var(--sidebar-border);
}

.sidebar .sidebar-footer :deep(.profile-name),
.sidebar .sidebar-footer :deep(.language-label) {
  color: var(--sidebar-text-active);
  flex: 1;
  text-align: left;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar .sidebar-footer :deep(.chevron),
.sidebar .sidebar-footer :deep(.globe-icon) {
  color: var(--sidebar-text-muted);
}

/* Desktop collapsed state. Wrapped in a media query so the mobile drawer is always full width. */
@media (min-width: 901px) {
  .is-collapsed .sidebar {
    width: var(--sidebar-width-collapsed);
  }

  .is-collapsed .sidebar-label,
  .is-collapsed .sidebar-section-label,
  .is-collapsed .brand-text {
    display: none;
  }

  .is-collapsed .sidebar-brand {
    justify-content: center;
    padding: 0;
  }

  .is-collapsed .sidebar-section + .sidebar-section {
    border-top: 1px solid var(--sidebar-border);
    margin-top: var(--space-2);
    padding-top: var(--space-2);
  }

  .is-collapsed .sidebar-link {
    justify-content: center;
    padding: 0;
  }

  .is-collapsed .sidebar-footer {
    align-items: center;
  }

  .is-collapsed .footer-actions {
    flex-direction: column;
    width: 100%;
  }

  /* Stacked vertically, so the buttons must not flex-shrink their height */
  .is-collapsed .footer-actions .icon-btn {
    flex: 0 0 36px;
    width: 100%;
  }

  .is-collapsed .sidebar-footer :deep(.profile-menu),
  .is-collapsed .sidebar-footer :deep(.language-switcher) {
    width: 100%;
  }

  .is-collapsed .sidebar-footer :deep(.profile-button),
  .is-collapsed .sidebar-footer :deep(.language-button) {
    justify-content: center;
    padding: var(--space-2) 0;
  }

  .is-collapsed .sidebar-footer :deep(.profile-name),
  .is-collapsed .sidebar-footer :deep(.language-label),
  .is-collapsed .sidebar-footer :deep(.chevron) {
    display: none;
  }
}

/* 900px matches the drawer breakpoint used across the shell */
@media (max-width: 900px) {
  .sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    max-width: 86vw;
    transform: translateX(-100%);
    /* Hidden (not just off-screen) when closed so its links leave the tab order */
    visibility: hidden;
    transition: transform 0.2s ease, visibility 0s linear 0.2s;
    box-shadow: var(--shadow-lg);
    /* Must sit above the backdrop, otherwise the backdrop swallows clicks meant for the drawer */
    z-index: calc(var(--z-backdrop) + 1);
  }

  .sidebar.is-open {
    transform: none;
    visibility: visible;
    transition: transform 0.2s ease;
  }

  .drawer-close {
    display: inline-flex;
  }

  .collapse-btn {
    display: none;
  }

  .sidebar-link,
  .icon-btn {
    min-height: 44px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar.is-open {
    transition: none;
  }
}
</style>
