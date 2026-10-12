<template>
  <div class="language-switcher">
    <button
      class="language-button"
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
  display: flex;
  align-items: center;
  gap: var(--uui-space-6);
  height: var(--uui-size-36);
  padding: 0 var(--uui-space-12);
  background: var(--uui-control-bg);
  border: 1px solid var(--uui-border);
  border-radius: var(--uui-radius-6);
  cursor: pointer;
  transition: all 0.12s ease;
  font-family: var(--uui-font);
  font-size: var(--uui-text-s-size);
  font-weight: var(--uui-fw-semibold);
  color: var(--uui-text-primary);
}

.language-button:hover {
  background: var(--uui-night-100);
  border-color: var(--uui-border-strong);
}

.globe-icon {
  color: var(--uui-icon);
  flex-shrink: 0;
}

.language-label {
  font-weight: var(--uui-fw-semibold);
}

.chevron {
  color: var(--uui-icon);
  transition: transform 0.12s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + var(--uui-space-6));
  right: 0;
  min-width: 160px;
  background: var(--uui-surface-higher);
  border: 1px solid var(--uui-border);
  border-radius: var(--uui-radius-12);
  box-shadow: var(--uui-shadow-300);
  z-index: var(--uui-z-dropdown);
  overflow: hidden;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--uui-space-12);
  padding: var(--uui-space-12);
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.12s ease;
  font-family: var(--uui-font);
  font-size: var(--uui-text-s-size);
  font-weight: var(--uui-fw-semibold);
  color: var(--uui-text-primary);
}

.dropdown-item:hover {
  background: var(--uui-night-100);
}

.dropdown-item.active {
  background: var(--uui-primary-subtle);
  color: var(--uui-blue-80);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--uui-primary);
  flex-shrink: 0;
}
</style>
