<template>
  <div class="language-switcher" :class="{ compact }">
    <button
      class="language-button"
      @click="toggleDropdown"
      @blur="handleBlur"
      :title="compact ? localeName : undefined"
      :aria-label="localeName"
      aria-haspopup="menu"
      :aria-expanded="isDropdownOpen"
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

// compact: icon-rail mode in the sidebar (globe icon only)
defineProps({ compact: { type: Boolean, default: false } })

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
.language-switcher { position: relative; }

.language-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color var(--duration) var(--ease), color var(--duration) var(--ease);
  font-size: var(--text-base);
  color: var(--sidebar-text);
}
.language-button:hover { background: var(--sidebar-item-hover); color: var(--sidebar-text-active); }
.compact .language-button { justify-content: center; }
.compact .language-label, .compact .chevron { display: none; }

.globe-icon { flex-shrink: 0; }
.language-label { flex: 1; text-align: left; font-weight: 500; }
.chevron { flex-shrink: 0; transition: transform var(--duration) var(--ease); }
.chevron-open { transform: rotate(-90deg); }

/* Opens toward the content area, anchored to the bottom of the trigger */
.dropdown-menu {
  position: absolute;
  left: calc(100% + var(--space-2));
  bottom: 0;
  min-width: 160px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  overflow: hidden;
}
/* Drawer (below 1024px): open upward within the drawer width */
@media (max-width: 1023px) {
  .dropdown-menu { left: 0; right: 0; bottom: calc(100% + var(--space-2)); min-width: 0; }
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background-color var(--duration) var(--ease);
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--text-secondary);
}
.dropdown-item:hover { background: var(--surface-muted); }
.dropdown-item.active { background: var(--accent-soft); color: var(--text); }
.language-name { flex: 1; }
.check-icon { color: var(--accent-hover); flex-shrink: 0; }
</style>
