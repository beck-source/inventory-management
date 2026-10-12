<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card controls-card">
      <div class="control-group">
        <label>{{ t('restocking.warehouse') }}</label>
        <select v-model="selectedWarehouse" class="filter-select">
          <option value="San Francisco">{{ t('warehouses.sanFrancisco') }}</option>
          <option value="London">{{ t('warehouses.london') }}</option>
          <option value="Tokyo">{{ t('warehouses.tokyo') }}</option>
        </select>
      </div>

      <div class="control-group budget-group">
        <label>{{ t('restocking.budget') }}</label>
        <input
          type="range"
          min="0"
          max="500000"
          step="1000"
          v-model.number="budget"
          class="budget-slider"
        />
        <span class="budget-amount">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ itemsSelectedCount }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</div>
        </div>
        <div class="stat-card" :class="budgetRemaining < 0 ? 'danger' : 'success'">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budgetRemaining.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="checkbox-cell">
                  <input
                    type="checkbox"
                    v-model="allSelected"
                    :title="t('restocking.selectAll')"
                  />
                </th>
                <th>{{ t('restocking.sku') }}</th>
                <th>{{ t('restocking.productName') }}</th>
                <th>{{ t('restocking.category') }}</th>
                <th>{{ t('restocking.currentStock') }}</th>
                <th>{{ t('restocking.forecastedDemand') }}</th>
                <th>{{ t('restocking.recommendedQty') }}</th>
                <th>{{ t('restocking.unitCost') }}</th>
                <th>{{ t('restocking.totalCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations"
                :key="item.sku"
                :class="{ selected: item.selected }"
              >
                <td class="checkbox-cell">
                  <input type="checkbox" v-model="item.selected" />
                </td>
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td>{{ item.quantityOnHand }}</td>
                <td>{{ item.forecastedDemand }}</td>
                <td>
                  <input
                    type="number"
                    min="0"
                    class="qty-input"
                    v-model.number="item.qty"
                    @change="clampQty(item)"
                  />
                </td>
                <td>{{ currencySymbol }}{{ item.unitCost.toFixed(2) }}</td>
                <td><strong>{{ currencySymbol }}{{ (item.qty * item.unitCost).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card order-section">
        <div class="order-actions">
          <button
            class="btn-primary"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
          <button class="btn-secondary" @click="resetSelections" :disabled="submitting">
            {{ t('restocking.reset') }}
          </button>
        </div>

        <div v-if="itemsSelectedCount === 0" class="order-hint">
          {{ t('restocking.selectAtLeastOne') }}
        </div>
        <div v-else-if="budgetRemaining < 0" class="order-hint over-budget">
          {{ t('restocking.overBudget') }}
        </div>

        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
        <div v-if="submitError" class="error">{{ submitError }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

const { t, currentCurrency, translateProductName } = useI18n()
const { selectedLocation } = useFilters()

const VALID_WAREHOUSES = ['San Francisco', 'London', 'Tokyo']

const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

const selectedWarehouse = ref(
  VALID_WAREHOUSES.includes(selectedLocation.value) ? selectedLocation.value : 'San Francisco'
)
const budget = ref(50000)

const loading = ref(true)
const error = ref(null)
const recommendations = ref([])

const submitting = ref(false)
const successMessage = ref('')
const submitError = ref('')

const translateCategory = (category) => {
  const categoryMap = {
    'Circuit Boards': t('categories.circuitBoards'),
    'Sensors': t('categories.sensors'),
    'Actuators': t('categories.actuators'),
    'Controllers': t('categories.controllers'),
    'Power Supplies': t('categories.powerSupplies')
  }
  return categoryMap[category] || category
}

const loadRecommendations = async () => {
  loading.value = true
  error.value = null
  successMessage.value = ''
  submitError.value = ''

  try {
    const [forecasts, inventoryItems] = await Promise.all([
      api.getDemandForecasts(),
      api.getInventory({ warehouse: selectedWarehouse.value })
    ])

    const forecastMap = new Map(forecasts.map((f) => [f.item_sku, f]))

    const calculated = inventoryItems
      .map((item) => {
        const forecast = forecastMap.get(item.sku)
        const forecastedDemand = forecast ? forecast.forecasted_demand : 0
        const deficit = Math.max(0, item.reorder_point - item.quantity_on_hand)
        const score = forecastedDemand * 0.7 + deficit * 0.3
        const recommendedQty = deficit + Math.floor(forecastedDemand / 3)

        return {
          sku: item.sku,
          name: item.name,
          category: item.category,
          quantityOnHand: item.quantity_on_hand,
          forecastedDemand,
          unitCost: item.unit_cost,
          score,
          recommendedQty,
          qty: recommendedQty,
          selected: true
        }
      })
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)

    recommendations.value = calculated
  } catch (err) {
    error.value = 'Failed to load restocking recommendations: ' + err.message
    console.error(err)
  } finally {
    loading.value = false
  }
}

const clampQty = (item) => {
  if (!Number.isFinite(item.qty) || item.qty < 0) {
    item.qty = 0
  } else {
    item.qty = Math.floor(item.qty)
  }
}

const allSelected = computed({
  get: () => recommendations.value.length > 0 && recommendations.value.every((i) => i.selected),
  set: (value) => {
    recommendations.value.forEach((i) => {
      i.selected = value
    })
  }
})

const itemsSelectedCount = computed(() => recommendations.value.filter((i) => i.selected).length)

const totalCost = computed(() =>
  recommendations.value
    .filter((i) => i.selected)
    .reduce((sum, i) => sum + i.qty * i.unitCost, 0)
)

const budgetRemaining = computed(() => budget.value - totalCost.value)

const canPlaceOrder = computed(
  () => itemsSelectedCount.value > 0 && budgetRemaining.value >= 0 && !submitting.value
)

const resetSelections = () => {
  recommendations.value.forEach((i) => {
    i.qty = i.recommendedQty
    i.selected = true
  })
  successMessage.value = ''
  submitError.value = ''
}

const placeOrder = async () => {
  if (!canPlaceOrder.value) return

  submitting.value = true
  successMessage.value = ''
  submitError.value = ''

  try {
    const selectedItems = recommendations.value.filter((i) => i.selected)

    const orderData = {
      warehouse: selectedWarehouse.value,
      items: selectedItems.map((i) => ({ sku: i.sku, quantity: i.qty })),
      budget: budget.value,
      recommended_items: recommendations.value.map((i) => ({
        sku: i.sku,
        recommended_qty: i.recommendedQty,
        ordered_qty: i.selected ? i.qty : 0
      }))
    }

    await api.submitRestockingOrder(orderData)
    successMessage.value = `Order placed successfully for ${selectedItems.length} item${selectedItems.length === 1 ? '' : 's'}.`
  } catch (err) {
    submitError.value = 'Failed to place order: ' + err.message
    console.error(err)
  } finally {
    submitting.value = false
  }
}

watch(selectedWarehouse, () => {
  loadRecommendations()
})

onMounted(() => loadRecommendations())
</script>

<style scoped>
.controls-card {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2rem;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.control-group label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.filter-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.875rem;
  color: #0f172a;
  background: white;
  cursor: pointer;
  min-width: 160px;
}

.filter-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.budget-group {
  flex: 1;
  min-width: 280px;
}

.budget-slider {
  flex: 1;
  min-width: 200px;
  accent-color: #2563eb;
}

.budget-amount {
  font-weight: 700;
  color: #0f172a;
  font-size: 1rem;
  min-width: 90px;
  text-align: right;
}

.empty-state {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.checkbox-cell {
  width: 40px;
  text-align: center;
}

.checkbox-cell input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #2563eb;
}

tbody tr.selected {
  background: #eff6ff;
}

tbody tr.selected:hover {
  background: #dbeafe;
}

.qty-input {
  width: 80px;
  padding: 0.375rem 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #0f172a;
  font-family: inherit;
}

.qty-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.order-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.order-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-primary {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  border-color: #94a3b8;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.625rem 1.5rem;
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

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.order-hint {
  font-size: 0.875rem;
  color: #64748b;
}

.order-hint.over-budget {
  color: #dc2626;
  font-weight: 600;
}

.success-message {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.938rem;
}
</style>
