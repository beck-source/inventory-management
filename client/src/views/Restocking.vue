<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set a budget and review recommended restock orders based on demand forecasts.</p>
    </div>

    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">Restocking Budget</h3>
      </div>
      <div class="budget-controls">
        <input
          type="range"
          min="5000"
          max="200000"
          step="5000"
          v-model.number="budget"
          class="budget-slider"
        />
        <div class="budget-display">
          <span class="budget-label">Available Budget:</span>
          <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading recommendations...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">Items Recommended</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">Total Cost</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Budget Remaining</div>
          <div class="stat-value">{{ currencySymbol }}{{ budgetRemaining.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? 'Placing...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="successMessage" class="success-banner">
          {{ successMessage }}
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No items fit within the current budget. Try increasing it.
        </div>

        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Quantity</th>
                <th>Unit Cost</th>
                <th>Line Total</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>{{ item.quantity.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td><strong>{{ currencySymbol }}{{ item.line_total.toLocaleString() }}</strong></td>
                <td>
                  <span :class="['badge', getTrendClass(item.trend)]">
                    {{ item.trend }}
                  </span>
                </td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td colspan="4"><strong>Total</strong></td>
                <td><strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong></td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? String.fromCharCode(165) : '$'
    })

    const budget = ref(50000)
    const recommendations = ref([])
    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const successMessage = ref('')

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.line_total, 0)
    })

    const budgetRemaining = computed(() => {
      return budget.value - totalCost.value
    })

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        recommendations.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return
      try {
        placing.value = true
        const order = await api.placeRestockingOrder(budget.value, recommendations.value)
        successMessage.value = 'Order ' + order.order_number + ' placed. Expected delivery in ' + order.lead_time_days + ' days.'
        setTimeout(() => { successMessage.value = '' }, 5000)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    const getTrendClass = (trend) => {
      const map = { increasing: 'success', stable: 'info', decreasing: 'warning' }
      return map[trend] || 'info'
    }

    watch(budget, loadRecommendations)
    onMounted(loadRecommendations)

    return {
      budget,
      recommendations,
      loading,
      error,
      placing,
      successMessage,
      totalCost,
      budgetRemaining,
      currencySymbol,
      placeOrder,
      getTrendClass
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-controls {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #0f172a;
  cursor: pointer;
  border: none;
}

.budget-display {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.budget-label {
  font-size: 0.875rem;
  color: #64748b;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #0f172a;
}

.restock-table {
  width: 100%;
  table-layout: fixed;
}

.restock-table th,
.restock-table td {
  text-align: left;
  padding: 0.75rem 1rem;
}

.total-row {
  border-top: 2px solid #e2e8f0;
  background: #f8fafc;
}

.total-row td {
  padding-top: 1rem;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-banner {
  margin: 1rem;
  padding: 0.75rem 1rem;
  background: #dcfce7;
  border: 1px solid #86efac;
  border-radius: 6px;
  color: #166534;
  font-size: 0.875rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
