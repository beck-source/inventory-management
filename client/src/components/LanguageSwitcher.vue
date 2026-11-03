<template>
  <div class="language-switcher">
    <button
      class="language-button"
      :title="localeName"
      :aria-label="localeName"
      aria-haspopup="true"
      :aria-expanded="isDropdownOpen"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <svg
        width="20"
        height="20"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
      </svg>
      <span class="language-label">{{ localeName }}</span>
      <svg
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
        width="16"
        height="16"
        viewBox="0 0 16 16"
        fill="none"
      >
        <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        class="dropdown-item"
        :class="{ active: currentLocale === locale }"
        @mousedown.prevent="selectLanguage(locale)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg
          v-if="currentLocale === locale"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          class="check-icon"
        >
          <path d="M4 9L7.5 12.5L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

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
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-3);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
  font-family: inherit;
  font-size: var(--text-sm);
  color: var(--sidebar-text);
}

.language-button:hover {
  background: var(--sidebar-item-hover);
  color: var(--color-text);
}

.globe-icon {
  flex-shrink: 0;
}

.language-label {
  flex: 1;
  min-width: 0;
  text-align: left;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chevron {
  color: var(--color-text-muted);
  transition: transform var(--transition-base);
  flex-shrink: 0;
  transform: rotate(180deg);
}

.chevron-open {
  transform: rotate(0deg);
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + var(--space-2));
  left: 0;
  right: 0;
  min-width: 160px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-overlay);
  z-index: 1;
  overflow: hidden;
  padding: var(--space-1);
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  height: 36px;
  padding: 0 var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  text-align: left;
  cursor: pointer;
  transition: background var(--transition-fast);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.dropdown-item:hover {
  background: var(--color-surface-muted);
}

.dropdown-item.active {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--color-primary);
  flex-shrink: 0;
}

/* Collapsed sidebar: icon only, menu opens over the content area from the sidebar edge */
@media (min-width: 768px) {
  .sidebar-collapsed .language-button {
    justify-content: center;
    padding: 0;
  }

  .sidebar-collapsed .language-label,
  .sidebar-collapsed .chevron {
    display: none;
  }

  .sidebar-collapsed .dropdown-menu {
    right: auto;
    width: max-content;
    min-width: 160px;
  }
}
</style>
