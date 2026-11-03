import { ref, watch } from 'vue'

const STORAGE_KEY = 'ui.sidebarCollapsed'

function readCollapsed() {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    return false
  }
}

// Desktop: collapsed = icon rail. Mobile: mobileOpen = drawer visible.
// They are separate so collapsing on desktop never hides the nav on mobile.
const collapsed = ref(readCollapsed())
const mobileOpen = ref(false)

watch(collapsed, (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, value ? '1' : '0')
  } catch {
    // Ignore: the toggle still works for this session.
  }
})

export function useSidebar() {
  const toggleCollapsed = () => { collapsed.value = !collapsed.value }
  const openMobile = () => { mobileOpen.value = true }
  const closeMobile = () => { mobileOpen.value = false }
  return { collapsed, mobileOpen, toggleCollapsed, openMobile, closeMobile }
}
