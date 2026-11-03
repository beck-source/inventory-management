<template>
  <!-- Dialog provides Escape-to-close, focus trap and scroll lock; the guard keeps the body from rendering with null data. -->
  <Dialog :open="isOpen" @update:open="(open) => { if (!open) close() }">
    <!-- p-0/gap-0 so header, body and footer own their padding; sm:max-w-[90vw] matches the old container width -->
    <DialogContent class="sm:max-w-[90vw] max-h-[90vh] p-0 gap-0 overflow-hidden flex flex-col">
      <DialogHeader class="p-6 border-b border-border">
        <DialogTitle class="text-base font-semibold text-[var(--ink-primary)]">{{ t('profileDetails.title') }}</DialogTitle>
        <DialogDescription class="sr-only">{{ t('profileDetails.title') }}</DialogDescription>
      </DialogHeader>

      <div class="flex-1 overflow-y-auto p-6">
        <div class="avatar-section">
          <div class="avatar-xl">
            {{ getInitials(currentUser.name) }}
          </div>
          <h4 class="profile-name">{{ currentUser.name }}</h4>
          <p class="profile-job-title">{{ currentUser.jobTitle }}</p>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.email') }}</div>
            <div class="info-value">{{ currentUser.email }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.department') }}</div>
            <div class="info-value">{{ currentUser.department }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.location') }}</div>
            <div class="info-value">{{ currentUser.location }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.phone') }}</div>
            <div class="info-value">{{ currentUser.phone }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.joinDate') }}</div>
            <div class="info-value">{{ formatDate(currentUser.joinDate) }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">{{ t('profileDetails.employeeId') }}</div>
            <div class="info-value mono">CC-{{ currentUser.id.toString().padStart(5, '0') }}</div>
          </div>
        </div>
      </div>

      <DialogFooter class="p-6 border-t border-border">
        <Button variant="ghost" @click="close">{{ t('profileDetails.close') }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<script setup>
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'

const { currentUser, getInitials } = useAuth()
const { t, currentLocale } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

const close = () => emit('close')

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
  return date.toLocaleDateString(locale, { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<style scoped>
.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 24px;
}

.avatar-xl {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 24px;
}

.profile-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--ink-primary);
  margin: 0;
}

.profile-job-title {
  font-size: 13px;
  color: var(--ink-muted);
  margin: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-muted);
}

.info-value {
  font-size: 13px;
  color: var(--ink-primary);
  font-weight: 500;
}

.info-value.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: var(--accent);
}
</style>
