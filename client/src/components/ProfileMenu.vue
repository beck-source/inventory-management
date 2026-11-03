<template>
  <div class="profile-menu" :class="{ 'is-compact': compact }">
    <button
      class="profile-button"
      aria-haspopup="true"
      :aria-expanded="isDropdownOpen ? 'true' : 'false'"
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
        aria-hidden="true"
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

// Additive and optional: AppSidebar passes its collapsed state so only the avatar shows
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
/*
  This menu lives in the dark sidebar footer: the trigger is styled for a dark background
  and the dropdown opens upward (or sideways when only the avatar is visible).
  Do not put overflow:hidden on any sidebar ancestor, it would clip the dropdown.
*/
.profile-menu {
  position: relative;
}

.profile-button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: 0;
  border-radius: var(--radius-md);
  color: var(--text-on-sidebar);
  text-align: left;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
  font-family: inherit;
}

.profile-button:hover {
  background: var(--bg-sidebar-hover);
  color: var(--text-on-sidebar-strong);
}

/* White ring: the global accent ring has too little contrast on the dark sidebar */
.profile-button:focus-visible {
  outline: 2px solid #fff;
  outline-offset: -2px;
}

.avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.75rem;
  letter-spacing: 0.025em;
}

.profile-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-weight: 500;
  color: inherit;
}

/* The dropdown opens upward, so the closed chevron points up and flips down when open */
.chevron {
  flex-shrink: 0;
  color: inherit;
  opacity: 0.7;
  transform: rotate(180deg);
  transition: transform 0.2s ease;
}

.chevron-open {
  transform: rotate(0deg);
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 0.5rem);
  left: 0;
  min-width: 280px;
  max-width: calc(100vw - 1rem);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 25px rgb(15 23 42 / 0.2);
  z-index: 1000;
  overflow: hidden;
}

/* Avatar-only mode, manual collapse (>= 720px; the mobile drawer is always full width) */
@media (min-width: 720px) {
  .profile-menu.is-compact .profile-button {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }

  /* Visually hidden rather than display:none so the button keeps an accessible name */
  .profile-menu.is-compact .profile-name {
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }

  .profile-menu.is-compact .chevron {
    display: none;
  }

  /* Open to the side, aligned with the trigger, so the narrow sidebar does not clip it */
  .profile-menu.is-compact .dropdown-menu {
    bottom: 0;
    left: calc(100% + 0.5rem);
  }
}

/* Same avatar-only mode when the sidebar is forced to icons-only (720px - 1099px) */
@media (min-width: 720px) and (max-width: 1099px) {
  .profile-button {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }

  .profile-name {
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }

  .chevron {
    display: none;
  }

  .dropdown-menu {
    bottom: 0;
    left: calc(100% + 0.5rem);
  }
}

.dropdown-header {
  padding: var(--space-4);
  display: flex;
  gap: 0.875rem;
  align-items: center;
  background: var(--bg-app);
}

.avatar-large {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  color: white;
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
  color: var(--text);
  font-size: 0.938rem;
  margin-bottom: var(--space-1);
}

.user-email {
  font-size: 0.813rem;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  background: var(--border);
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
  transition: background 0.15s ease;
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-secondary);
}

.dropdown-item:hover {
  background: var(--bg-app);
}

.dropdown-item svg {
  color: var(--text-muted);
  flex-shrink: 0;
}

.dropdown-item.logout {
  color: #dc2626;
}

.dropdown-item.logout svg {
  color: #dc2626;
}

.dropdown-item.logout:hover {
  background: #fef2f2;
}

.task-badge {
  margin-left: auto;
  background: var(--accent);
  color: white;
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 0.125rem var(--space-2);
  border-radius: 12px;
  min-width: 20px;
  text-align: center;
}
</style>
