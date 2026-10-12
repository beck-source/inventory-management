<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Allocate your budget across forecasted demand to build a restocking order.</p>
    </div>

    <div v-if="successBanner" class="banner banner-success">
      <span>{{ successBanner }}</span>
      <button class="banner-dismiss" @click="successBanner = null">Dismiss</button>
    </div>

    <div v-if="errorBanner" class="banner banner-error">
      <span>{{ errorBanner }}</span>
      <button class="banner-dismiss" @click="errorBanner = null">Dismiss</button>
    </div>

    <div class="card budget-card">
      <div class="budget-header">
        <span class="budget-label">Available Budget</span>
        <span class="budget-amount">{{ formatCurrency(budget) }}</span>
      </div>
      <input
        type="range"
        class="budget-slider"
        :min="5000"
        :max="100000"
        :step="500"
        v-model.number="budget"
        @input="onBudgetChange"
      />
      <div class="budget-stats">
        <span class="budget-stat">Items within budget: <strong>{{ itemsWithinBudgetCount }}</strong></span>
        <span class="budget-stat">Total selected cost: <strong>{{ formatCurrency(totalSelectedCost) }}</strong></span>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Demand Forecast Recommendations ({{ recommendations.length }})</h3>
      </div>

      <div v-if="loading" class="loading">Loading...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else class="table-container">
        <table class="restock-table">
          <thead>
            <tr>
              <th class="col-check"></th>
              <th class="col-priority">Priority</th>
              <th class="col-name">Item Name</th>
              <th class="col-sku">SKU</th>
              <th class="col-trend">Trend</th>
              <th class="col-qty">Forecast Qty</th>
              <th class="col-unit">Unit Cost</th>
              <th class="col-total">Total Cost</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in recommendations"
              :key="item.sku"
              :class="{ 'row-dimmed': isDimmed(item) }"
            >
              <td class="col-check">
                <input
                  type="checkbox"
                  :checked="selectedSkus.has(item.sku)"
                  @change="onToggleItem(item, $event.target.checked)"
                  class="row-checkbox"
                />
              </td>
              <td class="col-priority">
                <span :class="['badge', item.priority.toLowerCase()]">
                  {{ capitalize(item.priority) }}
                </span>
              </td>
              <td class="col-name">{{ item.item_name }}</td>
              <td class="col-sku"><strong>{{ item.sku }}</strong></td>
              <td class="col-trend">
                <span :class="['badge', item.trend.toLowerCase()]">
                  {{ capitalize(item.trend) }}
                </span>
              </td>
              <td class="col-qty">{{ item.recommended_quantity.toLocaleString() }}</td>
              <td class="col-unit">{{ formatCurrency(item.unit_cost) }}</td>
              <td class="col-total"><strong>{{ formatCurrency(item.total_cost) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="summary-bar">
      <div class="summary-stats">
        <span class="summary-count">{{ selectedSkus.size }} items selected</span>
        <span class="summary-sep">·</span>
        <span>Total: <strong>{{ formatCurrency(totalSelectedCost) }}</strong></span>
        <span class="summary-sep">·</span>
        <span>Budget remaining: <strong :class="budgetRemaining < 0 ? 'over-budget' : ''">{{ formatCurrency(budgetRemaining) }}</strong></span>
      </div>
      <button
        class="btn-place-order"
        :disabled="selectedSkus.size === 0 || submitting"
        @click="placeOrder"
      >
        <span v-if="submitting">Placing Order...</span>
        <span v-else>Place Order</span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const recommendations = ref([])
    const budget = ref(25000)
    const selectedSkus = ref(new Set())
    const submitting = ref(false)
    const successBanner = ref(null)
    const errorBanner = ref(null)

    const totalSelectedCost = computed(() => {
      return recommendations.value
        .filter(item => selectedSkus.value.has(item.sku))
        .reduce((sum, item) => sum + item.total_cost, 0)
    })

    const budgetRemaining = computed(() => {
      return budget.value - totalSelectedCost.value
    })

    const itemsWithinBudgetCount = computed(() => {
      let running = 0
      let count = 0
      for (const item of recommendations.value) {
        if (running + item.total_cost <= budget.value) {
          running += item.total_cost
          count++
        }
      }
      return count
    })

    const isDimmed = (item) => {
      if (selectedSkus.value.has(item.sku)) return false
      return budgetRemaining.value < item.total_cost
    }

    const runGreedySelection = () => {
      const newSelected = new Set()
      let running = 0
      for (const item of recommendations.value) {
        if (running + item.total_cost <= budget.value) {
          newSelected.add(item.sku)
          running += item.total_cost
        }
      }
      selectedSkus.value = newSelected
    }

    const onBudgetChange = () => {
      runGreedySelection()
    }

    const onToggleItem = (item, checked) => {
      const next = new Set(selectedSkus.value)
      if (checked) {
        next.add(item.sku)
      } else {
        next.delete(item.sku)
      }
      selectedSkus.value = next
    }

    const formatCurrency = (value) => {
      return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    const capitalize = (str) => {
      if (!str) return ''
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
    }

    const placeOrder = async () => {
      if (selectedSkus.value.size === 0) return
      submitting.value = true
      errorBanner.value = null
      successBanner.value = null
      try {
        const items = recommendations.value
          .filter(item => selectedSkus.value.has(item.sku))
          .map(item => ({
            sku: item.sku,
            item_name: item.item_name,
            quantity: item.recommended_quantity,
            unit_cost: item.unit_cost
          }))
        const result = await api.placeRestockingOrder(items)
        successBanner.value = `Order ${result.order_number} placed successfully. Estimated delivery: ${result.estimated_delivery} (14-day lead time).`
        selectedSkus.value = new Set()
      } catch (err) {
        errorBanner.value = 'Failed to place order: ' + (err?.response?.data?.detail || err.message)
      } finally {
        submitting.value = false
      }
    }

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockingRecommendations()
        recommendations.value = data
        runGreedySelection()
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      loading,
      error,
      recommendations,
      budget,
      selectedSkus,
      submitting,
      successBanner,
      errorBanner,
      totalSelectedCost,
      budgetRemaining,
      itemsWithinBudgetCount,
      isDimmed,
      onBudgetChange,
      onToggleItem,
      formatCurrency,
      capitalize,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  height: 6px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
  margin-bottom: 0.875rem;
  accent-color: #2563eb;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.budget-stats {
  display: flex;
  gap: 2rem;
}

.budget-stat {
  font-size: 0.875rem;
  color: #64748b;
}

.restock-table {
  table-layout: fixed;
  width: 100%;
}

.col-check {
  width: 40px;
}

.col-priority {
  width: 100px;
}

.col-name {
  width: 220px;
}

.col-sku {
  width: 120px;
}

.col-trend {
  width: 110px;
}

.col-qty {
  width: 110px;
}

.col-unit {
  width: 110px;
}

.col-total {
  width: 120px;
}

.row-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #2563eb;
}

.row-dimmed {
  opacity: 0.5;
}

.summary-bar {
  position: sticky;
  bottom: 0;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.06);
  margin-top: 0.25rem;
}

.summary-stats {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.938rem;
  color: #334155;
}

.summary-count {
  font-weight: 600;
  color: #0f172a;
}

.summary-sep {
  color: #cbd5e1;
}

.over-budget {
  color: #dc2626;
}

.btn-place-order {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-place-order:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-place-order:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

.banner-success {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
}

.banner-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.banner-dismiss {
  background: none;
  border: none;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  margin-left: 1rem;
  color: inherit;
  opacity: 0.75;
  transition: opacity 0.2s;
}

.banner-dismiss:hover {
  opacity: 1;
}
</style>
