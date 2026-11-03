import { ref, watch } from 'vue'

const STORAGE_KEY = 'app-theme'

// localStorage can throw (private mode, blocked storage), so every access is guarded.
const readStoredTheme = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored === 'dark' || stored === 'light' ? stored : null
  } catch {
    return null
  }
}

const getSystemTheme = () => {
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

// Setting data-theme on <html> lets the CSS variable overrides in App.vue take effect globally.
export const applyTheme = (theme) => {
  document.documentElement.setAttribute('data-theme', theme)
}

// Module-level state so every caller shares one theme (same pattern as useI18n).
// Saved choice wins; otherwise follow the OS preference.
const theme = ref(readStoredTheme() || getSystemTheme())
applyTheme(theme.value)

watch(theme, (value) => {
  applyTheme(value)
  try {
    localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Persistence is best-effort; the theme still applies for this session.
  }
})

export function useTheme() {
  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }
  return { theme, toggleTheme }
}
