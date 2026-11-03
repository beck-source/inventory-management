import { ref, watch } from 'vue'

// Storage can be blocked (private mode, disabled cookies), so every access is wrapped.
const read = (key, fallback) => {
  try {
    return localStorage.getItem(key) ?? fallback
  } catch {
    return fallback
  }
}

const write = (key, value) => {
  try {
    localStorage.setItem(key, value)
  } catch {
    // Non-fatal: the preference just will not persist
  }
}

const prefersDark = () =>
  typeof window !== 'undefined' &&
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(prefers-color-scheme: dark)').matches

// Initialised from storage at module load so the first paint is already correct (no layout jump).
const savedTheme = read('theme', null)
const collapsed = ref(read('sidebar-collapsed', 'false') === 'true')
const theme = ref(savedTheme === 'dark' || savedTheme === 'light' ? savedTheme : prefersDark() ? 'dark' : 'light')
const drawerOpen = ref(false)

// Only persist explicit user choices; an unsaved theme keeps following the OS default.
let themeChosen = savedTheme === 'dark' || savedTheme === 'light'

watch(collapsed, (v) => write('sidebar-collapsed', String(v)))
watch(
  theme,
  (v) => {
    document.documentElement.dataset.theme = v
    if (themeChosen) write('theme', v)
  },
  { immediate: true }
)

export function useLayout() {
  const toggleCollapse = () => {
    collapsed.value = !collapsed.value
  }

  const toggleTheme = () => {
    themeChosen = true
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  return { collapsed, theme, drawerOpen, toggleCollapse, toggleTheme }
}
