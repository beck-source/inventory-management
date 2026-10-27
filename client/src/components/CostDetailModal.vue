<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && costData" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ costData.month }} Cost Breakdown</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="cost-summary">
              <div class="summary-card total">
                <div class="summary-label">Total Costs</div>
                <div class="summary-value">{{ currencySymbol }}{{ totalCosts.toLocaleString() }}</div>
              </div>
            </div>

            <div class="cost-breakdown">
              <div class="cost-item procurement">
                <div class="cost-header">
                  <div class="cost-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <rect x="4" y="6" width="16" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                      <path d="M8 6V4M16 6V4M4 10H20" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="cost-info">
                    <div class="cost-name">Procurement</div>
                    <div class="cost-amount">{{ currencySymbol }}{{ costData.procurement.toLocaleString() }}</div>
                  </div>
                </div>
                <div class="cost-percentage">{{ getProcurementPercentage() }}% of total</div>
              </div>

              <div class="cost-item operational">
                <div class="cost-header">
                  <div class="cost-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="2"/>
                      <path d="M12 8V12L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="cost-info">
                    <div class="cost-name">Operational</div>
                    <div class="cost-amount">{{ currencySymbol }}{{ costData.operational.toLocaleString() }}</div>
                  </div>
                </div>
                <div class="cost-percentage">{{ getOperationalPercentage() }}% of total</div>
              </div>

              <div class="cost-item labor">
                <div class="cost-header">
                  <div class="cost-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="2"/>
                      <path d="M6 20C6 16.6863 8.68629 14 12 14C15.3137 14 18 16.6863 18 20" stroke="currentColor" stroke-width="2"/>
                    </svg>
                  </div>
                  <div class="cost-info">
                    <div class="cost-name">Labor</div>
                    <div class="cost-amount">{{ currencySymbol }}{{ costData.labor.toLocaleString() }}</div>
                  </div>
                </div>
                <div class="cost-percentage">{{ getLaborPercentage() }}% of total</div>
              </div>

              <div class="cost-item overhead">
                <div class="cost-header">
                  <div class="cost-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M3 12L5 10M5 10L12 3L19 10M5 10V20C5 20.5523 5.44772 21 6 21H9M19 10L21 12M19 10V20C19 20.5523 18.5523 21 18 21H15M9 21C9 21 9 18 9 16C9 14 10 14 12 14C14 14 15 14 15 16C15 18 15 21 15 21M9 21H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="cost-info">
                    <div class="cost-name">Overhead</div>
                    <div class="cost-amount">{{ currencySymbol }}{{ costData.overhead.toLocaleString() }}</div>
                  </div>
                </div>
                <div class="cost-percentage">{{ getOverheadPercentage() }}% of total</div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">Close</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'

const { currentCurrency } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  costData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const totalCosts = computed(() => {
  if (!props.costData) return 0
  return props.costData.procurement + props.costData.operational +
         props.costData.labor + props.costData.overhead
})

const getProcurementPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.procurement / totalCosts.value) * 100).toFixed(1)
}

const getOperationalPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.operational / totalCosts.value) * 100).toFixed(1)
}

const getLaborPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.labor / totalCosts.value) * 100).toFixed(1)
}

const getOverheadPercentage = () => {
  if (!props.costData || totalCosts.value === 0) return 0
  return ((props.costData.overhead / totalCosts.value) * 100).toFixed(1)
}

const close = () => {
  emit('close')
}
</script>

<style scoped>
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

.modal-container {
  background: var(--color-surface);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-md);
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
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--text-lg);
  font-weight: var(--weight-bold);
  color: var(--color-heading);
  letter-spacing: -0.025em;
}

/* Shared icon-button treatment: control-sized square with a visible focus ring */
.close-button {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  width: var(--control-height);
  height: var(--control-height);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-control);
  transition: background-color 0.15s ease, color 0.15s ease;
}

.close-button:hover {
  background: var(--color-hover);
  color: var(--color-heading);
}

.close-button:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.cost-summary {
  margin-bottom: var(--space-6);
}

.summary-card {
  padding: var(--space-6);
  border-radius: var(--radius-card);
  text-align: center;
}

.summary-card.total {
  background: var(--color-accent);
  color: var(--color-surface);
}

.summary-label {
  font-size: var(--text-base);
  font-weight: var(--weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.9;
  margin-bottom: var(--space-2);
}

.summary-value {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
}

.cost-breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.cost-item {
  padding: var(--space-5);
  border-radius: var(--radius-card);
  border: 1px solid;
}

.cost-item.procurement {
  border-color: var(--color-info-tint);
  background: var(--color-accent-tint);
}

.cost-item.operational {
  border-color: var(--color-border-strong);
  background: var(--color-bg);
}

.cost-item.labor {
  border-color: var(--color-success-tint);
  background: var(--color-bg);
}

.cost-item.overhead {
  border-color: var(--color-warning-tint);
  background: var(--color-bg);
}

.cost-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-2);
}

.cost-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-card);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.cost-item.procurement .cost-icon {
  background: var(--color-info);
  color: var(--color-surface);
}

.cost-item.operational .cost-icon {
  background: var(--color-text-muted);
  color: var(--color-surface);
}

.cost-item.labor .cost-icon {
  background: var(--color-success);
  color: var(--color-surface);
}

.cost-item.overhead .cost-icon {
  background: var(--color-warning);
  color: var(--color-surface);
}

.cost-info {
  flex: 1;
}

.cost-name {
  font-weight: var(--weight-semibold);
  color: var(--color-heading);
  font-size: var(--text-md);
  margin-bottom: var(--space-1);
}

.cost-amount {
  font-size: var(--text-xl);
  font-weight: var(--weight-bold);
  color: var(--color-heading);
}

.cost-percentage {
  font-size: var(--text-base);
  color: var(--color-text-muted);
  font-weight: var(--weight-medium);
}

.modal-footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}

.btn-secondary {
  height: var(--control-height);
  padding: 0 var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-control);
  font-weight: var(--weight-medium);
  font-size: var(--text-base);
  color: var(--color-text);
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--color-hover);
}

.btn-secondary:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

/* Modal transition animations */
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
