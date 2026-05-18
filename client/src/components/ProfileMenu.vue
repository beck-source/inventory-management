<template>
  <div class="profile-menu">
    <button
      ref="buttonRef"
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

    <Teleport to="body">
      <div
        v-if="isDropdownOpen"
        class="profile-dropdown-teleport"
        :style="{ position: 'fixed', bottom: dropdownPos.bottom + 'px', left: dropdownPos.left + 'px', zIndex: 2000 }"
      >
        <div class="dropdown-menu">
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
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

const { currentUser, logout, getInitials } = useAuth()
const { t } = useI18n()

const isDropdownOpen = ref(false)
const buttonRef = ref(null)
const dropdownPos = ref({ bottom: 0, left: 0 })
const emit = defineEmits(['show-profile-details', 'show-tasks'])

const pendingTaskCount = computed(() => {
  return currentUser.value.tasks.filter(task => task.status === 'pending').length
})

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
  if (isDropdownOpen.value) {
    nextTick(() => {
      const rect = buttonRef.value?.getBoundingClientRect()
      if (rect) {
        dropdownPos.value = {
          bottom: window.innerHeight - rect.top + 6,
          left: rect.left
        }
      }
    })
  }
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
  min-width: 0;
  overflow: visible;
  flex: 1;
}

.profile-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.375rem 0.625rem;
  width: 100%;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 5px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  font-family: inherit;
  min-width: 0;
  overflow: hidden;
  color: var(--color-text-secondary);
}

.profile-button:hover {
  background: var(--color-bg-overlay);
  border-color: var(--color-text-muted);
}

.avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-accent) 0%, #0090cc 100%);
  color: #0d1117;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.65rem;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.profile-name {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
}

.chevron {
  color: var(--color-text-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron-open {
  transform: rotate(180deg);
}

.dropdown-menu {
  min-width: 240px;
  background: var(--color-bg-overlay);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.dropdown-header {
  padding: 0.875rem 1rem;
  display: flex;
  gap: 0.75rem;
  align-items: center;
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
}

.avatar-large {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-accent) 0%, #0090cc 100%);
  color: #0d1117;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.875rem;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 0.875rem;
  margin-bottom: 0.2rem;
}

.user-email {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-divider {
  height: 1px;
  background: var(--color-border);
  margin: 0.25rem 0;
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 1rem;
  background: none;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.1s;
  font-family: inherit;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.dropdown-item:hover {
  background: var(--color-bg-elevated);
  color: var(--color-text-primary);
}

.dropdown-item svg {
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.dropdown-item.logout {
  color: var(--color-danger);
}

.dropdown-item.logout svg {
  color: var(--color-danger);
}

.dropdown-item.logout:hover {
  background: rgba(248, 81, 73, 0.08);
}

.task-badge {
  margin-left: auto;
  background: var(--color-accent);
  color: #0d1117;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  min-width: 18px;
  text-align: center;
}
</style>
