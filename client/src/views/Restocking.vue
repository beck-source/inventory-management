<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Recommendations</h2>
      <p>Set your budget and get AI-powered restocking recommendations based on demand forecasts</p>
    </div>

    <!-- Budget Control Card -->
    <div class="card budget-card">
      <div class="budget-header">
        <div class="budget-info">
          <h3 class="budget-label">Available Budget</h3>
          <div class="budget-value">${{ budget.toLocaleString() }}</div>
        </div>
      </div>
      <div class="budget-slider-container">
        <input
          v-model.number="budget"
          type="range"
          min="0"
          max="100000"
          step="1000"
          class="budget-slider"
          @input="handleBudgetChange"
        />
        <div class="slider-labels">
          <span>$0</span>
          <span>$50K</span>
          <span>$100K</span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">Loading recommendations...</div>

    <!-- Error State -->
    <div v-else-if="error" class="error">{{ error }}</div>

    <!-- Recommendations -->
    <div v-else-if="recommendations.length > 0">
      <!-- Recommendations Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Quantity to Restock</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
                <th>Current Demand</th>
                <th>Forecasted Demand</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td><strong>{{ item.quantity_to_restock }}</strong></td>
                <td>${{ item.unit_cost.toFixed(2) }}</td>
                <td><strong>${{ (item.quantity_to_restock * item.unit_cost).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong></td>
                <td>{{ item.current_demand }}</td>
                <td>{{ item.forecasted_demand }}</td>
                <td>
                  <span :class="['badge', getTrendClass(item.trend)]">
                    {{ getTrendLabel(item.trend) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Summary and Action Card -->
      <div class="card summary-card">
        <div class="summary-content">
          <div class="summary-stats">
            <div class="summary-stat">
              <span class="summary-label">Total Items</span>
              <span class="summary-value">{{ recommendations.length }}</span>
            </div>
            <div class="summary-stat">
              <span class="summary-label">Total Cost</span>
              <span class="summary-value">${{ totalCost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</span>
            </div>
            <div class="summary-stat">
              <span class="summary-label">Remaining Budget</span>
              <span class="summary-value" :class="{ 'negative': remainingBudget < 0 }">
                ${{ remainingBudget.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}
              </span>
            </div>
          </div>
          <button
            @click="placeOrder"
            :disabled="recommendations.length === 0 || placingOrder"
            class="place-order-btn"
          >
            {{ placingOrder ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="orderSuccess" class="success-message">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="success-icon">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <p class="success-text">Order placed successfully! Recommendations have been cleared.</p>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <p>Adjust your budget to see restocking recommendations</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(50000)
    const recommendations = ref([])
    const loading = ref(false)
    const error = ref(null)
    const placingOrder = ref(false)
    const orderSuccess = ref(false)
    let debounceTimer = null

    // Computed properties
    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => {
        return sum + (item.quantity_to_restock * item.unit_cost)
      }, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - totalCost.value
    })

    // Load recommendations from API
    const loadRecommendations = async () => {
      if (budget.value === 0) {
        recommendations.value = []
        return
      }

      loading.value = true
      error.value = null
      orderSuccess.value = false

      try {
        const data = await api.getRestockingRecommendations(budget.value)
        // API returns { recommendations: [...], total_cost: ..., remaining_budget: ... }
        // Map API response to match component expectations
        recommendations.value = data.recommendations.map(item => ({
          sku: item.item_sku,
          name: item.item_name,
          quantity_to_restock: item.quantity,
          unit_cost: item.unit_cost,
          current_demand: item.current_demand,
          forecasted_demand: item.forecasted_demand,
          trend: item.trend,
          warehouse: item.warehouse,
          category: item.category
        }))
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
        console.error('Load error:', err)
      } finally {
        loading.value = false
      }
    }

    // Debounced budget change handler
    const handleBudgetChange = () => {
      // Clear existing timer
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }

      // Set new timer
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 500)
    }

    // Place order
    const placeOrder = async () => {
      if (recommendations.value.length === 0) return

      placingOrder.value = true
      error.value = null

      try {
        // Backend expects item_sku and item_name (not sku and name)
        const orderData = {
          items: recommendations.value.map(item => ({
            item_sku: item.sku,
            item_name: item.name,
            quantity: item.quantity_to_restock,
            unit_cost: item.unit_cost
          })),
          total_cost: totalCost.value,
          // Use warehouse from first item, or default to 'Main'
          warehouse: recommendations.value[0]?.warehouse || 'Main'
        }

        await api.createRestockingOrder(orderData)

        // Show success message
        orderSuccess.value = true

        // Clear recommendations and reset form after 2 seconds
        setTimeout(() => {
          recommendations.value = []
          budget.value = 50000
          orderSuccess.value = false
        }, 2000)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
        console.error('Order error:', err)
      } finally {
        placingOrder.value = false
      }
    }

    // Get trend CSS class
    const getTrendClass = (trend) => {
      if (trend === 'increasing') return 'increasing'
      if (trend === 'decreasing') return 'decreasing'
      return 'stable'
    }

    // Get trend label
    const getTrendLabel = (trend) => {
      if (trend === 'increasing') return 'Increasing'
      if (trend === 'decreasing') return 'Decreasing'
      return 'Stable'
    }

    // Load initial recommendations
    loadRecommendations()

    return {
      budget,
      recommendations,
      loading,
      error,
      placingOrder,
      orderSuccess,
      totalCost,
      remainingBudget,
      handleBudgetChange,
      placeOrder,
      getTrendClass,
      getTrendLabel
    }
  }
}
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

/* Budget Card */
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.budget-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  margin: 0;
}

.budget-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

/* Budget Slider */
.budget-slider-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-slider {
  width: 100%;
  height: 8px;
  border-radius: 4px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.4);
  transition: all 0.2s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #2563eb;
  transform: scale(1.1);
}

.budget-slider::-moz-range-thumb {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.4);
  transition: all 0.2s ease;
}

.budget-slider::-moz-range-thumb:hover {
  background: #2563eb;
  transform: scale(1.1);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
}

/* Summary Card */
.summary-card {
  margin-top: 1.5rem;
}

.summary-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.summary-stats {
  display: flex;
  gap: 3rem;
  flex: 1;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.summary-value {
  font-size: 1.875rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.summary-value.negative {
  color: #ef4444;
}

/* Place Order Button */
.place-order-btn {
  padding: 1rem 2.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  transform: none;
}

/* Success Message */
.success-message {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  border-radius: 8px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.success-icon {
  width: 32px;
  height: 32px;
  color: #059669;
  flex-shrink: 0;
}

.success-text {
  color: #065f46;
  font-weight: 600;
  font-size: 1rem;
  margin: 0;
}

/* Empty State */
.empty-state {
  padding: 4rem 2rem;
  text-align: center;
  color: #94a3b8;
  font-size: 1rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

/* Loading State */
.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
}

/* Error State */
.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
