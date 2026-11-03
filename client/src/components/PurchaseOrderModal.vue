<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" type="button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
              <div class="item-meta">
                SKU: {{ backlogItem.item_sku }} &middot; {{ backlogItem.order_id }} &middot;
                {{ t('purchaseOrder.shortage') }}: {{ shortage }}
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loading" class="state-message">{{ t('purchaseOrder.loadingPO') }}</div>
              <div v-else-if="notFound" class="state-message warning">{{ t('purchaseOrder.notFound') }}</div>
              <div v-else-if="loadError" class="state-message danger">{{ loadError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div v-for="field in viewFields" :key="field.key" class="info-item">
                  <div class="info-label">{{ field.label }}</div>
                  <div class="info-value">
                    <span v-if="field.key === 'status'" class="badge" :class="statusClass">{{ field.value }}</span>
                    <template v-else>{{ field.value }}</template>
                  </div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" novalidate @submit.prevent="submit">
              <div class="form-group">
                <label for="po-supplier">{{ t('purchaseOrder.supplierName') }}</label>
                <input id="po-supplier" v-model="form.supplier_name" type="text" :class="{ invalid: errors.supplier_name }" />
                <div v-if="errors.supplier_name" class="field-error">{{ errors.supplier_name }}</div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model.number="form.quantity" type="number" min="1" step="1" :class="{ invalid: errors.quantity }" />
                  <div v-if="errors.quantity" class="field-error">{{ errors.quantity }}</div>
                </div>
                <div class="form-group">
                  <label for="po-cost">{{ t('purchaseOrder.unitCost') }}</label>
                  <input id="po-cost" v-model="form.unit_cost" type="number" min="0" step="0.01" :class="{ invalid: errors.unit_cost }" />
                  <div v-if="errors.unit_cost" class="field-error">{{ errors.unit_cost }}</div>
                </div>
              </div>

              <div class="form-group">
                <label for="po-date">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input id="po-date" v-model="form.expected_delivery_date" type="date" :class="{ invalid: errors.expected_delivery_date }" />
                <div v-if="errors.expected_delivery_date" class="field-error">{{ errors.expected_delivery_date }}</div>
              </div>

              <div class="form-group">
                <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                <textarea id="po-notes" v-model="form.notes" rows="3"></textarea>
              </div>

              <div v-if="submitError" class="state-message danger" role="alert">{{ submitError }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode !== 'view'"
              class="btn-primary"
              type="submit"
              form="po-form"
              :disabled="saving"
            >
              {{ saving ? t('purchaseOrder.saving') : t('purchaseOrder.submit') }}
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

const { t, translateProductName } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: { type: String, default: 'create' }
})

const emit = defineEmits(['close', 'po-created'])

const form = reactive({
  supplier_name: '',
  quantity: 1,
  unit_cost: '',
  expected_delivery_date: '',
  notes: ''
})
const errors = reactive({})
const saving = ref(false)
const submitError = ref('')

const purchaseOrder = ref(null)
const loading = ref(false)
const notFound = ref(false)
const loadError = ref('')

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
})

const statusClass = computed(() => {
  const s = (purchaseOrder.value?.status || '').toLowerCase()
  if (s === 'received' || s === 'delivered') return 'success'
  if (s === 'cancelled') return 'danger'
  if (s === 'pending') return 'warning'
  return 'info'
})

