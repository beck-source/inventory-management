<template>
  <div class="language-switcher">
    <button
      class="language-button"
      type="button"
      :aria-label="t('language.selectLanguage')"
      aria-haspopup="menu"
      :aria-expanded="String(isDropdownOpen)"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <AppIcon name="globe" :size="16" class="globe-icon" />
      <span class="language-label">{{ localeName }}</span>
      <AppIcon
        name="chevron-down"
        :size="14"
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
      />
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu" role="menu">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="dropdown-item"
        type="button"
        role="menuitem"
        :class="{ active: currentLocale === locale }"
        @mousedown.prevent="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <AppIcon
          v-if="currentLocale === locale"
          name="checkmark"
          :size="16"
          class="check-icon"
        />
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'
import AppIcon from './AppIcon.vue'

const { t, currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const handleBlur = () => {
  // Delay to allow mousedown events on dropdown items to fire first
  setTimeout(() => {
    isDropdownOpen.value = false
  }, 200)
}

const selectLanguage = (locale) => {
  setLocale(locale)
  isDropdownOpen.value = false
}
</script>

<style scoped>
.language-switcher {
  position: relative;
}

.language-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease), border-color var(--duration-fast) var(--ease);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.language-button:hover {
  background: var(--color-surface-hover);
}

/* The global :focus-visible rule rounds to --radius-sm; keep each control's own radius. */
.language-button:focus-visible {
  border-radius: var(--radius-md);
}

.globe-icon,
.chevron {
  color: var(--color-text-subtle);
}

.language-label {
  white-space: nowrap;
}

.chevron {
  transition: transform var(--duration) var(--ease);
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + var(--space-2));
  right: 0;
  min-width: 160px;
  padding: var(--space-1);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: var(--z-dropdown);
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  text-align: left;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.dropdown-item:hover {
  background: var(--color-surface-hover);
}

.dropdown-item.active {
  background: var(--color-accent-soft);
  color: var(--color-accent-text);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--color-accent-text);
}

/* Icon-only on narrow screens so the top bar fits on a phone. */
@media (max-width: 639px) {
  .language-label,
  .chevron { display: none; }
  .language-button { padding: 0; width: 36px; justify-content: center; }
}
</style>
