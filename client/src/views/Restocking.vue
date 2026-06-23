<template>
  <div class="restocking">
    <div class="page-header">
      <h1>Restocking</h1>
      <p class="subtitle">Forecast-driven recommendations that fit your budget.</p>
    </div>

    <!-- Budget card -->
    <div class="card budget-card">
      <div class="budget-value">{{ fmtWhole(budget) }}</div>
      <input
        type="range"
        min="10000"
        max="500000"
        step="5000"
        v-model.number="budget"
        class="budget-slider"
      />
      <div class="slider-hints">
        <span>$10,000</span>
        <span>$500,000</span>
      </div>
    </div>

    <!-- Success banner -->
    <div v-if="successOrderNumber" class="success-banner">
      Order {{ successOrderNumber }} submitted &mdash; view in Orders tab
    </div>

    <!-- Recommendations card -->
    <div class="card recommendations-card">
      <div class="card-header">
        <h3 class="card-title">Recommended Items</h3>
        <p class="card-subtitle">
          {{ itemsIncluded }} items totaling {{ fmt(totalCost) }}, {{ fmt(remainingBudget) }} remaining
        </p>
      </div>

      <div v-if="loading" class="state-message">Loading recommendations...</div>
      <div v-else-if="error" class="state-message error">{{ error }}</div>
      <div v-else-if="recommendations.length === 0" class="state-message">
        No items need restocking at this budget. Try increasing the budget.
      </div>
      <div v-else class="table-container">
        <table class="recommendations-table">
          <thead>
            <tr>
              <th class="text-left">SKU</th>
              <th class="text-left">Item</th>
              <th class="text-left">Category</th>
              <th class="text-right">Current Stock</th>
              <th class="text-right">Forecast</th>
              <th class="text-right">Shortfall</th>
              <th class="text-right">Qty to Order</th>
              <th class="text-right">Unit Cost</th>
              <th class="text-right">Line Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendations" :key="item.sku">
              <td class="mono">{{ item.sku }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.category }}</td>
              <td class="text-right">{{ item.current_stock.toLocaleString() }}</td>
              <td class="text-right">{{ item.forecasted_demand.toLocaleString() }}</td>
              <td class="text-right">{{ item.shortfall.toLocaleString() }}</td>
              <td class="text-right">{{ item.quantity.toLocaleString() }}</td>
              <td class="text-right">{{ fmt(item.unit_cost) }}</td>
              <td class="text-right">{{ fmt(item.line_total) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="action-bar">
        <div class="action-summary">
          {{ itemsIncluded }} items &middot; {{ fmt(totalCost) }} total &middot; {{ fmt(remainingBudget) }} remaining
        </div>
        <button
          class="submit-btn"
          :disabled="recommendations.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? 'Submitting...' : 'Place Order' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(100000)
    const recommendations = ref([])
    const totalCost = ref(0)
    const remainingBudget = ref(0)
    const itemsIncluded = ref(0)
    const loading = ref(false)
    const submitting = ref(false)
    const error = ref(null)
    const successOrderNumber = ref(null)

    // Inline debounce handle (no extra deps)
    let debounceHandle = null

    const fmt = (n) => {
      return '$' + Number(n).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    // Whole-dollar formatter for the large budget display (no cents)
    const fmtWhole = (n) => {
      return '$' + Number(n).toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      })
    }

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockingRecommendations(budget.value)
        recommendations.value = data.recommendations || []
        totalCost.value = data.total_cost || 0
        remainingBudget.value = data.remaining_budget || 0
        itemsIncluded.value = data.items_included || 0
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + (err.message || 'unknown error')
        recommendations.value = []
        totalCost.value = 0
        remainingBudget.value = 0
        itemsIncluded.value = 0
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return
      try {
        submitting.value = true
        error.value = null
        const result = await api.createRestockingOrder({
          items: recommendations.value,
          total_cost: totalCost.value
        })
        successOrderNumber.value = result.order_number
        // Re-fetch since stock state may shift after order placement
        await loadRecommendations()
      } catch (err) {
        error.value = 'Failed to submit order: ' + (err.message || 'unknown error')
      } finally {
        submitting.value = false
      }
    }

    watch(budget, () => {
      if (debounceHandle) clearTimeout(debounceHandle)
      debounceHandle = setTimeout(loadRecommendations, 250)
      successOrderNumber.value = null
    })

    onMounted(loadRecommendations)

    return {
      budget,
      recommendations,
      totalCost,
      remainingBudget,
      itemsIncluded,
      loading,
      submitting,
      error,
      successOrderNumber,
      placeOrder,
      fmt,
      fmtWhole
    }
  }
}
</script>

<style scoped>
.restocking {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  color: #0f172a;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.subtitle {
  color: #64748b;
  margin: 0;
  font-size: 14px;
}

.card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}

.budget-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.budget-value {
  font-size: 28px;
  font-weight: 600;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #475569;
  cursor: pointer;
}

.slider-hints {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
}

.success-banner {
  background: #f0fdf4;
  border: 1px solid #16a34a;
  color: #16a34a;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
}

.recommendations-card {
  padding: 0;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.card-subtitle {
  font-size: 13px;
  color: #64748b;
  margin: 0;
}

.state-message {
  padding: 40px 24px;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}

.state-message.error {
  color: #dc2626;
}

.table-container {
  overflow-x: auto;
}

.recommendations-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.recommendations-table thead th {
  text-align: left;
  padding: 12px 16px;
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid #e2e8f0;
}

.recommendations-table tbody td {
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  color: #0f172a;
}

.recommendations-table tbody tr:last-child td {
  border-bottom: none;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.mono {
  font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, 'Courier New', monospace;
  font-size: 13px;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

.action-summary {
  color: #64748b;
  font-size: 14px;
}

.submit-btn {
  background: #2563eb;
  color: #ffffff;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.submit-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.submit-btn:disabled {
  background: #cbd5e1;
  color: #ffffff;
  cursor: not-allowed;
}
</style>
