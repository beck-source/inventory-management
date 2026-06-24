<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <div class="header-title-group">
              <div class="po-icon">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M5 2.5h7L16 6v11.5H5z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                  <path d="M12 2.5V6h4" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>
                  <path d="M7.5 10h5M7.5 13h5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
                </svg>
              </div>
              <h3 class="modal-title">
                {{ mode === 'view' ? 'Purchase Order Details' : 'Create Purchase Order' }}
              </h3>
            </div>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Item context (shared by both modes) -->
            <div class="item-context">
              <div class="item-context-text">
                <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} Priority
              </span>
            </div>

            <!-- CREATE MODE -->
            <template v-if="mode !== 'view'">
              <div class="context-summary">
                <div class="summary-card danger">
                  <div class="summary-label">Shortage</div>
                  <div class="summary-value">{{ shortage }} units</div>
                </div>
                <div class="summary-card accent">
                  <div class="summary-label">Recommended Qty</div>
                  <div class="summary-value">{{ shortage }} units</div>
                </div>
              </div>

              <form class="po-form" @submit.prevent="submit">
                <div class="form-grid">
                  <div class="field field-wide">
                    <label class="field-label" for="po-supplier">Supplier</label>
                    <input
                      id="po-supplier"
                      v-model.trim="form.supplier_name"
                      type="text"
                      class="field-input"
                      placeholder="e.g. Acme Components Ltd."
                      required
                    />
                  </div>

                  <div class="field">
                    <label class="field-label" for="po-qty">Quantity</label>
                    <input
                      id="po-qty"
                      v-model.number="form.quantity"
                      type="number"
                      class="field-input"
                      min="1"
                      step="1"
                      required
                    />
                  </div>

                  <div class="field">
                    <label class="field-label" for="po-cost">Unit Cost (USD)</label>
                    <input
                      id="po-cost"
                      v-model.number="form.unit_cost"
                      type="number"
                      class="field-input"
                      min="0"
                      step="0.01"
                      placeholder="0.00"
                      required
                    />
                  </div>

                  <div class="field">
                    <label class="field-label" for="po-date">Expected Delivery</label>
                    <input
                      id="po-date"
                      v-model="form.expected_delivery_date"
                      type="date"
                      class="field-input"
                      required
                    />
                  </div>

                  <div class="field">
                    <span class="field-label">Order Total</span>
                    <div class="field-static">{{ formatUSD(orderTotal) }}</div>
                  </div>

                  <div class="field field-wide">
                    <label class="field-label" for="po-notes">Notes <span class="optional">(optional)</span></label>
                    <textarea
                      id="po-notes"
                      v-model.trim="form.notes"
                      class="field-input field-textarea"
                      rows="2"
                      placeholder="Delivery instructions, quality requirements…"
                    ></textarea>
                  </div>
                </div>

                <p v-if="error" class="form-error" role="alert">{{ error }}</p>
              </form>
            </template>

            <!-- VIEW MODE -->
            <template v-else>
              <div v-if="loading" class="state-message">Loading purchase order…</div>
              <div v-else-if="error" class="state-message error">{{ error }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">PO Number</div>
                  <div class="info-value po-id">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Status</div>
                  <div class="info-value">
                    <span class="badge" :class="statusClass(purchaseOrder.status)">{{ purchaseOrder.status }}</span>
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
                  <div class="info-value">{{ formatUSD(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Order Total</div>
                  <div class="info-value">{{ formatUSD(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
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
                  <div class="info-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </template>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="close">
              {{ mode === 'view' ? 'Close' : 'Cancel' }}
            </button>
            <button
              v-if="mode !== 'view'"
              type="button"
              class="btn-primary"
              :disabled="!canSubmit || submitting"
              @click="submit"
            >
              {{ submitting ? 'Creating…' : 'Create Purchase Order' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
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
    default: 'create'
  }
})

const emit = defineEmits(['close', 'po-created'])

const submitting = ref(false)
const loading = ref(false)
const error = ref(null)
const purchaseOrder = ref(null)

const form = reactive({
  supplier_name: '',
  quantity: 0,
  unit_cost: null,
  expected_delivery_date: '',
  notes: ''
})

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const orderTotal = computed(() => {
  const qty = Number(form.quantity) || 0
  const cost = Number(form.unit_cost) || 0
  return qty * cost
})

const canSubmit = computed(() => {
  return (
    form.supplier_name.length > 0 &&
    Number(form.quantity) >= 1 &&
    form.unit_cost !== null &&
    Number(form.unit_cost) >= 0 &&
    form.expected_delivery_date !== ''
  )
})

// Default the expected delivery date to two weeks out, formatted YYYY-MM-DD for
// the native date input (the backend stores it verbatim as a string).
const defaultDeliveryDate = () => {
  const d = new Date()
  d.setDate(d.getDate() + 14)
  return d.toISOString().slice(0, 10)
}

const resetForm = () => {
  form.supplier_name = ''
  form.quantity = shortage.value > 0 ? shortage.value : 1
  form.unit_cost = null
  form.expected_delivery_date = defaultDeliveryDate()
  form.notes = ''
  error.value = null
}

const loadPurchaseOrder = async () => {
  if (!props.backlogItem) return
  try {
    loading.value = true
    error.value = null
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    error.value = 'Failed to load purchase order'
    console.error('Load PO error:', err)
  } finally {
    loading.value = false
  }
}

// Initialize whenever the modal opens (or its item/mode changes): seed the
// create form, or fetch the existing PO for view mode.
watch(
  () => [props.isOpen, props.mode, props.backlogItem],
  () => {
    if (!props.isOpen) return
    if (props.mode === 'view') {
      loadPurchaseOrder()
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

const submit = async () => {
  if (!canSubmit.value || submitting.value || !props.backlogItem) return
  try {
    submitting.value = true
    error.value = null
    const poData = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name,
      quantity: Number(form.quantity),
      unit_cost: Number(form.unit_cost),
      expected_delivery_date: form.expected_delivery_date,
      notes: form.notes || null
    })
    emit('po-created', poData)
    emit('close')
  } catch (err) {
    error.value = 'Failed to create purchase order. Please try again.'
    console.error('Create PO error:', err)
  } finally {
    submitting.value = false
  }
}

const close = () => {
  emit('close')
}

const formatUSD = (value) => {
  const n = Number(value) || 0
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const statusClass = (status) => {
  const s = (status || '').toLowerCase()
  if (s === 'delivered' || s === 'completed') return 'success'
  if (s === 'pending' || s === 'processing') return 'warning'
  return 'info'
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

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.header-title-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.po-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: #1e293b;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
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

.item-context {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.item-context-text {
  min-width: 0;
}

.item-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.375rem 0;
}

.item-sku {
  font-size: 0.875rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.priority-badge {
  padding: 0.375rem 0.875rem;
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

.context-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.75rem;
}

.summary-card {
  padding: 1rem 1.25rem;
  border-radius: 10px;
  border: 2px solid;
}

.summary-card.danger {
  border-color: #fecaca;
  background: #fef2f2;
}

.summary-card.accent {
  border-color: #bfdbfe;
  background: #eff6ff;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  margin-bottom: 0.375rem;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.summary-card.danger .summary-value {
  color: #dc2626;
}

.summary-card.accent .summary-value {
  color: #2563eb;
}

/* Form */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
}

.field-wide {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.field-label .optional {
  text-transform: none;
  letter-spacing: 0;
  font-weight: 500;
  color: #94a3b8;
}

.field-input {
  width: 100%;
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  background: white;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.field-input::placeholder {
  color: #94a3b8;
}

.field-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
}

.field-textarea {
  resize: vertical;
  min-height: 2.5rem;
}

.field-static {
  padding: 0.625rem 0;
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.form-error {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  font-size: 0.875rem;
}

/* View mode */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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

.info-value.po-id {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
}

.badge.success {
  background: #dcfce7;
  color: #166534;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.state-message {
  padding: 2rem 0;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.state-message.error {
  color: #991b1b;
}

/* Footer */
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
  font-weight: 600;
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
  opacity: 0.55;
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

@media (prefers-reduced-motion: reduce) {
  .modal-enter-active,
  .modal-leave-active,
  .modal-enter-active .modal-container,
  .modal-leave-active .modal-container {
    transition: none;
  }
}

@media (max-width: 560px) {
  .form-grid,
  .context-summary {
    grid-template-columns: 1fr;
  }
}
</style>
