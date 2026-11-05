<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">Inventory Shortage Details</h3>
            <button class="btn btn-icon btn-ghost close-button" @click="close">
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
              <span class="badge priority-badge" :class="backlogItem.priority">
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
            <button class="btn btn-secondary" @click="close">Close</button>
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
/* Overlay, header, body and footer chrome come from theme.css (.modal-*). */
.modal-overlay {
  z-index: 2000;
}

.modal-container {
  width: min(700px, 100%);
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.close-button {
  flex-shrink: 0;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-8);
  gap: var(--space-6);
}

.shortage-header {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-5);
  padding-bottom: var(--space-6);
  border-bottom: 1px solid var(--line);
}

.shortage-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-md);
  border: 1px solid currentColor;
  color: var(--danger);
  background: var(--danger-bg);
  box-shadow: 0 0 18px var(--danger-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.shortage-title-section {
  flex: 1 1 180px;
  min-width: 0;
}

.item-name {
  font-size: var(--fs-xl);
  font-weight: 700;
  color: var(--text);
  margin: 0 0 var(--space-2) 0;
  overflow-wrap: anywhere;
}

.item-sku {
  font-size: var(--fs-sm);
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.priority-badge {
  flex-shrink: 0;
}

/* Low priority was blue in the light theme; keep it informational. */
.priority-badge.low {
  color: var(--info);
  background: var(--info-bg);
}

.shortage-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
}

.summary-card {
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid var(--line);
  background: var(--surface-sunken);
}

.summary-card.danger {
  border-color: var(--danger);
  background: var(--danger-bg);
}

.summary-card.warning {
  border-color: var(--warning);
  background: var(--warning-bg);
}

.summary-label,
.info-label {
  font-family: var(--font-mono);
  font-size: var(--fs-xs);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--text-faint);
}

.summary-label {
  margin-bottom: var(--space-2);
}

.summary-value {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
  font-size: var(--fs-2xl);
  font-weight: 700;
  color: var(--text);
}

.summary-card.danger .summary-value {
  color: var(--danger);
}

.summary-card.warning .summary-value {
  color: var(--warning);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-4);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--surface-sunken);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
}

.info-value {
  font-size: var(--fs-md);
  color: var(--text);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.info-value.order-id,
.info-value.sku {
  font-family: var(--font-mono);
  font-size: var(--fs-md);
  color: var(--cyan);
}

@media (max-width: 520px) {
  .modal-body {
    padding: var(--space-5);
  }
}

/* Modal transition animations (disabled by theme.css under reduced motion) */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--t-fast) var(--ease);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--t-fast) var(--ease);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
