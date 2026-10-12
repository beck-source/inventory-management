<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Set your budget and we'll recommend items to restock — items below reorder point first, then those with increasing demand.</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Available Budget</h3>
      </div>
      <div class="budget-display">{{ formatCurrency(budget) }}</div>
      <input
        type="range"
        min="0"
        max="100000"
        step="1000"
        v-model.number="budget"
        class="budget-slider"
      />
      <div class="slider-marks">
        <span>$0</span>
        <span>$100K</span>
      </div>
    </div>

    <div v-if="!submitted">
      <div v-if="loading && recommendations.length === 0" class="loading">Loading recommendations...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <template v-else>
        <div class="stats-grid">
          <div class="stat-card info">
            <div class="stat-label">Items to restock</div>
            <div class="stat-value">{{ itemsCount }}</div>
          </div>
          <div class="stat-card warning">
            <div class="stat-label">Total cost</div>
            <div class="stat-value">{{ formatCurrency(totalCost) }}</div>
          </div>
          <div :class="['stat-card', budgetRemaining >= 0 ? 'success' : 'danger']">
            <div class="stat-label">Budget remaining</div>
            <div class="stat-value">{{ formatCurrency(budgetRemaining) }}</div>
          </div>
        </div>

        <div :class="['card', { 'loading-overlay': loading && recommendations.length > 0 }]">
          <div class="card-header">
            <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
          </div>
          <div v-if="recommendations.length === 0" class="empty-state">
            No items fit in this budget. Try increasing the budget.
          </div>
          <div v-else class="table-container">
            <table class="restock-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Warehouse</th>
                  <th>Stock (curr / reorder)</th>
                  <th>Qty to Order</th>
                  <th>Unit Cost</th>
                  <th>Line Cost</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations" :key="item.sku">
                  <td class="sku-cell">{{ item.sku }}</td>
                  <td>{{ translateProductName(item.name) }}</td>
                  <td>{{ item.category }}</td>
                  <td>{{ item.warehouse }}</td>
                  <td class="stock-cell">
                    <span :class="{ deficit: item.current_quantity < item.reorder_point }">{{ item.current_quantity }}</span>
                    <span class="stock-sep"> / </span>
                    <span>{{ item.reorder_point }}</span>
                  </td>
                  <td><strong>{{ item.quantity_to_order }}</strong></td>
                  <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                  <td><strong>{{ formatCurrency(item.line_cost) }}</strong></td>
                  <td>
                    <span :class="['badge', item.reason === 'below_reorder_point' ? 'danger' : 'info']">
                      {{ item.reason === 'below_reorder_point' ? 'Below reorder' : 'Trend up' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="place-order-bar">
          <button
            class="btn-primary"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing order...' : `Place Order (${formatCurrency(totalCost)})` }}
          </button>
        </div>
      </template>
    </div>

    <div v-else class="card success-card">
      <div class="card-header">
        <h3 class="card-title">Order placed</h3>
      </div>
      <div class="success-details">
        <div class="success-row">
          <span class="success-label">Order number</span>
          <span class="success-value mono">{{ submittedOrder.order_number }}</span>
        </div>
        <div class="success-row">
          <span class="success-label">Total cost</span>
          <span class="success-value">{{ formatCurrency(submittedOrder.total_cost) }}</span>
        </div>
        <div class="success-row">
          <span class="success-label">Items ordered</span>
          <span class="success-value">{{ submittedOrder.total_items }}</span>
        </div>
        <div class="success-row">
          <span class="success-label">Expected delivery</span>
          <span class="success-value">{{ formatDate(submittedOrder.expected_delivery) }}</span>
        </div>
        <div class="success-row">
          <span class="success-label">Lead time</span>
          <span class="success-value">{{ submittedOrder.max_lead_time_days }} days</span>
        </div>
      </div>
      <p class="success-hint">View it in the Orders tab under Submitted Restocking Orders.</p>
      <div class="place-order-bar">
        <button class="btn-outline" @click="resetAndReload">Plan another order</button>
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
    const { t, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const budget = ref(50000)
    const loading = ref(false)
    const error = ref(null)
    const recommendations = ref([])
    const itemsCount = ref(0)
    const totalCost = ref(0)

    const submitting = ref(false)
    const submitted = ref(false)
    const submittedOrder = ref(null)

    const budgetRemaining = computed(() => budget.value - totalCost.value)

    const formatCurrency = (value) =>
      `${currencySymbol.value}${Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}`

    const formatDate = (dateString) => {
      const d = new Date(dateString)
      if (isNaN(d.getTime())) return dateString
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const loadRecommendations = async () => {
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockingRecommendations(budget.value)
        recommendations.value = data.recommendations
        itemsCount.value = data.items_count
        totalCost.value = data.total_cost
      } catch (err) {
        error.value = 'Failed to load recommendations. Please check that the backend is running.'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      error.value = null
      try {
        const items = recommendations.value.map(item => ({
          sku: item.sku,
          name: item.name,
          category: item.category,
          warehouse: item.warehouse,
          unit_cost: item.unit_cost,
          quantity: item.quantity_to_order
        }))
        const result = await api.submitRestockingOrder({ items, budget: budget.value })
        submittedOrder.value = result
        submitted.value = true
      } catch (err) {
        error.value = 'Failed to submit order. Please try again.'
        console.error(err)
      } finally {
        submitting.value = false
      }
    }

    const resetAndReload = () => {
      submitted.value = false
      submittedOrder.value = null
      loadRecommendations()
    }

    // Debounce slider changes to avoid hammering the API on every tick
    let debounceTimer = null
    watch(budget, () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadRecommendations, 300)
    })

    onMounted(() => loadRecommendations())

    return {
      t,
      currencySymbol,
      budget,
      loading,
      error,
      recommendations,
      itemsCount,
      totalCost,
      budgetRemaining,
      submitting,
      submitted,
      submittedOrder,
      formatCurrency,
      formatDate,
      placeOrder,
      resetAndReload,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-display {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 1rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  height: 6px;
}

.slider-marks {
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 0.813rem;
  margin-top: 0.5rem;
}

.loading-overlay {
  opacity: 0.6;
  pointer-events: none;
  transition: opacity 0.2s;
}

.sku-cell {
  font-family: 'Courier New', Courier, monospace;
  color: #475569;
  font-size: 0.813rem;
}

.stock-cell .deficit {
  color: #dc2626;
  font-weight: 600;
}

.stock-sep {
  color: #94a3b8;
}

.place-order-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.btn-primary {
  padding: 0.875rem 1.75rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #1e293b;
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-card {
  border-left: 4px solid #059669;
}

.empty-state {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #64748b;
  font-size: 0.938rem;
}

.success-details {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}

.success-row {
  display: flex;
  gap: 1rem;
  align-items: baseline;
}

.success-label {
  width: 160px;
  flex-shrink: 0;
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.success-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 600;
}

.success-value.mono {
  font-family: 'Courier New', Courier, monospace;
  color: #475569;
}

.success-hint {
  font-size: 0.813rem;
  color: #94a3b8;
  margin-bottom: 1.25rem;
}

.btn-outline {
  padding: 0.625rem 1.5rem;
  background: white;
  color: #0f172a;
  border: 1.5px solid #0f172a;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-outline:hover {
  background: #f1f5f9;
}

.restock-table {
  width: 100%;
  border-collapse: collapse;
}
</style>
