<!--
  Reference sidebar for the vue-saas-redesign skill. Copy into src/components/ and adapt.

  Props
    items        [{ to, label, icon?, exact? }]. Add { heading: 'Analytics' } entries to group.
                 `icon` is a key of icons.js; `exact: true` highlights only on an exact match
                 (use it for '/' when routes are nested).
    mobileOpen   drawer state on narrow screens; owned by the shell, toggled from the top bar.
    collapseLabel / expandLabel   pass translated strings in i18n apps.
  Emits
    close        drawer should close (backdrop click, Escape, or route change).
  Slots
    brand        full brand block (logo + name), shown when expanded.
    brand-mini   compact mark (monogram), shown when collapsed.
    footer       optional content above the collapse toggle; receives { collapsed }.

  Shell usage (App.vue):
    <div class="app-shell">
      <AppSidebar :items="navItems" :mobile-open="drawerOpen" @close="drawerOpen = false">
        <template #brand>...</template>
        <template #brand-mini>AC</template>
      </AppSidebar>
      <div class="app-main">
        <header class="app-topbar">
          <button class="app-menu-button" aria-controls="app-sidebar"
                  :aria-expanded="drawerOpen" @click="drawerOpen = true">...</button>
          <div class="app-topbar-title">{{ pageTitle }}</div>
          <div class="app-topbar-actions"><LanguageSwitcher /><ProfileMenu /></div>
        </header>
        <div class="app-toolbar"><FilterBar /></div>
        <main class="app-content"><router-view /></main>
      </div>
    </div>
-->
<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { icons } from './icons.js'

const props = defineProps({
  items: { type: Array, required: true },
  mobileOpen: { type: Boolean, default: false },
  collapseLabel: { type: String, default: 'Collapse sidebar' },
  expandLabel: { type: String, default: 'Expand sidebar' }
})
const emit = defineEmits(['close'])

// Desktop collapse preference survives reloads
const STORAGE_KEY = 'sidebar-collapsed'
const collapsed = ref(localStorage.getItem(STORAGE_KEY) === '1')
watch(collapsed, (value) => localStorage.setItem(STORAGE_KEY, value ? '1' : '0'))

// On narrow screens the sidebar is a full-width drawer, so the collapsed (icon-only) mode
// is ignored there; otherwise a user who collapsed on desktop gets an unlabeled drawer on mobile.
const narrowQuery = window.matchMedia('(max-width: 900px)')
const isNarrow = ref(narrowQuery.matches)
const onQueryChange = (event) => { isNarrow.value = event.matches }
const isCollapsed = computed(() => collapsed.value && !isNarrow.value)

// Navigating from the drawer should close it
const route = useRoute()
watch(() => route.fullPath, () => emit('close'))

const onKeydown = (event) => {
  if (event.key === 'Escape' && props.mobileOpen) emit('close')
}

onMounted(() => {
  narrowQuery.addEventListener('change', onQueryChange)
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  narrowQuery.removeEventListener('change', onQueryChange)
  window.removeEventListener('keydown', onKeydown)
})

const iconPath = (name) => icons[name] || icons.circle
</script>

