import { ref, watchEffect } from 'vue'

// Shared sidebar UI state (singleton pattern, consistent with useFilters).
// `collapsed` = desktop icon-only mode, persisted across reloads.
// `mobileOpen` = off-canvas overlay state below the 768px breakpoint.
const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
const mobileOpen = ref(false)

watchEffect(() => {
  localStorage.setItem('sidebar-collapsed', String(collapsed.value))
})

export function useSidebar() {
  const toggleCollapsed = () => {
    collapsed.value = !collapsed.value
  }

  const toggleMobile = () => {
    mobileOpen.value = !mobileOpen.value
  }

  const closeMobile = () => {
    mobileOpen.value = false
  }

  return {
    collapsed,
    mobileOpen,
    toggleCollapsed,
    toggleMobile,
    closeMobile
  }
}
