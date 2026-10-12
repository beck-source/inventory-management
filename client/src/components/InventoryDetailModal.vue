<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && inventoryItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">Inventory Item Details</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-header">
              <div class="item-icon" :class="getStockIconClass()">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5"/>
                  <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                  <path d="M16 28H32M16 34H24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="item-title-section">
                <h4 class="item-name">{{ translateProductName(inventoryItem.name) }}</h4>
                <div class="item-sku">SKU: {{ inventoryItem.sku }}</div>
              </div>
              <span class="stock-badge" :class="getStockStatusClass()">
                {{ getStockStatus() }}
              </span>
            </div>

            <div class="stock-summary">
              <div class="summary-card primary">
                <div class="summary-label">Quantity on Hand</div>
                <div class="summary-value">{{ inventoryItem.quantity_on_hand }} units</div>
              </div>
              <div class="summary-card" :class="getSummaryCardClass()">
                <div class="summary-label">Stock Level</div>
                <div class="summary-value">{{ stockPercentage }}%</div>
                <div class="summary-subtitle">vs. reorder point</div>
              </div>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">Category</div>
                <div class="info-value">{{ inventoryItem.category }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Location</div>
                <div class="info-value">{{ inventoryItem.location }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Reorder Point</div>
                <div class="info-value">{{ inventoryItem.reorder_point }} units</div>
              </div>

              <div class="info-item">
                <div class="info-label">Units Remaining</div>
                <div class="info-value">
                  <span :style="{ color: inventoryItem.quantity_on_hand <= inventoryItem.reorder_point ? 'var(--uui-error)' : 'var(--uui-success)' }">
                    {{ inventoryItem.quantity_on_hand - inventoryItem.reorder_point }} units
                  </span>
                </div>
              </div>

              <div class="info-item">
                <div class="info-label">Unit Cost</div>
                <div class="info-value">{{ currencySymbol }}{{ inventoryItem.unit_cost.toFixed(2) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Total Value</div>
                <div class="info-value total-value">
                  {{ currencySymbol }}{{ totalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}
                </div>
              </div>

              <div class="info-item">
                <div class="info-label">Warehouse</div>
                <div class="info-value">{{ translateWarehouse(inventoryItem.location) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value">
                  <span :class="['badge', getStockStatusClass()]">
                    {{ getStockStatus() }}
                  </span>
                </div>
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

const { currentCurrency, translateProductName, translateWarehouse } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  inventoryItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const totalValue = computed(() => {
  if (!props.inventoryItem) return 0
  return props.inventoryItem.quantity_on_hand * props.inventoryItem.unit_cost
})

const stockPercentage = computed(() => {
  if (!props.inventoryItem || props.inventoryItem.reorder_point === 0) return 0
  return Math.round((props.inventoryItem.quantity_on_hand / props.inventoryItem.reorder_point) * 100)
})

const close = () => {
  emit('close')
}

const getStockStatus = () => {
  if (!props.inventoryItem) return 'Unknown'
  if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point) {
    return 'Low Stock'
  } else if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point * 1.5) {
    return 'Adequate'
  } else {
    return 'In Stock'
  }
}

const getStockStatusClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger'
  if (status === 'Adequate') return 'warning'
  return 'success'
}

const getStockIconClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger-icon'
  if (status === 'Adequate') return 'warning-icon'
  return 'success-icon'
}

const getSummaryCardClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger-card'
  if (status === 'Adequate') return 'warning-card'
  return 'success-card'
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
  max-width: 700px;
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

.item-header {
  display: flex;
  align-items: center;
  gap: var(--uui-space-18);
  padding-bottom: var(--uui-space-18);
  border-bottom: 1px solid var(--uui-divider);
  margin-bottom: var(--uui-space-18);
}

.item-icon {
  width: 60px;
  height: 60px;
  border-radius: var(--uui-radius-12);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--uui-white);
  flex-shrink: 0;
}

.item-icon.success-icon {
  background: var(--uui-green-60);
}

.item-icon.warning-icon {
  background: var(--uui-amber-60);
}

.item-icon.danger-icon {
  background: var(--uui-fire-60);
}

.item-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: var(--uui-h3-size);
  font-weight: var(--uui-fw-bold);
  color: var(--uui-text-primary);
  margin: 0 0 var(--uui-space-6) 0;
}

.item-sku {
  font-size: var(--uui-text-s-size);
  color: var(--uui-text-secondary);
  font-family: var(--uui-font-mono);
}

.stock-badge {
  height: var(--uui-size-30);
  padding: 0 var(--uui-space-12);
  display: inline-flex;
  align-items: center;
  border-radius: var(--uui-radius-6);
  font-size: var(--uui-text-xs-size);
  font-weight: var(--uui-fw-semibold);
  text-transform: uppercase;
  letter-spacing: var(--uui-overline-tracking);
  flex-shrink: 0;
}

.stock-badge.success {
  background: var(--uui-success-subtle);
  color: var(--uui-green-70);
}

.stock-badge.warning {
  background: var(--uui-warning-subtle);
  color: var(--uui-amber-70);
}

.stock-badge.danger {
  background: var(--uui-error-subtle);
  color: var(--uui-fire-70);
}

.stock-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--uui-space-12);
  margin-bottom: var(--uui-space-24);
}

.summary-card {
  padding: var(--uui-space-18);
  border-radius: var(--uui-radius-12);
  border: 1px solid;
}

.summary-card.primary {
  border-color: var(--uui-blue-20);
  background: var(--uui-primary-subtle);
}

.summary-card.success-card {
  border-color: var(--uui-green-30);
  background: var(--uui-success-subtle);
}

.summary-card.warning-card {
  border-color: var(--uui-amber-30);
  background: var(--uui-warning-subtle);
}

.summary-card.danger-card {
  border-color: var(--uui-fire-30);
  background: var(--uui-error-subtle);
}

.summary-label {
  font-size: var(--uui-overline-size);
  font-weight: var(--uui-fw-semibold);
  text-transform: uppercase;
  letter-spacing: var(--uui-overline-tracking);
  color: var(--uui-text-secondary);
  margin-bottom: var(--uui-space-6);
}

.summary-value {
  font-size: 30px;
  font-weight: var(--uui-fw-bold);
  color: var(--uui-text-primary);
  line-height: 1;
}

.summary-subtitle {
  font-size: var(--uui-text-xs-size);
  color: var(--uui-text-secondary);
  margin-top: var(--uui-space-3);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--uui-space-18);
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

.info-value.total-value {
  font-size: var(--uui-h4-size);
  color: var(--uui-primary);
  font-weight: var(--uui-fw-bold);
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
