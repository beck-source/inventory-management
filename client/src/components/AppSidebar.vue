<template>
  <aside
    id="app-sidebar"
    class="sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-mobile-open': mobileOpen }"
  >
    <div class="sidebar-brand">
      <router-link to="/" class="brand-lockup" :title="t('nav.companyName')">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M12 3l8 4.5-8 4.5-8-4.5L12 3z" fill="currentColor" />
            <path d="M4 12l8 4.5 8-4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.6" />
            <path d="M4 16.5L12 21l8-4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.32" />
          </svg>
        </span>
        <span class="brand-text">
          <h1 class="brand-name">{{ t('nav.companyName') }}</h1>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </span>
      </router-link>

      <button
        ref="closeButton"
        type="button"
        class="sidebar-close"
        :aria-label="t('nav.closeMenu')"
        @click="$emit('close-mobile')"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round">
          <path d="M18 6L6 18" />
          <path d="M6 6l12 12" />
        </svg>
      </button>
    </div>

    <nav class="sidebar-nav" :aria-label="t('nav.primaryNavigation')">
      <div v-for="group in navGroups" :key="group.id" class="nav-group">
        <p class="nav-group-label">{{ t(group.labelKey) }}</p>
        <ul class="nav-list">
          <li v-for="item in group.items" :key="item.path">
            <router-link
              :to="item.path"
              class="nav-item"
              :class="{ active: route.path === item.path }"
              :aria-current="route.path === item.path ? 'page' : undefined"
              :title="collapsed ? t(item.labelKey) : undefined"
              @click="$emit('close-mobile')"
            >
              <span class="nav-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                  <path v-for="d in icons[item.icon]" :key="d" :d="d" />
                </svg>
              </span>
              <span class="nav-label">{{ t(item.labelKey) }}</span>
            </router-link>
          </li>
        </ul>
      </div>
    </nav>

    <div class="sidebar-footer">
      <div class="env-chip" :title="t('nav.demoEnvironment')">
        <span class="env-dot" aria-hidden="true"></span>
        <span class="env-text">{{ t('nav.demoEnvironment') }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'

defineProps({
  collapsed: { type: Boolean, default: false },
  mobileOpen: { type: Boolean, default: false }
})

defineEmits(['close-mobile'])

const route = useRoute()
const { t } = useI18n()
const closeButton = ref(null)

// Lets the shell move keyboard focus into the drawer when it opens.
defineExpose({
  focusFirst: () => closeButton.value?.focus()
})

const navGroups = [
  {
    id: 'general',
    labelKey: 'nav.groupGeneral',
    items: [
      { path: '/', labelKey: 'nav.overview', icon: 'overview' }
    ]
  },
  {
    id: 'operations',
    labelKey: 'nav.groupOperations',
    items: [
      { path: '/inventory', labelKey: 'nav.inventory', icon: 'inventory' },
      { path: '/orders', labelKey: 'nav.orders', icon: 'orders' },
      { path: '/restocking', labelKey: 'nav.restocking', icon: 'restocking' }
    ]
  },
  {
    id: 'insights',
    labelKey: 'nav.groupInsights',
    items: [
      { path: '/spending', labelKey: 'nav.finance', icon: 'finance' },
      { path: '/demand', labelKey: 'nav.demandForecast', icon: 'demand' },
      { path: '/reports', labelKey: 'nav.reports', icon: 'reports' }
    ]
  }
]

// Stroke-only 24x24 icon paths, rendered as <path> elements (no v-html).
const icons = {
  overview: ['M4 4h6v7H4z', 'M14 4h6v4h-6z', 'M14 12h6v8h-6z', 'M4 15h6v5H4z'],
  inventory: [
    'M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z',
    'M3.27 6.96L12 12.01l8.73-5.05',
    'M12 22.08V12'
  ],
  orders: [
    'M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2',
    'M9 2h6a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z',
    'M8 12h8',
    'M8 16h5'
  ],
  finance: [
    'M21 5H3a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1z',
    'M2 10h20',
    'M6 15h4'
  ],
  restocking: [
    'M3 7h13v10H3z',
    'M16 10h3.5a1 1 0 0 1 .86.5L22 13v4h-6',
    'M7.5 20a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z',
    'M18 20a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z'
  ],
  demand: ['M22 7l-8.5 8.5-5-5L2 17', 'M16 7h6v6'],
  reports: ['M18 20V10', 'M12 20V4', 'M6 20v-6', 'M3 20h18']
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 200;
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  transition: width var(--transition), transform var(--transition), visibility var(--transition);
  overflow: hidden;
}

.sidebar.is-collapsed {
  width: var(--sidebar-width-collapsed);
}

/* ---------- Brand ---------- */

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: var(--topbar-height);
  flex-shrink: 0;
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--border);
}

