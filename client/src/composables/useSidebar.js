import { ref, computed, getCurrentInstance, onMounted, onBeforeUnmount } from 'vue'

const STORAGE_KEY = 'sidebar-collapsed'
const SMALL_SCREEN_QUERY = '(max-width: 1023px)'

// Read the persisted desktop preference. Storage can be unavailable (private
// mode, blocked cookies) or hold garbage, so never let it throw.
const readCollapsed = () => {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) === true
  } catch (err) {
    return false
  }
}

const writeCollapsed = (value) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
  } catch (err) {
    // Preference simply will not persist; the session state still works.
  }
}

const getMediaQuery = () =>
  typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia(SMALL_SCREEN_QUERY)
    : null

// Shared sidebar state (singleton pattern, like useFilters)
// `collapsed` is ONLY the desktop preference and is the only value persisted.
const collapsed = ref(readCollapsed())
// Small-screen overlay state is session-only so it never touches the preference.
const overlayOpen = ref(false)
const mediaQuery = getMediaQuery()
// Initialised synchronously so the first paint already has the right layout.
const isSmallScreen = ref(mediaQuery ? mediaQuery.matches : false)

const onMediaChange = (event) => {
  isSmallScreen.value = event.matches
  // Crossing the breakpoint in either direction always starts with the overlay closed.
  overlayOpen.value = false
}

// Number of mounted consumers; the listener lives only while at least one exists.
let consumers = 0

const attach = () => {
  if (!mediaQuery) return
  if (consumers === 0) {
    mediaQuery.addEventListener('change', onMediaChange)
    // The viewport may have changed between module load and mount.
    isSmallScreen.value = mediaQuery.matches
  }
  consumers++
}

const detach = () => {
  if (!mediaQuery || consumers === 0) return
  consumers--
  if (consumers === 0) {
    mediaQuery.removeEventListener('change', onMediaChange)
  }
}

export function useSidebar() {
  // Desktop: expanded unless the user collapsed it.
  // Small screens: the in-flow rail is always icons-only; "expanded" means the overlay is open.
  const isExpanded = computed(() =>
    isSmallScreen.value ? overlayOpen.value : !collapsed.value
  )

  const toggle = () => {
    if (isSmallScreen.value) {
      overlayOpen.value = !overlayOpen.value
    } else {
      collapsed.value = !collapsed.value
      writeCollapsed(collapsed.value)
    }
  }

  const closeOverlay = () => {
    overlayOpen.value = false
  }

  // Only register the media listener when used inside a component, so it is
  // removed again on unmount.
  if (getCurrentInstance()) {
    onMounted(attach)
    onBeforeUnmount(detach)
  }

  return {
    collapsed,
    isSmallScreen,
    overlayOpen,
    isExpanded,
    toggle,
    closeOverlay
  }
}
