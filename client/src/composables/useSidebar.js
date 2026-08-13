import { ref, computed } from 'vue'

// Singleton state
const userCollapsed = ref(false)
const screenWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1920)

export function useSidebar() {
  // Mobile detection
  const isMobile = computed(() => screenWidth.value < 1024)

  // Effective state: mobile OR user preference
  const isCollapsed = computed(() => isMobile.value || userCollapsed.value)

  // Load from localStorage
  const loadSavedState = () => {
    if (typeof window === 'undefined') return
    const saved = localStorage.getItem('sidebarCollapsed')
    if (saved !== null) {
      try {
        userCollapsed.value = JSON.parse(saved)
      } catch (e) {
        console.warn('Failed to parse sidebar state:', e)
      }
    }
  }

  // Save to localStorage
  const saveState = (collapsed) => {
    userCollapsed.value = collapsed
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebarCollapsed', JSON.stringify(collapsed))
    }
  }

  // Toggle function
  const toggleSidebar = () => {
    saveState(!userCollapsed.value)
  }

  // Handle resize
  const handleResize = () => {
    if (typeof window !== 'undefined') {
      screenWidth.value = window.innerWidth
    }
  }

  return {
    isCollapsed,
    isMobile,
    toggleSidebar,
    loadSavedState,
    handleResize
  }
}
