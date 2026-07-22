<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="wc-overlay" @click.self="$emit('close')">
        <div class="wc-modal" role="dialog" aria-modal="true" aria-labelledby="wc-title">

          <div class="wc-header">
            <div class="wc-header-icon">
              <!-- Gavel / legal SVG -->
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14.5 2.5l7 7-3.5 3.5-7-7 3.5-3.5z"/>
                <path d="M2.5 21.5l7-7"/>
                <path d="M10 14l-1.5-1.5"/>
              </svg>
            </div>
            <h2 class="wc-title" id="wc-title">Works Council Notification Required</h2>
            <button class="wc-close" @click="$emit('close')" aria-label="Close">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M14 4L4 14M4 4L14 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="wc-body">
            <!-- Submitted confirmation state -->
            <div v-if="submitted" class="wc-submitted">
              <div class="submitted-icon">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                  <polyline points="22 4 12 14.01 9 11.01"/>
                </svg>
              </div>
              <p class="submitted-text">
                Submitted to Works Council. Reference: <strong>WC-{{ referenceNumber }}</strong>.
                You will receive a response within 6 weeks as required by Directive 2009/38/EC.
              </p>
              <button class="btn-primary" @click="$emit('close')">Close</button>
            </div>

            <!-- Normal state -->
            <template v-else>
              <p class="wc-description">
                This action requires notification to the Works Council under §87 BetrVG and
                EU Works Council Directive 2009/38/EC. The following action has been flagged for review:
              </p>

              <div class="wc-action-box">
                "{{ actionDescription }}"
              </div>

              <p class="wc-consultation">
                Expected consultation period: <strong>up to 6 weeks</strong>
              </p>

              <div class="wc-actions">
                <button class="btn-primary" @click="submitForReview">
                  Submit for Works Council Review
                </button>
                <button class="btn-danger-outline" @click="handleOverrideClick">
                  Management Override (Audit Log Entry Created)
                </button>
              </div>

              <p class="wc-footnote">
                Non-compliance may result in action being deemed invalid under §23 BetrVG.
              </p>
            </template>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'WorksCouncilModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    actionDescription: {
      type: String,
      default: ''
    }
  },
  emits: ['close', 'approve', 'override'],
  setup(props, { emit }) {
    const submitted = ref(false)
    const referenceNumber = ref('')

    const submitForReview = () => {
      referenceNumber.value = String(Math.floor(1000 + Math.random() * 9000))
      submitted.value = true
      emit('approve')
    }

    const handleOverrideClick = () => {
      submitted.value = false
      emit('override')
    }

    // Reset state when modal closes
    const reset = () => {
      submitted.value = false
      referenceNumber.value = ''
    }

    return { submitted, referenceNumber, submitForReview, handleOverrideClick, reset }
  }
}
</script>

<style scoped>
.wc-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.wc-modal {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 540px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.wc-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  background: #fef9f0;
}

.wc-header-icon {
  width: 40px;
  height: 40px;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #92400e;
  flex-shrink: 0;
}

.wc-title {
  flex: 1;
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  line-height: 1.3;
}

.wc-close {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}

.wc-close:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.wc-body {
  padding: 1.5rem;
}

.wc-description {
  font-size: 0.9rem;
  color: #334155;
  line-height: 1.6;
  margin: 0 0 1.25rem 0;
}

.wc-action-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #f59e0b;
  border-radius: 6px;
  padding: 0.875rem 1.125rem;
  font-size: 0.9rem;
  color: #0f172a;
  font-style: italic;
  margin-bottom: 1.25rem;
  line-height: 1.5;
}

.wc-consultation {
  font-size: 0.875rem;
  color: #475569;
  margin-bottom: 1.5rem;
}

.wc-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
  width: 100%;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-danger-outline {
  background: transparent;
  color: #dc2626;
  border: 1px solid #dc2626;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  font-family: inherit;
  width: 100%;
}

.btn-danger-outline:hover {
  background: #fef2f2;
}

.wc-footnote {
  font-size: 0.75rem;
  color: #94a3b8;
  line-height: 1.5;
}

/* Submitted state */
.wc-submitted {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.25rem;
  padding: 1rem 0;
  text-align: center;
}

.submitted-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #d1fae5;
  border: 2px solid #6ee7b7;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #059669;
}

.submitted-text {
  font-size: 0.9rem;
  color: #334155;
  line-height: 1.6;
  max-width: 380px;
}

/* Modal transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
