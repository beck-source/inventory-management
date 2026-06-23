<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order Details' }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Item context header -->
            <div class="item-context">
              <div class="item-context-info">
                <div class="item-context-name">{{ backlogItem.item_name }}</div>
                <div class="item-context-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} Priority
              </span>
            </div>

            <!-- CREATE MODE -->
            <template v-if="mode === 'create'">
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label" for="po-supplier">Supplier Name</label>
                  <input
                    id="po-supplier"
                    v-model="form.supplier"
                    type="text"
                    class="form-input"
                    placeholder="Enter supplier name"
                  />
                </div>

                <div class="form-group">
                  <label class="form-label" for="po-quantity">Quantity to Order</label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    class="form-input"
                    min="1"
                  />
                  <div class="form-hint">Shortage: {{ shortage }} units</div>
                </div>

                <div class="form-group">
                  <label class="form-label" for="po-delivery">Expected Delivery Date</label>
                  <input
                    id="po-delivery"
                    v-model="form.delivery_date"
                    type="date"
                    class="form-input"
                  />
                </div>

                <div class="form-group">
                  <label class="form-label" for="po-priority">Priority</label>
                  <select id="po-priority" v-model="form.priority" class="form-select">
                    <option value="urgent">Urgent</option>
                    <option value="standard">Standard</option>
                    <option value="low">Low</option>
                  </select>
                </div>
              </div>
            </template>

            <!-- VIEW MODE -->
            <template v-else-if="mode === 'view'">
              <template v-if="backlogItem.purchase_order">
                <div class="po-details-grid">
                  <div class="po-detail-item">
                    <div class="po-detail-label">PO ID</div>
                    <div class="po-detail-value po-id">{{ backlogItem.purchase_order.id }}</div>
                  </div>
                  <div class="po-detail-item">
                    <div class="po-detail-label">Supplier</div>
                    <div class="po-detail-value">{{ backlogItem.purchase_order.supplier }}</div>
                  </div>
                  <div class="po-detail-item">
                    <div class="po-detail-label">Quantity Ordered</div>
                    <div class="po-detail-value">{{ backlogItem.purchase_order.quantity }} units</div>
                  </div>
                  <div class="po-detail-item">
                    <div class="po-detail-label">Expected Delivery</div>
                    <div class="po-detail-value">{{ formatDate(backlogItem.purchase_order.delivery_date) }}</div>
                  </div>
                  <div class="po-detail-item">
                    <div class="po-detail-label">Priority</div>
                    <div class="po-detail-value">
                      <span class="priority-badge" :class="backlogItem.purchase_order.priority">
                        {{ backlogItem.purchase_order.priority }}
                      </span>
                    </div>
                  </div>
                  <div class="po-detail-item">
                    <div class="po-detail-label">Status</div>
                    <div class="po-detail-value">
                      <span class="status-badge">{{ backlogItem.purchase_order.status }}</span>
                    </div>
                  </div>
                  <div class="po-detail-item">
                    <div class="po-detail-label">Created At</div>
                    <div class="po-detail-value">{{ formatDate(backlogItem.purchase_order.created_at) }}</div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="empty-state">
                  <div class="empty-state-icon">
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                      <rect x="8" y="6" width="24" height="28" rx="3" stroke="#94a3b8" stroke-width="2"/>
                      <path d="M14 14h12M14 20h8M14 26h6" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </div>
                  <div class="empty-state-text">No purchase order created yet</div>
                  <div class="empty-state-hint">Use "Create PO" from the backlog to generate a purchase order for this item.</div>
                </div>
              </template>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">Close</button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="!isFormValid"
              @click="submitPO"
            >
              Create Purchase Order
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create',
    validator: (val) => ['create', 'view'].includes(val)
  }
})

const emit = defineEmits(['close', 'po-created'])

// Shortage amount = quantity needed minus what is available
const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
})

// Form state with defaults
const form = ref({
  supplier: '',
  quantity: 0,
  delivery_date: '',
  priority: 'standard'
})

// Reset form when modal opens or backlog item changes
watch(
  () => [props.isOpen, props.backlogItem],
  ([isOpen]) => {
    if (isOpen && props.backlogItem) {
      form.value = {
        supplier: '',
        quantity: shortage.value,
        delivery_date: '',
        priority: props.backlogItem.priority === 'high' ? 'urgent' : (props.backlogItem.priority || 'standard')
      }
    }
  },
  { immediate: true }
)

const isFormValid = computed(() => {
  return (
    form.value.supplier.trim().length > 0 &&
    form.value.quantity > 0 &&
    form.value.delivery_date.length > 0
  )
})

const close = () => {
  emit('close')
}

const submitPO = () => {
  if (!isFormValid.value || !props.backlogItem) return

  const poData = {
    id: 'PO-' + Date.now(),
    backlog_item_id: props.backlogItem.id,
    supplier: form.value.supplier.trim(),
    quantity: form.value.quantity,
    delivery_date: form.value.delivery_date,
    priority: form.value.priority,
    status: 'pending',
    created_at: new Date().toISOString()
  }

  emit('po-created', poData)
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
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
  padding: 2rem;
}

/* Item context row at top of body */
.item-context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.item-context-name {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.25rem;
}

.item-context-sku {
  font-size: 0.813rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.priority-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.priority-badge.high,
.priority-badge.urgent {
  background: #fecaca;
  color: #991b1b;
}

.priority-badge.medium,
.priority-badge.standard {
  background: #fed7aa;
  color: #92400e;
}

.priority-badge.low {
  background: #dbeafe;
  color: #1e40af;
}

/* Create mode form */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

/* Supplier field spans full width */
.form-group:first-child {
  grid-column: 1 / -1;
}

.form-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.form-input,
.form-select {
  padding: 0.625rem 0.875rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  background: white;
  font-family: inherit;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  outline: none;
}

.form-input:focus,
.form-select:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-hint {
  font-size: 0.813rem;
  color: #64748b;
}

/* View mode PO details */
.po-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.5rem;
}

.po-detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.po-detail-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.po-detail-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.po-detail-value.po-id {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 4px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

/* Empty state for view mode with no PO */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.5rem;
  text-align: center;
  gap: 1rem;
}

.empty-state-icon {
  width: 64px;
  height: 64px;
  background: #f1f5f9;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state-text {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
}

.empty-state-hint {
  font-size: 0.875rem;
  color: #64748b;
  max-width: 320px;
}

.modal-footer {
  padding: 1.5rem;
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

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
