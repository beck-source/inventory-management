<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import Icon from './Icon.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const { collapsed, mobileOpen, toggleCollapsed, closeMobile } = useSidebar()

// Nav items are derived from the route table (see main.js meta.titleKey /
// meta.icon) rather than hardcoded here, so sidebar and router can't drift.
const navItems = computed(() => {
  return router.options.routes
    .filter(r => r.meta && r.meta.nav !== false)
    .map(r => ({
      path: r.path,
      label: r.meta.titleKey ? t(r.meta.titleKey) : (r.meta.title ?? r.path),
      icon: r.meta.icon ?? 'circle'
    }))
})

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <aside class="app-sidebar" :class="{ collapsed, 'is-open': mobileOpen }">
    <div class="sidebar-top">
      <div class="sidebar-brand">
        <div class="brand-mark">CC</div>
        <div class="brand-text">
          <span class="brand-name">{{ t('nav.companyName') }}</span>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>
      <button class="sidebar-close-btn" @click="closeMobile" aria-label="Close navigation menu">
        <Icon name="chevron-left" :size="18" />
      </button>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ 'is-active': isActive(item.path) }"
        @click="closeMobile"
      >
        <Icon :name="item.icon" :size="20" />
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <button
      class="collapse-toggle"
      @click="toggleCollapsed"
      :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
    >
      <Icon :name="collapsed ? 'chevron-right' : 'chevron-left'" :size="16" />
      <span class="collapse-label">Collapse</span>
    </button>
  </aside>
</template>

<style scoped>
.app-sidebar {
  --sidebar-width: 240px;
  width: var(--sidebar-width);
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  transition: width 0.2s ease;
}

.app-sidebar.collapsed {
  width: 64px;
}

.app-sidebar.collapsed .nav-label,
.app-sidebar.collapsed .brand-text,
.app-sidebar.collapsed .collapse-label {
  display: none;
}

.app-sidebar.collapsed .collapse-toggle {
  justify-content: center;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  min-height: 70px;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--color-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.813rem;
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name {
  font-size: 0.938rem;
  font-weight: 700;
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}

.brand-subtitle {
  font-size: 0.688rem;
  color: var(--color-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-close-btn {
  display: none;
  background: none;
  border: none;
  color: var(--color-muted);
  cursor: pointer;
  padding: var(--space-1);
  flex-shrink: 0;
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  text-decoration: none;
  font-size: var(--text-body);
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item svg {
  flex-shrink: 0;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item:hover {
  background: var(--color-bg);
  color: var(--color-ink);
}

.nav-item.is-active {
  background: var(--color-accent-soft);
  color: var(--color-accent);
  font-weight: 600;
}

.collapse-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: var(--space-2) var(--space-3) var(--space-4);
  padding: var(--space-2) var(--space-3);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  cursor: pointer;
  font-size: var(--text-caption);
  font-weight: 600;
  transition: all 0.15s ease;
}

.collapse-toggle:hover {
  background: var(--color-bg);
  color: var(--color-ink);
}

@media (max-width: 768px) {
  .app-sidebar {
    position: fixed;
    inset: 0 25% 0 0;
    height: 100vh;
    width: auto;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: var(--shadow-md);
    z-index: 40;
  }

  .app-sidebar.collapsed {
    width: auto;
  }

  /* A sidebar left collapsed on desktop should still show full labels once
     it becomes a mobile off-canvas overlay -- collapse is a desktop-only
     concept. These rules come after the base .collapsed rules above, so
     they win at this breakpoint without needing extra JS state. */
  .app-sidebar.collapsed .nav-label {
    display: inline;
  }

  .app-sidebar.collapsed .brand-text {
    display: flex;
  }

  .app-sidebar.collapsed .collapse-toggle {
    justify-content: flex-start;
  }

  .app-sidebar.is-open {
    transform: translateX(0);
  }

  .sidebar-close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .collapse-toggle {
    display: none;
  }
}
</style>
