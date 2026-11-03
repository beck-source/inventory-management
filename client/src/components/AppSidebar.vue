<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'

const { t } = useI18n()
const route = useRoute()
const { isSmallScreen, overlayOpen, isExpanded, toggle, closeOverlay } = useSidebar()

const NAV_ID = 'app-sidebar-nav'
const toggleButton = ref(null)

// Hand-written 24x24 stroke icons; each entry is a list of path `d` strings
// (unique within an icon, so the string doubles as the v-for key).
const navItems = [
  {
    to: '/',
    labelKey: 'nav.overview',
    icon: ['M4 4h6v6H4z', 'M14 4h6v6h-6z', 'M4 14h6v6H4z', 'M14 14h6v6h-6z']
  },
  {
    to: '/inventory',
    labelKey: 'nav.inventory',
    icon: ['M21 8l-9-5-9 5v8l9 5 9-5z', 'M3 8l9 5 9-5', 'M12 13v8']
  },
  {
    to: '/orders',
    labelKey: 'nav.orders',
    icon: [
      'M9 4h6a1 1 0 011 1v1H8V5a1 1 0 011-1z',
      'M8 6H6a1 1 0 00-1 1v13a1 1 0 001 1h12a1 1 0 001-1V7a1 1 0 00-1-1h-2',
      'M9 12h6',
      'M9 16h4'
    ]
  },
  {
    to: '/spending',
    labelKey: 'nav.finance',
    icon: ['M3 7h18v10H3z', 'M14.5 12a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z', 'M6.5 12h.01', 'M17.5 12h.01']
  },
  {
    to: '/demand',
    labelKey: 'nav.demandForecast',
    icon: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6']
  },
  {
    to: '/restocking',
    labelKey: 'nav.restocking',
    icon: ['M20 11a8 8 0 00-14.9-3.5L3 9', 'M3 4v5h5', 'M4 13a8 8 0 0014.9 3.5L21 15', 'M21 20v-5h-5']
  },
  {
    to: '/reports',
    labelKey: 'nav.reports',
    icon: ['M3 21h18', 'M7 21V12', 'M12 21V4', 'M17 21v-6']
  }
]

const companyName = computed(() => t('nav.companyName'))
// Compact mark for the icons-only rail; Array.from keeps multi-byte (Japanese) characters intact.
const companyInitial = computed(() => Array.from(companyName.value)[0] || '')

const toggleLabel = computed(() =>
  isExpanded.value ? t('nav.collapseSidebar') : t('nav.expandSidebar')
)

// Use the router path (same rule as the old tab strip) for the active state.
const isActive = (to) => route.path === to

// Navigating closes the overlay (small screens only; a no-op otherwise).
watch(() => route.path, closeOverlay)

