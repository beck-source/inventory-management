<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ t('profileDetails.title') }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="profile-section">
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
                  <div class="info-value">CC-{{ currentUser.id.toString().padStart(5, '0') }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">{{ t('profileDetails.close') }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

const { currentUser, getInitials } = useAuth()
const { t, currentLocale } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
  return date.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: var(--uui-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--uui-z-modal);
  padding: var(--uui-space-24);
}

.modal-container {
  background: var(--uui-surface-main);
  border-radius: var(--uui-radius-12);
  box-shadow: var(--uui-shadow-400);
  max-width: 600px;
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
  padding: var(--uui-space-18) var(--uui-space-24);
  border-bottom: 1px solid var(--uui-divider);
}

.modal-title {
  font-size: var(--uui-h4-size);
  font-weight: var(--uui-fw-bold);
  color: var(--uui-text-primary);
}

.close-button {
  width: var(--uui-size-36);
  height: var(--uui-size-36);
  background: none;
  border: none;
  color: var(--uui-icon);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--uui-radius-6);
  transition: all 0.12s ease;
}

.close-button:hover {
  background: var(--uui-night-100);
  color: var(--uui-icon-active);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--uui-space-24);
}

.profile-section {
  display: flex;
  flex-direction: column;
  gap: var(--uui-space-24);
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--uui-space-12);
  padding-bottom: var(--uui-space-24);
  border-bottom: 1px solid var(--uui-divider);
}

.avatar-xl {
  width: 96px;
  height: 96px;
  border-radius: var(--uui-radius-full);
  background: var(--uui-primary);
  color: var(--uui-white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--uui-fw-bold);
  font-size: 2rem;
  box-shadow: var(--uui-shadow-200);
}

.profile-name {
  font-size: var(--uui-h3-size);
  font-weight: var(--uui-fw-bold);
  color: var(--uui-text-primary);
  margin: 0;
}

.profile-job-title {
  font-size: var(--uui-text-m-size);
  color: var(--uui-text-secondary);
  margin: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--uui-space-24);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--uui-space-6);
}

.info-label {
  font-size: var(--uui-overline-size);
  font-weight: var(--uui-fw-semibold);
  text-transform: uppercase;
  letter-spacing: var(--uui-overline-tracking);
  color: var(--uui-text-secondary);
}

.info-value {
  font-size: var(--uui-text-s-size);
  color: var(--uui-text-primary);
  font-weight: var(--uui-fw-semibold);
}

.modal-footer {
  padding: var(--uui-space-18) var(--uui-space-24);
  border-top: 1px solid var(--uui-divider);
  display: flex;
  justify-content: flex-end;
  gap: var(--uui-space-12);
}

.btn-secondary {
  height: var(--uui-size-36);
  padding: 0 var(--uui-space-18);
  background: var(--uui-night-100);
  border: 1px solid var(--uui-border);
  border-radius: var(--uui-radius-6);
  font-family: var(--uui-font);
  font-weight: var(--uui-fw-semibold);
  font-size: var(--uui-text-s-size);
  color: var(--uui-text-primary);
  cursor: pointer;
  transition: all 0.12s ease;
}

.btn-secondary:hover {
  background: var(--uui-night-200);
  border-color: var(--uui-border-strong);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.15s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.15s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.96);
}
</style>
