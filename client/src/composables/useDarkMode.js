import { ref } from 'vue'

const STORAGE_KEY = 'darkMode'

function getInitialDark() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored !== null) return stored === 'true'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

const isDark = ref(getInitialDark())

function applyDark(value) {
  if (value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
  localStorage.setItem(STORAGE_KEY, String(value))
}

applyDark(isDark.value)

export function useDarkMode() {
  const toggleDark = () => {
    isDark.value = !isDark.value
    applyDark(isDark.value)
  }

  return {
    isDark,
    toggleDark
  }
}
