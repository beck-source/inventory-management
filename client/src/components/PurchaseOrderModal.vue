<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'create' ? t('purchaseOrder.createTitle') : t('purchaseOrder.viewTitle') }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-summary">
              <div class="item-summary-row">
                <span class="item-summary-label">{{ t('purchaseOrder.itemLabel') }}</span>
                <span class="item-summary-value">{{ translateProductName(backlogItem.item_name) }}</span>
              </div>
              <div class="item-summary-row">
                <span class="item-summary-label">{{ t('purchaseOrder.skuLabel') }}</span>
                <span class="item-summary-value sku">{{ backlogItem.item_sku }}</span>
              </div>
              <div class="item-summary-row">
                <span class="item-summary-label">{{ t('purchaseOrder.shortageLabel') }}</span>
                <span class="item-summary-value danger">{{ shortage }} {{ t('dashboard.inventoryShortages.unitsShort') }}</span>
              </div>
            </div>

            <!-- Create Mode -->
            <form v-if="mode === 'create'" class="po-form" @submit.prevent="handleSubmit">
              <div class="form-row">
                <div class="form-group flex-1">
                  <label for="po-supplier">{{ t('purchaseOrder.supplierName') }}</label>
                  <input
                    id="po-supplier"
                    v-model="formData.supplierName"
                    type="text"
                    :placeholder="t('purchaseOrder.supplierNamePlaceholder')"
                    class="po-input"
                    required
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input
                    id="po-quantity"
                    v-model.number="formData.quantity"
                    type="number"
                    min="1"
                    class="po-input"
                    required
                  />
                </div>

                <div class="form-group">
                  <label for="po-unit-cost">{{ t('purchaseOrder.unitCost') }}</label>
                  <input
                    id="po-unit-cost"
                    v-model.number="formData.unitCost"
                    type="number"
                    min="0"
                    step="0.01"
                    class="po-input"
                    required
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group flex-1">
                  <label for="po-delivery-date">{{ t('purchaseOrder.expectedDeliveryDate') }}</label>
                  <input
                    id="po-delivery-date"
                    v-model="formData.expectedDeliveryDate"
                    type="date"
                    class="po-input"
                    required
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group flex-1">
                  <label for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                  <textarea
                    id="po-notes"
                    v-model="formData.notes"
                    :placeholder="t('purchaseOrder.notesPlaceholder')"
                    class="po-textarea"
                    rows="3"
                  ></textarea>
                </div>
              </div>

              <div v-if="submitError" class="form-error">{{ submitError }}</div>
            </form>

            <!-- View Mode -->
            <div v-else class="po-view">
              <div v-if="viewLoading" class="po-status-message">{{ t('purchaseOrder.loading') }}</div>
              <div v-else-if="viewError" class="po-status-message error">{{ viewError }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplier') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value">
                    <span class="badge status">{{ purchaseOrder.status }}</span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrder.quantity }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ formatCurrency(purchaseOrder.unit_cost, selectedCurrency) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.totalCost') }}</div>
                  <div class="info-value">{{ formatCurrency(purchaseOrder.quantity * purchaseOrder.unit_cost, selectedCurrency) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDeliveryDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div v-if="purchaseOrder.notes" class="info-item full-width">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="submitting"
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
import { api } from '../api'
import { formatCurrency } from '../utils/currency'

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
      default: 'create'
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentLocale, currentCurrency, translateProductName } = useI18n()

    const submitting = ref(false)
    const submitError = ref(null)

    const viewLoading = ref(false)
    const viewError = ref(null)
    const purchaseOrder = ref(null)

    const defaultFormData = () => ({
      supplierName: '',
      quantity: shortage.value > 0 ? shortage.value : 1,
      unitCost: 0,
      expectedDeliveryDate: '',
      notes: ''
    })

    const formData = ref({
      supplierName: '',
      quantity: 1,
      unitCost: 0,
      expectedDeliveryDate: '',
      notes: ''
    })

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
    })

    const resetForm = () => {
      submitError.value = null
      formData.value = defaultFormData()
    }

    const loadPurchaseOrder = async () => {
      if (!props.backlogItem) return
      viewLoading.value = true
      viewError.value = null
      purchaseOrder.value = null
      try {
        purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        viewError.value = t('purchaseOrder.notFound')
        console.error('Failed to load purchase order:', err)
      } finally {
        viewLoading.value = false
      }
    }

    watch(() => props.isOpen, (open) => {
      if (!open || !props.backlogItem) return
      if (props.mode === 'create') {
        resetForm()
      } else {
        loadPurchaseOrder()
      }
    })

    const close = () => {
      emit('close')
    }

    const handleSubmit = async () => {
      if (!props.backlogItem) return
      submitting.value = true
      submitError.value = null
      try {
        const response = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: formData.value.supplierName,
          quantity: formData.value.quantity,
          unit_cost: formData.value.unitCost,
          expected_delivery_date: formData.value.expectedDeliveryDate,
          notes: formData.value.notes || null
        })
        emit('po-created', response)
      } catch (err) {
        submitError.value = t('purchaseOrder.createError')
        console.error('Failed to create purchase order:', err)
      } finally {
        submitting.value = false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return '-'
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'long', day: 'numeric' })
    }

    return {
      t,
      shortage,
      formData,
      submitting,
      submitError,
      viewLoading,
      viewError,
      purchaseOrder,
      close,
      handleSubmit,
      formatDate,
      formatCurrency,
      selectedCurrency: currentCurrency,
      translateProductName
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
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.item-summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.item-summary-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.item-summary-value {
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
  text-align: right;
}

.item-summary-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.item-summary-value.danger {
  color: #dc2626;
}

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
  transition: border-color 0.2s ease;
  font-family: inherit;
}

.po-input:focus,
.po-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.po-textarea {
  resize: vertical;
}

.form-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
}

.po-view {
  min-height: 100px;
}

.po-status-message {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.95rem;
}

.po-status-message.error {
  color: #991b1b;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.5rem;
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
  margin-bottom: 0.375rem;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.badge.status {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.813rem;
  font-weight: 600;
  background: #fef3c7;
  color: #92400e;
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
