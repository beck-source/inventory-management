import { ref } from 'vue'

// Module-level reactive state (singleton pattern)
const isCollapsed = ref(false)
const isMobileOpen = ref(false)

export function useSidebar() {
  const toggleSidebar = () => {
    isCollapsed.value = !isCollapsed.value
  }

  const toggleMobileMenu = () => {
    isMobileOpen.value = !isMobileOpen.value
  }

  const closeMobileMenu = () => {
    isMobileOpen.value = false
  }

  return {
    isCollapsed,
    isMobileOpen,
    toggleSidebar,
    toggleMobileMenu,
    closeMobileMenu
  }
}
