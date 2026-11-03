<!--
  Dark primary sidebar. Three responsive tiers (breakpoints are repeated in the CSS below):
    >= 1100px   full width, manual collapse toggle (persisted in localStorage)
    720-1099px  forced icons-only via CSS, toggle hidden
    < 720px     off-canvas drawer, opened from the hamburger in the top bar (state lives in App.vue)
-->
<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from '../composables/useI18n'

const props = defineProps({
  // [{ to: '/inventory', label: 'Inventory', icon: '<svg path data>' }] - label is already translated
  items: { type: Array, required: true },
  brand: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  // Mobile drawer state, controlled by the shell
  open: { type: Boolean, default: false }
})
const emit = defineEmits(['close'])

const { t } = useI18n()

const STORAGE_KEY = 'sidebar-collapsed'

// Read synchronously in setup (not onMounted) so a persisted collapsed sidebar
// renders collapsed on the first paint instead of flashing wide and then shrinking.
const readCollapsed = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch (err) {
    return false // storage can be blocked (private mode, policies); default to expanded
  }
}
const collapsed = ref(readCollapsed())

watch(collapsed, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value ? '1' : '0')
  } catch (err) {
    // Persistence is best-effort only
  }
})

const sidebarEl = ref(null)

const onKeydown = (event) => {
  if (event.key === 'Escape') {
    emit('close', { restoreFocus: true })
  }
}

// Escape is only listened for while the drawer is open, and focus moves into the
// drawer so keyboard users land inside it rather than behind the scrim.
watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      document.addEventListener('keydown', onKeydown)
      await nextTick()
      // Note: a comma selector would return the first match in DOM order, not prefer the active item
      const target =
        sidebarEl.value?.querySelector('.nav-item.router-link-exact-active') ||
        sidebarEl.value?.querySelector('.nav-item')
      target?.focus()
    } else {
      document.removeEventListener('keydown', onKeydown)
    }
  }
)

// If the viewport grows past the drawer breakpoint while the drawer is open, reset
// the shell state so the hamburger's aria-expanded does not go stale.
let wideQuery = null
const onWideChange = (event) => {
  if (event.matches && props.open) emit('close')
}

