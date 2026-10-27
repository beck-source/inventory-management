<template>
  <div class="profile-menu" :class="{ compact }">
    <button
      class="profile-button"
      :title="compact ? currentUser.name : undefined"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <div class="avatar">
        {{ getInitials(currentUser.name) }}
      </div>
      <span class="profile-name">{{ currentUser.name }}</span>
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

// compact: icon-only rail mode driven by the sidebar collapse state.
defineProps({
  compact: { type: Boolean, default: false }
})

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
  width: 100%;
}

.profile-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 44px;
  padding: var(--space-1) var(--space-2);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-control);
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
  font-family: inherit;
}

.profile-button:hover {
  background: var(--color-bg);
  border-color: var(--color-border-strong);
}

.profile-button:focus-visible {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: var(--focus-ring);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--weight-semibold);
  font-size: var(--text-xs);
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.profile-name {
  flex: 1;
  min-width: 0;
  text-align: left;
  font-size: var(--text-base);
  font-weight: var(--weight-medium);
  color: var(--color-heading);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  color: var(--color-text-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

/* Sidebar footer sits at the bottom of the viewport, so the menu flips upward.
   Left/right 0 keeps it within the sidebar width (240px minus footer padding). */
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

/* Compact (rail) mode: anchor to the left edge with a fixed min-width so the menu
   extends right over the content instead of being squeezed into the rail. */
.compact .dropdown-menu {
  right: auto;
  min-width: 200px;
}

.compact .profile-button {
  justify-content: center;
  padding: var(--space-1);
}

/* Name stays in the DOM as the button's accessible name. */
.compact .profile-name {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  flex: none;
  clip: rect(0, 0, 0, 0);
}

.compact .chevron {
  display: none;
}

.dropdown-header {
  padding: var(--space-3);
  display: flex;
  gap: var(--space-3);
  align-items: center;
  background: var(--color-bg);
}

.avatar-large {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--weight-bold);
  font-size: var(--text-base);
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: var(--weight-semibold);
  color: var(--color-heading);
  font-size: var(--text-base);
  margin-bottom: var(--space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-email {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
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

.dropdown-item svg {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.dropdown-item.logout,
.dropdown-item.logout svg {
  color: var(--color-danger);
}

.dropdown-item.logout:hover {
  background: #fef2f2;
}

.task-badge {
  margin-left: auto;
  background: var(--color-accent);
  color: white;
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  padding: 2px var(--space-2);
  border-radius: 12px;
  min-width: 20px;
  text-align: center;
}

@media (prefers-reduced-motion: reduce) {
  .chevron,
  .profile-button,
  .dropdown-item {
    transition: none;
  }
}
</style>
