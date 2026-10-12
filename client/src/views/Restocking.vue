<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set a budget and get smart restocking recommendations based on demand forecasts.</p>
    </div>

    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">Budget Allocation</h3>
        <span class="budget-display">${{ budget.toLocaleString() }}</span>
      </div>
      <div class="slider-section">
        <div class="slider-labels">
          <span>$0</span>
          <span>$500K</span>
        </div>
        <input
          type="range"
          class="budget-slider"
          min="0"
          max="500000"
          step="5000"
          v-model.number="budget"
        />
      </div>
      <div class="budget-meta">
        <span>Estimated spend: <strong>${{ estimatedSpend.toLocaleString() }}</strong></span>
        <span>Items covered: <strong>{{ recommendations.length }}</strong></span>
        <span>Remaining: <strong>${{ remaining.toLocaleString() }}</strong></span>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading recommendations...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
          <button
            class="btn-primary"
            :disabled="recommendations.length === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          <p>No items can be restocked within this budget. Try increasing the budget.</p>
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Current Stock</th>
                <th>Forecasted Demand</th>
                <th>Restock Qty</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
                <th>Trend</th>
                <th>Priority</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>{{ item.current_stock.toLocaleString() }}</td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td><strong>{{ item.restock_quantity.toLocaleString() }}</strong></td>
                <td>${{ item.unit_cost.toFixed(2) }}</td>
                <td><strong>${{ item.total_cost.toLocaleString() }}</strong></td>
                <td>
                  <span :class="['badge', trendClass(item.trend)]">{{ item.trend }}</span>
                </td>
                <td>
                  <span :class="['badge', item.priority]">{{ item.priority }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="successMessage" class="success-banner">
        {{ successMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { api } from '../api'

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(100000)
    const recommendations = ref([])
    const loading = ref(false)
    const error = ref(null)
    const placing = ref(false)
    const successMessage = ref('')

    const estimatedSpend = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.total_cost, 0)
    )

    const remaining = computed(() => Math.max(0, budget.value - estimatedSpend.value))

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

    let debounceTimer = null
    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 300)
    }, { immediate: true })

    const trendClass = (trend) => {
      return { increasing: 'increasing', stable: 'stable', decreasing: 'decreasing' }[trend] || 'info'
    }

    const placeOrder = async () => {
      try {
        placing.value = true
        successMessage.value = ''
        const items = recommendations.value.map(r => ({
          sku: r.sku,
          item_name: r.item_name,
          quantity: r.restock_quantity,
          unit_cost: r.unit_cost
        }))
        await api.placeRestockingOrder(items, budget.value)
        successMessage.value = `Order placed for ${items.length} item(s) totaling $${estimatedSpend.value.toLocaleString()}. Check the Orders tab for delivery details.`
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    return {
      budget,
      recommendations,
      loading,
      error,
      placing,
      successMessage,
      estimatedSpend,
      remaining,
      trendClass,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
}

.slider-section {
  padding: 0.5rem 0 0.75rem;
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
  -webkit-appearance: none;
  appearance: none;
  background: #e2e8f0;
  border-radius: 3px;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.4);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: none;
}

.budget-meta {
  display: flex;
  gap: 2rem;
  font-size: 0.875rem;
  color: #475569;
  padding-top: 0.5rem;
  border-top: 1px solid #f1f5f9;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.empty-state {
  padding: 2.5rem;
  text-align: center;
  color: #64748b;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  margin-top: 1rem;
}
</style>
