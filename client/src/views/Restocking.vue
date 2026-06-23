<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Set your budget and review AI-recommended items to restock</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Section -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Budget</h3>
          <span class="budget-display">${{ budget.toLocaleString() }}</span>
        </div>
        <div class="budget-slider-container">
          <div class="slider-labels">
            <span>$10,000</span>
            <span>$500,000</span>
          </div>
          <input
            type="range"
            class="budget-slider"
            :min="10000"
            :max="500000"
            :step="5000"
            v-model.number="budget"
          />
        </div>
      </div>

      <!-- Recommendations Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            Recommended Items
            <span class="badge info count-badge">{{ recommendations.length }}</span>
          </h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No items can be recommended within the current budget.
        </div>
        <div v-else class="table-container">
          <table class="recommendations-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Forecasted Demand</th>
                <th>Trend</th>
                <th>Unit Cost</th>
                <th>Qty to Order</th>
                <th>Total Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><code class="sku-code">{{ item.sku }}</code></td>
                <td>{{ item.name }}</td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
                <td>${{ item.unit_cost.toLocaleString() }}</td>
                <td>{{ item.recommended_qty.toLocaleString() }}</td>
                <td><strong>${{ item.item_cost.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Summary Row -->
        <div class="summary-row">
          <div class="summary-item">
            <span class="summary-label">Items selected:</span>
            <span class="summary-value">{{ recommendations.length }} of {{ allCandidates.length }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Total cost:</span>
            <span class="summary-value">${{ totalCost.toLocaleString() }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Budget remaining:</span>
            <span :class="['summary-value', budgetRemaining >= 0 ? 'positive' : 'negative']">
              ${{ Math.abs(budgetRemaining).toLocaleString() }}
              {{ budgetRemaining < 0 ? ' over' : '' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Place Order Button -->
      <div class="actions-row">
        <button
          class="btn-primary"
          :disabled="recommendations.length === 0 || loading || submitting"
          @click="placeOrder"
        >
          {{ submitting ? 'Submitting...' : 'Place Order' }}
        </button>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="success-message">
        <p>{{ successMessage }}</p>
        <router-link to="/orders" class="view-orders-link">View in Orders tab</router-link>
      </div>

      <!-- Submit Error -->
      <div v-if="submitError" class="error">{{ submitError }}</div>
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
    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)

    const demandForecasts = ref([])
    const inventoryItems = ref([])
    const budget = ref(100000)

    // Join demand forecasts with inventory by SKU to get unit_cost
    const allCandidates = computed(() => {
      return demandForecasts.value
        .map(forecast => {
          const inventoryItem = inventoryItems.value.find(inv => inv.sku === forecast.item_sku)
          // Skip items with no matching inventory (no unit_cost available)
          if (!inventoryItem) return null

          const recommended_qty = forecast.forecasted_demand
          const item_cost = recommended_qty * inventoryItem.unit_cost

          return {
            sku: forecast.item_sku,
            name: forecast.item_name,
            forecasted_demand: forecast.forecasted_demand,
            trend: forecast.trend,
            unit_cost: inventoryItem.unit_cost,
            recommended_qty,
            item_cost
          }
        })
        .filter(Boolean)
        // Sort by forecasted_demand descending
        .sort((a, b) => b.forecasted_demand - a.forecasted_demand)
    })

    // Greedy selection: pick items in demand order until budget would be exceeded
    const recommendations = computed(() => {
      let remaining = budget.value
      const selected = []
      for (const item of allCandidates.value) {
        if (remaining - item.item_cost < 0) break
        selected.push(item)
        remaining -= item.item_cost
      }
      return selected
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.item_cost, 0)
    })

    const budgetRemaining = computed(() => {
      return budget.value - totalCost.value
    })

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        // Fetch demand forecasts and inventory in parallel
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        demandForecasts.value = forecasts
        inventoryItems.value = inventory
      } catch (err) {
        error.value = 'Failed to load restocking data'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return

      submitting.value = true
      submitError.value = null
      successMessage.value = null

      try {
        const items = recommendations.value.map(item => ({
          sku: item.sku,
          name: item.name,
          quantity: item.recommended_qty,
          unit_cost: item.unit_cost,
          total_cost: item.item_cost
        }))

        const response = await api.createRestockingOrder({
          items,
          total_cost: totalCost.value,
          budget: budget.value
        })

        successMessage.value = `Restocking order ${response.order_number} submitted. Expected delivery in 7 days.`
      } catch (err) {
        submitError.value = 'Failed to submit restocking order. Please try again.'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      loading,
      error,
      submitting,
      submitError,
      successMessage,
      budget,
      allCandidates,
      recommendations,
      totalCost,
      budgetRemaining,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding-bottom: 2rem;
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.025em;
}

.budget-slider-container {
  padding: 0.5rem 0 0.25rem;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  margin-bottom: 0.5rem;
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
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
}

.count-badge {
  margin-left: 0.5rem;
  font-size: 0.75rem;
}

.recommendations-table {
  width: 100%;
  table-layout: auto;
}

.sku-code {
  font-family: 'Courier New', monospace;
  font-size: 0.813rem;
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  color: #475569;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.summary-row {
  display: flex;
  gap: 2rem;
  padding: 1rem 0.75rem 0.25rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.summary-label {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.summary-value {
  font-size: 0.938rem;
  font-weight: 700;
  color: #0f172a;
}

.summary-value.positive {
  color: #059669;
}

.summary-value.negative {
  color: #dc2626;
}

.actions-row {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-message {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.success-message p {
  font-size: 0.938rem;
  font-weight: 500;
}

.view-orders-link {
  color: #065f46;
  font-weight: 600;
  font-size: 0.875rem;
  text-decoration: underline;
}

.view-orders-link:hover {
  color: #047857;
}
</style>
