<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Create mode -->
          <form v-if="mode === 'create'" class="po-form" @submit.prevent="submit">
            <div class="modal-body">
              <div class="form-grid">
                <label class="form-field full">
                  <span class="info-label">{{ t('purchaseOrder.supplierName') }}</span>
                  <input v-model="form.supplier_name" type="text" class="form-input" required />
                </label>
                <label class="form-field">
                  <span class="info-label">{{ t('purchaseOrder.quantity') }}</span>
                  <input v-model.number="form.quantity" type="number" min="1" step="1" class="form-input" required />
                </label>
                <label class="form-field">
                  <span class="info-label">{{ t('purchaseOrder.unitCost') }}</span>
                  <input v-model.number="form.unit_cost" type="number" min="0" step="0.01" class="form-input" required />
                </label>
                <label class="form-field full">
                  <span class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</span>
                  <input v-model="form.expected_delivery_date" type="date" class="form-input" required />
                </label>
                <label class="form-field full">
                  <span class="info-label">{{ t('purchaseOrder.notes') }}</span>
                  <textarea v-model="form.notes" rows="3" class="form-input" :placeholder="t('purchaseOrder.notesPlaceholder')"></textarea>
                </label>
              </div>
              <div v-if="error" class="error-message">{{ error }}</div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn-secondary" @click="close">{{ t('common.cancel') }}</button>
              <button type="submit" class="btn-primary" :disabled="!isValid || submitting">
                {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
              </button>
            </div>
          </form>

          <!-- View mode -->
          <template v-else>
            <div class="modal-body">
              <div v-if="loading" class="state-message">{{ t('common.loading') }}</div>
              <div v-else-if="notFound" class="state-message">{{ t('purchaseOrder.noPurchaseOrder') }}</div>
              <div v-else-if="error" class="error-message">{{ error }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div v-for="field in viewFields" :key="field.key" class="info-item">
                  <div class="info-label">{{ field.label }}</div>
                  <div class="info-value">{{ field.value }}</div>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn-secondary" @click="close">{{ t('common.close') }}</button>
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

const { t } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: { type: String, default: 'create' } // 'create' | 'view'
})

const emit = defineEmits(['close', 'po-created'])

const form = ref({})
const submitting = ref(false)
const loading = ref(false)
const error = ref(null)
const notFound = ref(false)
const purchaseOrder = ref(null)

const close = () => emit('close')

// Default quantity is the shortfall, never below 1
const defaultQuantity = () => {
  const item = props.backlogItem
  return Math.max(1, (item?.quantity_needed ?? 0) - (item?.quantity_available ?? 0))
}

const isValid = computed(() => {
  const f = form.value
  return (
    !!f.supplier_name?.trim() &&
    Number.isInteger(f.quantity) && f.quantity >= 1 &&
    typeof f.unit_cost === 'number' && f.unit_cost >= 0 &&
    !!f.expected_delivery_date
  )
})

const submit = async () => {
  if (!isValid.value || submitting.value) return
  submitting.value = true
  error.value = null
  try {
    const created = await api.createPurchaseOrder({
      backlog_item_id: String(props.backlogItem.id),
      supplier_name: form.value.supplier_name.trim(),
      quantity: form.value.quantity,
      unit_cost: form.value.unit_cost,
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes
    })
    emit('po-created', created)
  } catch (err) {
    console.error('Create PO error:', err)
    error.value = t('purchaseOrder.createError')
  } finally {
    submitting.value = false
  }
}

const loadPurchaseOrder = async () => {
  loading.value = true
  try {
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(String(props.backlogItem.id))
  } catch (err) {
    // A 404 just means no PO exists yet for this backlog item; not an error
    if (err?.response?.status === 404) {
      notFound.value = true
    } else {
      console.error('Load PO error:', err)
      error.value = t('purchaseOrder.loadError')
    }
  } finally {
    loading.value = false
  }
}

const formatDate = (value) => {
  if (!value) return 'N/A'
  const date = new Date(value)
  if (isNaN(date.getTime())) return value
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}

const viewFields = computed(() => {
  const po = purchaseOrder.value
  if (!po) return []
  return [
    { key: 'id', label: t('purchaseOrder.id'), value: po.id },
    { key: 'supplier', label: t('purchaseOrder.supplierName'), value: po.supplier_name },
    { key: 'quantity', label: t('purchaseOrder.quantity'), value: po.quantity },
    { key: 'unit_cost', label: t('purchaseOrder.unitCost'), value: po.unit_cost },
    { key: 'expected', label: t('purchaseOrder.expectedDelivery'), value: formatDate(po.expected_delivery_date) },
    { key: 'status', label: t('purchaseOrder.status'), value: po.status },
    { key: 'created', label: t('purchaseOrder.createdDate'), value: formatDate(po.created_date) },
    { key: 'notes', label: t('purchaseOrder.notes'), value: po.notes || '-' }
  ]
})

// Reset all state each time the modal opens, then load data in view mode
watch(
  () => props.isOpen,
  (open) => {
    if (!open || !props.backlogItem) return
    form.value = {
      supplier_name: '',
      quantity: defaultQuantity(),
      unit_cost: 0,
      expected_delivery_date: '',
      notes: ''
    }
    submitting.value = false
    loading.value = false
    error.value = null
    notFound.value = false
    purchaseOrder.value = null
    if (props.mode === 'view') loadPurchaseOrder()
  },
  { immediate: true }
)
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

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field.full {
  grid-column: 1 / -1;
}

.form-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
}

.form-input:focus {
  outline: none;
  border-color: #2563eb;
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

.state-message {
  color: #64748b;
  text-align: center;
  padding: 1rem 0;
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
