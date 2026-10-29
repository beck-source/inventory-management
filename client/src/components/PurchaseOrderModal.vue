<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ isViewMode ? 'Purchase Order' : 'Create Purchase Order' }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
              <div class="item-meta">
                <span>SKU: {{ backlogItem.item_sku }}</span>
                <span>Order: {{ backlogItem.order_id }}</span>
                <span>Shortage: {{ shortage }} units</span>
              </div>
            </div>

            <!-- View mode -->
            <template v-if="isViewMode">
              <div v-if="isLoading" class="state-message">Loading purchase order...</div>
              <div v-else-if="errorMessage" class="error-message">{{ errorMessage }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">PO Number</div>
                  <div class="info-value mono">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Status</div>
                  <div class="info-value">
                    <span class="badge">{{ purchaseOrder.status }}</span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">Supplier</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Quantity</div>
                  <div class="info-value">{{ purchaseOrder.quantity }} units</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Unit Cost</div>
                  <div class="info-value">{{ formatMoney(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Total Cost</div>
                  <div class="info-value">{{ formatMoney(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Expected Delivery</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Created</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div v-if="purchaseOrder.notes" class="info-item full-row">
                  <div class="info-label">Notes</div>
                  <div class="info-value notes">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" @submit.prevent="submitForm">
              <div class="form-group">
                <label for="po-supplier">Supplier Name</label>
                <input
                  id="po-supplier"
                  v-model="form.supplierName"
                  type="text"
                  class="form-input"
                  placeholder="Enter supplier name"
                />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">Quantity</label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    min="1"
                    step="1"
                    class="form-input"
                  />
                </div>

                <div class="form-group">
                  <label for="po-unit-cost">Unit Cost ($)</label>
                  <input
                    id="po-unit-cost"
                    v-model.number="form.unitCost"
                    type="number"
                    min="0.01"
                    step="0.01"
                    class="form-input"
                  />
                </div>
              </div>

              <div class="form-group">
                <label for="po-delivery-date">Expected Delivery Date</label>
                <input
                  id="po-delivery-date"
                  v-model="form.expectedDeliveryDate"
                  type="date"
                  class="form-input"
                />
              </div>

              <div class="form-group">
                <label for="po-notes">Notes (optional)</label>
                <textarea
                  id="po-notes"
                  v-model="form.notes"
                  rows="3"
                  class="form-input"
                ></textarea>
              </div>

              <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">Close</button>
            <button
              v-if="!isViewMode"
              type="submit"
              form="po-form"
              class="btn-primary"
              :disabled="!isFormValid || isSubmitting"
            >
              {{ isSubmitting ? 'Creating...' : 'Create Purchase Order' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const DATE_ONLY_PATTERN = /^\d{4}-\d{2}-\d{2}$/

export default {
  name: 'PurchaseOrderModal',
  props: {
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
      validator: (value) => ['create', 'view'].includes(value)
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { translateProductName } = useI18n()

    const form = ref({
      supplierName: '',
      quantity: 1,
      unitCost: null,
      expectedDeliveryDate: '',
      notes: ''
    })
    const purchaseOrder = ref(null)
    const isLoading = ref(false)
    const isSubmitting = ref(false)
    const errorMessage = ref('')

    // Guards against a slow response from a previous open overwriting the current one
    let requestId = 0

    const isViewMode = computed(() => props.mode === 'view')

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
    })

    const isFormValid = computed(() => {
      const { supplierName, quantity, unitCost, expectedDeliveryDate } = form.value
      return supplierName.trim() !== '' &&
        Number.isInteger(quantity) && quantity >= 1 &&
        typeof unitCost === 'number' && unitCost > 0 &&
        expectedDeliveryDate !== ''
    })

    const getErrorMessage = (err, fallback) => {
      const detail = err.response?.data?.detail
      return typeof detail === 'string' && detail ? detail : fallback
    }

    const resetState = () => {
      requestId++
      form.value = {
        supplierName: '',
        quantity: Math.max(1, shortage.value),
        unitCost: null,
        expectedDeliveryDate: '',
        notes: ''
      }
      purchaseOrder.value = null
      isLoading.value = false
      isSubmitting.value = false
      errorMessage.value = ''
    }

    const loadPurchaseOrder = async () => {
      const currentRequest = ++requestId
      isLoading.value = true
      try {
        const result = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
        if (currentRequest !== requestId) return
        purchaseOrder.value = result
      } catch (err) {
        if (currentRequest !== requestId) return
        console.error('Failed to load purchase order:', err)
        errorMessage.value = getErrorMessage(err, 'Failed to load purchase order')
      } finally {
        if (currentRequest === requestId) isLoading.value = false
      }
    }

    const submitForm = async () => {
      if (!isFormValid.value || isSubmitting.value) return
      const currentRequest = ++requestId
      isSubmitting.value = true
      errorMessage.value = ''
      try {
        const created = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplierName.trim(),
          quantity: form.value.quantity,
          unit_cost: form.value.unitCost,
          expected_delivery_date: form.value.expectedDeliveryDate,
          notes: form.value.notes.trim() || null
        })
        if (currentRequest !== requestId) return
        emit('po-created', created)
      } catch (err) {
        if (currentRequest !== requestId) return
        console.error('Failed to create purchase order:', err)
        errorMessage.value = getErrorMessage(err, 'Failed to create purchase order')
      } finally {
        if (currentRequest === requestId) isSubmitting.value = false
      }
    }

    const close = () => {
      emit('close')
    }

    const formatMoney = (value) => {
      return Number(value).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      // Date-only strings parse as UTC and can render a day early in negative-offset timezones
      const date = new Date(DATE_ONLY_PATTERN.test(dateString) ? `${dateString}T00:00:00` : dateString)
      if (isNaN(date.getTime())) return 'N/A'
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    }

    // Reset every time the modal opens, then fetch the PO if viewing
    watch(() => props.isOpen, (isOpen) => {
      if (!isOpen) return
      resetState()
      if (isViewMode.value && props.backlogItem) loadPurchaseOrder()
    }, { immediate: true })

    return {
      translateProductName,
      form,
      purchaseOrder,
      isLoading,
      isSubmitting,
      errorMessage,
      isViewMode,
      shortage,
      isFormValid,
      submitForm,
      close,
      formatMoney,
      formatDate
    }
  }
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

.item-summary {
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.item-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.5rem 0;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.5rem;
  font-size: 0.875rem;
  color: #64748b;
}

.state-message {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

.error-message {
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  font-size: 0.875rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.full-row {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.813rem;
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

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.info-value.notes {
  white-space: pre-wrap;
  font-weight: 400;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  background: #dbeafe;
  color: #1e40af;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.form-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  transition: border-color 0.15s ease;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
}

textarea.form-input {
  resize: vertical;
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
  background: #3b82f6;
  border: 1px solid #3b82f6;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
  border-color: #2563eb;
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
