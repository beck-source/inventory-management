<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order Details' }}</h3>
            <button class="close-button" type="button" aria-label="Close" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-header">
              <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
              <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
            </div>

            <div v-if="loading" class="state-message">Loading...</div>
            <div v-else-if="loadError" class="state-message error">{{ loadError }}</div>

            <!-- Create mode -->
            <form v-else-if="mode === 'create'" id="po-form" class="po-form" @submit.prevent="submit">
              <div class="form-field">
                <label for="po-supplier">Supplier Name</label>
                <input id="po-supplier" v-model.trim="form.supplier_name" type="text" required />
              </div>
              <div class="form-row">
                <div class="form-field">
                  <label for="po-quantity">Quantity</label>
                  <input id="po-quantity" v-model.number="form.quantity" type="number" min="1" step="1" required />
                </div>
                <div class="form-field">
                  <label for="po-cost">Unit Cost</label>
                  <input id="po-cost" v-model.number="form.unit_cost" type="number" min="0" step="0.01" required />
                </div>
              </div>
              <div class="form-field">
                <label for="po-date">Expected Delivery Date</label>
                <input id="po-date" v-model="form.expected_delivery_date" type="date" required />
              </div>
              <div class="form-field">
                <label for="po-notes">Notes</label>
                <textarea id="po-notes" v-model="form.notes" rows="3"></textarea>
              </div>
              <div v-if="submitError" class="state-message error">{{ submitError }}</div>
            </form>

            <!-- View mode -->
            <div v-else-if="purchaseOrder" class="info-grid">
              <div v-for="row in viewRows" :key="row.key" class="info-item">
                <div class="info-label">{{ row.label }}</div>
                <div class="info-value">{{ row.value }}</div>
              </div>
            </div>
            <div v-else class="state-message">No purchase order found.</div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="close">
              {{ mode === 'create' ? 'Cancel' : 'Close' }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              type="submit"
              form="po-form"
              :disabled="submitting"
            >
              {{ submitting ? 'Creating...' : 'Create Purchase Order' }}
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
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: {
    type: String,
    default: 'create',
    validator: (v) => ['create', 'view'].includes(v)
  }
})

const emit = defineEmits(['close', 'po-created'])

const loading = ref(false)
const loadError = ref(null)
const submitting = ref(false)
const submitError = ref(null)
const purchaseOrder = ref(null)

const form = reactive({
  supplier_name: '',
  quantity: 1,
  unit_cost: 0,
  expected_delivery_date: '',
  notes: ''
})

const resetForm = () => {
  const item = props.backlogItem
  const shortage = item ? (item.quantity_needed || 0) - (item.quantity_available || 0) : 0
  form.supplier_name = ''
  form.quantity = Math.max(shortage, 1)
  form.unit_cost = 0
  form.expected_delivery_date = ''
  form.notes = ''
  submitError.value = null
}

const loadPO = async () => {
  loading.value = true
  loadError.value = null
  purchaseOrder.value = null
  try {
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    loadError.value = 'Failed to load purchase order'
    console.error('Failed to load purchase order:', err)
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.isOpen, props.backlogItem?.id, props.mode],
  () => {
    if (!props.isOpen || !props.backlogItem) return
    loadError.value = null
    if (props.mode === 'view') {
      loadPO()
    } else {
      loading.value = false
      resetForm()
    }
  },
  { immediate: true }
)

const submit = async () => {
  submitting.value = true
  submitError.value = null
  try {
    const po = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name,
      quantity: form.quantity,
      unit_cost: form.unit_cost,
      expected_delivery_date: form.expected_delivery_date,
      notes: form.notes
    })
    emit('po-created', po)
  } catch (err) {
    submitError.value = 'Failed to create purchase order'
    console.error('Failed to create purchase order:', err)
  } finally {
    submitting.value = false
  }
}

const close = () => emit('close')

const formatDate = (value) => {
  if (!value) return 'N/A'
  const date = new Date(value)
  if (isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const viewRows = computed(() => {
  const po = purchaseOrder.value
  if (!po) return []
  const total = (Number(po.quantity) || 0) * (Number(po.unit_cost) || 0)
  return [
    { key: 'id', label: 'PO Number', value: po.id },
    { key: 'status', label: 'Status', value: po.status || 'N/A' },
    { key: 'supplier', label: 'Supplier', value: po.supplier_name },
    { key: 'quantity', label: 'Quantity', value: `${po.quantity} units` },
    { key: 'unit_cost', label: 'Unit Cost', value: `$${Number(po.unit_cost || 0).toFixed(2)}` },
    { key: 'total', label: 'Total Cost', value: `$${total.toFixed(2)}` },
    { key: 'delivery', label: 'Expected Delivery', value: formatDate(po.expected_delivery_date) },
    { key: 'created', label: 'Created', value: formatDate(po.created_date) },
    { key: 'notes', label: 'Notes', value: po.notes || 'None' }
  ]
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
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

.item-header {
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
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
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: #64748b;
  box-shadow: 0 0 0 3px rgba(100, 116, 139, 0.15);
}

.state-message {
  padding: 1rem;
  color: #64748b;
  text-align: center;
  font-size: 0.938rem;
}

.state-message.error {
  color: #991b1b;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
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
