import { ref, watch } from 'vue'

const isDark = ref(false)

// Initialize from localStorage or system preference
const stored = localStorage.getItem('theme')
if (stored) {
  isDark.value = stored === 'dark'
} else {
  isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches
}

// Apply to document root so CSS [data-theme="dark"] selectors work globally
function applyTheme(dark) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}

applyTheme(isDark.value)

watch(isDark, (val) => {
  applyTheme(val)
  localStorage.setItem('theme', val ? 'dark' : 'light')
})

export function useDarkMode() {
  const toggleDark = () => {
    isDark.value = !isDark.value
  }

  return { isDark, toggleDark }
}
