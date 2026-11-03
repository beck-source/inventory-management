import { ref, watch } from 'vue'

// Module-level state so every component shares one sidebar; collapse choice persists across reloads
const collapsed = ref(localStorage.getItem('sidebar-collapsed') === 'true')
const mobileOpen = ref(false)
watch(collapsed, v => localStorage.setItem('sidebar-collapsed', String(v)))

export function useSidebar() {
  return {
    collapsed,
    mobileOpen,
    toggle: () => { collapsed.value = !collapsed.value },
    openMobile: () => { mobileOpen.value = true },
    closeMobile: () => { mobileOpen.value = false }
  }
}
