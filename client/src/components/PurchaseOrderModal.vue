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

          <div class="modal-body">
            <div class="item-summary">
              <div class="item-name">{{ translateProductName(backlogItem.item_name) }}</div>
              <div class="item-meta">
                SKU: {{ backlogItem.item_sku }} &middot;
                {{ t('purchaseOrder.shortage') }}: {{ shortage }}
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loadingPO" class="state-message">{{ t('common.loading') }}</div>
              <div v-else-if="loadError" class="error-message">{{ loadError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poNumber') }}</div>
                  <div class="info-value mono">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value"><span class="badge">{{ purchaseOrder.status }}</span></div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrder.quantity }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ money(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.total') }}</div>
                  <div class="info-value">{{ money(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div class="info-item full-width">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value notes">{{ purchaseOrder.notes || '-' }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" novalidate @submit.prevent="submit">
              <div class="form-group">
                <label for="po-supplier">{{ t('purchaseOrder.supplier') }}</label>
                <input id="po-supplier" v-model="form.supplier_name" type="text" class="po-input"
                       maxlength="200" :disabled="saving" />
                <div v-if="errors.supplier_name" class="field-error">{{ errors.supplier_name }}</div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model="form.quantity" type="number" min="1" step="1"
                         class="po-input" :disabled="saving" />
                  <div v-if="errors.quantity" class="field-error">{{ errors.quantity }}</div>
                </div>
                <div class="form-group">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }} (USD)</label>
                  <input id="po-unit-cost" v-model="form.unit_cost" type="number" min="0" step="0.01"
                         class="po-input" :disabled="saving" />
                  <div v-if="errors.unit_cost" class="field-error">{{ errors.unit_cost }}</div>
                </div>
              </div>

              <div class="form-group">
                <label for="po-date">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input id="po-date" v-model="form.expected_delivery_date" type="date"
                       class="po-input" :disabled="saving" />
                <div v-if="errors.expected_delivery_date" class="field-error">{{ errors.expected_delivery_date }}</div>
              </div>

              <div class="form-group">
                <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                <textarea id="po-notes" v-model="form.notes" rows="3" class="po-input"
                          maxlength="2000" :disabled="saving"></textarea>
                <div v-if="errors.notes" class="field-error">{{ errors.notes }}</div>
              </div>

              <div class="total-row">
                <span class="info-label">{{ t('purchaseOrder.total') }}</span>
                <span class="total-value">{{ money(total) }}</span>
              </div>

              <div v-if="submitError" class="error-message">{{ submitError }}</div>
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

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: { type: Boolean, default: false },
    backlogItem: { type: Object, default: null },
    mode: { type: String, default: 'create', validator: (v) => ['create', 'view'].includes(v) }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, translateProductName, currentCurrency } = useI18n()

    const form = ref({})
    const errors = ref({})
    const submitError = ref('')
    const saving = ref(false)
    const purchaseOrder = ref(null)
    const loadingPO = ref(false)
    const loadError = ref('')
    // Guards against a stale response overwriting state after the modal is reopened for another item
    let requestToken = 0

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
    })

    const total = computed(() => {
      const q = Number(form.value.quantity)
      const c = Number(form.value.unit_cost)
      return Number.isFinite(q) && Number.isFinite(c) ? q * c : 0
    })

    const money = (amount) => formatCurrencyWithDecimals(Number(amount) || 0, currentCurrency.value, 2)

    const formatDate = (value) => {
      if (!value) return 'N/A'
      // Date-only strings parse as UTC; append time so the local day is not shifted
      const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00` : value)
      if (isNaN(date.getTime())) return 'N/A'
      return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
    }

    const resetState = () => {
      requestToken++
      form.value = {
        supplier_name: '',
        quantity: shortage.value >= 1 ? shortage.value : 1,
        unit_cost: '',
        expected_delivery_date: '',
        notes: ''
      }
      errors.value = {}
      submitError.value = ''
      saving.value = false
      purchaseOrder.value = null
      loadError.value = ''
      loadingPO.value = false
    }

    const loadPO = async () => {
      if (!props.backlogItem) return
      const token = ++requestToken
      loadingPO.value = true
      try {
        const po = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
        if (token === requestToken) purchaseOrder.value = po
      } catch (err) {
        if (token !== requestToken) return
        loadError.value = err.response?.data?.detail || t('purchaseOrder.loadFailed')
        console.error('Failed to load purchase order:', err)
      } finally {
        if (token === requestToken) loadingPO.value = false
      }
    }

    // Mirrors backend rules: supplier 1-200 chars, quantity >= 1, unit_cost > 0, notes <= 2000
    const validate = () => {
      const e = {}
      const supplier = form.value.supplier_name.trim()
      if (supplier.length < 1 || supplier.length > 200) e.supplier_name = t('purchaseOrder.errSupplier')
      const q = Number(form.value.quantity)
      if (form.value.quantity === '' || !Number.isInteger(q) || q < 1) e.quantity = t('purchaseOrder.errQuantity')
      const c = Number(form.value.unit_cost)
      if (form.value.unit_cost === '' || !Number.isFinite(c) || c <= 0) e.unit_cost = t('purchaseOrder.errUnitCost')
      const d = form.value.expected_delivery_date
      if (!d || isNaN(new Date(`${d}T00:00:00`).getTime())) e.expected_delivery_date = t('purchaseOrder.errDate')
      if (form.value.notes.length > 2000) e.notes = t('purchaseOrder.errNotes')
      errors.value = e
      return Object.keys(e).length === 0
    }

    const submit = async () => {
      if (saving.value) return
      submitError.value = ''
      if (!validate()) return
      saving.value = true
      const token = requestToken
      try {
        const po = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplier_name.trim(),
          quantity: Number(form.value.quantity),
          unit_cost: Number(form.value.unit_cost),
          expected_delivery_date: form.value.expected_delivery_date,
          notes: form.value.notes
        })
        emit('po-created', po)
      } catch (err) {
        if (token !== requestToken) return
        const detail = err.response?.data?.detail
        // FastAPI 422 detail can be an array of objects; only show plain strings
        submitError.value = typeof detail === 'string' ? detail : t('purchaseOrder.createFailed')
        console.error('Failed to create purchase order:', err)
      } finally {
        if (token === requestToken) saving.value = false
      }
    }

    const close = () => emit('close')

    const onKeydown = (e) => {
      if (e.key === 'Escape' && props.isOpen) close()
    }

    watch(() => props.isOpen, (open) => {
      if (!open) return
      resetState()
      if (props.mode === 'view') loadPO()
    }, { immediate: true })

    onMounted(() => document.addEventListener('keydown', onKeydown))
    onUnmounted(() => document.removeEventListener('keydown', onKeydown))

    return {
      t, translateProductName, form, errors, submitError, saving, purchaseOrder,
      loadingPO, loadError, shortage, total, money, formatDate, submit, close
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
  font-size: 0.875rem;
  color: #64748b;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
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

.po-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  font-family: inherit;
  color: #0f172a;
  background: white;
}

.po-input:focus {
  outline: none;
  border-color: #64748b;
}

.po-input:disabled {
  background: #f8fafc;
  color: #64748b;
}

textarea.po-input {
  resize: vertical;
}

.field-error {
  font-size: 0.813rem;
  color: #dc2626;
}

.error-message {
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

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.total-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
  min-width: 0;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-value {
  font-size: 0.938rem;
  font-weight: 500;
  color: #0f172a;
  overflow-wrap: anywhere;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
}

.info-value.notes {
  white-space: pre-wrap;
  font-weight: 400;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: capitalize;
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
