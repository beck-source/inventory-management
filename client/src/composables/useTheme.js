import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'theme'

function readInitial() {
  // Storage can throw (private mode, blocked site data): fall back to system preference
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'light' || saved === 'dark') return saved
  } catch {
    /* fall through */
  }
  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
  return prefersDark ? 'dark' : 'light'
}

// Module-level state so every consumer shares one theme
const theme = ref(readInitial())

// immediate: apply on first import so the attribute is set before the app mounts
watch(
  theme,
  (v) => {
    document.documentElement.dataset.theme = v
  },
  { immediate: true }
)

const isDark = computed(() => theme.value === 'dark')

function toggleTheme() {
  theme.value = isDark.value ? 'light' : 'dark'
  // Persist only explicit user choices, so the system preference applies until then
  try {
    localStorage.setItem(STORAGE_KEY, theme.value)
  } catch {
    /* non-critical */
  }
}

export function useTheme() {
  return { theme, isDark, toggleTheme }
}
