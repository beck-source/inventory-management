<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" :aria-label="t('common.close')" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <div>
                <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <div class="item-shortage">
                {{ t('purchaseOrder.shortage') }}: {{ shortage }} {{ t('purchaseOrder.units') }}
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loadingPO" class="state-message">{{ t('purchaseOrder.loading') }}</div>
              <div v-else-if="loadError" class="error">{{ loadError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poNumber') }}</div>
                  <div class="info-value order-id">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value">
                    <span class="badge info">{{ purchaseOrder.status }}</span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrder.quantity }} {{ t('purchaseOrder.units') }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ formatUsd(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.totalCost') }}</div>
                  <div class="info-value">{{ formatUsd(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div v-if="purchaseOrder.notes" class="info-item notes-item">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value notes-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" novalidate @submit.prevent="submit">
              <div class="form-grid">
                <div class="form-field full" :class="{ invalid: errors.supplier_name }">
                  <label for="po-supplier">{{ t('purchaseOrder.supplier') }}</label>
                  <input id="po-supplier" v-model="form.supplier_name" type="text" maxlength="200" />
                  <span v-if="errors.supplier_name" class="field-error">{{ errors.supplier_name }}</span>
                </div>
                <div class="form-field" :class="{ invalid: errors.quantity }">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model="form.quantity" type="number" min="1" step="1" />
                  <span v-if="errors.quantity" class="field-error">{{ errors.quantity }}</span>
                </div>
                <div class="form-field" :class="{ invalid: errors.unit_cost }">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }}</label>
                  <input id="po-unit-cost" v-model="form.unit_cost" type="number" min="0" step="0.01" />
                  <span v-if="errors.unit_cost" class="field-error">{{ errors.unit_cost }}</span>
                </div>
                <div class="form-field full" :class="{ invalid: errors.expected_delivery_date }">
                  <label for="po-date">{{ t('purchaseOrder.expectedDelivery') }}</label>
                  <input id="po-date" v-model="form.expected_delivery_date" type="date" />
                  <span v-if="errors.expected_delivery_date" class="field-error">{{
                    errors.expected_delivery_date
                  }}</span>
                </div>
                <div class="form-field full" :class="{ invalid: errors.notes }">
                  <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                  <textarea
                    id="po-notes"
                    v-model="form.notes"
                    rows="3"
                    maxlength="1000"
                    :placeholder="t('purchaseOrder.notesPlaceholder')"
                  ></textarea>
                  <span v-if="errors.notes" class="field-error">{{ errors.notes }}</span>
                </div>
              </div>
              <div v-if="submitError" class="error server-error" role="alert">{{ submitError }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
            <button v-if="mode !== 'view'" type="submit" form="po-form" class="btn-primary" :disabled="saving">
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

const { t, currentLocale, translateProductName } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  backlogItem: {
    type: Object,
    default: null,
  },
  // 'create' | 'view'
  mode: {
    type: String,
    default: 'create',
  },
})

const emit = defineEmits(['close', 'po-created'])

const form = reactive({
  supplier_name: '',
  quantity: 1,
  unit_cost: '',
  expected_delivery_date: '',
  notes: '',
})
const errors = reactive({})
const saving = ref(false)
const submitError = ref('')

const purchaseOrder = ref(null)
const loadingPO = ref(false)
const loadError = ref('')

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return Math.max(props.backlogItem.quantity_needed - props.backlogItem.quantity_available, 1)
})

const close = () => {
  emit('close')
}

const extractDetail = (err, fallback) => {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  // FastAPI 422 returns a list of { loc, msg } objects
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = Array.isArray(d.loc) ? d.loc[d.loc.length - 1] : ''
        return field ? `${field}: ${d.msg}` : d.msg
      })
      .join('; ')
  }
  return fallback
}

const resetForm = () => {
  form.supplier_name = ''
  form.quantity = shortage.value
  form.unit_cost = ''
  form.expected_delivery_date = ''
  form.notes = ''
  Object.keys(errors).forEach((k) => delete errors[k])
  submitError.value = ''
  saving.value = false
}

const loadPO = async () => {
  purchaseOrder.value = null
  loadError.value = ''
  loadingPO.value = true
  const itemId = props.backlogItem.id
  try {
    const po = await api.getPurchaseOrderByBacklogItem(itemId)
    // Ignore stale responses if the modal switched items meanwhile
    if (props.backlogItem?.id === itemId) purchaseOrder.value = po
  } catch (err) {
    if (props.backlogItem?.id === itemId) {
      loadError.value = extractDetail(err, t('purchaseOrder.loadError'))
    }
  } finally {
    loadingPO.value = false
  }
}

