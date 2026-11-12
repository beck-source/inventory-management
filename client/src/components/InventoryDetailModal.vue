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
                  <span :style="{ color: inventoryItem.quantity_on_hand <= inventoryItem.reorder_point ? '#ef4444' : '#10b981' }">
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
  width: min(700px, 100%);
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

.item-header {
  display: flex;
  /* On phones the status badge wraps under the title instead of squeezing it. */
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-6);
}

.item-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-surface);
  flex-shrink: 0;
}

.item-icon.success-icon {
  background: var(--color-success);
}

.item-icon.warning-icon {
  background: var(--color-warning);
}

.item-icon.danger-icon {
  background: var(--color-danger);
}

/* The basis (not flex: 1 alone) is what makes the badge wrap on narrow screens. */
.item-title-section {
  flex: 1 1 180px;
  min-width: 0;
}

.item-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 var(--space-2) 0;
  overflow-wrap: anywhere;
}

.item-sku {
  font-size: 0.875rem;
  color: var(--color-muted);
  font-family: 'Monaco', 'Courier New', monospace;
}

.stock-badge {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

/* Status tints: the text colours have no token, so they stay literal. */
.stock-badge.success {
  background: var(--color-success-soft);
  color: #065f46;
}

.stock-badge.warning {
  background: var(--color-warning-soft);
  color: #92400e;
}

.stock-badge.danger {
  background: var(--color-danger-soft);
  color: #991b1b;
}

.stock-summary {
  display: grid;
  /* auto-fit wraps the two cards on narrow screens so the large numbers never overflow. */
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.summary-card {
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid;
}

/* Card tints without a token (#bfdbfe, #a7f3d0, #fef2f2, #fffbeb) stay literal. */
.summary-card.primary {
  border-color: #bfdbfe;
  background: var(--color-primary-soft);
}

.summary-card.success-card {
  border-color: #a7f3d0;
  background: var(--color-success-soft);
}

.summary-card.warning-card {
  border-color: var(--color-warning-soft);
  background: #fffbeb;
}

.summary-card.danger-card {
  border-color: var(--color-danger-soft);
  background: #fef2f2;
}

.summary-label {
  font-size: 0.8125rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-muted);
  margin-bottom: var(--space-2);
}

.summary-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--color-text);
}

.summary-subtitle {
  font-size: 0.75rem;
  color: var(--color-muted);
  margin-top: var(--space-1);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

.info-value.total-value {
  font-size: 1.125rem;
  color: var(--color-primary);
  font-weight: 700;
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
