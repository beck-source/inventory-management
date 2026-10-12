<template>
  <button class="dark-mode-toggle" @click="toggleDark" :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'">
    <svg v-if="isDark" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="4" stroke="currentColor" stroke-width="1.5"/>
      <path d="M10 2V4M10 16V18M2 10H4M16 10H18M4.22 4.22L5.64 5.64M14.36 14.36L15.78 15.78M15.78 4.22L14.36 5.64M5.64 14.36L4.22 15.78" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M17.5 10.9A7.5 7.5 0 0 1 9.1 2.5a7.5 7.5 0 1 0 8.4 8.4z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
    </svg>
  </button>
</template>

<script>
import { useDarkMode } from '../composables/useDarkMode'

export default {
  name: 'DarkModeToggle',
  setup() {
    const { isDark, toggleDark } = useDarkMode()
    return { isDark, toggleDark }
  }
}
</script>

<style scoped>
.dark-mode-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s ease;
  margin-right: 0.75rem;
  flex-shrink: 0;
}

.dark-mode-toggle:hover {
  background: #f1f5f9;
  color: #0f172a;
  border-color: #cbd5e1;
}

:global(html.dark) .dark-mode-toggle {
  border-color: #334155;
  color: #94a3b8;
}

:global(html.dark) .dark-mode-toggle:hover {
  background: #1e293b;
  color: #f1f5f9;
  border-color: #475569;
}
</style>
