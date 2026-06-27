import { ref } from 'vue'

const mq = window.matchMedia('(prefers-color-scheme: dark)')
const isDark = ref(mq.matches)

function applyTheme(dark) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
}

applyTheme(isDark.value)

mq.addEventListener('change', (e) => {
  isDark.value = e.matches
  applyTheme(e.matches)
})

export function useTheme() {
  const toggleTheme = () => {
    isDark.value = !isDark.value
    applyTheme(isDark.value)
  }

  return { isDark, toggleTheme }
}