// Esc closes the overlay and hands focus back to the toggle.
const onKeydown = (event) => {
  if (event.key === 'Escape' && isSmallScreen.value && overlayOpen.value) {
    closeOverlay()
    toggleButton.value?.focus()
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <!-- The slot reserves the in-flow width. On small screens the aside is fixed, so the
       slot stays a 64px rail and the expanded overlay never pushes the content. -->
  <div
    class="sidebar-slot"
    :class="{ 'is-small': isSmallScreen, 'is-expanded': isExpanded }"
  >
    <Transition name="sidebar-fade">
      <div
        v-if="isSmallScreen && overlayOpen"
        class="sidebar-backdrop"
        aria-hidden="true"
        @click="closeOverlay"
      ></div>
    </Transition>

    <aside class="sidebar" :class="{ 'is-expanded': isExpanded, 'is-small': isSmallScreen }">
      <div class="brand" :title="companyName">
        <span v-show="!isExpanded" class="brand-mark" aria-hidden="true">{{ companyInitial }}</span>
        <!-- Kept in the DOM when collapsed (visually hidden) so the page keeps its h1. -->
        <div class="brand-text" :class="{ 'visually-hidden': !isExpanded }">
          <h1>{{ companyName }}</h1>
          <span class="brand-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>

      <nav :id="NAV_ID" class="sidebar-nav" :aria-label="t('nav.mainNavigation')">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="sidebar-link"
          :class="{ active: isActive(item.to) }"
          :aria-current="isActive(item.to) ? 'page' : undefined"
          :aria-label="isExpanded ? undefined : t(item.labelKey)"
          :title="isExpanded ? undefined : t(item.labelKey)"
          @click="closeOverlay"
        >
          <svg
            class="sidebar-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
            focusable="false"
          >
            <path v-for="d in item.icon" :key="d" :d="d" />
          </svg>
          <!-- v-show (display: none) removes the label from the accessibility tree when collapsed -->
          <span v-show="isExpanded" class="sidebar-label">{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>

      <button
        ref="toggleButton"
        type="button"
        class="sidebar-toggle"
        :aria-expanded="isExpanded ? 'true' : 'false'"
        :aria-controls="NAV_ID"
        :aria-label="toggleLabel"
        :title="toggleLabel"
        @click="toggle"
      >
        <svg
          class="sidebar-icon chevron"
          :class="{ flipped: !isExpanded }"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
          focusable="false"
        >
          <path d="M15 18l-6-6 6-6" />
        </svg>
        <span v-show="isExpanded" class="sidebar-label">{{ toggleLabel }}</span>
      </button>
    </aside>
  </div>
</template>

<style scoped>
/* Widths: 240px expanded, 64px icons-only. Keep slot and aside transitions in sync. */
.sidebar-slot {
  flex: 0 0 auto;
  width: 64px;
  transition: width 200ms ease;
}

.sidebar-slot.is-expanded:not(.is-small) {
  width: 240px;
}

/* Small screens: the slot is always the 64px rail */
.sidebar-slot.is-small {
  width: 64px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  /* Clips labels while the width animates */
  overflow-x: hidden;
  overflow-y: auto;
  /* Below the header (100), FilterBar-dropdowns (1000) and modals (2000) */
  z-index: 80;
  transition: width 200ms ease, box-shadow 200ms ease;
  position: sticky;
  top: 0;
}

/* Small screens: take the sidebar out of flow so expanding overlays the content */
.sidebar.is-small {
  position: fixed;
  top: 0;
  left: 0;
  width: 64px;
}

.sidebar.is-small.is-expanded {
  width: 240px;
  z-index: 200;
  box-shadow: 4px 0 16px rgba(15, 23, 42, 0.15);
}

.sidebar-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.4);
  z-index: 190;
}

.sidebar-fade-enter-active,
.sidebar-fade-leave-active {
  transition: opacity 200ms ease;
}

.sidebar-fade-enter-from,
.sidebar-fade-leave-to {
  opacity: 0;
}

/* Brand: height matches the top bar so the two bottom borders line up */
.brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 0 0 auto;
  height: var(--header-height, 70px);
  padding: 0 1rem;
  border-bottom: 1px solid #e2e8f0;
  overflow: hidden;
  white-space: nowrap;
}

/* Collapsed: center the compact mark in the rail */
.sidebar:not(.is-expanded) .brand {
  justify-content: center;
  padding: 0;
}

.brand-mark {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #0f172a;
  color: #ffffff;
  font-size: 1.125rem;
  font-weight: 700;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-text h1 {
  font-size: 1.0625rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  line-height: 1.25;
  overflow: hidden;
  text-overflow: ellipsis;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1 1 auto;
  /* Room for the 2px focus ring offset so it is never clipped by the aside */
  padding: 0.75rem 0.5rem;
}

.sidebar-link,
.sidebar-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  min-height: 44px;
  padding: 0 0.75rem;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  font: inherit;
  font-weight: 500;
  font-size: 0.938rem;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

/* Center the icon in the 64px rail */
.sidebar:not(.is-expanded) .sidebar-link,
.sidebar:not(.is-expanded) .sidebar-toggle {
  justify-content: center;
  padding: 0;
}

.sidebar-link:hover,
.sidebar-toggle:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.sidebar-link.active {
  color: #2563eb;
  background: #eff6ff;
}

/* 3px blue indicator on the left edge of the active item */
.sidebar-link.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: #2563eb;
}

.sidebar-link:focus-visible,
.sidebar-toggle:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.sidebar-icon {
  flex: 0 0 auto;
  width: 24px;
  height: 24px;
}

.sidebar-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-toggle {
  flex: 0 0 auto;
  width: calc(100% - 1rem);
  margin: 0 0.5rem 0.75rem;
}

.chevron {
  transition: transform 200ms ease;
}

/* Chevron points left when expanded (collapse) and right when collapsed (expand) */
.chevron.flipped {
  transform: rotate(180deg);
}

@media (prefers-reduced-motion: reduce) {
  .sidebar-slot,
  .sidebar,
  .sidebar-link,
  .sidebar-toggle,
  .chevron,
  .sidebar-fade-enter-active,
  .sidebar-fade-leave-active {
    transition: none;
  }
}
</style>
