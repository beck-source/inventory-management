<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import { navItems } from '../navItems'
import NavIcon from './NavIcon.vue'
import ProfileMenu from './ProfileMenu.vue'
import LanguageSwitcher from './LanguageSwitcher.vue'

const emit = defineEmits(['show-profile-details', 'show-tasks'])

const { t } = useI18n()
const route = useRoute()
const { collapsed, mobileOpen, toggleCollapsed, closeMobile } = useSidebar()

// Close the drawer after navigating
watch(() => route.path, closeMobile)

// The icon rail only applies on desktop; the drawer is always expanded
const desktopQuery = window.matchMedia('(min-width: 1024px)')
const isDesktop = ref(desktopQuery.matches)
const onQueryChange = (e) => { isDesktop.value = e.matches }
const rail = computed(() => collapsed.value && isDesktop.value)

const onKey = (e) => { if (e.key === 'Escape') closeMobile() }
onMounted(() => {
  window.addEventListener('keydown', onKey)
  desktopQuery.addEventListener('change', onQueryChange)
})
onBeforeUnmount(() => {
  desktopQuery.removeEventListener('change', onQueryChange)
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <div v-if="mobileOpen" class="sidebar-backdrop" @click="closeMobile" />
  <aside id="app-sidebar" class="sidebar" :class="{ 'is-collapsed': collapsed, 'is-open': mobileOpen }">
    <div class="sidebar-brand">
      <div class="brand-mark" aria-hidden="true">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="square">
          <path d="M4 20V10l8-6 8 6v10M9 20v-6h6v6" />
        </svg>
      </div>
      <div class="brand-text">
        <span class="brand-name">{{ t('nav.companyName') }}</span>
        <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
      </div>
    </div>

    <nav class="sidebar-nav" :aria-label="t('nav.mainNav')">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        custom
        v-slot="{ href, navigate, isActive, isExactActive }"
      >
        <a
          :href="href"
          class="nav-item"
          :class="{ active: item.exact ? isExactActive : isActive }"
          :aria-current="(item.exact ? isExactActive : isActive) ? 'page' : undefined"
          :title="collapsed ? t(item.label) : undefined"
          :aria-label="t(item.label)"
          @click="navigate"
        >
          <NavIcon :name="item.icon" />
          <span class="nav-label">{{ t(item.label) }}</span>
        </a>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <LanguageSwitcher :compact="rail" />
      <ProfileMenu
        :compact="rail"
        @show-profile-details="emit('show-profile-details')"
        @show-tasks="emit('show-tasks')"
      />
      <button
        class="sidebar-collapse"
        type="button"
        :aria-expanded="!collapsed"
        aria-controls="app-sidebar"
        :aria-label="collapsed ? t('nav.expand') : t('nav.collapse')"
        :title="collapsed ? t('nav.expand') : undefined"
        @click="toggleCollapsed"
      >
        <NavIcon name="chevrons" :class="{ flipped: collapsed }" />
        <span class="nav-label">{{ t('nav.collapse') }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* overflow stays visible so profile/language dropdowns can open over the content area */
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  flex: none;
  width: var(--sidebar-width-expanded);
  display: flex;
  flex-direction: column;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  transition: width var(--duration) var(--ease);
  z-index: var(--z-sidebar);
}
.sidebar.is-collapsed { width: var(--sidebar-width-collapsed); }

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: var(--header-height);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--sidebar-border);
  overflow: hidden;
}
.brand-mark {
  flex: none;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  background: var(--accent);
  color: var(--accent-ink);
}
.brand-text { display: flex; flex-direction: column; min-width: 0; }
.brand-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: var(--text-md);
  color: var(--sidebar-text-active);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--sidebar-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  padding: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  overflow-y: auto;
  overflow-x: hidden;
}
.nav-item,
.sidebar-collapse {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  color: var(--sidebar-text);
  text-decoration: none;
  white-space: nowrap;
  font-size: var(--text-base);
  font-weight: 500;
  transition: background-color var(--duration) var(--ease), color var(--duration) var(--ease);
}
.nav-item svg, .sidebar-collapse svg { flex: none; }
.nav-item:hover, .sidebar-collapse:hover { background: var(--sidebar-item-hover); color: var(--sidebar-text-active); }
.nav-item:focus-visible, .sidebar-collapse:focus-visible { box-shadow: inset 0 0 0 2px var(--accent); }
.nav-item.active { background: var(--sidebar-item-active); color: var(--sidebar-text-active); }
/* Active indicator: 3px amber bar on the left edge */
.nav-item.active::before {
  content: '';
  position: absolute;
  left: calc(var(--space-3) * -1);
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: var(--accent);
}

.sidebar-footer {
  padding: var(--space-3);
  border-top: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.sidebar-collapse {
  width: 100%;
  background: none;
  border: 0;
  cursor: pointer;
  font-family: inherit;
  height: 36px;
}
.flipped { transform: rotate(180deg); }

/* Icon rail: hide labels, center icons (labels stay exposed via title/aria-label) */
.is-collapsed .nav-label,
.is-collapsed .brand-text { display: none; }
.is-collapsed .nav-item,
.is-collapsed .sidebar-collapse { justify-content: center; padding: 0; }
.is-collapsed .sidebar-brand { justify-content: center; padding-left: 0; padding-right: 0; }

.sidebar-backdrop { display: none; }

/* Below 1024px: off-canvas drawer, always expanded when open */
@media (max-width: 1023px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: var(--z-drawer);
    width: var(--sidebar-width-expanded);
    transform: translateX(-100%);
    transition: transform var(--duration) var(--ease), visibility 0s linear var(--duration);
    visibility: hidden;
    box-shadow: var(--shadow-lg);
  }
  .sidebar.is-open { transform: translateX(0); visibility: visible; transition-delay: 0s; }
  .sidebar.is-collapsed { width: var(--sidebar-width-expanded); }
  .is-collapsed .nav-label { display: inline; }
  .is-collapsed .brand-text { display: flex; }
  .is-collapsed .nav-item { justify-content: flex-start; padding: 0 var(--space-3); }
  .is-collapsed .sidebar-brand { justify-content: flex-start; padding: var(--space-3) var(--space-4); }
  .sidebar-collapse { display: none; }
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: var(--overlay);
    z-index: var(--z-backdrop);
  }
}
</style>
