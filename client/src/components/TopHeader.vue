<template>
  <header class="top-header">
    <!-- Mobile hamburger -->
    <button
      class="hamburger-btn"
      @click="$emit('open-mobile-sidebar')"
      aria-label="Open navigation"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
    </button>

    <!-- Page title -->
    <div class="header-title">
      <span class="page-eyebrow">Workspace</span>
      <h1 class="current-page">{{ currentPageTitle }}</h1>
    </div>

    <!-- Search -->
    <div class="header-search">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 20 20" fill="none">
        <circle cx="9" cy="9" r="6" stroke="currentColor" stroke-width="1.8"/>
        <path d="M14 14L17 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <input
        type="text"
        :placeholder="t('common.search') + '…'"
        class="search-input"
        v-model="searchQuery"
      />
      <span class="search-kbd">⌘K</span>
    </div>

    <!-- Right side actions -->
    <div class="header-actions">
      <button class="icon-btn" aria-label="Notifications" title="Notifications">
        <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
          <path d="M10 3C7.79 3 6 4.79 6 7V10L4.5 12.5H15.5L14 10V7C14 4.79 12.21 3 10 3Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
          <path d="M8.5 15C8.5 15.83 9.17 16.5 10 16.5C10.83 16.5 11.5 15.83 11.5 15" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
        </svg>
        <span class="notification-dot"></span>
      </button>
      <LanguageSwitcher />
      <div class="header-divider"></div>
      <ProfileMenu
        @show-profile-details="$emit('show-profile-details')"
        @show-tasks="$emit('show-tasks')"
      />
    </div>
  </header>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

defineEmits(['open-mobile-sidebar', 'show-profile-details', 'show-tasks'])

const route = useRoute()
const { t } = useI18n()
const searchQuery = ref('')

const currentPageTitle = computed(() => {
  const pathMap = {
    '/': t('nav.overview'),
    '/inventory': t('nav.inventory'),
    '/orders': t('nav.orders'),
    '/spending': t('nav.finance'),
    '/reports': t('nav.analytics'),
    '/demand': t('nav.demandForecast')
  }
  return pathMap[route.path] || ''
})
</script>

<style scoped>
.top-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--header-height);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
  gap: 1rem;
}

.hamburger-btn {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.hamburger-btn:hover {
  color: var(--color-text-primary);
  background: var(--color-surface-alt);
  border-color: var(--color-border-strong);
}

.header-title {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  flex-shrink: 0;
}

.page-eyebrow {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--color-text-faint);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  line-height: 1;
  margin-bottom: 3px;
}

.current-page {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
  line-height: 1.2;
  margin: 0;
}

/* Search */
.header-search {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  max-width: 420px;
  margin: 0 auto 0 1.5rem;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--color-text-faint);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.5rem 3rem 0.5rem 2.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  color: var(--color-text-primary);
  background: var(--color-surface-sunken);
  transition: all 0.15s ease;
}

.search-input::placeholder {
  color: var(--color-text-faint);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: var(--color-surface);
  box-shadow: var(--shadow-focus);
}

.search-kbd {
  position: absolute;
  right: 0.625rem;
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--color-text-faint);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  padding: 0.125rem 0.375rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  pointer-events: none;
}

/* Right side */
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.icon-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.icon-btn:hover {
  background: var(--color-surface-alt);
  color: var(--color-text-primary);
}

.notification-dot {
  position: absolute;
  top: 8px;
  right: 9px;
  width: 7px;
  height: 7px;
  background: var(--color-error);
  border: 2px solid var(--color-surface);
  border-radius: 50%;
}

.header-divider {
  width: 1px;
  height: 24px;
  background: var(--color-border);
  margin: 0 0.25rem;
}

/* Mobile */
@media (max-width: 1024px) {
  .header-search {
    max-width: 280px;
  }

  .search-kbd {
    display: none;
  }
}

@media (max-width: 768px) {
  .hamburger-btn {
    display: flex;
  }

  .page-eyebrow {
    display: none;
  }

  .header-search {
    display: none;
  }

  .top-header {
    padding: 0 1rem;
  }
}
</style>
