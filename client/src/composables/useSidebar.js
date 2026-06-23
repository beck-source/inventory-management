import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const STORAGE_KEY = 'sidebar.collapsed'
const MOBILE_BREAKPOINT = '(max-width: 1024px)'

// Singleton state shared across components
const userCollapsed = ref(loadStored())
const isMobile = ref(false)

function loadStored() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === 'true'
  } catch {
    return false
  }
}

function persist(value) {
  try {
    window.localStorage.setItem(STORAGE_KEY, value ? 'true' : 'false')
  } catch {
    // localStorage unavailable (private mode, quota); ignore — state still
    // works for the session, just won't persist across reloads.
  }
}

let mediaQuery = null
let listener = null
let mountedCount = 0

export function useSidebar() {
  // Effective collapsed state: forced when mobile, otherwise user preference.
  // Mobile force does NOT overwrite the stored preference — when the user
  // resizes back above the breakpoint, their last manual choice is restored.
  const isCollapsed = computed(() => isMobile.value || userCollapsed.value)

  const toggle = () => {
    if (isMobile.value) return  // toggle is a no-op when force-collapsed
    userCollapsed.value = !userCollapsed.value
    persist(userCollapsed.value)
  }

  onMounted(() => {
    mountedCount += 1
    if (!mediaQuery) {
      mediaQuery = window.matchMedia(MOBILE_BREAKPOINT)
      isMobile.value = mediaQuery.matches
      listener = (e) => { isMobile.value = e.matches }
      mediaQuery.addEventListener('change', listener)
    }
  })

  onBeforeUnmount(() => {
    mountedCount -= 1
    if (mountedCount === 0 && mediaQuery && listener) {
      mediaQuery.removeEventListener('change', listener)
      mediaQuery = null
      listener = null
    }
  })

  return {
    isCollapsed,
    isMobile,
    toggle,
  }
}
