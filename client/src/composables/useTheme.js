import { ref, computed } from 'vue'

// Module-level state so every caller shares one theme.
const STORAGE_KEY = 'ui.theme' // keep in sync with theme-init.html
const media = typeof window !== 'undefined'
  ? window.matchMedia('(prefers-color-scheme: dark)')
  : null

function readPreference() {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === 'light' || value === 'dark' ? value : 'system'
  } catch {
    return 'system'
  }
}

const preference = ref(readPreference()) // 'light' | 'dark' | 'system'
const systemDark = ref(media ? media.matches : false)

const resolvedTheme = computed(() => {
  if (preference.value === 'system') return systemDark.value ? 'dark' : 'light'
  return preference.value
})

function apply() {
  document.documentElement.setAttribute('data-theme', resolvedTheme.value)
}

// Follow OS changes live, but only matters while preference is 'system'.
if (media) {
  media.addEventListener('change', (event) => {
    systemDark.value = event.matches
    apply()
  })
}

export function useTheme() {
  const setTheme = (value) => {
    preference.value = value
    try {
      if (value === 'system') localStorage.removeItem(STORAGE_KEY)
      else localStorage.setItem(STORAGE_KEY, value)
    } catch {
      // Persisting is a convenience; the theme still applies for this session.
    }
    apply()
  }

  // Cycle order for a single icon button: system -> light -> dark -> system.
  const cycleTheme = () => {
    const order = ['system', 'light', 'dark']
    setTheme(order[(order.indexOf(preference.value) + 1) % order.length])
  }

  return { preference, resolvedTheme, setTheme, cycleTheme }
}