.brand-lockup {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
  flex: 1;
  text-decoration: none;
  border-radius: var(--radius-md);
}

.brand-lockup:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}

.brand-mark {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 9px;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-xs);
}

.brand-mark svg {
  width: 20px;
  height: 20px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 1px;
}

.brand-name {
  font-size: 0.938rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: 0.688rem;
  font-weight: 500;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-close {
  display: none;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  padding: 0;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--text-muted);
  cursor: pointer;
}

.sidebar-close svg {
  width: 18px;
  height: 18px;
}

.sidebar-close:hover {
  background: var(--surface-sunken);
  color: var(--text-primary);
}

/* ---------- Navigation ---------- */

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-5) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.nav-group-label {
  padding: 0 var(--space-3);
  margin-bottom: var(--space-2);
  font-size: 0.688rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #94a3b8;
  white-space: nowrap;
}

.nav-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  transition: background var(--transition), color var(--transition);
}

.nav-item:hover {
  background: var(--surface-sunken);
  color: var(--text-primary);
}

.nav-item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.nav-item.active {
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-weight: 600;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: calc(var(--space-3) * -1);
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  border-radius: 0 3px 3px 0;
  background: var(--accent);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--text-muted);
  transition: color var(--transition);
}

.nav-item:hover .nav-icon {
  color: var(--text-secondary);
}

.nav-item.active .nav-icon {
  color: var(--accent);
}

.nav-icon svg {
  width: 19px;
  height: 19px;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ---------- Footer ---------- */

.sidebar-footer {
  flex-shrink: 0;
  padding: var(--space-3) var(--space-3) var(--space-4);
  border-top: 1px solid var(--border);
}

.env-chip {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 34px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-full);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
}

.env-dot {
  width: 7px;
  height: 7px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

/* ---------- Collapsed state (desktop only) ---------- */

.sidebar.is-collapsed .brand-text,
.sidebar.is-collapsed .nav-label,
.sidebar.is-collapsed .env-text {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sidebar.is-collapsed .sidebar-brand {
  padding-left: var(--space-3);
  padding-right: var(--space-3);
}

.sidebar.is-collapsed .brand-lockup {
  justify-content: center;
}

.sidebar.is-collapsed .nav-group .nav-group-label {
  height: 1px;
  margin: 0 var(--space-2) var(--space-3);
  padding: 0;
  overflow: hidden;
  color: transparent;
  background: var(--border);
}

.sidebar.is-collapsed .nav-group:first-child .nav-group-label {
  display: none;
}

.sidebar.is-collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.sidebar.is-collapsed .env-chip {
  justify-content: center;
  padding: 0;
  width: 34px;
  margin: 0 auto;
}

/* ---------- Mobile drawer ---------- */

@media (max-width: 1024px) {
  .sidebar,
  .sidebar.is-collapsed {
    width: var(--sidebar-width);
    transform: translateX(-100%);
    /* visibility (not just transform) removes the closed drawer from the
       tab order and the accessibility tree */
    visibility: hidden;
    box-shadow: none;
  }

  .sidebar.is-collapsed .brand-text,
  .sidebar.is-collapsed .nav-label,
  .sidebar.is-collapsed .env-text {
    position: static;
    width: auto;
    height: auto;
    padding: 0;
    margin: 0;
    overflow: visible;
    clip: auto;
    white-space: normal;
  }

  .sidebar.is-collapsed .sidebar-brand {
    padding-left: var(--space-4);
    padding-right: var(--space-4);
  }

  .sidebar.is-collapsed .brand-lockup {
    justify-content: flex-start;
  }

  .sidebar.is-collapsed .nav-item {
    justify-content: flex-start;
    padding: 0 var(--space-3);
  }

  .sidebar.is-collapsed .nav-group .nav-group-label,
  .sidebar.is-collapsed .nav-group:first-child .nav-group-label {
    display: block;
    height: auto;
    margin: 0 0 var(--space-2);
    padding: 0 var(--space-3);
    color: #94a3b8;
    background: none;
  }

  .sidebar.is-collapsed .env-chip {
    justify-content: flex-start;
    width: auto;
    padding: 0 var(--space-3);
  }

  .sidebar.is-mobile-open,
  .sidebar.is-collapsed.is-mobile-open {
    transform: translateX(0);
    visibility: visible;
    box-shadow: var(--shadow-md);
  }

  .sidebar-close {
    display: flex;
  }
}
</style>
