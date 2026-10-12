<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget Slider -->
    <div class="card budget-card">
      <div class="budget-header">
        <label for="budget-slider" class="budget-label">{{ t('restocking.budgetLabel') }}</label>
        <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
      </div>
      <input
        id="budget-slider"
        v-model.number="budget"
        type="range"
        min="0"
        max="100000"
        step="1000"
        class="budget-slider"
      />
      <div class="budget-range-labels">
        <span>{{ currencySymbol }}0</span>
        <span>{{ currencySymbol }}100,000</span>
      </div>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card info">
        <div class="stat-label">{{ t('restocking.stats.recommendedSpend') }}</div>
        <div class="stat-value">{{ currencySymbol }}{{ formatNumber(totalRecommendedCost) }}</div>
      </div>
      <div class="stat-card success">
        <div class="stat-label">{{ t('restocking.stats.budgetRemaining') }}</div>
        <div class="stat-value">{{ currencySymbol }}{{ formatNumber(budgetRemaining) }}</div>
      </div>
      <div class="stat-card info-alt">
        <div class="stat-label">{{ t('restocking.stats.itemsSelected') }}</div>
        <div class="stat-value">{{ selectedItems.length }}</div>
      </div>
    </div>

    <!-- Recommendations Table -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendationsTitle') }} ({{ filteredRecommendations.length }})</h3>
        <button class="btn-secondary refresh-btn" @click="loadRecommendations" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          {{ t('restocking.refresh') }}
        </button>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="filteredRecommendations.length === 0" class="empty-state">
        {{ t('restocking.noRecommendations') }}
      </div>
      <div v-else class="table-container">
        <table class="restocking-table">
          <thead>
            <tr>
              <th class="col-checkbox">
                <input
                  type="checkbox"
                  v-model="selectAll"
                  @change="toggleSelectAll"
                  :aria-label="t('restocking.selectAll')"
                />
              </th>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.itemName') }}</th>
              <th>{{ t('restocking.table.currentStock') }}</th>
              <th>{{ t('restocking.table.recommendedQty') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.totalCost') }}</th>
              <th>{{ t('restocking.table.demandTrend') }}</th>
              <th>{{ t('restocking.table.urgencyScore') }}</th>
              <th>{{ t('restocking.table.reason') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredRecommendations" :key="item.item_sku">
              <td class="col-checkbox">
                <input
                  type="checkbox"
                  :checked="isSelected(item.item_sku)"
                  @change="toggleSelection(item)"
                />
              </td>
              <td class="sku-cell">{{ item.item_sku }}</td>
              <td>{{ translateProductName(item.item_name) }}</td>
              <td>{{ item.current_stock }}</td>
              <td>{{ item.recommended_quantity }}</td>
              <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
              <td><strong>{{ currencySymbol }}{{ formatNumber(item.total_cost) }}</strong></td>
              <td>
                <span :class="['badge', trendBadgeClass(item.trend)]">
                  {{ t(`trends.${item.trend}`) }}
                </span>
              </td>
              <td>
                <div class="urgency-cell">
                  <div class="urgency-bar-track">
                    <div
                      class="urgency-bar-fill"
                      :style="{ width: Math.min(item.urgency_score, 100) + '%' }"
                    ></div>
                  </div>
                  <span class="urgency-value">{{ item.urgency_score }}</span>
                </div>
              </td>
              <td class="reason-cell">{{ item.reason }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="action-bar">
      <button class="btn-secondary" @click="clearSelection" :disabled="selectedItems.length === 0">
        {{ t('restocking.clearSelection') }}
      </button>
      <button
        class="btn-primary"
        @click="submitOrder"
        :disabled="selectedItems.length === 0 || loading"
      >
        {{ t('restocking.placeOrder', { count: selectedItems.length }) }}
      </button>
    </div>

    <OrderSubmittedModal
      v-if="submittedOrder"
      :is-open="showSuccessModal"
      :order="submittedOrder"
      @close="handleModalClose"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import OrderSubmittedModal from '../components/OrderSubmittedModal.vue'

const { t, currentCurrency, translateProductName } = useI18n()
const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

// Reactive state
const budget = ref(50000)
const recommendations = ref([])
const selectedItems = ref([])
const loading = ref(false)
const error = ref(null)
const selectAll = ref(false)
const showSuccessModal = ref(false)
const submittedOrder = ref(null)

// Computed
const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

const totalRecommendedCost = computed(() =>
  recommendations.value.reduce((sum, item) => sum + item.total_cost, 0)
)

const totalSelectedCost = computed(() =>
  selectedItems.value.reduce((sum, item) => sum + item.total_cost, 0)
)

const budgetRemaining = computed(() => budget.value - totalSelectedCost.value)

const filteredRecommendations = computed(() => {
  return recommendations.value.filter(
    (item) => isSelected(item.item_sku) || item.total_cost <= budgetRemaining.value
  )
})

// Methods
const formatNumber = (value) => {
  const num = Number(value)
  if (isNaN(num)) return '0'
  return num.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

const trendBadgeClass = (trend) => `trend-${trend}`

const isSelected = (sku) => selectedItems.value.some((item) => item.item_sku === sku)

const loadRecommendations = async () => {
  loading.value = true
  error.value = null
  try {
    const filters = getCurrentFilters()
    recommendations.value = await api.getRestockingRecommendations(budget.value, filters)

    // Keep selections only if they're still present (visible) and still fit the budget
    const validSkus = new Set(recommendations.value.map((item) => item.item_sku))
    const kept = []
    let runningTotal = 0
    for (const item of selectedItems.value) {
      if (validSkus.has(item.item_sku) && runningTotal + item.total_cost <= budget.value) {
        kept.push(item)
        runningTotal += item.total_cost
      }
    }
    selectedItems.value = kept
  } catch (err) {
    error.value = `${t('restocking.loadError')}: ${err.message}`
    recommendations.value = []
  } finally {
    loading.value = false
  }
}

const toggleSelection = (item) => {
  const idx = selectedItems.value.findIndex((i) => i.item_sku === item.item_sku)
  if (idx !== -1) {
    selectedItems.value.splice(idx, 1)
    error.value = null
    return
  }

  if (totalSelectedCost.value + item.total_cost > budget.value) {
    error.value = t('restocking.budgetExceeded')
    return
  }

  error.value = null
  selectedItems.value.push(item)
}

const toggleSelectAll = () => {
  if (selectAll.value) {
    // Select as many visible items as fit the remaining budget, in displayed order
    const newSelection = []
    let total = 0
    for (const item of filteredRecommendations.value) {
      if (total + item.total_cost <= budget.value) {
        newSelection.push(item)
        total += item.total_cost
      }
    }
    selectedItems.value = newSelection
    error.value = null
  } else {
    selectedItems.value = []
  }
}

const clearSelection = () => {
  selectedItems.value = []
  error.value = null
}

const submitOrder = async () => {
  if (selectedItems.value.length === 0) return

  loading.value = true
  error.value = null
  try {
    const filters = getCurrentFilters()
    const orderData = {
      items: selectedItems.value.map((item) => ({
        sku: item.item_sku,
        name: item.item_name,
        quantity: item.recommended_quantity,
        unit_price: item.unit_cost
      })),
      budget: budget.value,
      warehouse: filters.warehouse && filters.warehouse !== 'all' ? filters.warehouse : null,
      category: filters.category && filters.category !== 'all' ? filters.category : null
    }

    submittedOrder.value = await api.createRestockingOrder(orderData)
    showSuccessModal.value = true
  } catch (err) {
    error.value = `${t('restocking.orderError')}: ${err.message}`
  } finally {
    loading.value = false
  }
}

const handleModalClose = () => {
  showSuccessModal.value = false
  submittedOrder.value = null
  clearSelection()
  loadRecommendations()
}

// Watchers
let budgetDebounceTimer = null
watch(budget, () => {
  clearTimeout(budgetDebounceTimer)
  budgetDebounceTimer = setTimeout(() => {
    loadRecommendations()
  }, 300)
})

watch([selectedLocation, selectedCategory], () => {
  loadRecommendations()
})

// Keep the "select all" checkbox in sync with individual selections
watch(
  [selectedItems, filteredRecommendations],
  () => {
    selectAll.value =
      filteredRecommendations.value.length > 0 &&
      filteredRecommendations.value.every((item) => isSelected(item.item_sku))
  },
  { deep: true }
)

onMounted(() => loadRecommendations())
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  appearance: none;
  cursor: pointer;
  margin: 0.5rem 0;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 3px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
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

.refresh-btn:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #cbd5e1;
  border-top-color: #2563eb;
  border-radius: 50%;
  display: inline-block;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Table columns */
.restocking-table {
  table-layout: fixed;
  width: 100%;
}

.col-checkbox {
  width: 44px;
  text-align: center;
}

.col-checkbox input[type='checkbox'] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #2563eb;
}

.sku-cell {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.813rem;
  color: #2563eb;
}

.reason-cell {
  font-size: 0.813rem;
  color: #64748b;
}

/* Trend badges: scoped overrides so this page can use distinct colors
   (increasing=green, stable=yellow, decreasing=red) without affecting
   the shared .badge.stable style used elsewhere in the app */
.badge.trend-increasing {
  background: #d1fae5;
  color: #065f46;
}

.badge.trend-decreasing {
  background: #fecaca;
  color: #991b1b;
}

.badge.trend-stable {
  background: #fef9c3;
  color: #854d0e;
}

/* Urgency score progress bar */
.urgency-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 120px;
}

.urgency-bar-track {
  flex: 1;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.urgency-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  border-radius: 4px;
  transition: width 0.2s ease;
}

.urgency-value {
  font-size: 0.813rem;
  font-weight: 600;
  color: #334155;
  min-width: 28px;
  text-align: right;
}

/* Action bar */
.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.25rem;
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

.btn-secondary:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .action-bar {
    flex-direction: column-reverse;
  }

  .btn-secondary,
  .btn-primary {
    width: 100%;
    text-align: center;
  }
}
</style>
