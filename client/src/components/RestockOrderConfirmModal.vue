<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="emit('close')">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ t('restocking.confirmTitle') }}</h3>
            <button class="close-button" @click="emit('close')">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <p class="confirm-copy">{{ t('restocking.confirmCopy') }}</p>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">{{ t('restocking.table.lineTotal') }}</div>
                <div class="info-value info-value--prominent">{{ formatCurrency(total, currentCurrency) }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">{{ t('restocking.budget') }}</div>
                <div class="info-value">{{ formatCurrency(budget, currentCurrency) }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">{{ t('orders.leadTime') }}</div>
                <div class="info-value">{{ t('orders.leadTimeDays', { days: maxLeadTimeDays }) }}</div>
              </div>
            </div>

            <div class="items-recap">
              <div
                v-for="item in items"
                :key="item.sku"
                class="recap-row"
              >
                <span class="recap-sku">{{ item.sku }}</span>
                <span class="recap-name">{{ translateProductName(item.name) }}</span>
                <span class="recap-qty">x{{ item.quantity }}</span>
                <span class="recap-total">{{ formatCurrency(item.line_total, currentCurrency) }}</span>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="emit('close')" :disabled="placing">
              {{ t('restocking.cancel') }}
            </button>
            <button
              class="btn-primary"
              @click="emit('confirm')"
              :disabled="placing"
            >
              {{ placing ? t('restocking.placing') : t('restocking.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const { t, currentCurrency, translateProductName } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  items: {
    type: Array,
    default: () => []
  },
  total: {
    type: Number,
    default: 0
  },
  budget: {
    type: Number,
    default: 0
  },
  maxLeadTimeDays: {
    type: Number,
    default: 0
  },
  placing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'confirm'])
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 560px;
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
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.confirm-copy {
  font-size: 0.938rem;
  color: #475569;
  line-height: 1.6;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.info-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value--prominent {
  font-size: 1.125rem;
  font-weight: 700;
  color: #1e40af;
}

.items-recap {
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.recap-row {
  display: grid;
  grid-template-columns: 90px 1fr 48px 90px;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.875rem;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.875rem;
}

.recap-row:last-child {
  border-bottom: none;
}

.recap-row:nth-child(odd) {
  background: #f8fafc;
}

.recap-sku {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 600;
}

.recap-name {
  color: #0f172a;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recap-qty {
  color: #64748b;
  font-weight: 600;
  text-align: right;
}

.recap-total {
  color: #0f172a;
  font-weight: 600;
  text-align: right;
}

.modal-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #1e40af;
  border: 1px solid #1e3a8a;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
  min-width: 140px;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1e40af;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transition animations — mirrors ProductDetailModal.vue */
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
