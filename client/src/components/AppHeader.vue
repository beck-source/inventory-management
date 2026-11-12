<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import { useTheme } from '../composables/useTheme'
import { navItems } from '../navItems'
import NavIcon from './NavIcon.vue'

const { t } = useI18n()
const route = useRoute()
const { mobileOpen, openMobile } = useSidebar()
const { isDark, toggleTheme } = useTheme()

// Label describes the action the button will perform
const themeLabel = computed(() => t(isDark.value ? 'nav.themeToLight' : 'nav.themeToDark'))

// Page title comes from the matching nav item (exact match for "/")
const title = computed(() => {
  const item = navItems.find(i => (i.exact ? route.path === i.to : route.path.startsWith(i.to)))
  return item ? t(item.label) : t('nav.companyName')
})
</script>

<template>
  <header class="app-header">
    <button
      class="hamburger"
      type="button"
      aria-controls="app-sidebar"
      :aria-expanded="mobileOpen"
      :aria-label="t('nav.openMenu')"
      @click="openMobile"
    >
      <NavIcon name="menu" />
    </button>
    <span class="header-title">{{ title }}</span>
    <button
      class="theme-toggle"
      type="button"
      :aria-label="themeLabel"
      :title="themeLabel"
      :aria-pressed="isDark"
      @click="toggleTheme"
    >
      <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
      </svg>
      <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    </button>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--header-height);
  padding: 0 var(--space-8);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}
.header-title {
  font-family: var(--font-display);
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: var(--label-tracking);
  color: var(--text-muted);
  margin-right: auto; /* pushes controls to the right edge */
}
.hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text);
  cursor: pointer;
  transition: background-color var(--duration) var(--ease);
}
.hamburger:hover { background: var(--surface-muted); }

@media (max-width: 1023px) {
  .app-header { padding: 0 var(--space-4); }
  .hamburger { display: inline-flex; }
}
.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--control-height);
  height: var(--control-height);
  background: none;
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  color: var(--text);
  cursor: pointer;
  transition: background-color var(--duration) var(--ease);
}
.theme-toggle:hover { background: var(--surface-muted); }
.theme-toggle:focus-visible { outline: none; box-shadow: var(--focus-ring); }
</style>
