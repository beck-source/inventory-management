import { ref, computed, onMounted, onUnmounted } from 'vue'

const STORAGE_KEY = 'sidebar-collapsed'
const NARROW_QUERY = '(max-width: 1024px)'

const readStoredPreference = () => {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    if (value === 'true') return true
    if (value === 'false') return false
  } catch {
    // localStorage can throw when blocked (privacy mode, disabled storage)
  }
  return null
}

const storePreference = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(value))
  } catch {
    // Preference stays in memory for this session
  }
}

const getNarrowMatch = () => {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return window.matchMedia(NARROW_QUERY).matches
}

// Shared sidebar state (singleton pattern)
// null means the user has not chosen, so the viewport width decides
const userPreference = ref(readStoredPreference())
const isNarrow = ref(getNarrowMatch())

const collapsed = computed(() => userPreference.value ?? isNarrow.value)

const toggleSidebar = () => {
  userPreference.value = !collapsed.value
  storePreference(userPreference.value)
}

// Call from a component that lives as long as the app shell; it owns the matchMedia listener
export function useSidebar() {
  let mediaQuery = null

  const onChange = (event) => {
    isNarrow.value = event.matches
  }

  onMounted(() => {
    if (typeof window.matchMedia !== 'function') return
    mediaQuery = window.matchMedia(NARROW_QUERY)
    isNarrow.value = mediaQuery.matches
    mediaQuery.addEventListener('change', onChange)
  })

  onUnmounted(() => {
    if (mediaQuery) mediaQuery.removeEventListener('change', onChange)
    mediaQuery = null
  })

  return {
    collapsed,
    toggleSidebar
  }
}
