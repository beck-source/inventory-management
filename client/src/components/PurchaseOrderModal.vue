<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="$emit('close')">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" :aria-label="t('common.close')" @click="$emit('close')">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" />
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div v-if="backlogItem" class="po-item">
              <div class="po-item-name">{{ translateProductName(backlogItem.item_name) }}</div>
              <div class="po-item-meta">
                {{ backlogItem.item_sku }} &middot; {{ backlogItem.order_id }} &middot;
                {{ t('purchaseOrder.shortage', { count: shortage }) }}
              </div>
            </div>

            <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
            <p v-else-if="error" class="error">{{ error }}</p>

            <!-- View mode: the order already exists -->
            <dl v-else-if="mode === 'view' && purchaseOrder" class="po-grid">
              <div class="po-field">
                <dt>{{ t('purchaseOrder.poNumber') }}</dt>
                <dd>{{ purchaseOrder.id }}</dd>
              </div>
              <div class="po-field">
                <dt>{{ t('purchaseOrder.status') }}</dt>
                <dd><span class="badge info">{{ purchaseOrder.status }}</span></dd>
              </div>
              <div class="po-field">
                <dt>{{ t('purchaseOrder.supplier') }}</dt>
                <dd>{{ purchaseOrder.supplier_name }}</dd>
              </div>
              <div class="po-field">
                <dt>{{ t('purchaseOrder.quantity') }}</dt>
                <dd>{{ purchaseOrder.quantity.toLocaleString() }}</dd>
              </div>
              <div class="po-field">
                <dt>{{ t('purchaseOrder.unitCost') }}</dt>
                <dd>{{ formatUnitCost(purchaseOrder.unit_cost) }}</dd>
              </div>
              <div class="po-field">
                <dt>{{ t('purchaseOrder.total') }}</dt>
                <dd><strong>{{ formatCurrency(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</strong></dd>
              </div>
              <div class="po-field">
                <dt>{{ t('purchaseOrder.expectedDelivery') }}</dt>
                <dd>{{ purchaseOrder.expected_delivery_date }}</dd>
              </div>
              <div class="po-field po-field-wide" v-if="purchaseOrder.notes">
                <dt>{{ t('purchaseOrder.notes') }}</dt>
                <dd>{{ purchaseOrder.notes }}</dd>
              </div>
            </dl>

            <!-- Create mode -->
            <form v-else class="po-form" @submit.prevent="submit">
              <div class="po-row">
                <label class="po-control">
                  <span>{{ t('purchaseOrder.supplier') }}</span>
                  <input v-model="form.supplier_name" type="text" required />
                </label>
                <label class="po-control">
                  <span>{{ t('purchaseOrder.expectedDelivery') }}</span>
                  <input v-model="form.expected_delivery_date" type="date" required />
                </label>
              </div>
              <div class="po-row">
                <label class="po-control">
                  <span>{{ t('purchaseOrder.quantity') }}</span>
                  <input v-model.number="form.quantity" type="number" min="1" required />
                </label>
                <label class="po-control">
                  <span>{{ t('purchaseOrder.unitCost') }}</span>
                  <input v-model.number="form.unit_cost" type="number" min="0" step="0.01" required />
                </label>
              </div>
              <label class="po-control">
                <span>{{ t('purchaseOrder.notes') }}</span>
                <textarea v-model="form.notes" rows="2"></textarea>
              </label>
              <p class="po-total">
                {{ t('purchaseOrder.total') }}: <strong>{{ formatCurrency(estimatedTotal) }}</strong>
              </p>
            </form>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="$emit('close')">{{ t('common.close') }}</button>
            <button
              v-if="mode !== 'view'"
              class="btn-primary"
              :disabled="!canSubmit"
              @click="submit"
            >
              {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import {
  formatCurrency as formatCurrencyUtil,
  formatCurrencyWithDecimals
} from '../utils/currency'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: { type: String, default: 'create' }
})

const emit = defineEmits(['close', 'po-created'])

const { t, currentCurrency, translateProductName } = useI18n()

// Server amounts are USD; convert only at display time.
const formatCurrency = (value) => formatCurrencyUtil(value, currentCurrency.value)
const formatUnitCost = (value) => formatCurrencyWithDecimals(value, currentCurrency.value, 2)

const loading = ref(false)
const submitting = ref(false)
const error = ref(null)
const purchaseOrder = ref(null)

const form = ref({
  supplier_name: '',
  quantity: 0,
  unit_cost: 0,
  expected_delivery_date: '',
  notes: ''
})

const shortage = computed(() =>
  props.backlogItem
    ? props.backlogItem.quantity_needed - props.backlogItem.quantity_available
    : 0
)

const estimatedTotal = computed(() => (form.value.quantity || 0) * (form.value.unit_cost || 0))

const canSubmit = computed(() =>
  !submitting.value &&
  form.value.supplier_name.trim().length > 0 &&
  form.value.quantity > 0 &&
  form.value.unit_cost >= 0 &&
  form.value.expected_delivery_date.length > 0
)

const loadExisting = async () => {
  try {
    loading.value = true
    error.value = null
    purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
  } catch (err) {
    error.value = t('purchaseOrder.loadFailed', { message: err.response?.data?.detail || err.message })
  } finally {
    loading.value = false
  }
}

// Reset on every open so a previous item's values never leak into the next one.
watch(() => [props.isOpen, props.backlogItem, props.mode], () => {
  if (!props.isOpen || !props.backlogItem) return

  error.value = null
  purchaseOrder.value = null

  if (props.mode === 'view') {
    loadExisting()
    return
  }

  form.value = {
    supplier_name: '',
    // Default to the exact shortfall — the most likely quantity to order.
    quantity: shortage.value > 0 ? shortage.value : 1,
    unit_cost: 0,
    expected_delivery_date: '',
    notes: ''
  }
}, { immediate: true })

const submit = async () => {
  if (!canSubmit.value) return

  try {
    submitting.value = true
    error.value = null

    const created = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      supplier_name: form.value.supplier_name,
      quantity: form.value.quantity,
      unit_cost: form.value.unit_cost,
      expected_delivery_date: form.value.expected_delivery_date,
      notes: form.value.notes || null
    })

    emit('po-created', created)
  } catch (err) {
    error.value = t('purchaseOrder.submitFailed', { message: err.response?.data?.detail || err.message })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  z-index: 2000;
}

.modal-container {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.25);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.063rem;
  font-weight: 700;
  color: #0f172a;
}

.close-button {
  display: flex;
  padding: 0.375rem;
  background: none;
  border: none;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.close-button svg {
  width: 18px;
  height: 18px;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
}

.po-item {
  padding: 0.875rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-bottom: 1.25rem;
}

.po-item-name {
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
}

.po-item-meta {
  font-size: 0.813rem;
  color: #64748b;
  margin-top: 0.125rem;
}

.po-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.po-field-wide {
  grid-column: 1 / -1;
}

.po-field dt {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}

.po-field dd {
  font-size: 0.938rem;
  color: #0f172a;
  margin: 0;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.po-row {
  display: flex;
  gap: 1rem;
}

.po-control {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  flex: 1;
}

.po-control > span {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
}

.po-control input,
.po-control textarea {
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.875rem;
  font-family: inherit;
  color: #0f172a;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.po-control input:focus,
.po-control textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.po-total {
  font-size: 0.938rem;
  color: #0f172a;
  padding-top: 0.25rem;
  border-top: 1px solid #e2e8f0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.btn-secondary,
.btn-primary {
  padding: 0.5rem 1.125rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #475569;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.btn-primary {
  background: #3b82f6;
  border: none;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-primary:disabled {
  background: #cbd5e1;
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
</style>
