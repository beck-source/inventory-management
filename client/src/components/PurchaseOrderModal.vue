<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'create' ? 'Create Purchase Order' : 'Purchase Order Details' }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <div class="item-header">
              <div class="item-info">
                <h4 class="item-name">{{ backlogItem.item_name }}</h4>
                <span class="item-sku">SKU: {{ backlogItem.item_sku }}</span>
              </div>
              <span class="shortage-badge">
                {{ backlogItem.quantity_needed - backlogItem.quantity_available }} units short
              </span>
            </div>

            <form v-if="mode === 'create'" class="po-form" @submit.prevent="submit">
              <div class="form-group">
                <label for="po-supplier">Supplier Name</label>
                <input
                  id="po-supplier"
                  v-model="form.supplier_name"
                  type="text"
                  required
                  placeholder="Enter supplier name"
                  class="form-input"
                />
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label for="po-qty">Quantity</label>
                  <input
                    id="po-qty"
                    v-model.number="form.quantity"
                    type="number"
                    required
                    min="1"
                    class="form-input"
                  />
                </div>
                <div class="form-group">
                  <label for="po-cost">Unit Cost ($)</label>
                  <input
                    id="po-cost"
                    v-model.number="form.unit_cost"
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    class="form-input"
                  />
                </div>
              </div>
              <div class="form-group">
                <label for="po-delivery">Expected Delivery Date</label>
                <input
                  id="po-delivery"
                  v-model="form.expected_delivery_date"
                  type="date"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="po-notes">Notes <span class="optional">(optional)</span></label>
                <textarea
                  id="po-notes"
                  v-model="form.notes"
                  rows="3"
                  placeholder="Add notes..."
                  class="form-input"
                ></textarea>
              </div>
              <div v-if="submitError" class="form-error">{{ submitError }}</div>
            </form>

            <div v-else class="po-view">
              <p v-if="!poData && !loadError" class="loading-text">Loading...</p>
              <p v-if="loadError" class="form-error">{{ loadError }}</p>
              <div v-if="poData" class="info-grid">
                <div class="info-item">
                  <div class="info-label">Supplier</div>
                  <div class="info-value">{{ poData.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Quantity</div>
                  <div class="info-value">{{ poData.quantity }} units</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Unit Cost</div>
                  <div class="info-value">${{ poData.unit_cost.toFixed(2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Total Cost</div>
                  <div class="info-value">${{ (poData.quantity * poData.unit_cost).toFixed(2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Expected Delivery</div>
                  <div class="info-value">{{ formatDate(poData.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Status</div>
                  <div class="info-value"><span class="badge info">{{ poData.status }}</span></div>
                </div>
                <div v-if="poData.notes" class="info-item full-width">
                  <div class="info-label">Notes</div>
                  <div class="info-value">{{ poData.notes }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">
              {{ mode === 'create' ? 'Cancel' : 'Close' }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="submitting"
              @click="submit"
            >
              {{ submitting ? 'Creating...' : 'Create PO' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  backlogItem: { type: Object, default: null },
  mode: { type: String, default: 'create' }
})

const emit = defineEmits(['close', 'po-created'])

const form = ref({ supplier_name: '', quantity: 0, unit_cost: 0, expected_delivery_date: '', notes: '' })
const submitting = ref(false)
const submitError = ref(null)
const poData = ref(null)
const loadError = ref(null)

watch(
  () => [props.isOpen, props.backlogItem, props.mode],
  ([open, item, mode]) => {
    if (!open || !item) return
    submitError.value = null
    loadError.value = null
    if (mode === 'create') {
      const shortage = Math.max(item.quantity_needed - item.quantity_available, 1)
      form.value = { supplier_name: '', quantity: shortage, unit_cost: 0, expected_delivery_date: '', notes: '' }
    } else {
      loadPOData(item.id)
    }
  },
  { immediate: true }
)

const loadPOData = async (backlogItemId) => {
  poData.value = null
  try {
    poData.value = await api.getPurchaseOrderByBacklogItem(backlogItemId)
  } catch {
    loadError.value = 'Could not load purchase order details.'
  }
}

const submit = async () => {
  submitting.value = true
  submitError.value = null
  try {
    const created = await api.createPurchaseOrder({
      backlog_item_id: props.backlogItem.id,
      ...form.value
    })
    emit('po-created', created)
  } catch (err) {
    submitError.value = err.response?.data?.detail || 'Failed to create purchase order.'
  } finally {
    submitting.value = false
  }
}

const close = () => emit('close')

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
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
  max-width: 560px;
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
  padding: 1.5rem;
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.item-name {
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.25rem 0;
}

.item-sku {
  font-size: 0.813rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

.shortage-badge {
  padding: 0.375rem 0.75rem;
  background: #fef2f2;
  color: #dc2626;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

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

.form-group label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #374151;
}

.optional {
  font-weight: 400;
  color: #94a3b8;
}

.form-input {
  padding: 0.625rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #0f172a;
  font-family: inherit;
  transition: border-color 0.15s ease;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

textarea.form-input {
  resize: vertical;
  min-height: 80px;
}

.form-error {
  padding: 0.75rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 0.875rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.25rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  font-weight: 500;
  color: #0f172a;
}

.loading-text {
  color: #64748b;
  font-size: 0.875rem;
  text-align: center;
  padding: 2rem 0;
}

.modal-footer {
  padding: 1.25rem 1.5rem;
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

.badge.info {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  background: #dbeafe;
  color: #1e40af;
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
