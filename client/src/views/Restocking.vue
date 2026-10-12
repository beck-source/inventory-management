<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="controls-grid">
        <div class="control-group">
          <label class="control-label">
            {{ t('restocking.budget') }}: <strong>{{ formatCurrency(budget, currentCurrency) }}</strong>
          </label>
          <input
            v-model.number="budget"
            type="range"
            min="0"
            max="50000"
            step="500"
            class="budget-slider"
          />
          <div class="slider-range">
            <span>{{ formatCurrency(0, currentCurrency) }}</span>
            <span>{{ formatCurrency(50000, currentCurrency) }}</span>
          </div>
        </div>

        <div class="control-group">
          <label class="control-label" for="supplier-select">{{ t('restocking.supplier') }}</label>
          <select id="supplier-select" v-model="selectedSupplier" class="supplier-select">
            <option value="">{{ t('restocking.selectSupplier') }}</option>
            <option v-for="supplier in suppliers" :key="supplier.id" :value="supplier.id">
              {{ supplier.name }} ({{ supplier.lead_time_days }}d lead time)
            </option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
      </div>

      <div v-if="recommendations.length === 0" class="empty-state">
        {{ t('restocking.noRecommendations') }}
      </div>

      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th class="col-select">{{ t('restocking.table.select') }}</th>
              <th>{{ t('restocking.table.itemName') }}</th>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.currentStock') }}</th>
              <th>{{ t('restocking.table.suggestedQty') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.itemCost') }}</th>
              <th>{{ t('restocking.table.reason') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sortedRecommendations" :key="item.sku">
              <td class="col-select">
                <input
                  type="checkbox"
                  :checked="selectedItems.has(item.sku)"
                  @change="toggleItemSelection(item.sku, $event.target.checked, item.suggested_quantity)"
                />
              </td>
              <td>{{ translateProductName(item.name) }}</td>
              <td><strong>{{ item.sku }}</strong></td>
              <td>{{ item.quantity_on_hand }}</td>
              <td>{{ item.suggested_quantity }}</td>
              <td>{{ formatCurrency(item.unit_cost, currentCurrency) }}</td>
              <td><strong>{{ formatCurrency(item.total_cost, currentCurrency) }}</strong></td>
              <td>
                <span :class="['badge', item.reason === 'critical' ? 'danger' : 'warning']">
                  {{ item.reason === 'critical' ? t('restocking.reasonCritical') : t('restocking.reasonHighDemand') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="order-summary">
        <div class="total-cost">
          <span class="total-label">{{ t('restocking.totalSelectedCost') }}</span>
          <span :class="['total-value', { 'over-budget': totalSelectedCost > budget }]">
            {{ formatCurrency(totalSelectedCost, currentCurrency) }}
          </span>
        </div>

        <button
          class="place-order-btn"
          :disabled="!canPlaceOrder || submitting"
          @click="submitRestockingOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="submitSuccess" class="submit-message success">{{ submitSuccess }}</div>
      <div v-if="submitError" class="submit-message error">{{ submitError }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const { t, currentCurrency, translateProductName } = useI18n()

const budget = ref(25000)
const suppliers = ref([])
const selectedSupplier = ref('')
const recommendations = ref([])
const selectedItems = ref(new Map())
const selectedQuantities = ref(new Map())

const loading = ref(false)
const error = ref(null)
const submitting = ref(false)
const submitSuccess = ref(null)
const submitError = ref(null)

let debounceTimer = null

const sortedRecommendations = computed(() => {
  // Critical items first, then high-demand items
  return recommendations.value.slice().sort((a, b) => {
    if (a.reason === b.reason) return 0
    return a.reason === 'critical' ? -1 : 1
  })
})

const totalSelectedCost = computed(() => {
  let total = 0
  for (const [sku, isSelected] of selectedItems.value.entries()) {
    if (!isSelected) continue
    const item = recommendations.value.find(r => r.sku === sku)
    if (!item) continue
    const qty = selectedQuantities.value.get(sku) ?? item.suggested_quantity
    total += qty * item.unit_cost
  }
  return Math.round(total * 100) / 100
})

const hasSelectedItems = computed(() => {
  return Array.from(selectedItems.value.values()).some(v => v)
})

const canPlaceOrder = computed(() => {
  return (
    hasSelectedItems.value &&
    !!selectedSupplier.value &&
    totalSelectedCost.value <= budget.value
  )
})

const loadSuppliers = async () => {
  try {
    suppliers.value = await api.getSuppliers()
  } catch (err) {
    error.value = 'Failed to load suppliers: ' + err.message
  }
}

const loadRecommendations = async (currentBudget) => {
  try {
    loading.value = true
    error.value = null
    recommendations.value = await api.getRestockingRecommendations(currentBudget)
    // Reset selections when recommendations change
    selectedItems.value = new Map()
    selectedQuantities.value = new Map()
  } catch (err) {
    error.value = 'Failed to load restocking recommendations: ' + err.message
  } finally {
    loading.value = false
  }
}

const toggleItemSelection = (sku, checked, suggestedQty) => {
  const items = new Map(selectedItems.value)
  const quantities = new Map(selectedQuantities.value)

  items.set(sku, checked)
  if (checked) {
    quantities.set(sku, suggestedQty)
  } else {
    quantities.delete(sku)
  }

  selectedItems.value = items
  selectedQuantities.value = quantities
}

const submitRestockingOrder = async () => {
  if (!canPlaceOrder.value) return

  submitSuccess.value = null
  submitError.value = null

  if (!selectedSupplier.value) {
    submitError.value = t('restocking.selectSupplierError')
    return
  }
  if (!hasSelectedItems.value) {
    submitError.value = t('restocking.noItemsSelected')
    return
  }
  if (totalSelectedCost.value > budget.value) {
    submitError.value = t('restocking.overBudget')
    return
  }

  const items = []
  for (const [sku, isSelected] of selectedItems.value.entries()) {
    if (!isSelected) continue
    const item = recommendations.value.find(r => r.sku === sku)
    if (!item) continue
    const qty = selectedQuantities.value.get(sku) ?? item.suggested_quantity
    items.push({
      sku: item.sku,
      quantity: qty,
      warehouse: item.warehouse
    })
  }

  try {
    submitting.value = true
    await api.submitRestockingOrder(items, selectedSupplier.value)
    submitSuccess.value = t('restocking.orderSuccess')
    await loadRecommendations(budget.value)
  } catch (err) {
    submitError.value = t('restocking.orderError') + ': ' + err.message
  } finally {
    submitting.value = false
  }
}

watch(budget, (newBudget) => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    loadRecommendations(newBudget)
  }, 500)
})

onMounted(() => {
  loadSuppliers()
  loadRecommendations(budget.value)
})
</script>

<style scoped>
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin-bottom: 0.25rem;
}

.page-header p {
  color: #64748b;
  font-size: 0.875rem;
}

.controls-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
  align-items: start;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.slider-range {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
}

.supplier-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #0f172a;
  background: #f8fafc;
}

.supplier-select:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1.5rem;
  padding-bottom: 0.875rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.col-select {
  width: 60px;
  text-align: center;
}

.col-select input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.order-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.total-cost {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.total-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.total-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.total-value.over-budget {
  color: #dc2626;
}

.place-order-btn {
  padding: 0.75rem 1.75rem;
  border: none;
  border-radius: 8px;
  background: #2563eb;
  color: white;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.submit-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
}

.submit-message.success {
  background: #d1fae5;
  color: #065f46;
}

.submit-message.error {
  background: #fecaca;
  color: #991b1b;
}

.loading,
.error {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.error {
  color: #ef4444;
}
</style>
