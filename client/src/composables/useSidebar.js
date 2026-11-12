import { ref, watch } from 'vue'

const STORAGE_KEY = 'sidebar-collapsed'

function readCollapsed() {
  // Storage can throw (private mode, blocked site data): fall back to expanded
  try { return localStorage.getItem(STORAGE_KEY) === '1' } catch { return false }
}

// Module-level state so the sidebar and header share it without props
const collapsed = ref(readCollapsed())
const mobileOpen = ref(false)

watch(collapsed, (v) => {
  try { localStorage.setItem(STORAGE_KEY, v ? '1' : '0') } catch { /* non-critical */ }
})

// Lock page scroll behind the open mobile drawer
watch(mobileOpen, (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
})

export function useSidebar() {
  return {
    collapsed,
    mobileOpen,
    toggleCollapsed: () => { collapsed.value = !collapsed.value },
    openMobile: () => { mobileOpen.value = true },
    closeMobile: () => { mobileOpen.value = false }
  }
}
