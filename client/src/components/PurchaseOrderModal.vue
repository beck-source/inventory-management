<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order' }}</h3>
            <button class="close-button" @click="close" aria-label="Close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <h4 class="item-name">{{ backlogItem.item_name }}</h4>
              <div class="item-meta">
                <span class="item-sku">SKU: {{ backlogItem.item_sku }}</span>
                <span>Order {{ backlogItem.order_id }}</span>
                <span>Shortage: {{ shortage }} units</span>
              </div>
            </div>

            <div v-if="error" class="error-message" role="alert">{{ error }}</div>

            <!-- Create mode -->
            <form v-if="mode === 'create'" id="po-form" class="po-form" novalidate @submit.prevent="submit">
              <div class="form-field">
                <label class="form-label" for="po-supplier">Supplier Name</label>
                <input id="po-supplier" v-model="form.supplier_name" type="text" class="form-input"
                       :class="{ invalid: fieldErrors.supplier_name }" :disabled="submitting" />
                <div v-if="fieldErrors.supplier_name" class="field-error">{{ fieldErrors.supplier_name }}</div>
              </div>

              <div class="form-row">
                <div class="form-field">
                  <label class="form-label" for="po-quantity">Quantity</label>
                  <input id="po-quantity" v-model="form.quantity" type="number" min="1" step="1" class="form-input"
                         :class="{ invalid: fieldErrors.quantity }" :disabled="submitting" />
                  <div v-if="fieldErrors.quantity" class="field-error">{{ fieldErrors.quantity }}</div>
                </div>
                <div class="form-field">
                  <label class="form-label" for="po-cost">Unit Cost (USD)</label>
                  <input id="po-cost" v-model="form.unit_cost" type="number" min="0" step="0.01" class="form-input"
                         :class="{ invalid: fieldErrors.unit_cost }" :disabled="submitting" />
                  <div v-if="fieldErrors.unit_cost" class="field-error">{{ fieldErrors.unit_cost }}</div>
                </div>
              </div>

              <div class="form-field">
                <label class="form-label" for="po-date">Expected Delivery Date</label>
                <input id="po-date" v-model="form.expected_delivery_date" type="date" class="form-input"
                       :class="{ invalid: fieldErrors.expected_delivery_date }" :disabled="submitting" />
                <div v-if="fieldErrors.expected_delivery_date" class="field-error">{{ fieldErrors.expected_delivery_date }}</div>
              </div>

              <div class="form-field">
                <label class="form-label" for="po-notes">Notes (optional)</label>
                <textarea id="po-notes" v-model="form.notes" rows="3" class="form-input" :disabled="submitting"></textarea>
              </div>
            </form>

            <!-- View mode -->
            <template v-else>
              <div v-if="loading" class="state-message">Loading purchase order...</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">PO ID</div>
                  <div class="info-value mono">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Status</div>
                  <div class="info-value">
                    <span class="badge" :class="statusClass">{{ purchaseOrder.status }}</span>
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
                  <div class="info-value">{{ formatMoney(purchaseOrder.unit_cost * purchaseOrder.quantity) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Expected Delivery</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Created</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div v-if="purchaseOrder.notes" class="info-item info-item-wide">
                  <div class="info-label">Notes</div>
                  <div class="info-value notes">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="close">
              {{ mode === 'create' ? 'Cancel' : 'Close' }}
            </button>
            <button v-if="mode === 'create'" class="btn-primary" type="submit" form="po-form" :disabled="submitting">
              {{ submitting ? 'Creating...' : 'Create Purchase Order' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: { type: Boolean, default: false },
    backlogItem: { type: Object, default: null },
    mode: {
      type: String,
      default: 'create',
      validator: (value) => ['create', 'view'].includes(value)
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const form = reactive({
      supplier_name: '',
      quantity: '',
      unit_cost: '',
      expected_delivery_date: '',
      notes: ''
    })
    const fieldErrors = reactive({})
    const error = ref(null)
    const submitting = ref(false)
    const loading = ref(false)
    const purchaseOrder = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
    })

    const statusClass = computed(() => {
      const status = (purchaseOrder.value?.status || '').toLowerCase()
      if (['delivered', 'received', 'completed'].includes(status)) return 'success'
      if (['cancelled', 'canceled', 'rejected'].includes(status)) return 'danger'
      if (['pending', 'draft'].includes(status)) return 'warning'
      return 'info'
    })

    // Prefer the server's {detail} message; fall back to a generic text
    const errorMessage = (err, fallback) => err?.response?.data?.detail || fallback

    const resetState = () => {
      form.supplier_name = ''
      form.quantity = shortage.value > 0 ? shortage.value : ''
      form.unit_cost = ''
      form.expected_delivery_date = ''
      form.notes = ''
      Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
      error.value = null
      submitting.value = false
      loading.value = false
      purchaseOrder.value = null
    }

    const loadPurchaseOrder = async () => {
      if (!props.backlogItem) return
      loading.value = true
      error.value = null
      try {
        purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        error.value = errorMessage(err, 'Failed to load purchase order')
        console.error('Purchase order load error:', err)
      } finally {
        loading.value = false
      }
    }

    // Reset every time the modal opens; view mode also fetches the PO.
    watch(() => props.isOpen, (open) => {
      if (!open) return
      resetState()
      if (props.mode === 'view') loadPurchaseOrder()
    }, { immediate: true })

    const validate = () => {
      Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
      if (!form.supplier_name.trim()) fieldErrors.supplier_name = 'Supplier name is required'

      // v-model on number inputs yields '' when empty, so check for that before Number()
      const quantity = Number(form.quantity)
      if (form.quantity === '' || !Number.isFinite(quantity) || quantity <= 0) {
        fieldErrors.quantity = 'Quantity must be greater than 0'
      } else if (!Number.isInteger(quantity)) {
        fieldErrors.quantity = 'Quantity must be a whole number'
      }

      const unitCost = Number(form.unit_cost)
      if (form.unit_cost === '' || !Number.isFinite(unitCost) || unitCost < 0) {
        fieldErrors.unit_cost = 'Unit cost must be 0 or more'
      }

      if (!form.expected_delivery_date) {
        fieldErrors.expected_delivery_date = 'Expected delivery date is required'
      } else if (isNaN(new Date(form.expected_delivery_date).getTime())) {
        fieldErrors.expected_delivery_date = 'Enter a valid date'
      }

      return Object.keys(fieldErrors).length === 0
    }

    const submit = async () => {
      if (submitting.value || !props.backlogItem) return
      error.value = null
      if (!validate()) return

      submitting.value = true
      try {
        const payload = {
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier_name.trim(),
          quantity: Number(form.quantity),
          unit_cost: Number(form.unit_cost),
          expected_delivery_date: form.expected_delivery_date
        }
        // Notes are optional: omit the key entirely when empty
        const notes = form.notes.trim()
        if (notes) payload.notes = notes

        const po = await api.createPurchaseOrder(payload)
        emit('po-created', po)
      } catch (err) {
        error.value = errorMessage(err, 'Failed to create purchase order')
        console.error('Purchase order create error:', err)
      } finally {
        submitting.value = false
      }
    }

    const close = () => emit('close')

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return 'N/A'
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    }

    const formatMoney = (value) => {
      const amount = Number(value)
      if (!Number.isFinite(amount)) return 'N/A'
      return amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }

    return {
      form,
      fieldErrors,
      error,
      submitting,
      loading,
      purchaseOrder,
      shortage,
      statusClass,
      submit,
      close,
      formatDate,
      formatMoney
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
  gap: 0.5rem 1.25rem;
  font-size: 0.875rem;
  color: #64748b;
}

.item-sku {
  font-family: 'Monaco', 'Courier New', monospace;
}

.error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.state-message {
  text-align: center;
  color: #64748b;
  padding: 2rem 0;
  font-size: 0.938rem;
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

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
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
  font-family: inherit;
  color: #0f172a;
  background: white;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-input.invalid {
  border-color: #ef4444;
}

.form-input:disabled {
  background: #f8fafc;
  color: #94a3b8;
}

textarea.form-input {
  resize: vertical;
}

.field-error {
  font-size: 0.813rem;
  color: #dc2626;
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

.info-item-wide {
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
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
}

.badge.success { background: #dcfce7; color: #166534; }
.badge.info { background: #dbeafe; color: #1e40af; }
.badge.warning { background: #fef3c7; color: #92400e; }
.badge.danger { background: #fecaca; color: #991b1b; }

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
  background: #0f172a;
  border: 1px solid #0f172a;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled {
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
