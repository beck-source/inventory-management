<template>
  <div class="language-switcher">
    <button
      ref="buttonRef"
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

    <Teleport to="body">
      <div
        v-if="isDropdownOpen"
        class="lang-dropdown-teleport"
        :style="{ position: 'fixed', bottom: dropdownPos.bottom + 'px', left: dropdownPos.left + 'px', zIndex: 2000 }"
      >
        <div class="dropdown-menu">
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
    </Teleport>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentLocale, setLocale, availableLocales, localeName } = useI18n()

const isDropdownOpen = ref(false)
const buttonRef = ref(null)
const dropdownPos = ref({ bottom: 0, left: 0 })

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
  if (isDropdownOpen.value) {
    nextTick(() => {
      const rect = buttonRef.value?.getBoundingClientRect()
      if (rect) {
        dropdownPos.value = {
          bottom: window.innerHeight - rect.top + 6,
          left: rect.left
        }
      }
    })
  }
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
  flex-shrink: 0;
}

.language-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.625rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 5px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  font-family: inherit;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.language-button:hover {
  background: var(--color-bg-overlay);
  border-color: var(--color-text-muted);
}

.globe-icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.language-label {
  font-weight: 500;
}

.chevron {
  color: var(--color-text-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  min-width: 160px;
  background: var(--color-bg-overlay);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.dropdown-item:hover {
  background: var(--color-bg-elevated);
  color: var(--color-text-primary);
}

.dropdown-item.active {
  background: rgba(0, 212, 255, 0.1);
  color: var(--color-accent);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}
</style>
