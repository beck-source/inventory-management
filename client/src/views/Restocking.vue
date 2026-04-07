<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Recommend items to restock based on demand trends and available budget</p>
    </div>

    <!-- Success banner -->
    <div v-if="successMessage" class="success-banner">
      <span>{{ successMessage }}</span>
      <button class="banner-close" @click="successMessage = ''">&#x2715;</button>
    </div>

    <!-- Budget section -->
    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">Available Budget</h3>
      </div>
      <div class="budget-controls">
        <div class="slider-row">
          <input
            type="range"
            class="budget-slider"
            min="10000"
            max="500000"
            step="10000"
            v-model.number="budget"
          />
          <span class="budget-display">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="slider-labels">
          <span>$10K</span>
          <span>$500K</span>
        </div>
      </div>
    </div>

    <!-- Summary stats -->
    <div v-if="!loading && recommendations.length > 0" class="stats-grid">
      <div class="stat-card info">
        <div class="stat-label">Items to Restock</div>
        <div class="stat-value">{{ recommendations.length }}</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-label">Total Cost</div>
        <div class="stat-value">{{ formatCurrency(totalCost) }}</div>
      </div>
      <div class="stat-card" :class="remainingBudget >= 0 ? 'success' : 'danger'">
        <div class="stat-label">Remaining Budget</div>
        <div class="stat-value">{{ formatCurrency(remainingBudget) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Avg Unit Cost</div>
        <div class="stat-value">{{ formatCurrency(avgUnitCost) }}</div>
      </div>
    </div>

    <!-- Recommendations table -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recommended Restocking</h3>
      </div>

      <div v-if="loading" class="loading">Loading recommendations...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="recommendations.length === 0" class="empty-state">
        Adjust the budget slider to see restocking recommendations
      </div>
      <div v-else class="table-container">
        <table class="restock-table">
          <thead>
            <tr>
              <th class="col-item">Item / SKU</th>
              <th class="col-category">Category</th>
              <th class="col-warehouse">Warehouse</th>
              <th class="col-num">On Hand</th>
              <th class="col-num">Reorder Point</th>
              <th class="col-num">Qty to Order</th>
              <th class="col-cost">Unit Cost</th>
              <th class="col-cost">Total Cost</th>
              <th class="col-trend">Demand Trend</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendations" :key="item.sku">
              <td class="col-item">
                <div class="item-name">{{ item.name }}</div>
                <div class="item-sku">{{ item.sku }}</div>
              </td>
              <td class="col-category">{{ item.category }}</td>
              <td class="col-warehouse">{{ item.warehouse }}</td>
              <td class="col-num">{{ item.quantity_on_hand.toLocaleString() }}</td>
              <td class="col-num">{{ item.reorder_point.toLocaleString() }}</td>
              <td class="col-num"><strong>{{ item.quantity_to_order.toLocaleString() }}</strong></td>
              <td class="col-cost">${{ item.unit_cost.toFixed(2) }}</td>
              <td class="col-cost"><strong>${{ item.total_cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong></td>
              <td class="col-trend">
                <span :class="['badge', item.trend]">{{ item.trend }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Place Order button -->
      <div class="order-actions">
        <button
          class="btn-place-order"
          :disabled="recommendations.length === 0 || submitting"
          @click="placeOrder"
        >
          <span v-if="submitting">Placing Order...</span>
          <span v-else>Place Restocking Order ({{ formatCurrency(totalCost) }})</span>
        </button>
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

    const budget = ref(150000)
    const recommendations = ref([])
    const loading = ref(false)
    const error = ref(null)
    const submitting = ref(false)
    const successMessage = ref('')

    let debounceTimer = null

    const formatCurrency = (value) => {
      const symbol = currentCurrency.value === 'JPY' ? '¥' : '$'
      return symbol + Number(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })
    }

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.total_cost, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - totalCost.value
    })

    const avgUnitCost = computed(() => {
      if (recommendations.value.length === 0) return 0
      const total = recommendations.value.reduce((sum, item) => sum + item.unit_cost, 0)
      return total / recommendations.value.length
    })

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockingRecommendations(budget.value)
        recommendations.value = data
      } catch (err) {
        error.value = 'Failed to load recommendations'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || submitting.value) return
      submitting.value = true
      error.value = null
      try {
        const items = recommendations.value.map(r => ({
          sku: r.sku,
          name: r.name,
          quantity: r.quantity_to_order,
          unit_price: r.unit_cost
        }))
        const result = await api.submitRestockingOrder({
          items,
          total_value: totalCost.value
        })

        const deliveryDate = result.expected_delivery
          ? formatDate(result.expected_delivery)
          : 'N/A'
        successMessage.value = `Order ${result.order_number} placed successfully. Expected delivery: ${deliveryDate}`

        // Reload recommendations after placing order
        await loadRecommendations()
      } catch (err) {
        error.value = 'Failed to place order'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'N/A'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return 'N/A'
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    }

    watch(budget, () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 400)
    })

    onMounted(() => {
      loadRecommendations()
    })

    return {
      budget,
      recommendations,
      loading,
      error,
      submitting,
      successMessage,
      totalCost,
      remainingBudget,
      avgUnitCost,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.success-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

.banner-close {
  background: none;
  border: none;
  color: #065f46;
  cursor: pointer;
  font-size: 1rem;
  padding: 0 0.25rem;
  line-height: 1;
}

.banner-close:hover {
  color: #064e3b;
}

.budget-card {
  margin-bottom: 1.25rem;
}

.budget-controls {
  padding: 0.5rem 0;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  cursor: pointer;
  outline: none;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 130px;
  text-align: right;
  letter-spacing: -0.025em;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.restock-table {
  table-layout: fixed;
  width: 100%;
}

.col-item {
  width: 220px;
}

.col-category {
  width: 150px;
}

.col-warehouse {
  width: 130px;
}

.col-num {
  width: 100px;
  text-align: right;
}

.col-cost {
  width: 110px;
  text-align: right;
}

.col-trend {
  width: 120px;
}

.item-name {
  font-size: 0.875rem;
  font-weight: 500;
  color: #0f172a;
}

.item-sku {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.125rem;
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 1rem;
  margin-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.btn-place-order {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-place-order:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-place-order:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
</style>