<template>
  <div
    v-if="mobileOpen && isNarrow"
    class="sidebar-backdrop"
    aria-hidden="true"
    @click="emit('close')"
  />
  <aside
    id="app-sidebar"
    class="sidebar"
    :class="{ 'is-collapsed': isCollapsed, 'is-open': mobileOpen }"
  >
    <div class="sidebar-brand">
      <slot v-if="isCollapsed" name="brand-mini" />
      <slot v-else name="brand" />
    </div>

    <nav class="sidebar-nav" aria-label="Main">
      <template v-for="(item, index) in items" :key="item.to || `heading-${index}`">
        <div v-if="item.heading && isCollapsed" class="sidebar-divider" role="separator" />
        <div v-else-if="item.heading" class="sidebar-heading">{{ item.heading }}</div>
        <router-link
          v-else
          v-slot="{ href, navigate, isActive, isExactActive }"
          :to="item.to"
          custom
        >
          <a
            :href="href"
            class="sidebar-link"
            :class="{ 'is-active': item.exact ? isExactActive : isActive }"
            :aria-current="(item.exact ? isExactActive : isActive) ? 'page' : undefined"
            :title="isCollapsed ? item.label : undefined"
            @click="navigate"
          >
            <svg class="sidebar-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path :d="iconPath(item.icon)" />
            </svg>
            <span class="sidebar-label">{{ item.label }}</span>
          </a>
        </router-link>
      </template>
    </nav>

    <div class="sidebar-footer">
      <slot name="footer" :collapsed="isCollapsed" />
      <button
        type="button"
        class="sidebar-collapse"
        :aria-label="isCollapsed ? expandLabel : collapseLabel"
        :title="isCollapsed ? expandLabel : undefined"
        @click="collapsed = !collapsed"
      >
        <svg class="sidebar-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path :d="isCollapsed ? icons.chevronsRight : icons.chevronsLeft" />
        </svg>
        <span class="sidebar-label">{{ collapseLabel }}</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
  width: var(--sidebar-width);
  height: 100vh;
  overflow: hidden;
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  border-right: 1px solid var(--sidebar-border);
  transition: width var(--transition-base);
}

.sidebar.is-collapsed {
  width: var(--sidebar-width-collapsed);
}

.sidebar-brand {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  height: var(--topbar-height);
  padding: 0 var(--space-5);
  overflow: hidden;
  white-space: nowrap;
  color: var(--sidebar-item-active-text);
  border-bottom: 1px solid var(--sidebar-border);
}

.is-collapsed .sidebar-brand {
  justify-content: center;
  padding: 0;
}

.sidebar-nav {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-4) var(--space-3);
  overflow-y: auto;
}

.sidebar-heading {
  padding: var(--space-4) var(--space-3) var(--space-2);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  white-space: nowrap;
  color: var(--sidebar-heading);
}

.sidebar-divider {
  height: 1px;
  margin: var(--space-3) var(--space-2);
  background: var(--sidebar-border);
}

.sidebar-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 40px;
  padding: 0 var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--sidebar-text);
  text-decoration: none;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.sidebar-link:hover {
  background: var(--sidebar-item-hover-bg);
  color: var(--sidebar-text-hover);
}

.sidebar-link.is-active {
  background: var(--sidebar-item-active-bg);
  color: var(--sidebar-item-active-text);
}

/* Accent bar on the left edge of the active item */
.sidebar-link.is-active::before {
  content: "";
  position: absolute;
  top: 8px;
  bottom: 8px;
  left: calc(var(--space-3) * -1);
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--sidebar-accent);
}

.is-collapsed .sidebar-link,
.is-collapsed .sidebar-collapse {
  justify-content: center;
  padding: 0;
}

.sidebar-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.sidebar-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Collapsed: hide labels visually but keep them for screen readers */
.is-collapsed .sidebar-label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.sidebar-footer {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
  border-top: 1px solid var(--sidebar-border);
}

.sidebar-collapse {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: 36px;
  padding: 0 var(--space-3);
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  font: inherit;
  font-size: var(--text-sm);
  color: var(--sidebar-text);
  cursor: pointer;
}

.sidebar-collapse:hover {
  background: var(--sidebar-item-hover-bg);
  color: var(--sidebar-text-hover);
}

.sidebar-link:focus-visible,
.sidebar-collapse:focus-visible {
  outline: 2px solid var(--sidebar-accent);
  outline-offset: -2px;
}

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-backdrop);
  background: rgba(15, 23, 42, 0.5);
}

@media (max-width: 900px) {
  .sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: var(--z-drawer);
    width: var(--sidebar-width);
    height: auto;
    box-shadow: var(--shadow-lg);
    transform: translateX(-100%);
    transition: transform var(--transition-base);
  }

  .sidebar.is-open {
    transform: none;
  }

  .sidebar-collapse {
    display: none;
  }
}
</style>
