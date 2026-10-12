<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Get budget-aware restocking recommendations based on demand forecasts and current inventory gaps</p>
    </div>

    <div v-if="loading" class="loading">Loading restocking recommendations...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Budget</h3>
        </div>
        <div class="budget-controls">
          <input
            type="range"
            class="budget-slider"
            min="0"
            :max="maxBudget"
            step="10"
            v-model.number="budget"
          />
          <div class="budget-figures">
            <div class="budget-value">${{ budget.toLocaleString() }}</div>
            <div class="budget-max">of ${{ maxBudget.toLocaleString() }} max</div>
          </div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">Budget Used</div>
          <div class="stat-value">${{ budgetUsed.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Budget Remaining</div>
          <div class="stat-value">${{ (budget - budgetUsed).toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Recommended Items</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommendations ({{ recommendations.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="submitSuccess" class="submit-success">{{ submitSuccess }}</div>
        <div v-if="submitError" class="submit-error">{{ submitError }}</div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No urgent restocking needs within this budget.
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Category</th>
                <th>Gap</th>
                <th>Recommended Qty</th>
                <th>Unit Cost</th>
                <th>Line Cost</th>
                <th>Lead Time (days)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ rec.name }}</td>
                <td>{{ rec.category }}</td>
                <td>{{ rec.gap }}</td>
                <td>{{ rec.recommended_quantity }}</td>
                <td>${{ rec.unit_cost.toLocaleString() }}</td>
                <td>${{ rec.line_cost.toLocaleString() }}</td>
                <td>{{ rec.lead_time_days }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)

    const maxBudget = ref(0)
    const budget = ref(0)
    const budgetUsed = ref(0)
    const recommendations = ref([])

    const submitting = ref(false)
    const submitSuccess = ref(null)
    const submitError = ref(null)

    let debounceTimer = null
    let initializing = true

    const loadRecommendations = async (budgetValue) => {
      try {
        const data = await api.getRestockRecommendations(budgetValue)
        budgetUsed.value = data.budget_used
        recommendations.value = data.recommendations
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      }
    }

    const init = async () => {
      try {
        loading.value = true
        // Call with no budget to bootstrap the max slider value
        const bootstrapData = await api.getRestockRecommendations()
        maxBudget.value = bootstrapData.max_budget
        budget.value = bootstrapData.max_budget
        budgetUsed.value = bootstrapData.budget_used
        recommendations.value = bootstrapData.recommendations
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
        initializing = false
      }
    }

    watch(budget, (newBudget) => {
      // Skip the change fired by init() setting the bootstrapped budget -
      // that call's data is already loaded, no need to refetch it.
      if (initializing) return
      submitSuccess.value = null
      submitError.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations(newBudget)
      }, 350)
    })

    onUnmounted(() => {
      clearTimeout(debounceTimer)
    })

    const placeOrder = async () => {
      submitting.value = true
      submitSuccess.value = null
      submitError.value = null
      try {
        const orderData = {
          budget: budget.value,
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.recommended_quantity,
            unit_price: r.unit_cost
          }))
        }
        const order = await api.submitRestockingOrder(orderData)
        submitSuccess.value = `Order ${order.order_number} placed successfully (${order.items.length} items, $${order.total_value.toLocaleString()}).`
      } catch (err) {
        submitError.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(init)

    return {
      loading,
      error,
      maxBudget,
      budget,
      budgetUsed,
      recommendations,
      submitting,
      submitSuccess,
      submitError,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-controls {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 6px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  border: 1px solid #cbd5e1;
  outline: none;
  cursor: pointer;
  transition: all 0.2s;
}

.budget-slider:hover {
  border-color: #94a3b8;
}

.budget-slider:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-figures {
  flex-shrink: 0;
  text-align: right;
  min-width: 160px;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-max {
  font-size: 0.813rem;
  color: #64748b;
}

.place-order-btn {
  padding: 0.5rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.submit-success {
  background: #d1fae5;
  color: #065f46;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.submit-error {
  background: #fee2e2;
  color: #991b1b;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}
</style>
