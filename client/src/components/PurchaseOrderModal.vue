<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'view' ? 'Purchase Order Details' : 'Create Purchase Order' }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Create mode -->
          <form v-if="mode !== 'view'" class="po-form" novalidate @submit.prevent="submit">
            <div class="modal-body">
              <div class="item-summary">
                <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">SKU</div>
                    <div class="info-value sku">{{ backlogItem.item_sku }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Order ID</div>
                    <div class="info-value order-id">{{ backlogItem.order_id }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Shortage</div>
                    <div class="info-value"><span class="badge danger">{{ shortage }} units</span></div>
                  </div>
                </div>
              </div>

              <div class="form-grid">
                <div class="form-field full">
                  <label for="po-supplier">Supplier Name</label>
                  <input
                    id="po-supplier"
                    v-model="form.supplier_name"
                    type="text"
                    maxlength="200"
                    :disabled="submitting"
                  />
                </div>

                <div class="form-field">
                  <label for="po-quantity">Quantity</label>
                  <input
                    id="po-quantity"
                    v-model.number="form.quantity"
                    type="number"
                    min="1"
                    step="1"
                    :disabled="submitting"
                  />
                </div>

                <div class="form-field">
                  <label for="po-unit-cost">Unit Cost (USD)</label>
                  <input
                    id="po-unit-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    min="0"
                    step="0.01"
                    :disabled="submitting"
                  />
                </div>

                <div class="form-field full">
                  <label for="po-date">Expected Delivery Date</label>
                  <input
                    id="po-date"
                    v-model="form.expected_delivery_date"
                    type="date"
                    :disabled="submitting"
                  />
                </div>

                <div class="form-field full">
                  <label for="po-notes">Notes (optional)</label>
                  <textarea
                    id="po-notes"
                    v-model="form.notes"
                    rows="3"
                    :disabled="submitting"
                  ></textarea>
                </div>
              </div>

              <div class="total-row">
                <span class="info-label">Total</span>
                <span class="total-value">{{ formatCurrency(formTotal) }}</span>
              </div>

              <div v-if="submitError" class="error-message" role="alert">{{ submitError }}</div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" @click="close">Cancel</button>
              <button type="submit" class="btn-primary" :disabled="!isFormValid || submitting">
                {{ submitting ? 'Creating...' : 'Create Purchase Order' }}
              </button>
            </div>
          </form>

          <!-- View mode -->
          <template v-else>
            <div class="modal-body">
              <div v-if="viewLoading" class="state-message">Loading purchase order...</div>
              <div v-else-if="viewError" class="error-message" role="alert">{{ viewError }}</div>
              <template v-else-if="po">
                <div class="item-summary">
                  <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
                  <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
                </div>

                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">PO ID</div>
                    <div class="info-value order-id">{{ po.id || 'N/A' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">
                      <span class="badge" :class="statusClass(po.status)">{{ formatStatus(po.status) }}</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Supplier</div>
                    <div class="info-value">{{ po.supplier_name || 'N/A' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Quantity</div>
                    <div class="info-value">{{ po.quantity != null ? po.quantity + ' units' : 'N/A' }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Unit Cost</div>
                    <div class="info-value">{{ formatCurrency(po.unit_cost) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Total</div>
                    <div class="info-value strong">{{ formatCurrency(poTotal) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Expected Delivery</div>
                    <div class="info-value">{{ formatDate(po.expected_delivery_date) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Created</div>
                    <div class="info-value">{{ formatDate(po.created_date) }}</div>
                  </div>
                  <div class="info-item full">
                    <div class="info-label">Notes</div>
                    <div class="info-value notes">{{ po.notes || '-' }}</div>
                  </div>
                </div>
              </template>
            </div>

            <div class="modal-footer">
              <button class="btn-secondary" @click="close">Close</button>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../api'
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
  },
  mode: {
    type: String,
    default: 'create',
    validator: (value) => ['create', 'view'].includes(value)
  }
})

const emit = defineEmits(['close', 'po-created'])

const emptyForm = () => ({
  supplier_name: '',
  quantity: null,
  unit_cost: null,
  expected_delivery_date: '',
  notes: ''
})

const form = ref(emptyForm())
const submitting = ref(false)
const submitError = ref(null)

const po = ref(null)
const viewLoading = ref(false)
const viewError = ref(null)

// Guards against a slow response from a previous open/item overwriting current state
let requestToken = 0

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
})

const isValidDateString = (value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return false
  return !isNaN(new Date(value).getTime())
}

const isFormValid = computed(() => {
  const f = form.value
  return (
    f.supplier_name.trim().length > 0 &&
    Number.isInteger(f.quantity) && f.quantity > 0 &&
    typeof f.unit_cost === 'number' && Number.isFinite(f.unit_cost) && f.unit_cost >= 0 &&
    isValidDateString(f.expected_delivery_date)
  )
})

const formTotal = computed(() => {
  const { quantity, unit_cost } = form.value
  if (typeof quantity !== 'number' || typeof unit_cost !== 'number') return 0
  return quantity * unit_cost
})

const poTotal = computed(() => {
  if (!po.value) return 0
  return (Number(po.value.quantity) || 0) * (Number(po.value.unit_cost) || 0)
})

const resetState = () => {
  requestToken++
  form.value = { ...emptyForm(), quantity: shortage.value > 0 ? shortage.value : null }
  submitting.value = false
  submitError.value = null
  po.value = null
  viewLoading.value = false
  viewError.value = null
}

const loadPO = async () => {
  const item = props.backlogItem
  if (item.purchase_order) {
    po.value = item.purchase_order
    return
  }
  const token = ++requestToken
  viewLoading.value = true
  try {
    const result = await api.getPurchaseOrderByBacklogItem(item.id)
    if (token !== requestToken) return
    po.value = result
  } catch (err) {
    if (token !== requestToken) return
    viewError.value = err.response?.status === 404
      ? 'No purchase order exists for this item.'
      : (err.response?.data?.detail || 'Failed to load purchase order.')
    console.error('Failed to load purchase order:', err)
  } finally {
    if (token === requestToken) viewLoading.value = false
  }
}

// Re-initialise whenever the modal opens or a different item/mode is supplied
watch(
  () => [props.isOpen, props.backlogItem, props.mode],
  ([isOpen, item, mode]) => {
    if (!isOpen || !item) return
    resetState()
    if (mode === 'view') loadPO()
  },
  { immediate: true }
)

const submit = async () => {
  if (!isFormValid.value || submitting.value) return
  const item = props.backlogItem
  const f = form.value
  const token = requestToken
  submitting.value = true
  submitError.value = null
  try {
    const createdPO = await api.createPurchaseOrder({
      backlog_item_id: item.id,
      supplier_name: f.supplier_name.trim(),
      quantity: f.quantity,
      unit_cost: f.unit_cost,
      expected_delivery_date: f.expected_delivery_date,
      notes: f.notes.trim() || null
    })
    emit('po-created', createdPO)
  } catch (err) {
    if (token !== requestToken) return
    const detail = err.response?.data?.detail
    submitError.value = typeof detail === 'string' ? detail : 'Failed to create purchase order. Please try again.'
    console.error('Failed to create purchase order:', err)
  } finally {
    if (token === requestToken) submitting.value = false
  }
}

const close = () => {
  emit('close')
}

const formatCurrency = (value) => {
  const num = Number(value)
  if (value == null || isNaN(num)) return 'N/A'
  return num.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  // Date-only strings are parsed as UTC; format in UTC to avoid off-by-one day shifts
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...(dateOnly ? { timeZone: 'UTC' } : {})
  })
}

const formatStatus = (status) => {
  if (!status) return 'N/A'
  return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' ')
}

const statusClass = (status) => {
  switch ((status || '').toLowerCase()) {
    case 'delivered':
    case 'received':
      return 'success'
    case 'pending':
      return 'warning'
    case 'cancelled':
      return 'danger'
    default:
      return 'info'
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
  max-width: 640px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.po-form {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
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
  margin: 0 0 0.75rem 0;
}

.item-summary .item-sku {
  font-size: 0.875rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1.25rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.full {
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

.info-value.strong {
  font-weight: 700;
}

.info-value.notes {
  white-space: pre-wrap;
  word-break: break-word;
}

.info-value.order-id,
.info-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
}

.badge.danger {
  background: #fecaca;
  color: #991b1b;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.success {
  background: #d1fae5;
  color: #065f46;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-field.full {
  grid-column: 1 / -1;
}

.form-field label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.form-field input,
.form-field textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-field textarea {
  resize: vertical;
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.form-field input:disabled,
.form-field textarea:disabled {
  background: #f8fafc;
  color: #64748b;
}

.total-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 1.5rem;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  font-size: 0.875rem;
}

.state-message {
  padding: 1.5rem 0;
  text-align: center;
  color: #64748b;
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