onMounted(() => {
  if (typeof window.matchMedia === 'function') {
    wideQuery = window.matchMedia('(min-width: 720px)')
    wideQuery.addEventListener?.('change', onWideChange)
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  wideQuery?.removeEventListener?.('change', onWideChange)
})
</script>

<template>
  <div v-if="open" class="sidebar-scrim" aria-hidden="true" @click="emit('close', { restoreFocus: true })" />
  <aside
    id="app-sidebar"
    ref="sidebarEl"
    class="sidebar"
    :class="{ collapsed, open }"
    :aria-label="brand"
  >
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">{{ brand.charAt(0) }}</span>
      <span class="brand-text">
        <span class="brand-name">{{ brand }}</span>
        <span class="brand-subtitle">{{ subtitle }}</span>
      </span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in items"
        :key="item.to"
        :to="item.to"
        class="nav-item"
        :title="item.label"
        @click="emit('close')"
      >
        <svg
          class="nav-icon"
          viewBox="0 0 24 24"
          width="20"
          height="20"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path :d="item.icon" />
        </svg>
        <span class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <slot name="footer" :collapsed="collapsed" />
      <button
        class="collapse-btn"
        type="button"
        :aria-label="collapsed ? t('nav.expand') : t('nav.collapse')"
        :title="collapsed ? t('nav.expand') : t('nav.collapse')"
        @click="collapsed = !collapsed"
      >
        <span class="nav-label">{{ collapsed ? t('nav.expand') : t('nav.collapse') }}</span>
        <svg
          viewBox="0 0 24 24"
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path :d="collapsed ? 'M9 6l6 6-6 6' : 'M15 6l-6 6 6 6'" />
        </svg>
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* No overflow:hidden on .sidebar itself: the profile dropdown opens outside its box. */
.sidebar {
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100vh;
  height: 100dvh;
  flex-shrink: 0;
  width: var(--sidebar-width);
  z-index: var(--z-sidebar);
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  color: var(--text-on-sidebar);
  transition: width 0.2s ease;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  height: var(--topbar-height);
  flex-shrink: 0;
  padding: 0 var(--space-4);
  border-bottom: 1px solid var(--bg-sidebar-hover);
  overflow: hidden;
}

.brand-mark {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: var(--text-on-sidebar-strong);
  font-weight: 700;
  font-size: var(--text-base);
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.25;
}

.brand-name,
.brand-subtitle {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.brand-name {
  color: var(--text-on-sidebar-strong);
  font-size: var(--text-sm);
  font-weight: 600;
}

.brand-subtitle {
  font-size: var(--text-xs);
  opacity: 0.75;
}

.sidebar-nav {
  flex: 1;
  min-height: 0;
  padding: var(--space-3) var(--space-2);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  overflow-y: auto;
}

.nav-item,
.collapse-btn {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 2.5rem;
  padding: var(--space-2) var(--space-3);
  color: inherit;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  white-space: nowrap;
  border-radius: var(--radius-md);
  transition: background-color 0.15s ease, color 0.15s ease;
}

.nav-item:hover,
.collapse-btn:hover {
  background: var(--bg-sidebar-hover);
  color: var(--text-on-sidebar-strong);
}

/* Active state is a filled background plus heavier weight, so it is not colour alone. */
.nav-item.router-link-exact-active {
  background: var(--accent);
  color: var(--text-on-sidebar-strong);
  font-weight: 600;
}

/* White ring: the global accent ring has too little contrast on the dark sidebar.
   Negative offset keeps it inside the scrolling nav so it is never clipped. */
.nav-item:focus-visible,
.collapse-btn:focus-visible {
  outline: 2px solid #fff;
  outline-offset: -2px;
}

.nav-icon {
  flex-shrink: 0;
}

.sidebar-footer {
  flex-shrink: 0;
  padding: var(--space-2);
  border-top: 1px solid var(--bg-sidebar-hover);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.collapse-btn {
  width: 100%;
  justify-content: space-between;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.sidebar-scrim {
  display: none;
}

/* ---- Collapsed (manual, >= 1100px) ---- */
@media (min-width: 1100px) {
  .sidebar.collapsed {
    width: var(--sidebar-width-collapsed);
  }

  .sidebar.collapsed .brand-text,
  .sidebar.collapsed .nav-label {
    /* Visually hidden rather than display:none so links and the toggle keep an accessible name */
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }

  .sidebar.collapsed .sidebar-brand,
  .sidebar.collapsed .nav-item,
  .sidebar.collapsed .collapse-btn {
    justify-content: center;
  }

  .sidebar.collapsed .sidebar-brand {
    padding: 0;
  }

  .sidebar.collapsed .nav-item,
  .sidebar.collapsed .collapse-btn {
    padding-left: 0;
    padding-right: 0;
  }
}

/* ---- Forced icons-only (720px - 1099px): same look as collapsed, toggle hidden ---- */
@media (min-width: 720px) and (max-width: 1099px) {
  .sidebar {
    width: var(--sidebar-width-collapsed);
  }

  .sidebar .brand-text,
  .sidebar .nav-label {
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }

  .sidebar .sidebar-brand,
  .sidebar .nav-item {
    justify-content: center;
  }

  .sidebar .sidebar-brand {
    padding: 0;
  }

  .sidebar .nav-item {
    padding-left: 0;
    padding-right: 0;
  }

  .collapse-btn {
    display: none;
  }
}

/* ---- Off-canvas drawer (< 720px) ---- */
@media (max-width: 719px) {
  .sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: var(--z-drawer);
    width: min(var(--sidebar-width), 85vw);
    transform: translateX(-100%);
    /* visibility removes the closed drawer from the tab order; it flips after the slide-out finishes */
    visibility: hidden;
    transition: transform 0.2s ease, visibility 0s linear 0.2s;
    box-shadow: var(--shadow-md);
  }

  .sidebar.open {
    transform: translateX(0);
    visibility: visible;
    transition: transform 0.2s ease, visibility 0s;
  }

  .sidebar-scrim {
    display: block;
    position: fixed;
    inset: 0;
    z-index: var(--z-scrim);
    background: rgb(15 23 42 / 0.5);
  }

  .collapse-btn {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .sidebar,
  .sidebar.open {
    transition: none;
  }
}
</style>
