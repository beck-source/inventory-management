import { ref } from 'vue'

// Shared layout state (singleton pattern, same style as useFilters.js)
const isCollapsed = ref(false)
const isDrawerOpen = ref(false)

// Auto icons-only breakpoint: on tablet-sized viewports the sidebar
// defaults to collapsed (icons-only), matching --sidebar-breakpoint-tablet in App.vue.
const TABLET_BREAKPOINT = 1024
let responsiveInitialized = false

const applyResponsiveCollapse = () => {
  if (typeof window === 'undefined') return
  isCollapsed.value = window.innerWidth <= TABLET_BREAKPOINT
}

const initResponsiveCollapse = () => {
  if (responsiveInitialized || typeof window === 'undefined') return
  responsiveInitialized = true
  applyResponsiveCollapse()
  window.addEventListener('resize', applyResponsiveCollapse)
}

export function useLayout() {
  // Set the initial icons-only state based on viewport width the first
  // time this composable is used, then keep it in sync on resize.
  initResponsiveCollapse()

  const toggleCollapsed = () => {
    isCollapsed.value = !isCollapsed.value
  }

  const openDrawer = () => {
    isDrawerOpen.value = true
  }

  const closeDrawer = () => {
    isDrawerOpen.value = false
  }

  const toggleDrawer = () => {
    isDrawerOpen.value = !isDrawerOpen.value
  }

  return {
    // State
    isCollapsed,
    isDrawerOpen,

    // Methods
    toggleCollapsed,
    openDrawer,
    closeDrawer,
    toggleDrawer
  }
}
