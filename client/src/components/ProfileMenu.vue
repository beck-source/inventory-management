<template>
  <div class="profile-menu">
    <button
      class="profile-button"
      type="button"
      aria-haspopup="menu"
      :aria-expanded="String(isDropdownOpen)"
      @click="toggleDropdown"
      @blur="handleBlur"
    >
      <div class="avatar">
        {{ getInitials(currentUser.name) }}
      </div>
      <span class="profile-name">{{ currentUser.name }}</span>
      <AppIcon
        name="chevron-down"
        :size="14"
        class="chevron"
        :class="{ 'chevron-open': isDropdownOpen }"
      />
    </button>

    <div v-if="isDropdownOpen" class="dropdown-menu" role="menu">
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
        type="button"
        role="menuitem"
        @mousedown.prevent="showProfileDetails"
      >
        <AppIcon name="user" :size="16" />
        {{ t('profile.profileDetails') }}
      </button>

      <button
        class="dropdown-item"
        type="button"
        role="menuitem"
        @mousedown.prevent="showTasks"
      >
        <AppIcon name="check" :size="16" />
        {{ t('profile.myTasks') }}
        <span v-if="pendingTaskCount > 0" class="task-badge">{{ pendingTaskCount }}</span>
      </button>

      <div class="dropdown-divider"></div>

      <button
        class="dropdown-item logout"
        type="button"
        role="menuitem"
        @mousedown.prevent="handleLogout"
      >
        <AppIcon name="logout" :size="16" />
        {{ t('profile.logout') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'
import AppIcon from './AppIcon.vue'

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
  gap: var(--space-2);
  height: 36px;
  /* 3px inset keeps the 28px avatar visually centered in the 36px pill. */
  padding: 0 var(--space-3) 0 3px;
  max-width: 220px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease), border-color var(--duration-fast) var(--ease);
  font-family: inherit;
}

.profile-button:hover {
  background: var(--color-surface-hover);
}

/* The global :focus-visible rule rounds to --radius-sm; keep each control's own radius. */
.profile-button:focus-visible {
  border-radius: var(--radius-md);
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  background: var(--color-accent);
  color: var(--color-on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: var(--weight-semibold);
  font-size: var(--text-xs);
  letter-spacing: 0.025em;
}

.profile-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.chevron {
  color: var(--color-text-subtle);
  transition: transform var(--duration) var(--ease);
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + var(--space-2));
  right: 0;
  width: 280px;
  max-width: calc(100vw - var(--space-8));
  padding-bottom: var(--space-1);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: var(--z-dropdown);
  overflow: hidden;
}

.dropdown-header {
  padding: var(--space-4);
  display: flex;
  gap: var(--space-3);
  align-items: center;
  background: var(--color-surface-muted);
}

.avatar-large {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-full);
  background: var(--color-accent);
  color: var(--color-on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--weight-bold);
  font-size: var(--text-md);
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: var(--weight-semibold);
  color: var(--color-text);
  font-size: var(--text-base);
  margin-bottom: var(--space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-email {
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  background: var(--color-border);
  margin: var(--space-1) 0;
}

.dropdown-item {
  width: calc(100% - var(--space-2));
  margin: 0 var(--space-1);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  text-align: left;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease);
  font-family: inherit;
  font-size: var(--text-sm);
  font-weight: var(--weight-medium);
  color: var(--color-text);
}

.dropdown-item:hover {
  background: var(--color-surface-hover);
}

.dropdown-item svg {
  color: var(--color-text-subtle);
}

.dropdown-item.logout,
.dropdown-item.logout svg {
  color: var(--color-danger);
}

.dropdown-item.logout:hover {
  background: var(--color-danger-soft);
}

.task-badge {
  margin-left: auto;
  background: var(--color-accent);
  color: var(--color-on-accent);
  font-size: var(--text-xs);
  font-weight: var(--weight-semibold);
  padding: 0 var(--space-2);
  border-radius: var(--radius-full);
  min-width: 20px;
  line-height: 20px;
  text-align: center;
}

/* Avatar only on narrow screens so the top bar fits on a phone. */
@media (max-width: 639px) {
  .profile-name,
  .chevron { display: none; }
  .profile-button { padding: 3px; }
}
</style>
