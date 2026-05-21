// Theme (light/dark) composable.
//
// Follows the singleton-refs-in-composable pattern used by useFilters.js:
// the `theme` ref lives at MODULE SCOPE so every component that calls
// useTheme() sees the same value. No Pinia/Vuex needed.
//
// Persistence: localStorage['sia.theme']. If unset, falls back to the OS
// `prefers-color-scheme`. The user's explicit choice always wins after that.
//
// Why the class strategy (vs. `darkMode: 'media'`): the user can override
// the OS preference per-app, and we can flip the whole UI in one place by
// toggling a single class on <html>.

import { ref } from 'vue'

const STORAGE_KEY = 'sia.theme'

function resolveInitialTheme() {
  if (typeof window === 'undefined') return 'light'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  // No explicit choice yet — defer to OS preference.
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

// Singleton — every consumer of useTheme() reads/writes the same ref.
const theme = ref(resolveInitialTheme())

function applyTheme(next) {
  if (typeof document === 'undefined') return
  // Tailwind's class strategy looks for `dark` on the root element specifically.
  const root = document.documentElement
  if (next === 'dark') root.classList.add('dark')
  else root.classList.remove('dark')
}

// Apply once at module load so the initial paint matches the resolved theme.
// Doing it here (rather than in onMounted of every consumer) avoids a flash
// of incorrect theme between hydration and the first effect tick.
applyTheme(theme.value)

export function useTheme() {
  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    window.localStorage.setItem(STORAGE_KEY, theme.value)
    applyTheme(theme.value)
  }

  const setTheme = (next) => {
    if (next !== 'light' && next !== 'dark') return
    theme.value = next
    window.localStorage.setItem(STORAGE_KEY, next)
    applyTheme(next)
  }

  return { theme, toggleTheme, setTheme }
}
