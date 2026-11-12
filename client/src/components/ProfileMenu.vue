<template>
  <div class="profile-menu">
    <button
      class="profile-button"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <div class="avatar">
        {{ getInitials(currentUser.name) }}
      </div>
      <span class="profile-name">{{ currentUser.name }}</span>
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
      <div class="dropdown-header">
        <div class="avatar-large">
          {{ getInitials(currentUser.name) }}
        </div>
        <div class="user-info">
          <div class="user-name">{{ currentUser.name }}</div>
          <div class="user-email">{{ currentUser.email }}</div>
        </div>
      </div>

      <div class="dropdown-divider"></div>

      <button
        class="dropdown-item"
        @mousedown.prevent="showProfileDetails"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M9 9C10.6569 9 12 7.65685 12 6C12 4.34315 10.6569 3 9 3C7.34315 3 6 4.34315 6 6C6 7.65685 7.34315 9 9 9Z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M15 15C15 12.7909 12.3137 11 9 11C5.68629 11 3 12.7909 3 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        {{ t('profile.profileDetails') }}
      </button>

      <button
        class="dropdown-item"
        @mousedown.prevent="showTasks"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M15 3H3C2.44772 3 2 3.44772 2 4V14C2 14.5523 2.44772 15 3 15H15C15.5523 15 16 14.5523 16 14V4C16 3.44772 15.5523 3 15 3Z" stroke="currentColor" stroke-width="1.5"/>
          <path d="M6 7L8 9L12 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('profile.myTasks') }}
        <span v-if="pendingTaskCount > 0" class="task-badge">{{ pendingTaskCount }}</span>
      </button>

      <div class="dropdown-divider"></div>

      <button
        class="dropdown-item logout"
        @mousedown.prevent="handleLogout"
      >
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M7 15H4C3.44772 15 3 14.5523 3 14V4C3 3.44772 3.44772 3 4 3H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M11 12L15 9M15 9L11 6M15 9H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('profile.logout') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

const { currentUser, logout, getInitials } = useAuth()
const { t } = useI18n()

const isDropdownOpen = ref(false)
const emit = defineEmits(['show-profile-details', 'show-tasks'])

const pendingTaskCount = computed(() => {
  return currentUser.value.tasks.filter(task => task.status === 'pending').length
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

const showProfileDetails = () => {
  isDropdownOpen.value = false
  emit('show-profile-details')
}

const showTasks = () => {
  isDropdownOpen.value = false
  emit('show-tasks')
}

const handleLogout = () => {
  isDropdownOpen.value = false
  logout()
}
</script>

<style scoped>
.profile-menu {
  position: relative;
}

/* 36px high to match the other topbar controls (menu button, language switcher). */
.profile-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-2);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color var(--transition-fast), border-color var(--transition-fast);
  font-family: inherit;
}

.profile-button:hover {
  background: var(--color-subtle);
  border-color: var(--color-border-strong);
}

.profile-button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* 24px avatar leaves 5px of breathing room inside the 36px button. Flat fill, no gradient. */
.avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 600;
  font-size: 0.625rem;
  letter-spacing: 0.025em;
}

.profile-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
}

.chevron {
  color: var(--color-muted);
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.chevron-open {
  transform: rotate(180deg);
}

/* Below 640px only the avatar and chevron remain, so the topbar fits on phones. */
@media (max-width: 639px) {
  .profile-name {
    display: none;
  }
}

/* Right-aligned to the button so it grows leftwards, away from the viewport edge.
   max-width caps it to the viewport minus the topbar gutters on very narrow screens.
   z-index is local to the topbar stacking context. */
.dropdown-menu {
  position: absolute;
  top: calc(100% + var(--space-2));
  right: 0;
  min-width: 280px;
  max-width: calc(100vw - 2 * var(--space-4));
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: 1000;
  overflow: hidden;
}

.dropdown-header {
  padding: var(--space-4);
  display: flex;
  gap: var(--space-3);
  align-items: center;
  background: var(--color-bg);
}

.avatar-large {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--color-text);
  font-size: 0.9375rem;
  margin-bottom: var(--space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-email {
  font-size: 0.8125rem;
  color: var(--color-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  background: var(--color-border);
  margin: var(--space-2) 0;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background-color var(--transition-fast);
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-soft);
}

.dropdown-item:hover {
  background: var(--color-bg);
}

.dropdown-item svg {
  color: var(--color-muted);
  flex-shrink: 0;
}

.dropdown-item.logout {
  color: var(--color-danger);
}

.dropdown-item.logout svg {
  color: var(--color-danger);
}

/* Pale red hover tint has no token (same value App.vue uses for .error), so it stays literal. */
.dropdown-item.logout:hover {
  background: #fef2f2;
}

/* Pill count badge. line-height fixes the height at 20px; the radius is large enough to round it fully. */
.task-badge {
  margin-left: auto;
  background: var(--color-primary);
  color: var(--color-surface);
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 20px;
  padding: 0 var(--space-2);
  border-radius: var(--radius-lg);
  min-width: 20px;
  text-align: center;
}
</style>
