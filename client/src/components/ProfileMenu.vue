<template>
  <div class="profile-menu">
    <button
      class="btn profile-button"
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

    <div v-if="isDropdownOpen" class="dropdown dropdown-menu">
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
  gap: var(--space-2);
  padding: 0 var(--space-3) 0 var(--space-1);
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--aurora);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: var(--fs-xs);
  letter-spacing: 0.04em;
  flex-shrink: 0;
}

.profile-name {
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--text);
  white-space: nowrap;
}

.chevron {
  color: var(--text-muted);
  transition: transform var(--t-fast) var(--ease);
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + var(--space-2));
  right: 0;
  min-width: 280px;
  z-index: 1000;
}

.dropdown-header {
  padding: var(--space-3);
  display: flex;
  gap: var(--space-3);
  align-items: center;
  background: var(--surface-sunken);
  border-radius: var(--radius-sm);
}

.avatar-large {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--aurora);
  color: var(--text-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: var(--fs-lg);
  flex-shrink: 0;
  box-shadow: var(--glow-violet);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--text);
  font-size: var(--fs-md);
  margin-bottom: var(--space-1);
}

.user-email {
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  background: var(--line);
  margin: var(--space-2) 0;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  text-align: left;
  cursor: pointer;
  transition: background var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
  font: inherit;
  font-size: var(--fs-sm);
  font-weight: 500;
  color: var(--text-muted);
}

.dropdown-item:hover {
  background: var(--surface-raised);
  color: var(--text);
}

.dropdown-item svg {
  color: var(--cyan);
  flex-shrink: 0;
}

.dropdown-item.logout,
.dropdown-item.logout svg {
  color: var(--danger);
}

.dropdown-item.logout:hover {
  background: var(--danger-bg);
}

.task-badge {
  margin-left: auto;
  background: var(--info-bg);
  color: var(--info);
  border: 1px solid currentColor;
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  font-weight: 600;
  padding: 0 var(--space-2);
  border-radius: var(--radius-pill);
  min-width: 20px;
  text-align: center;
}

@media (max-width: 1100px) {
  .profile-name {
    display: none;
  }
}
</style>
