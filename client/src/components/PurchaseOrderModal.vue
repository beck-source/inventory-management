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
            <!-- Read-only backlog item context, shown in both modes -->
            <div class="backlog-context">
              <div class="context-header">
                <div>
                  <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
                  <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
                </div>
                <span class="priority-badge" :class="backlogItem.priority">
                  {{ t(`priority.${backlogItem.priority}`) }}
                </span>
              </div>

              <div class="context-grid">
                <div class="context-item">
                  <div class="context-label">{{ t('purchaseOrder.backlogContext.orderId') }}</div>
                  <div class="context-value order-id">{{ backlogItem.order_id }}</div>
                </div>
                <div class="context-item">
                  <div class="context-label">{{ t('purchaseOrder.backlogContext.quantityNeeded') }}</div>
                  <div class="context-value">{{ backlogItem.quantity_needed }}</div>
                </div>
                <div class="context-item">
                  <div class="context-label">{{ t('purchaseOrder.backlogContext.quantityAvailable') }}</div>
                  <div class="context-value">{{ backlogItem.quantity_available }}</div>
                </div>
                <div class="context-item">
                  <div class="context-label">{{ t('purchaseOrder.backlogContext.shortage') }}</div>
                  <div class="context-value shortage">{{ shortage }}</div>
                </div>
              </div>
            </div>

            <div class="modal-divider"></div>

            <!-- Create mode: purchase order form -->
            <template v-if="mode === 'create'">
              <div v-if="submitError" class="error-banner">{{ submitError }}</div>

              <form class="po-form" @submit.prevent="handleSubmit">
                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="po-supplier">{{ t('purchaseOrder.form.supplierName') }} *</label>
                    <input
                      id="po-supplier"
                      v-model="form.supplierName"
                      type="text"
                      :placeholder="t('purchaseOrder.form.supplierNamePlaceholder')"
                      class="po-input"
                    />
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label for="po-quantity">{{ t('purchaseOrder.form.quantity') }} *</label>
                    <input
                      id="po-quantity"
                      v-model.number="form.quantity"
                      type="number"
                      min="1"
                      class="po-input"
                    />
                  </div>
                  <div class="form-group">
                    <label for="po-unit-cost">{{ t('purchaseOrder.form.unitCost') }} *</label>
                    <input
                      id="po-unit-cost"
                      v-model.number="form.unitCost"
                      type="number"
                      min="0.01"
                      step="0.01"
                      class="po-input"
                    />
                  </div>
                  <div class="form-group">
                    <label for="po-delivery-date">{{ t('purchaseOrder.form.expectedDeliveryDate') }} *</label>
                    <input
                      id="po-delivery-date"
                      v-model="form.expectedDeliveryDate"
                      type="date"
                      class="po-input"
                    />
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="po-notes">{{ t('purchaseOrder.form.notes') }}</label>
                    <textarea
                      id="po-notes"
                      v-model="form.notes"
                      :placeholder="t('purchaseOrder.form.notesPlaceholder')"
                      class="po-textarea"
                      rows="3"
                    ></textarea>
                  </div>
                </div>
              </form>
            </template>

            <!-- View mode: existing purchase order details -->
            <template v-else>
              <div v-if="viewLoading" class="view-state">{{ t('common.loading') }}</div>
              <div v-else-if="viewError" class="error-banner">{{ viewError }}</div>
              <div v-else-if="purchaseOrderDetails" class="po-details-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.details.supplier') }}</div>
                  <div class="info-value">{{ purchaseOrderDetails.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.details.status') }}</div>
                  <div class="info-value">
                    <span class="status-badge">{{ capitalize(purchaseOrderDetails.status) }}</span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.details.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrderDetails.quantity }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.details.unitCost') }}</div>
                  <div class="info-value">{{ formatCurrencyWithDecimals(purchaseOrderDetails.unit_cost, currentCurrency, 2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.details.total') }}</div>
                  <div class="info-value total">{{ formatCurrencyWithDecimals(totalCost, currentCurrency, 2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.details.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrderDetails.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.details.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrderDetails.created_date) }}</div>
                </div>
                <div class="info-item full-width">
                  <div class="info-label">{{ t('purchaseOrder.details.notes') }}</div>
                  <div class="info-value">{{ purchaseOrderDetails.notes || t('purchaseOrder.details.noNotes') }}</div>
                </div>
              </div>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">
              {{ mode === 'create' ? t('common.cancel') : t('common.close') }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="!isFormValid || submitting"
              @click="handleSubmit"
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
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'
import { api } from '../api'

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    },
    backlogItem: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create'
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentLocale, currentCurrency, translateProductName } = useI18n()

    // Create-mode form state
    const form = ref({
      supplierName: '',
      quantity: null,
      unitCost: null,
      expectedDeliveryDate: '',
      notes: ''
    })
    const submitting = ref(false)
    const submitError = ref(null)

    // View-mode state
    const purchaseOrderDetails = ref(null)
    const viewLoading = ref(false)
    const viewError = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(props.backlogItem.quantity_needed - props.backlogItem.quantity_available, 0)
    })

    const isFormValid = computed(() => {
      return (
        form.value.supplierName.trim().length > 0 &&
        Number(form.value.quantity) > 0 &&
        Number(form.value.unitCost) > 0 &&
        form.value.expectedDeliveryDate.length > 0
      )
    })

    const totalCost = computed(() => {
      if (!purchaseOrderDetails.value) return 0
      return purchaseOrderDetails.value.quantity * purchaseOrderDetails.value.unit_cost
    })

    // Reset the create form each time the modal is opened, defaulting quantity to the shortage amount
    const resetForm = () => {
      form.value = {
        supplierName: '',
        quantity: shortage.value > 0 ? shortage.value : null,
        unitCost: null,
        expectedDeliveryDate: '',
        notes: ''
      }
      submitError.value = null
    }

    // Load PO details for view mode: prefer the object already embedded on the backlog item,
    // otherwise fetch it from the API
    const loadPurchaseOrderDetails = async () => {
      if (!props.backlogItem) return

      if (props.backlogItem.purchase_order) {
        purchaseOrderDetails.value = props.backlogItem.purchase_order
        viewError.value = null
        return
      }

      viewLoading.value = true
      viewError.value = null
      purchaseOrderDetails.value = null
      try {
        purchaseOrderDetails.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        // 404 with a `detail` string is returned when the backlog item has no PO yet
        viewError.value = err.response?.data?.detail || t('purchaseOrder.loadError')
        console.error('Failed to load purchase order:', err)
      } finally {
        viewLoading.value = false
      }
    }

    // Re-initialize state whenever the modal transitions to open, so stale input/data
    // from a previous item never leaks into the next open
    watch(() => props.isOpen, (isNowOpen) => {
      if (!isNowOpen) return
      if (props.mode === 'create') {
        resetForm()
      } else {
        loadPurchaseOrderDetails()
      }
    })

    const close = () => {
      emit('close')
    }

    const handleSubmit = async () => {
      if (!isFormValid.value || submitting.value) return

      submitting.value = true
      submitError.value = null
      try {
        const requestBody = {
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplierName.trim(),
          quantity: Number(form.value.quantity),
          unit_cost: Number(form.value.unitCost),
          expected_delivery_date: form.value.expectedDeliveryDate,
          notes: form.value.notes.trim() ? form.value.notes.trim() : null
        }
        const response = await api.createPurchaseOrder(requestBody)
        emit('po-created', response)
      } catch (err) {
        // FastAPI error responses (404 unknown item, 400 duplicate/invalid quantity or cost,
        // 422 validation) all carry a human-readable `detail` string - prefer that over a
        // generic message so the user knows exactly what to fix
        submitError.value = err.response?.data?.detail || t('purchaseOrder.createError')
        console.error('Failed to create purchase order:', err)
      } finally {
        submitting.value = false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'

      // The backend always sends plain "YYYY-MM-DD" for these fields. `new Date('YYYY-MM-DD')`
      // parses that as UTC midnight (per the ES spec), so in any timezone behind UTC
      // (e.g. UTC-7) toLocaleDateString renders the previous calendar day. Parse the
      // Y-M-D parts ourselves and construct a LOCAL date to sidestep that shift entirely.
      let date
      const dateOnlyMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateString)
      if (dateOnlyMatch) {
        const [, year, month, day] = dateOnlyMatch
        date = new Date(Number(year), Number(month) - 1, Number(day))
      } else {
        // Fall back to normal parsing for full ISO datetimes, which parse as local time
        date = new Date(dateString)
      }

      if (isNaN(date.getTime())) return 'N/A'
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'long', day: 'numeric' })
    }

    const capitalize = (str) => {
      if (!str) return ''
      return str.charAt(0).toUpperCase() + str.slice(1)
    }

    return {
      t,
      currentCurrency,
      translateProductName,
      form,
      submitting,
      submitError,
      purchaseOrderDetails,
      viewLoading,
      viewError,
      shortage,
      isFormValid,
      totalCost,
      close,
      handleSubmit,
      formatDate,
      formatCurrencyWithDecimals,
      capitalize
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
  max-width: 700px;
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

.backlog-context {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.25rem;
}

.context-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1rem;
}

.item-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.25rem 0;
}

.item-sku {
  font-size: 0.813rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.priority-badge {
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
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

.context-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
}

.context-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.context-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.context-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 600;
}

.context-value.order-id {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.context-value.shortage {
  color: #dc2626;
}

.modal-divider {
  height: 1px;
  background: #e2e8f0;
  margin: 1.5rem 0;
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  font-size: 0.875rem;
  margin-bottom: 1.25rem;
}

.view-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.95rem;
}

/* Form */
.po-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.form-group.flex-1 {
  flex: 1;
}

label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.po-input,
.po-textarea {
  padding: 0.75rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  transition: border-color 0.2s ease;
}

.po-input:focus,
.po-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.po-textarea {
  resize: vertical;
}

/* View mode details */
.po-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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

.info-value.total {
  font-weight: 700;
  color: #0f172a;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  background: #dbeafe;
  color: #1e40af;
  text-transform: capitalize;
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
  background: #3b82f6;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
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