watch(
  () => [props.isOpen, props.mode, props.backlogItem?.id],
  ([open, mode]) => {
    if (!open || !props.backlogItem) return
    if (mode === 'view') loadPO()
    else resetForm()
  },
  { immediate: true }
)

const isValidDateString = (value) => {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false
  const d = new Date(`${value}T00:00:00`)
  return !isNaN(d.getTime()) && d.toISOString().slice(0, 10) === value
}

const validate = () => {
  Object.keys(errors).forEach((k) => delete errors[k])
  const supplier = form.supplier_name.trim()
  if (!supplier) errors.supplier_name = t('purchaseOrder.errors.supplierRequired')
  else if (supplier.length > 200) errors.supplier_name = t('purchaseOrder.errors.supplierTooLong')

  const qty = Number(form.quantity)
  if (form.quantity === '' || !Number.isInteger(qty) || qty <= 0) {
    errors.quantity = t('purchaseOrder.errors.quantityInvalid')
  }

  const cost = Number(form.unit_cost)
  if (form.unit_cost === '' || form.unit_cost === null || isNaN(cost) || cost < 0) {
    errors.unit_cost = t('purchaseOrder.errors.unitCostInvalid')
  }

  if (!isValidDateString(form.expected_delivery_date)) {
    errors.expected_delivery_date = t('purchaseOrder.errors.dateRequired')
  }

  if (form.notes.length > 1000) errors.notes = t('purchaseOrder.errors.notesTooLong')
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
      quantity: Number(form.quantity),
      unit_cost: Number(form.unit_cost),
      expected_delivery_date: form.expected_delivery_date,
    }
    const notes = form.notes.trim()
    if (notes) payload.notes = notes
    const po = await api.createPurchaseOrder(payload)
    emit('po-created', po)
  } catch (err) {
    submitError.value = extractDetail(err, t('purchaseOrder.saveError'))
  } finally {
    saving.value = false
  }
}

const formatUsd = (amount) => {
  const n = Number(amount)
  if (isNaN(n)) return '-'
  return `$${n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

const formatDate = (value) => {
  if (!value) return '-'
  // Date-only strings are parsed as local time to avoid off-by-one day shifts
  const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00` : value)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
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
  background: var(--overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-4);
}

.modal-container {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
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
  padding: var(--space-6);
  border-bottom: 1px solid var(--border);
}

.modal-title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: all var(--duration) var(--ease);
}

.close-button:hover {
  background: var(--surface-muted);
  color: var(--text);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-8);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-6);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-label {
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.info-value {
  font-size: var(--text-md);
  color: var(--text);
  font-weight: 500;
}

.info-value.order-id,
.info-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: var(--info);
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary {
  padding: var(--space-2) var(--space-5);
  background: var(--surface-muted);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  font-weight: 500;
  font-size: var(--text-base);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--border);
  border-color: var(--border-strong);
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--duration) var(--ease);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--duration) var(--ease);
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}

.item-summary {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--surface-subtle);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
}

.item-name {
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text);
}

.item-sku {
  font-size: var(--text-sm);
  color: var(--text-muted);
  font-family: 'Monaco', 'Courier New', monospace;
}

.item-shortage {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--danger);
  white-space: nowrap;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.form-field.full {
  grid-column: 1 / -1;
}

.form-field label {
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.form-field input,
.form-field textarea {
  padding: var(--space-2) var(--space-3);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: var(--text-base);
  color: var(--text);
}

.form-field input {
  height: var(--control-height);
}

.form-field input:focus,
.form-field textarea:focus {
  outline: none;
  border-color: var(--info);
  box-shadow: 0 0 0 3px var(--info-soft);
}

.form-field.invalid input,
.form-field.invalid textarea {
  border-color: var(--danger);
}

.field-error {
  font-size: var(--text-sm);
  color: var(--danger-ink);
}

.server-error {
  margin: var(--space-4) 0 0;
}

.state-message {
  text-align: center;
  padding: var(--space-8);
  color: var(--text-muted);
}

.badge {
  display: inline-block;
}

.notes-value {
  white-space: pre-wrap;
}
</style>
