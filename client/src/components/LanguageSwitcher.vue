<template>
  <div class="language-switcher" :class="{ compact }">
    <button
      class="language-button"
      :title="compact ? localeName : undefined"
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
        aria-hidden="true"
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

// compact: icon-only rail mode driven by the sidebar collapse state.
defineProps({
  compact: { type: Boolean, default: false }
})

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
  width: 100%;
}

.language-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: var(--control-height);
  padding: 0 var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-control);
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
  font-family: inherit;
  font-size: var(--text-base);
  color: var(--color-text);
}

.language-button:hover {
  background: var(--color-bg);
  border-color: var(--color-border-strong);
}

.language-button:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
}

.globe-icon {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.language-label {
  flex: 1;
  text-align: left;
  font-weight: var(--weight-medium);
}

.chevron {
  color: var(--color-text-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

/* Sidebar footer sits at the bottom of the viewport, so the menu flips upward and
   is pinned to the trigger's width to stay inside the sidebar. */
.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 0.5rem);
  left: 0;
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-md);
  z-index: 1000;
  overflow: hidden;
}

/* Compact (rail) mode: the rail is too narrow for a full-width menu, so anchor to the
   left edge with a fixed min-width and let it extend right over the content. */
.compact .dropdown-menu {
  right: auto;
  min-width: 200px;
}

.compact .language-button {
  justify-content: center;
  padding: 0;
}

/* Label stays in the DOM as the button's accessible name. */
.compact .language-label {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

.compact .chevron {
  display: none;
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
  transition: background-color 0.15s ease;
  font-family: inherit;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.dropdown-item:hover {
  background: var(--color-bg);
}

.dropdown-item:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: -2px;
}

.dropdown-item.active {
  background: var(--color-accent-tint);
  color: var(--color-accent);
}

.language-name {
  flex: 1;
}

.check-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}

@media (prefers-reduced-motion: reduce) {
  .chevron,
  .language-button,
  .dropdown-item {
    transition: none;
  }
}
</style>
