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
            <!-- Item summary header -->
            <div class="item-header">
              <div class="item-info">
                <div class="item-name">{{ backlogItem.item_name }}</div>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} Priority
              </span>
            </div>

            <!-- CREATE MODE: Form -->
            <form v-if="mode === 'create'" @submit.prevent="submitForm" class="po-form">
              <div class="form-group">
                <label class="form-label" for="supplier-name">Supplier Name</label>
                <input
                  id="supplier-name"
                  v-model="form.supplier_name"
                  type="text"
                  class="form-input"
                  placeholder="Enter supplier name"
                  required
                  :disabled="submitting"
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label class="form-label" for="quantity">Quantity</label>
                  <input
                    id="quantity"
                    v-model.number="form.quantity"
                    type="number"
                    class="form-input"
                    min="1"
                    required
                    :disabled="submitting"
                  />
                </div>

                <div class="form-group">
                  <label class="form-label" for="unit-cost">Unit Cost ($)</label>
                  <input
                    id="unit-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    class="form-input"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    required
                    :disabled="submitting"
                  />
                </div>
              </div>

              <!-- Computed total cost shown inline when both fields are filled -->
              <div v-if="form.quantity > 0 && form.unit_cost > 0" class="total-preview">
                <span class="total-label">Estimated Total:</span>
                <span class="total-value">{{ formatCurrency(form.quantity * form.unit_cost) }}</span>
              </div>

              <div class="form-group">
                <label class="form-label" for="delivery-date">Expected Delivery Date</label>
                <input
                  id="delivery-date"
                  v-model="form.expected_delivery_date"
                  type="date"
                  class="form-input"
                  required
                  :disabled="submitting"
                />
              </div>

              <div class="form-group">
                <label class="form-label" for="notes">Notes <span class="optional">(optional)</span></label>
                <textarea
                  id="notes"
                  v-model="form.notes"
                  class="form-input form-textarea"
                  placeholder="Additional notes or instructions..."
                  rows="3"
                  :disabled="submitting"
                ></textarea>
              </div>

              <div v-if="submitError" class="error-message">{{ submitError }}</div>
            </form>

            <!-- VIEW MODE: Read-only PO details -->
            <div v-else class="po-details">
              <div class="details-grid">
                <div class="detail-item">
                  <div class="detail-label">Supplier</div>
                  <div class="detail-value">{{ backlogItem.purchase_order?.supplier_name ?? 'N/A' }}</div>
                </div>

                <div class="detail-item">
                  <div class="detail-label">Status</div>
                  <div class="detail-value">
                    <span class="status-badge" :class="backlogItem.purchase_order?.status">
                      {{ backlogItem.purchase_order?.status ?? 'N/A' }}
                    </span>
                  </div>
                </div>

                <div class="detail-item">
                  <div class="detail-label">Quantity</div>
                  <div class="detail-value">{{ backlogItem.purchase_order?.quantity ?? 'N/A' }} units</div>
                </div>

                <div class="detail-item">
                  <div class="detail-label">Unit Cost</div>
                  <div class="detail-value">
                    {{ backlogItem.purchase_order?.unit_cost != null
                      ? formatCurrency(backlogItem.purchase_order.unit_cost)
                      : 'N/A' }}
                  </div>
                </div>

                <div class="detail-item">
                  <div class="detail-label">Total Cost</div>
                  <div class="detail-value total-cost">
                    {{ totalCost != null ? formatCurrency(totalCost) : 'N/A' }}
                  </div>
                </div>

                <div class="detail-item">
                  <div class="detail-label">Expected Delivery</div>
                  <div class="detail-value">{{ formatDate(backlogItem.purchase_order?.expected_delivery_date) }}</div>
                </div>

                <div class="detail-item">
                  <div class="detail-label">Created</div>
                  <div class="detail-value">{{ formatDate(backlogItem.purchase_order?.created_date) }}</div>
                </div>

                <div v-if="backlogItem.purchase_order?.notes" class="detail-item full-width">
                  <div class="detail-label">Notes</div>
                  <div class="detail-value notes-value">{{ backlogItem.purchase_order.notes }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <template v-if="mode === 'create'">
              <button class="btn-secondary" @click="close" :disabled="submitting">Cancel</button>
              <button
                class="btn-primary"
                @click="submitForm"
                :disabled="submitting"
              >
                {{ submitting ? 'Creating...' : 'Create Purchase Order' }}
              </button>
            </template>
            <template v-else>
              <button class="btn-secondary" @click="close">Close</button>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../api'

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
    default: 'create' // 'create' | 'view'
  }
})

