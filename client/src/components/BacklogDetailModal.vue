<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">Inventory Shortage Details</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="shortage-header">
              <div class="shortage-icon">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <path d="M24 8L24 28M24 34L24 36" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                  <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="3"/>
                </svg>
              </div>
              <div class="shortage-title-section">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} Priority
              </span>
            </div>

            <div class="shortage-summary">
              <div class="summary-card danger">
                <div class="summary-label">Shortage Amount</div>
                <div class="summary-value">{{ shortage }} units</div>
              </div>
              <div class="summary-card warning">
                <div class="summary-label">Days Delayed</div>
                <div class="summary-value">{{ backlogItem.days_delayed }} days</div>
              </div>
            </div>

            <div class="info-grid">
              <div class="info-item">
                <div class="info-label">Order ID</div>
                <div class="info-value order-id">{{ backlogItem.order_id }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Item SKU</div>
                <div class="info-value sku">{{ backlogItem.item_sku }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Quantity Needed</div>
                <div class="info-value">{{ backlogItem.quantity_needed }} units</div>
              </div>

              <div class="info-item">
                <div class="info-label">Quantity Available</div>
                <div class="info-value">{{ backlogItem.quantity_available }} units</div>
              </div>

              <div class="info-item">
                <div class="info-label">Expected Date</div>
                <div class="info-value">{{ formatDate(backlogItem.expected_date) }}</div>
              </div>

              <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value">
                  <span class="badge danger">Backordered</span>
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

const { translateProductName } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
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
   the min() keeps the desktop cap. 100vw is avoided because it includes the
   scrollbar on desktop. */
.modal-container {
  width: min(700px, 100%);
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  /* Deeper than --shadow-md on purpose: the panel floats over the dimmed page,
     so it needs more lift than an in-page card to read as a separate layer. */
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

.shortage-header {
  display: flex;
  /* On phones the priority badge wraps under the title instead of squeezing it. */
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-6);
}

.shortage-icon {
  width: 64px;
  height: 64px;
  background: var(--color-danger);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-surface);
  flex-shrink: 0;
}

/* The basis (not flex: 1 alone) is what makes the badge wrap on narrow screens. */
.shortage-title-section {
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

.priority-badge {
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.priority-badge.high {
  background: var(--color-danger-soft);
  color: #991b1b;
}

.priority-badge.medium {
  background: var(--color-warning-soft);
  color: #92400e;
}

/* No matching token for the light blue tint, so the value stays. */
.priority-badge.low {
  background: #dbeafe;
  color: #1e40af;
}

.shortage-summary {
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

/* The card tints (#fef2f2, #fffbeb) have no token, so they stay as literal values. */
.summary-card.danger {
  border-color: var(--color-danger-soft);
  background: #fef2f2;
}

.summary-card.warning {
  border-color: var(--color-warning-soft);
  background: #fffbeb;
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

.summary-card.danger .summary-value {
  color: var(--color-danger);
}

/* Uses --color-warning (darker orange) rather than amber, for readable contrast on the pale card. */
.summary-card.warning .summary-value {
  color: var(--color-warning);
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

.info-value.order-id,
.info-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: var(--color-primary);
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
