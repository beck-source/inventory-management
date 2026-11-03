<template>
  <button
    type="button"
    class="theme-toggle"
    :aria-label="t('theme.toggle')"
    :aria-pressed="isDark"
    :title="isDark ? t('theme.switchToLight') : t('theme.switchToDark')"
    @click="toggleTheme"
  >
    <!-- Sun shown in dark mode (click to go light), moon shown in light mode -->
    <svg v-if="isDark" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="3.5" stroke="currentColor" stroke-width="1.5"/>
      <path d="M10 2.5V4.5M10 15.5V17.5M2.5 10H4.5M15.5 10H17.5M4.7 4.7L6.1 6.1M13.9 13.9L15.3 15.3M4.7 15.3L6.1 13.9M13.9 6.1L15.3 4.7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M16.5 11.5A7 7 0 0 1 8.5 3.5a7 7 0 1 0 8 8Z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
    </svg>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useTheme } from '../composables/useTheme'
import { useI18n } from '../composables/useI18n'

const { theme, toggleTheme } = useTheme()
const { t } = useI18n()
const isDark = computed(() => theme.value === 'dark')
</script>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}

.theme-toggle:hover {
  background: var(--bg);
  border-color: var(--border-strong);
  color: var(--text);
}
</style>
