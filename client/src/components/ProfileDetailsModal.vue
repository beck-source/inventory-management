<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ t('profileDetails.title') }}</h3>
            <Button variant="ghost" size="sm" @click="close">
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </Button>
          </div>

          <div class="modal-body">
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

          <div class="modal-footer">
            <Button variant="ghost" @click="close">{{ t('profileDetails.close') }}</Button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'
import Button from './ui/Button.vue'

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
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 16px;
}

.modal-container {
  background: var(--surface-card);
  border-radius: var(--r-lg);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  max-width: 90vw;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid var(--line);
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink-primary);
  margin: 0;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

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

.modal-footer {
  padding: 24px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