const formatDate = (value) => {
  if (!value) return 'N/A'
  const d = new Date(value)
  if (isNaN(d.getTime())) return value
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const formatMoney = (n) => Number(n).toLocaleString('en-US', { style: 'currency', currency: 'USD' })

const viewFields = computed(() => {
  const po = purchaseOrder.value
  if (!po) return []
  const fields = [
    { key: 'id', label: t('purchaseOrder.poNumber'), value: po.id },
    { key: 'status', label: t('purchaseOrder.status'), value: po.status },
    { key: 'supplier_name', label: t('purchaseOrder.supplierName'), value: po.supplier_name },
    { key: 'quantity', label: t('purchaseOrder.quantity'), value: po.quantity },
    { key: 'unit_cost', label: t('purchaseOrder.unitCost'), value: formatMoney(po.unit_cost) },
    { key: 'total', label: t('purchaseOrder.totalCost'), value: formatMoney(po.quantity * po.unit_cost) },
    { key: 'expected_delivery_date', label: t('purchaseOrder.expectedDelivery'), value: formatDate(po.expected_delivery_date) },
    { key: 'created_date', label: t('purchaseOrder.createdDate'), value: formatDate(po.created_date) }
  ]
  if (po.notes) fields.push({ key: 'notes', label: t('purchaseOrder.notes'), value: po.notes })
  return fields
})

const loadPO = async () => {
  loading.value = true
  try {
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    // A 404 just means no PO exists yet; anything else is a real load failure
    if (err?.response?.status === 404) {
      notFound.value = true
    } else {
      loadError.value = t('purchaseOrder.loadError')
      console.error('Failed to load purchase order:', err)
    }
  } finally {
    loading.value = false
  }
}

// Reset all state, then load data if in view mode. Runs on open and on item/mode change.
const reset = () => {
  Object.keys(errors).forEach((k) => delete errors[k])
  submitError.value = ''
  saving.value = false
  purchaseOrder.value = null
  notFound.value = false
  loadError.value = ''
  loading.value = false
  form.supplier_name = ''
  form.unit_cost = ''
  form.expected_delivery_date = ''
  form.notes = ''
  // Default quantity is the shortage, but never below the minimum of 1
  form.quantity = Math.max(1, shortage.value)

  if (props.isOpen && props.backlogItem && props.mode === 'view') loadPO()
}

watch(() => [props.isOpen, props.backlogItem, props.mode], () => {
  if (props.isOpen) reset()
}, { immediate: true })

const validate = () => {
  Object.keys(errors).forEach((k) => delete errors[k])
  if (!form.supplier_name.trim()) errors.supplier_name = t('purchaseOrder.supplierRequired')
  if (!Number.isInteger(form.quantity) || form.quantity < 1) errors.quantity = t('purchaseOrder.quantityInvalid')
  if (form.unit_cost === '' || form.unit_cost === null) {
    errors.unit_cost = t('purchaseOrder.unitCostRequired')
  } else if (isNaN(Number(form.unit_cost)) || Number(form.unit_cost) < 0) {
    errors.unit_cost = t('purchaseOrder.unitCostInvalid')
  }
  if (!form.expected_delivery_date) errors.expected_delivery_date = t('purchaseOrder.deliveryRequired')
  return Object.keys(errors).length === 0
}

const submit = async () => {
  if (saving.value) return
  submitError.value = ''
  if (!validate()) return

  saving.value = true
  try {
    const payload = {
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.supplier_name.trim(),
      quantity: form.quantity,
      unit_cost: Number(form.unit_cost),
      expected_delivery_date: form.expected_delivery_date
    }
    if (form.notes.trim()) payload.notes = form.notes.trim()
    const created = await api.createPurchaseOrder(payload)
    emit('po-created', created)
  } catch (err) {
    submitError.value = t('purchaseOrder.submitError')
    console.error('Failed to create purchase order:', err)
  } finally {
    saving.value = false
  }
}

const close = () => {
  emit('close')
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
  padding: 1.5rem 2rem;
}

.item-summary {
  padding-bottom: 1rem;
  margin-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.item-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.item-meta {
  margin-top: 0.25rem;
  font-size: 0.813rem;
  color: #64748b;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label,
.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.form-group input,
.form-group textarea {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.form-group input.invalid {
  border-color: #ef4444;
}

.field-error {
  font-size: 0.813rem;
  color: #dc2626;
}

.state-message {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  background: #f1f5f9;
  color: #64748b;
}

.state-message.warning {
  background: #fffbeb;
  color: #92400e;
}

.state-message.danger {
  background: #fef2f2;
  color: #991b1b;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.25rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
  overflow-wrap: anywhere;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
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
