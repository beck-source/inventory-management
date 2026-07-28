<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order Details' }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Item summary header shown in both modes -->
            <div class="item-header">
              <div class="item-icon">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                  <rect x="3" y="7" width="22" height="17" rx="2" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 7V5a5 5 0 0110 0v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="item-title-section">
                <h4 class="item-name">{{ backlogItem.item_name }}</h4>
                <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} Priority
              </span>
            </div>

            <!-- CREATE MODE: form -->
            <template v-if="mode === 'create'">
              <div class="shortage-summary">
                <div class="summary-card warning">
                  <div class="summary-label">Shortage</div>
                  <div class="summary-value">{{ shortageAmount }} units</div>
                </div>
                <div class="summary-card neutral">
                  <div class="summary-label">Order ID</div>
                  <div class="summary-value order-id">{{ backlogItem.order_id }}</div>
                </div>
              </div>

              <div v-if="errorMessage" class="error-banner">
                {{ errorMessage }}
              </div>

              <form class="po-form" @submit.prevent="submitForm">
                <div class="form-group">
                  <label class="form-label" for="supplier-name">Supplier Name <span class="required">*</span></label>
                  <input
                    id="supplier-name"
                    v-model="form.supplier_name"
                    type="text"
                    class="form-input"
                    placeholder="Enter supplier name"
                    required
                  />
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label" for="quantity">Quantity <span class="required">*</span></label>
                    <input
                      id="quantity"
                      v-model.number="form.quantity"
                      type="number"
                      class="form-input"
                      min="1"
                      required
                    />
                  </div>

                  <div class="form-group">
                    <label class="form-label" for="unit-cost">Unit Cost (USD) <span class="required">*</span></label>
                    <div class="input-prefix-wrapper">
                      <span class="input-prefix">$</span>
                      <input
                        id="unit-cost"
                        v-model.number="form.unit_cost"
                        type="number"
                        class="form-input with-prefix"
                        min="0"
                        step="0.01"
                        placeholder="0.00"
                        required
                      />
                    </div>
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label" for="delivery-date">Expected Delivery Date <span class="required">*</span></label>
                  <input
                    id="delivery-date"
                    v-model="form.expected_delivery_date"
                    type="date"
                    class="form-input"
                    :min="todayDate"
                    required
                  />
                </div>

                <div class="form-group">
                  <label class="form-label" for="notes">Notes <span class="optional">(optional)</span></label>
                  <textarea
                    id="notes"
                    v-model="form.notes"
                    class="form-input form-textarea"
                    rows="3"
                    placeholder="Add any relevant notes..."
                  ></textarea>
                </div>

                <div v-if="form.quantity && form.unit_cost" class="total-cost-row">
                  <span class="total-label">Estimated Total Cost</span>
                  <span class="total-value">{{ formattedTotalCost }}</span>
                </div>
              </form>
            </template>

            <!-- VIEW MODE: read-only display -->
            <template v-else-if="mode === 'view' && purchaseOrder">
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">PO ID</div>
                  <div class="info-value mono">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Status</div>
                  <div class="info-value">
                    <span class="badge" :class="statusBadgeClass">{{ purchaseOrder.status }}</span>
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
                  <div class="info-value">{{ formatCurrency(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Total Cost</div>
                  <div class="info-value highlight">{{ formatCurrency(purchaseOrder.unit_cost * purchaseOrder.quantity) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Expected Delivery</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Created Date</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div v-if="purchaseOrder.notes" class="info-item info-item-full">
                  <div class="info-label">Notes</div>
                  <div class="info-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </template>

            <!-- VIEW MODE: no PO data available -->
            <template v-else-if="mode === 'view' && !purchaseOrder">
              <div class="empty-state">No purchase order data available.</div>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">
              {{ mode === 'create' ? 'Cancel' : 'Close' }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="isSubmitting"
              @click="submitForm"
            >
              {{ isSubmitting ? 'Creating...' : 'Create Purchase Order' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { api } from '../api'

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

  data() {
    return {
      form: {
        supplier_name: '',
        quantity: 0,
        unit_cost: null,
        expected_delivery_date: '',
        notes: ''
      },
      isSubmitting: false,
      errorMessage: ''
    }
  },

  computed: {
    shortageAmount() {
      if (!this.backlogItem) return 0
      return this.backlogItem.quantity_needed - this.backlogItem.quantity_available
    },

    purchaseOrder() {
      if (!this.backlogItem) return null
      return this.backlogItem.purchase_order || null
    },

    todayDate() {
      return new Date().toISOString().split('T')[0]
    },

    formattedTotalCost() {
      const total = (this.form.quantity || 0) * (this.form.unit_cost || 0)
      return this.formatCurrency(total)
    },

    statusBadgeClass() {
      if (!this.purchaseOrder) return ''
      const status = (this.purchaseOrder.status || '').toLowerCase()
      if (status === 'pending') return 'badge-yellow'
      if (status === 'approved' || status === 'completed') return 'badge-green'
      if (status === 'cancelled') return 'badge-red'
      return 'badge-blue'
    }
  },

  watch: {
    // Pre-fill quantity whenever the modal opens or the backlog item changes
    isOpen(val) {
      if (val && this.mode === 'create') {
        this.resetForm()
      }
    },
    backlogItem() {
      if (this.isOpen && this.mode === 'create') {
        this.resetForm()
      }
    }
  },

  methods: {
    close() {
      this.$emit('close')
    },

    resetForm() {
      this.form = {
        supplier_name: '',
        quantity: this.shortageAmount > 0 ? this.shortageAmount : 1,
        unit_cost: null,
        expected_delivery_date: '',
        notes: ''
      }
      this.errorMessage = ''
      this.isSubmitting = false
    },

    async submitForm() {
      if (this.isSubmitting) return
      this.errorMessage = ''

      // Basic client-side validation
      if (!this.form.supplier_name.trim()) {
        this.errorMessage = 'Supplier name is required.'
        return
      }
      if (!this.form.quantity || this.form.quantity < 1) {
        this.errorMessage = 'Quantity must be at least 1.'
        return
      }
      if (!this.form.unit_cost || this.form.unit_cost <= 0) {
        this.errorMessage = 'Unit cost must be greater than zero.'
        return
      }
      if (!this.form.expected_delivery_date) {
        this.errorMessage = 'Expected delivery date is required.'
        return
      }

      this.isSubmitting = true
      try {
        const payload = {
          backlog_item_id: this.backlogItem.id,
          supplier_name: this.form.supplier_name.trim(),
          quantity: this.form.quantity,
          unit_cost: this.form.unit_cost,
          expected_delivery_date: this.form.expected_delivery_date,
          notes: this.form.notes.trim()
        }
        const response = await api.createPurchaseOrder(payload)
        this.$emit('po-created', response)
      } catch (err) {
        this.errorMessage =
          (err.response && err.response.data && err.response.data.detail) ||
          'Failed to create purchase order. Please try again.'
      } finally {
        this.isSubmitting = false
      }
    },

    formatDate(dateString) {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    },

    formatCurrency(value) {
      if (value == null || isNaN(value)) return '$0.00'
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
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

/* Item header (shared between modes) */
.item-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.item-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.item-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.375rem 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-sku {
  font-size: 0.875rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.priority-badge {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
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

/* Summary cards (create mode) */
.shortage-summary {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.75rem;
}

.summary-card {
  padding: 1.25rem;
  border-radius: 10px;
  border: 2px solid;
}

.summary-card.warning {
  border-color: #fed7aa;
  background: #fffbeb;
}

.summary-card.neutral {
  border-color: #e2e8f0;
  background: #f8fafc;
}

.summary-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-card.warning .summary-value {
  color: #f59e0b;
}

.summary-value.order-id {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 1rem;
  color: #2563eb;
}

/* Error banner */
.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #dc2626;
  font-size: 0.875rem;
  margin-bottom: 1.5rem;
}

/* Form */
.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
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

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
}

.required {
  color: #dc2626;
  margin-left: 0.125rem;
}

.optional {
  font-weight: 400;
  color: #94a3b8;
  font-size: 0.813rem;
}

.form-input {
  width: 100%;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  color: #0f172a;
  background: white;
  font-family: inherit;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: 2px solid #2563eb;
  outline-offset: 0;
  border-color: #2563eb;
}

.form-input::placeholder {
  color: #94a3b8;
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.input-prefix-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-prefix {
  position: absolute;
  left: 0.75rem;
  color: #64748b;
  font-size: 0.875rem;
  pointer-events: none;
  z-index: 1;
}

.form-input.with-prefix {
  padding-left: 1.75rem;
}

/* Total cost row */
.total-cost-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1rem;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
}

.total-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #0369a1;
}

.total-value {
  font-size: 1rem;
  font-weight: 700;
  color: #0369a1;
}

/* View mode: info grid */
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

.info-item-full {
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

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

.info-value.highlight {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

/* Status badges (view mode) */
.badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
}

.badge-green {
  background: #dcfce7;
  color: #166534;
}

.badge-yellow {
  background: #fef9c3;
  color: #854d0e;
}

.badge-red {
  background: #fee2e2;
  color: #991b1b;
}

.badge-blue {
  background: #dbeafe;
  color: #1e40af;
}

/* Empty state */
.empty-state {
  text-align: center;
  color: #64748b;
  padding: 2rem 0;
  font-size: 0.938rem;
}

/* Modal footer */
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
  border: none;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
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
