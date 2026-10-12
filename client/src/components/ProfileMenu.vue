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

.profile-button {
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
}

.profile-button:hover {
  background: var(--uui-night-100);
  border-color: var(--uui-border-strong);
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: var(--uui-radius-full);
  background: var(--uui-primary);
  color: var(--uui-white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--uui-fw-semibold);
  font-size: var(--uui-text-xs-size);
  flex-shrink: 0;
}

.profile-name {
  font-size: var(--uui-text-s-size);
  font-weight: var(--uui-fw-semibold);
  color: var(--uui-text-primary);
}

.chevron {
  color: var(--uui-icon);
  transition: transform 0.12s ease;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + var(--uui-space-6));
  right: 0;
  min-width: 280px;
  background: var(--uui-surface-higher);
  border: 1px solid var(--uui-border);
  border-radius: var(--uui-radius-12);
  box-shadow: var(--uui-shadow-300);
  z-index: var(--uui-z-dropdown);
  overflow: hidden;
}

.dropdown-header {
  padding: var(--uui-space-12);
  display: flex;
  gap: var(--uui-space-12);
  align-items: center;
  background: var(--uui-surface-lowest);
  border-bottom: 1px solid var(--uui-divider);
}

.avatar-large {
  width: var(--uui-size-48);
  height: var(--uui-size-48);
  border-radius: var(--uui-radius-full);
  background: var(--uui-primary);
  color: var(--uui-white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--uui-fw-bold);
  font-size: var(--uui-text-m-size);
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: var(--uui-fw-semibold);
  color: var(--uui-text-primary);
  font-size: var(--uui-text-m-size);
  margin-bottom: var(--uui-space-3);
}

.user-email {
  font-size: var(--uui-text-xs-size);
  color: var(--uui-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  background: var(--uui-divider);
  margin: var(--uui-space-3) 0;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--uui-space-12);
  padding: var(--uui-space-12) var(--uui-space-12);
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

.dropdown-item svg {
  color: var(--uui-icon);
  flex-shrink: 0;
}

.dropdown-item.logout {
  color: var(--uui-error);
}

.dropdown-item.logout svg {
  color: var(--uui-error);
}

.dropdown-item.logout:hover {
  background: var(--uui-error-subtle);
}

.task-badge {
  margin-left: auto;
  background: var(--uui-primary);
  color: var(--uui-white);
  font-size: var(--uui-text-xs-size);
  font-weight: var(--uui-fw-semibold);
  padding: 1px var(--uui-space-6);
  border-radius: var(--uui-radius-full);
  min-width: 20px;
  text-align: center;
}
</style>