const emit = defineEmits(['close', 'po-created'])

// Form state
const form = ref({
  supplier_name: '',
  quantity: 0,
  unit_cost: 0,
  expected_delivery_date: '',
  notes: ''
})

const submitting = ref(false)
const submitError = ref(null)

// Pre-fill quantity with shortage amount when modal opens
watch(
  () => [props.isOpen, props.backlogItem],
  ([isOpen, item]) => {
    if (isOpen && item && props.mode === 'create') {
      // Pre-fill quantity with the shortage (needed minus available)
      const shortage = (item.quantity_needed ?? 0) - (item.quantity_available ?? 0)
      form.value = {
        supplier_name: '',
        quantity: shortage > 0 ? shortage : 1,
        unit_cost: 0,
        expected_delivery_date: '',
        notes: ''
      }
      submitError.value = null
    }
  },
  { immediate: true }
)

// Total cost for view mode (quantity * unit_cost)
const totalCost = computed(() => {
  const po = props.backlogItem?.purchase_order
  if (!po || po.quantity == null || po.unit_cost == null) return null
  return po.quantity * po.unit_cost
})

const close = () => {
  emit('close')
}

const submitForm = async () => {
  if (submitting.value) return
  submitting.value = true
  submitError.value = null

  try {
    const payload = {
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplier_name,
      quantity: form.value.quantity,
      unit_cost: form.value.unit_cost,
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes || undefined
    }
    const createdPO = await api.createPurchaseOrder(payload)
    emit('po-created', createdPO)
  } catch (err) {
    submitError.value = 'Failed to create purchase order. Please try again.'
    console.error('PO creation failed:', err)
  } finally {
    submitting.value = false
  }
}

const formatCurrency = (value) => {
  if (value == null) return 'N/A'
  return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  // Validate date before formatting to avoid "Invalid Date" output
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
}

/* Item summary header */
.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.item-name {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 0.25rem;
}

.item-sku {
  font-size: 0.813rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.priority-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.priority-badge.high {
  background: #fecaca;
  color: #991b1b;
}

.priority-badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.priority-badge.low {
  background: #dbeafe;
  color: #1e40af;
}

/* Form styles */
.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.optional {
  font-weight: 400;
  color: #94a3b8;
}

.form-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  width: 100%;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-input:disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.total-preview {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
}

.total-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #166534;
}

.total-value {
  font-size: 1rem;
  font-weight: 700;
  color: #059669;
}

.error-message {
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #991b1b;
}

/* View mode details */
.details-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.detail-item.full-width {
  grid-column: 1 / -1;
}

.detail-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.detail-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.detail-value.total-cost {
  font-size: 1.125rem;
  font-weight: 700;
  color: #059669;
}

.notes-value {
  color: #475569;
  font-weight: 400;
  line-height: 1.5;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.pending {
  background: #fef9c3;
  color: #854d0e;
}

.status-badge.confirmed {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.shipped {
  background: #e0e7ff;
  color: #3730a3;
}

.status-badge.delivered {
  background: #dcfce7;
  color: #166534;
}

.status-badge.cancelled {
  background: #f1f5f9;
  color: #64748b;
}

/* Footer */
.modal-footer {
  padding: 1.25rem 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  border: none;
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
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  opacity: 0.6;
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
