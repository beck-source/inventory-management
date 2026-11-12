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
/* Overlay: position, inset and z-index keep the modal above the sidebar (100)
   and topbar (90). The dim colour matches the mobile drawer backdrop in App.vue. */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

/* Panel. The overlay padding is the gutter, so 100% already fits a 390px screen;
   the min() keeps the desktop cap. */
.modal-container {
  width: min(600px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  /* Deeper than --shadow-md on purpose: the panel floats over the dimmed page. */
  box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-shrink: 0;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.close-button:hover {
  background: var(--color-subtle);
  color: var(--color-text);
}

.close-button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.modal-body {
  flex: 1;
  /* min-height: 0 lets the body shrink inside the max-height panel, so it
     scrolls and the header and footer stay in view. */
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-6);
}

.profile-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

/* Flat fill (no gradient or glow) to match the other avatars in the app. */
.avatar-xl {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: var(--color-primary);
  color: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 700;
  font-size: 2rem;
  letter-spacing: 0.025em;
}

.profile-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0;
}

.profile-job-title {
  font-size: 1rem;
  color: var(--color-muted);
  margin: 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-6);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-label {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-muted);
}

.info-value {
  font-size: 0.9375rem;
  color: var(--color-text);
  font-weight: 500;
}

.modal-footer {
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-5) var(--space-6);
  border-top: 1px solid var(--color-border);
}

/* Secondary button: bordered surface, so it reads as an action without competing with primary. */
.btn-secondary {
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-soft);
  cursor: pointer;
  transition: background-color var(--transition-fast), border-color var(--transition-fast);
}

.btn-secondary:hover {
  background: var(--color-bg);
  border-color: var(--color-border-strong);
}

.btn-secondary:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-fast);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--transition-fast);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
