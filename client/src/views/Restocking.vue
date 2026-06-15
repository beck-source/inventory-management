<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Set your available budget and get recommendations based on demand forecasts.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Control Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
        </div>
        <div class="budget-controls">
          <div class="slider-input-row">
            <input
              type="range"
              class="budget-slider"
              min="1000"
              max="50000"
              step="1000"
              :value="budget"
              @input="onSliderInput"
            />
            <input
              type="number"
              class="budget-number-input"
              min="1000"
              max="50000"
              step="1000"
              :value="budget"
              @change="onNumberInput"
            />
          </div>
          <div class="budget-display">{{ formatBudgetDisplay(budget) }}</div>
          <div class="budget-range-labels">
            <span>$1,000</span>
            <span>$50,000</span>
          </div>
        </div>
      </div>

      <!-- Recommendations Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items</h3>
          <span class="badge info">
            {{ recommendations.length }} items &middot; {{ formatCurrency(totalCost) }} estimated
          </span>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No items can be recommended within this budget. Try increasing your budget.
        </div>

        <div v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>Item Name</th>
                  <th>SKU</th>
                  <th>Forecasted Demand</th>
                  <th>Unit Cost</th>
                  <th>Qty to Order</th>
                  <th>Est. Cost</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations" :key="item.sku">
                  <td><strong>{{ item.name }}</strong></td>
                  <td><span class="sku-label">{{ item.sku }}</span></td>
                  <td>{{ item.quantity.toLocaleString() }}</td>
                  <td>{{ formatCurrency(item.unit_cost) }}</td>
                  <td><strong>{{ item.quantity.toLocaleString() }}</strong></td>
                  <td><strong>{{ formatCurrency(item.total_cost) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="budget-summary">
            <span class="summary-text">
              {{ recommendations.length }} items selected &middot;
              {{ formatCurrency(totalCost) }} of {{ formatBudgetDisplay(budget) }} budget used
              ({{ budgetUsedPercent }}%)
            </span>
            <div class="budget-progress-bar">
              <div
                class="budget-progress-fill"
                :style="{ width: Math.min(budgetUsedPercent, 100) + '%' }"
                :class="{ 'over-budget': budgetUsedPercent > 100 }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Place Order Section -->
      <div class="order-action-section">
        <div v-if="successMessage" class="success-banner">
          {{ successMessage }}
        </div>
        <div v-if="errorMessage" class="error">
          {{ errorMessage }}
        </div>
        <button
          class="place-order-btn"
          :disabled="recommendations.length === 0 || submitting || !!successMessage"
          @click="placeOrder"
        >
          {{ submitting ? 'Placing Order...' : 'Place Order' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(10000)
    const forecasts = ref([])
    const inventory = ref([])
    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref('')
    const errorMessage = ref('')

    const formatCurrency = (val) =>
      '$' + val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const formatBudgetDisplay = (val) =>
      '$' + val.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })

    const onSliderInput = (e) => {
      budget.value = Number(e.target.value)
    }

    const onNumberInput = (e) => {
      const clamped = Math.max(1000, Math.min(50000, Number(e.target.value) || 1000))
      budget.value = clamped
      e.target.value = clamped
    }

    const inventoryMap = computed(() => {
      const map = new Map()
      inventory.value.forEach(item => map.set(item.sku, item.unit_cost))
      return map
    })

    const recommendations = computed(() => {
      const sorted = [...forecasts.value].sort((a, b) => b.forecasted_demand - a.forecasted_demand)
      let remaining = budget.value
      const result = []
      for (const f of sorted) {
        const unitCost = inventoryMap.value.get(f.item_sku)
        if (unitCost === undefined) continue
        const totalCost = f.forecasted_demand * unitCost
        if (remaining >= totalCost) {
          result.push({
            sku: f.item_sku,
            name: f.item_name,
            quantity: f.forecasted_demand,
            unit_cost: unitCost,
            total_cost: totalCost
          })
          remaining -= totalCost
        }
      }
      return result
    })

    const totalCost = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.total_cost, 0)
    )

    const budgetUsedPercent = computed(() =>
      Math.round((totalCost.value / budget.value) * 100)
    )

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        forecasts.value = forecastsData
        inventory.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load data. Please try again.'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      errorMessage.value = ''
      try {
        const order = await api.createRestockingOrder({
          items: recommendations.value,
          budget: budget.value
        })
        successMessage.value = `Order ${order.order_number} placed successfully! Expected delivery in 7 days.`
        setTimeout(() => {
          successMessage.value = ''
        }, 5000)
      } catch (err) {
        errorMessage.value = 'Failed to place order. Please try again.'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      budget,
      forecasts,
      inventory,
      loading,
      error,
      submitting,
      successMessage,
      errorMessage,
      recommendations,
      totalCost,
      budgetUsedPercent,
      formatCurrency,
      formatBudgetDisplay,
      onSliderInput,
      onNumberInput,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding-bottom: 2rem;
}

.budget-controls {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.slider-input-row {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
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
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.4);
}

.budget-number-input {
  width: 120px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
  text-align: right;
  outline: none;
  transition: border-color 0.2s;
  flex-shrink: 0;
}

.budget-number-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
  margin-top: -0.25rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #64748b;
  font-size: 0.938rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}

.sku-label {
  font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 0.813rem;
  color: #475569;
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.budget-summary {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.summary-text {
  font-size: 0.875rem;
  color: #475569;
  font-weight: 500;
}

.budget-progress-bar {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.budget-progress-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.budget-progress-fill.over-budget {
  background: #dc2626;
}

.order-action-section {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1rem;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 500;
  width: 100%;
}

.place-order-btn {
  background: #2563eb;
  color: #ffffff;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  border: none;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
  font-family: inherit;
  letter-spacing: -0.01em;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
