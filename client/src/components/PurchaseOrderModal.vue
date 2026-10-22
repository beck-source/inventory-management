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
            <div class="context-grid">
              <div class="info-item">
                <div class="info-label">{{ t('purchaseOrder.sku') }}</div>
                <div class="info-value sku">{{ backlogItem.item_sku }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">{{ t('purchaseOrder.item') }}</div>
                <div class="info-value">{{ translateProductName(backlogItem.item_name) }}</div>
              </div>
              <div class="info-item">
                <div class="info-label">{{ t('purchaseOrder.shortage') }}</div>
                <div class="info-value danger">{{ shortage }} {{ t('purchaseOrder.units') }}</div>
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loadingPO" class="state-message">{{ t('common.loading') }}</div>
              <div v-else-if="errorMessage" class="error-banner">{{ errorMessage }}</div>
              <div v-else-if="existingPO" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poNumber') }}</div>
                  <div class="info-value sku">{{ existingPO.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value"><span class="badge">{{ existingPO.status }}</span></div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                  <div class="info-value">{{ existingPO.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ existingPO.quantity }} {{ t('purchaseOrder.units') }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ formatMoney(existingPO.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.total') }}</div>
                  <div class="info-value">{{ formatMoney(existingPO.quantity * existingPO.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(existingPO.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(existingPO.created_date) }}</div>
                </div>
                <div v-if="existingPO.notes" class="info-item full-width">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value">{{ existingPO.notes }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" @submit.prevent="submit">
              <div class="form-group">
                <label for="po-supplier">{{ t('purchaseOrder.supplier') }}</label>
                <input id="po-supplier" v-model="form.supplier_name" type="text" class="form-input" />
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model.number="form.quantity" type="number" min="1" step="1" class="form-input" />
                </div>
                <div class="form-group">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }}</label>
                  <input id="po-unit-cost" v-model.number="form.unit_cost" type="number" min="0.01" step="0.01" class="form-input" />
                </div>
              </div>

              <div class="form-group">
                <label for="po-date">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input id="po-date" v-model="form.expected_delivery_date" type="date" class="form-input" />
              </div>

              <div class="form-group">
                <label for="po-notes">{{ t('purchaseOrder.notesOptional') }}</label>
                <textarea id="po-notes" v-model="form.notes" rows="3" class="form-input"></textarea>
              </div>

              <div class="total-row">
                <span class="info-label">{{ t('purchaseOrder.total') }}</span>
                <span class="total-value">{{ formatMoney(total) }}</span>
              </div>

              <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode !== 'view'"
              type="submit"
              form="po-form"
              class="btn-primary"
              :disabled="!isValid || submitting"
            >
              {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const emptyForm = () => ({
  supplier_name: '',
  quantity: 1,
  unit_cost: null,
  expected_delivery_date: '',
  notes: ''
})

export default {
  name: 'PurchaseOrderModal',
  props: {
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
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentLocale, translateProductName } = useI18n()

    const form = ref(emptyForm())
    const submitting = ref(false)
    const loadingPO = ref(false)
    const errorMessage = ref('')
    const existingPO = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
    })

    const total = computed(() => {
      const qty = Number(form.value.quantity)
      const cost = Number(form.value.unit_cost)
      return qty > 0 && cost > 0 ? qty * cost : 0
    })

    const isValid = computed(() => {
      const qty = Number(form.value.quantity)
      const cost = Number(form.value.unit_cost)
      return (
        form.value.supplier_name.trim().length > 0 &&
        Number.isInteger(qty) && qty >= 1 &&
        cost > 0 &&
        !!form.value.expected_delivery_date
      )
    })

    const errorFrom = (err) => {
      const detail = err?.response?.data?.detail
      if (typeof detail === 'string') return detail
      // FastAPI validation errors come back as a list of { msg }
      if (Array.isArray(detail)) return detail.map(d => d.msg).join('; ')
      return t('purchaseOrder.genericError')
    }

    const loadPO = async () => {
      loadingPO.value = true
      try {
        existingPO.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        console.error('Failed to load purchase order:', err)
        errorMessage.value = errorFrom(err)
      } finally {
        loadingPO.value = false
      }
    }

    // Reset state each time the modal opens (the component stays mounted between uses)
    watch(
      () => [props.isOpen, props.backlogItem?.id, props.mode],
      ([open]) => {
        if (!open || !props.backlogItem) return
        errorMessage.value = ''
        existingPO.value = null
        submitting.value = false
        if (props.mode === 'view') {
          loadPO()
        } else {
          form.value = { ...emptyForm(), quantity: Math.max(1, shortage.value) }
        }
      },
      { immediate: true }
    )

    const submit = async () => {
      if (!isValid.value || submitting.value) return
      submitting.value = true
      errorMessage.value = ''
      try {
        const payload = {
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplier_name.trim(),
          quantity: Number(form.value.quantity),
          unit_cost: Number(form.value.unit_cost),
          expected_delivery_date: form.value.expected_delivery_date
        }
        const notes = form.value.notes.trim()
        if (notes) payload.notes = notes
        const po = await api.createPurchaseOrder(payload)
        emit('po-created', po)
      } catch (err) {
        console.error('Failed to create purchase order:', err)
        errorMessage.value = errorFrom(err)
      } finally {
        submitting.value = false
      }
    }

    const close = () => {
      emit('close')
    }

    // Costs are entered and stored in USD, so display them in USD regardless of locale
    const formatMoney = (amount) => formatCurrencyWithDecimals(Number(amount) || 0, 'USD', 2)

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      // A bare YYYY-MM-DD is parsed as UTC by Date, which shows the previous day in
      // timezones behind UTC; append a time so it is parsed as local midnight instead.
      const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(dateString)
      const date = new Date(isDateOnly ? `${dateString}T00:00:00` : dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    return {
      t,
      translateProductName,
      form,
      submitting,
      loadingPO,
      errorMessage,
      existingPO,
      shortage,
      total,
      isValid,
      submit,
      close,
      formatMoney,
      formatDate
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

.context-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1.5rem;
  padding: 1.25rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  margin-bottom: 1.5rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.full-width {
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

.info-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.info-value.danger {
  color: #dc2626;
  font-weight: 700;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  background: #dbeafe;
  color: #1e40af;
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
  gap: 0.5rem;
}

label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.form-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  transition: border-color 0.15s ease;
}

.form-input:focus {
  outline: none;
  border-color: #64748b;
}

textarea.form-input {
  resize: vertical;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.error-banner {
  padding: 0.75rem 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #991b1b;
  font-size: 0.875rem;
}

.state-message {
  text-align: center;
  padding: 2rem;
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
