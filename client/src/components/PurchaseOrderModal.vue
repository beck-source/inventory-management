<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'view' ? 'Purchase Order' : 'Create Purchase Order' }}</h3>
            <button class="close-button" type="button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <form class="modal-form" novalidate @submit.prevent="submit">
            <div class="modal-body">
              <div class="item-summary">
                <div class="info-item">
                  <div class="info-label">Item</div>
                  <div class="info-value">{{ translateProductName(backlogItem.item_name) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">SKU</div>
                  <div class="info-value sku">{{ backlogItem.item_sku }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Shortage</div>
                  <div class="info-value shortage">{{ shortage }} units</div>
                </div>
              </div>

              <!-- View mode -->
              <template v-if="mode === 'view'">
                <div v-if="loadingPO" class="state-message">Loading purchase order...</div>
                <div v-else-if="loadError" class="error-message">{{ loadError }}</div>
                <div v-else-if="purchaseOrder" class="info-grid">
                  <div class="info-item">
                    <div class="info-label">PO Number</div>
                    <div class="info-value sku">{{ purchaseOrder.id }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value">{{ purchaseOrder.status }}</div>
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
                    <div class="info-value">{{ formatCurrencyWithDecimals(purchaseOrder.unit_cost, currentCurrency, 2) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Total</div>
                    <div class="info-value">{{ formatCurrency(purchaseOrder.quantity * purchaseOrder.unit_cost, currentCurrency) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Expected Delivery</div>
                    <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">Created</div>
                    <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                  </div>
                  <div class="info-item full-width">
                    <div class="info-label">Notes</div>
                    <div class="info-value">{{ purchaseOrder.notes || 'N/A' }}</div>
                  </div>
                </div>
              </template>

              <!-- Create mode -->
              <template v-else>
                <div class="form-grid">
                  <div class="form-field full-width">
                    <label for="po-supplier">Supplier name</label>
                    <input id="po-supplier" v-model="form.supplier_name" type="text" :disabled="saving" />
                  </div>
                  <div class="form-field">
                    <label for="po-quantity">Quantity</label>
                    <input id="po-quantity" v-model="form.quantity" type="number" min="1" step="1" :disabled="saving" />
                  </div>
                  <div class="form-field">
                    <label for="po-cost">Unit cost (USD)</label>
                    <input id="po-cost" v-model="form.unit_cost" type="number" min="0" step="0.01" :disabled="saving" />
                  </div>
                  <div class="form-field full-width">
                    <label for="po-date">Expected delivery date</label>
                    <input id="po-date" v-model="form.expected_delivery_date" type="date" :disabled="saving" />
                  </div>
                  <div class="form-field full-width">
                    <label for="po-notes">Notes (optional)</label>
                    <textarea id="po-notes" v-model="form.notes" rows="3" :disabled="saving"></textarea>
                  </div>
                </div>

                <div class="total-row">
                  <span class="info-label">Total</span>
                  <span class="total-value">{{ formatCurrency(total, currentCurrency) }}</span>
                </div>

                <div v-if="formError" class="error-message">{{ formError }}</div>
              </template>
            </div>

            <div class="modal-footer">
              <button class="btn-secondary" type="button" @click="close">
                {{ mode === 'view' ? 'Close' : 'Cancel' }}
              </button>
              <button v-if="mode !== 'view'" class="btn-primary" type="submit" :disabled="saving">
                {{ saving ? 'Saving...' : 'Create Purchase Order' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const { translateProductName, currentCurrency } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: { type: String, default: 'create' } // 'create' | 'view'
})

const emit = defineEmits(['close', 'po-created'])

const form = reactive({
  supplier_name: '',
  quantity: '',
  unit_cost: '',
  expected_delivery_date: '',
  notes: ''
})
const saving = ref(false)
const formError = ref('')
const purchaseOrder = ref(null)
const loadingPO = ref(false)
const loadError = ref('')

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const total = computed(() => {
  const q = Number(form.quantity)
  const c = Number(form.unit_cost)
  return Number.isFinite(q) && Number.isFinite(c) ? q * c : 0
})

const close = () => emit('close')

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const resetForm = () => {
  form.supplier_name = ''
  form.quantity = shortage.value > 0 ? shortage.value : ''
  form.unit_cost = ''
  form.expected_delivery_date = ''
  form.notes = ''
  formError.value = ''
  saving.value = false
}

const loadPO = async () => {
  purchaseOrder.value = null
  loadError.value = ''
  loadingPO.value = true
  // Capture the item so a stale response (modal reopened for another item) is ignored
  const itemId = props.backlogItem.id
  try {
    const po = await api.getPurchaseOrderByBacklogItem(itemId)
    if (props.backlogItem?.id === itemId) purchaseOrder.value = po
  } catch (err) {
    if (props.backlogItem?.id !== itemId) return
    loadError.value = err.response?.data?.detail || 'Failed to load purchase order'
    console.error('Load PO error:', err)
  } finally {
    if (props.backlogItem?.id === itemId) loadingPO.value = false
  }
}

// Reset / fetch every time the modal opens (or the item changes while open)
watch(
  () => [props.isOpen, props.backlogItem?.id, props.mode],
  () => {
    if (!props.isOpen || !props.backlogItem) return
    if (props.mode === 'view') loadPO()
    else resetForm()
  },
  { immediate: true }
)

const submit = async () => {
  formError.value = ''
  const quantity = Number(form.quantity)
  const unitCost = Number(form.unit_cost)

  if (!form.supplier_name.trim()) return (formError.value = 'Supplier name is required')
  if (!Number.isInteger(quantity) || quantity <= 0) return (formError.value = 'Quantity must be a whole number greater than 0')
  if (!Number.isFinite(unitCost) || unitCost <= 0) return (formError.value = 'Unit cost must be greater than 0')
  if (!form.expected_delivery_date) return (formError.value = 'Expected delivery date is required')

  saving.value = true
  try {
    const po = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name.trim(),
      quantity,
      unit_cost: unitCost,
      expected_delivery_date: form.expected_delivery_date,
      notes: form.notes.trim() || null
    })
    emit('po-created', po)
  } catch (err) {
    const detail = err.response?.data?.detail
    // FastAPI 422 returns detail as an array of {msg}; 404/409 return a string
    formError.value = Array.isArray(detail)
      ? detail.map(d => d.msg).join('; ')
      : detail || 'Failed to create purchase order'
    console.error('Create PO error:', err)
  } finally {
    saving.value = false
  }
}

const onKeydown = (e) => {
  if (e.key === 'Escape' && props.isOpen) close()
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
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

.modal-form {
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
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 1rem;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.info-grid,
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.full-width {
  grid-column: 1 / -1;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0;
}

.info-label,
.form-field label {
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
  overflow-wrap: anywhere;
}

.info-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.info-value.shortage {
  color: #dc2626;
  font-weight: 700;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
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
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #64748b;
  box-shadow: 0 0 0 3px rgba(100, 116, 139, 0.15);
}

.form-field input:disabled,
.form-field textarea:disabled {
  background: #f1f5f9;
  color: #64748b;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.state-message {
  color: #64748b;
  font-size: 0.938rem;
  text-align: center;
  padding: 1.5rem 0;
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

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary,
.btn-primary {
  padding: 0.625rem 1.25rem;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  background: #0f172a;
  border: 1px solid #0f172a;
  color: white;
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
