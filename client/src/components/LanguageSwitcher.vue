<template>
  <div class="language-switcher">
    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <button class="language-button">
          <svg width="16" height="16" viewBox="0 0 20 20" fill="none" class="globe-icon">
            <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
          </svg>
          <span class="language-label">{{ localeName }}</span>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        side="top"
        align="start"
        :side-offset="4"
        class="w-(--reka-dropdown-menu-trigger-width) overflow-hidden rounded-[10px] border-[var(--line)] bg-[var(--surface-card)] p-0 shadow-[0_8px_24px_rgba(15,23,42,0.08)]"
      >
        <DropdownMenuItem
          v-for="locale in availableLocales"
          :key="locale"
          :class="[
            'justify-between gap-3 rounded-none px-4 py-2.5 text-[13px] font-medium focus:bg-[var(--surface-muted)] focus:text-[var(--ink-secondary)]',
            currentLocale === locale
              ? 'bg-[rgba(59,130,246,0.08)] text-[var(--accent)] focus:bg-[rgba(59,130,246,0.08)] focus:text-[var(--accent)]'
              : 'text-[var(--ink-secondary)]'
          ]"
          @select="selectLanguage(locale)"
        >
          <span>{{ getLanguageName(locale) }}</span>
          <svg v-if="currentLocale === locale" width="16" height="16" viewBox="0 0 18 18" fill="none" class="text-[var(--accent)]">
            <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>

<script setup>
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { useI18n } from '../composables/useI18n'

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

// reka-ui closes the menu on select.
const selectLanguage = (locale) => {
  setLocale(locale)
}
</script>

<style scoped>
.language-button {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  background: transparent;
  border: none;
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: 12px;
  color: var(--ink-muted);
  width: 100%;
}

.language-button:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--surface-bg);
}

.globe-icon {
  flex-shrink: 0;
}

.language-label {
  font-weight: 500;
}
</style>
