<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import { navItems } from '../navItems'
import NavIcon from './NavIcon.vue'

const { t } = useI18n()
const route = useRoute()
const { mobileOpen, openMobile } = useSidebar()

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
</style>
