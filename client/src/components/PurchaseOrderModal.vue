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

            <!-- CREATE MODE -->
            <template v-if="mode === 'create'">
              <!-- Context: backlog item info -->
              <div class="context-section">
                <h4 class="context-title">Backlog Item</h4>
                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">Item Name</div>
                    <div class="info-value">{{ backlogItem.item_name }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">SKU</div>
                    <div class="info-value mono">{{ backlogItem.item_sku }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Order ID</div>
                    <div class="info-value mono">{{ backlogItem.order_id }}</div>
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
                    <div class="info-label">Shortage</div>
                    <div class="info-value shortage">{{ shortage }} units short</div>
                  </div>
                </div>
              </div>

              <div class="section-divider"></div>

              <!-- PO Form -->
              <div class="form-section">
                <h4 class="context-title">Order Details</h4>

                <div v-if="formError" class="error">{{ formError }}</div>

                <div class="form-group">
                  <label for="po-supplier">Supplier Name <span class="required">*</span></label>
                  <input
                    id="po-supplier"
                    v-model="form.supplier_name"
                    type="text"
                    class="form-input"
                    placeholder="Enter supplier name"
                  />
                </div>

                <div class="form-row-two">
                  <div class="form-group">
                    <label for="po-quantity">Quantity <span class="required">*</span></label>
                    <input
                      id="po-quantity"
                      v-model.number="form.quantity"
                      type="number"
                      class="form-input"
                      min="1"
                      placeholder="1"
                    />
                  </div>

                  <div class="form-group">
                    <label for="po-unit-cost">Unit Cost ($) <span class="required">*</span></label>
                    <input
                      id="po-unit-cost"
                      v-model.number="form.unit_cost"
                      type="number"
                      class="form-input"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <div class="form-group">
                  <label for="po-delivery-date">Expected Delivery Date <span class="required">*</span></label>
                  <input
                    id="po-delivery-date"
                    v-model="form.expected_delivery_date"
                    type="date"
                    class="form-input"
                  />
                </div>

                <div class="form-group">
                  <label for="po-notes">Notes</label>
                  <textarea
                    id="po-notes"
                    v-model="form.notes"
                    class="form-textarea"
                    rows="3"
                    placeholder="Optional notes..."
                  ></textarea>
                </div>

                <!-- Total preview -->
                <div v-if="form.quantity > 0 && form.unit_cost > 0" class="total-preview">
                  <span class="total-label">Estimated Total</span>
                  <span class="total-value">{{ formatCurrency(form.quantity * form.unit_cost) }}</span>
                </div>
              </div>
            </template>

            <!-- VIEW MODE -->
            <template v-else>
              <div v-if="viewLoading" class="state-message">Loading purchase order...</div>
              <div v-else-if="viewError" class="error">{{ viewError }}</div>
              <template v-else-if="poData">
                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">PO ID</div>
                    <div class="info-value mono">{{ poData.id }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">
                      <span class="status-badge" :class="poData.status">{{ poData.status }}</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Supplier</div>
                    <div class="info-value">{{ poData.supplier_name }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Quantity</div>
                    <div class="info-value">{{ poData.quantity }} units</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Unit Cost</div>
                    <div class="info-value">{{ formatCurrency(poData.unit_cost) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Total Value</div>
                    <div class="info-value total-value-display">{{ formatCurrency(poData.quantity * poData.unit_cost) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Expected Delivery</div>
                    <div class="info-value">{{ formatDate(poData.expected_delivery_date) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Created Date</div>
                    <div class="info-value">{{ formatDate(poData.created_date) }}</div>
                  </div>
                </div>
                <div v-if="poData.notes" class="notes-section">
                  <div class="info-label">Notes</div>
                  <div class="notes-body">{{ poData.notes }}</div>
                </div>
              </template>
            </template>

          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">Close</button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="!isFormValid || submitting"
              @click="submitPO"
            >
              {{ submitting ? 'Creating...' : 'Create Purchase Order' }}
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

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    },
    backlogItem: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create'
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    // Create mode form state
    const form = ref({
      supplier_name: '',
      quantity: 0,
      unit_cost: 0,
      expected_delivery_date: '',
      notes: ''
    })
    const formError = ref(null)
    const submitting = ref(false)

    // View mode state
    const poData = ref(null)
    const viewLoading = ref(false)
    const viewError = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
    })

    const isFormValid = computed(() => {
      return (
        form.value.supplier_name.trim().length > 0 &&
        form.value.quantity >= 1 &&
        form.value.unit_cost >= 0 &&
        form.value.expected_delivery_date.length > 0
      )
    })

    const resetForm = () => {
      form.value = {
        supplier_name: '',
        quantity: shortage.value > 0 ? shortage.value : 1,
        unit_cost: 0,
        expected_delivery_date: '',
        notes: ''
      }
      formError.value = null
      submitting.value = false
    }

    const fetchPO = async () => {
      if (!props.backlogItem) return
      viewLoading.value = true
      viewError.value = null
      poData.value = null
      try {
        poData.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        viewError.value = 'Could not load purchase order. It may not exist yet.'
      } finally {
        viewLoading.value = false
      }
    }

    // When the modal opens or mode changes, set up the correct state
    watch(
      () => props.isOpen,
      (isOpen) => {
        if (!isOpen) return
        if (props.mode === 'create') {
          resetForm()
        } else {
          fetchPO()
        }
      }
    )

    watch(
      () => props.mode,
      (newMode) => {
        if (!props.isOpen) return
        if (newMode === 'create') {
          resetForm()
        } else {
          fetchPO()
        }
      }
    )

    const close = () => {
      emit('close')
    }

    const submitPO = async () => {
      if (!isFormValid.value || submitting.value) return
      submitting.value = true
      formError.value = null
      try {
        const po = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplier_name.trim(),
          quantity: Number(form.value.quantity),
          unit_cost: Number(form.value.unit_cost),
          expected_delivery_date: form.value.expected_delivery_date,
          notes: form.value.notes.trim()
        })
        emit('po-created', po)
      } catch (err) {
        formError.value = 'Failed to create purchase order. Please try again.'
        submitting.value = false
      }
    }

    const formatCurrency = (value) => {
      if (value == null || isNaN(value)) return '$0.00'
      return Number(value).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    const formatDate = (value) => {
      if (!value) return '-'
      // Handle plain date-only strings (YYYY-MM-DD) without UTC shifting
      const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(value)
      const date = m ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : new Date(value)
      if (isNaN(date.getTime())) return '-'
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    }

    return {
      form,
      formError,
      submitting,
      poData,
      viewLoading,
      viewError,
      shortage,
      isFormValid,
      close,
      submitPO,
      formatCurrency,
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
  max-width: 620px;
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
  margin: 0;
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
  padding: 1.75rem;
}

.modal-footer {
  padding: 1.25rem 1.75rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* Context section */
.context-section {
  margin-bottom: 0;
}

.context-title {
  font-size: 0.813rem;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 1rem 0;
}

.section-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 1.5rem 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
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

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.info-value.shortage {
  color: #dc2626;
  font-weight: 600;
}

.info-value.total-value-display {
  color: #0f172a;
  font-weight: 700;
  font-size: 1rem;
}

/* Form */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-row-two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.required {
  color: #ef4444;
}

.form-input {
  padding: 0.625rem 0.875rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  background: white;
  transition: border-color 0.15s ease;
  font-family: inherit;
  width: 100%;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.form-textarea {
  padding: 0.625rem 0.875rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  background: white;
  transition: border-color 0.15s ease;
  font-family: inherit;
  resize: vertical;
  width: 100%;
  box-sizing: border-box;
}

.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.total-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.875rem 1rem;
}

.total-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.total-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

/* Status badge (view mode) */
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-badge.pending {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.approved {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.fulfilled {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.cancelled {
  background: #fecaca;
  color: #991b1b;
}

/* Notes (view mode) */
.notes-section {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.notes-body {
  font-size: 0.938rem;
  color: #475569;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

/* State messages */
.state-message {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

/* Buttons */
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
  padding: 0.625rem 1.375rem;
  background: #3b82f6;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
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
