<template>
  <div class="profile-menu">
    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <button class="profile-button">
          <div class="avatar">
            {{ getInitials(currentUser.name) }}
          </div>
          <span class="profile-name">{{ currentUser.name }}</span>
          <svg
            class="chevron"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
          >
            <path d="M4 6L8 10L12 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        side="top"
        align="start"
        :side-offset="8"
        class="w-(--reka-dropdown-menu-trigger-width) overflow-hidden rounded-[10px] border-[var(--line)] bg-[var(--surface-card)] p-0 shadow-[0_8px_24px_rgba(15,23,42,0.08)]"
      >
        <div class="dropdown-header">
          <div class="avatar-large">
            {{ getInitials(currentUser.name) }}
          </div>
          <div class="user-info">
            <div class="user-name">{{ currentUser.name }}</div>
            <div class="user-email">{{ currentUser.email }}</div>
          </div>
        </div>

        <DropdownMenuSeparator class="m-0 bg-[var(--line)]" />

        <DropdownMenuItem :class="itemClass" @select="showProfileDetails">
          <svg width="16" height="16" viewBox="0 0 18 18" fill="none">
            <path d="M9 9C10.6569 9 12 7.65685 12 6C12 4.34315 10.6569 3 9 3C7.34315 3 6 4.34315 6 6C6 7.65685 7.34315 9 9 9Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M15 15C15 12.7909 12.3137 11 9 11C5.68629 11 3 12.7909 3 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          {{ t('profile.profileDetails') }}
        </DropdownMenuItem>

        <DropdownMenuItem :class="itemClass" @select="showTasks">
          <svg width="16" height="16" viewBox="0 0 18 18" fill="none">
            <path d="M15 3H3C2.44772 3 2 3.44772 2 4V14C2 14.5523 2.44772 15 3 15H15C15.5523 15 16 14.5523 16 14V4C16 3.44772 15.5523 3 15 3Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M6 7L8 9L12 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          {{ t('profile.myTasks') }}
          <span v-if="pendingTaskCount > 0" class="task-badge">{{ pendingTaskCount }}</span>
        </DropdownMenuItem>

        <DropdownMenuSeparator class="m-0 bg-[var(--line)]" />

        <DropdownMenuItem
          variant="destructive"
          :class="itemClass"
          @select="handleLogout"
        >
          <svg width="16" height="16" viewBox="0 0 18 18" fill="none">
            <path d="M7 15H4C3.44772 15 3 14.5523 3 14V4C3 3.44772 3.44772 3 4 3H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M11 12L15 9M15 9L11 6M15 9H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          {{ t('profile.logout') }}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

const { currentUser, logout, getInitials } = useAuth()
const { t } = useI18n()

const emit = defineEmits(['show-profile-details', 'show-tasks'])

// Menu content is teleported to <body>, so scoped CSS can't reach it; item styling uses utilities.
const itemClass = 'gap-3 rounded-none px-4 py-2.5 text-[13px] font-medium text-[var(--ink-secondary)] focus:bg-[var(--surface-muted)] focus:text-[var(--ink-secondary)] data-[variant=destructive]:text-[var(--danger)] data-[variant=destructive]:focus:bg-[rgba(239,68,68,0.06)] data-[variant=destructive]:focus:text-[var(--danger)]'

const pendingTaskCount = computed(() => {
  return currentUser.value.tasks.filter(task => task.status === 'pending').length
})

// reka-ui closes the menu on select, so no manual open-state handling is needed.
const showProfileDetails = () => {
  emit('show-profile-details')
}

const showTasks = () => {
  emit('show-tasks')
}

const handleLogout = () => {
  logout()
}
</script>

<style scoped>
.profile-menu {
  margin-top: var(--sp-2);
}

.profile-button {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-3);
  background: transparent;
  border: none;
  border-radius: var(--r-sm);
  cursor: pointer;
  transition: background 0.15s ease;
  font-family: inherit;
  width: 100%;
  text-align: left;
}

.profile-button:hover {
  background: rgba(255, 255, 255, 0.06);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--ink-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
  flex-shrink: 0;
}

.profile-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--surface-bg);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  color: var(--ink-muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.profile-button[data-state='open'] .chevron {
  transform: rotate(180deg);
}

.dropdown-header {
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  align-items: center;
  background: var(--surface-muted);
}

.avatar-large {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--ink-inverse);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--ink-primary);
  font-size: 13px;
  margin-bottom: 4px;
}

.user-email {
  font-size: 11px;
  color: var(--ink-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-badge {
  margin-left: auto;
  background: var(--accent);
  color: var(--ink-inverse);
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 999px;
  min-width: 20px;
  text-align: center;
}
</style>
