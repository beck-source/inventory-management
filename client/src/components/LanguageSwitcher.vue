<template>
  <div class="language-switcher nav-label" ref="switcherRef">
    <button
      class="language-button"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <svg
        width="18"
        height="18"
        viewBox="0 0 20 20"
        fill="none"
        class="globe-icon"
      >
        <circle cx="10" cy="10" r="7.5" stroke="currentColor" stroke-width="1.5"/>
        <path d="M3 10H17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 7.5 5.5 7.5 10C7.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
        <path d="M10 3C10 3 12.5 5.5 12.5 10C12.5 14.5 10 17 10 17" stroke="currentColor" stroke-width="1.5"/>
      </svg>
    </button>

    <Teleport to="body">
      <div v-if="isDropdownOpen" class="dropdown-menu" :style="dropdownStyle">
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
    </Teleport>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentLocale, setLocale, availableLocales } = useI18n()

const isDropdownOpen = ref(false)
const switcherRef = ref(null)
const dropdownStyle = ref({})

const languageNames = {
  en: 'English',
  ja: '日本語'
}

const getLanguageName = (locale) => {
  return languageNames[locale] || locale
}

watch(isDropdownOpen, (val) => {
  if (val && switcherRef.value) {
    const rect = switcherRef.value.getBoundingClientRect()
    dropdownStyle.value = {
      position: 'fixed',
      bottom: `${window.innerHeight - rect.top}px`,
      left: `${rect.left}px`,
      minWidth: '160px',
      zIndex: '9999'
    }
  }
})

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
  flex-shrink: 0;
}

.language-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: var(--sidebar-text);
  transition: background 0.12s, color 0.12s;
  flex-shrink: 0;
}

.language-button:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #f1f5f9;
}

.globe-icon {
  flex-shrink: 0;
}

/* Dropdown rendered via Teleport */
.dropdown-menu {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
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
  font-size: 0.875rem;
  font-weight: 500;
  color: #334155;
}

.dropdown-item:hover {
  background: #f8fafc;
}

.dropdown-item.active {
  background: #eff6ff;
  color: #2563eb;
}

.language-name {
  flex: 1;
}

.check-icon {
  color: #2563eb;
  flex-shrink: 0;
}
</style>
