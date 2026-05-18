<template>
  <div class="restocking">
    <!-- Page header -->
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Budget-driven restock recommendations based on demand forecasts</p>
    </div>

    <!-- Budget control card -->
    <div class="card budget-card">
      <div class="card-header">
        <h3 class="card-title">Available Budget</h3>
      </div>
      <div class="budget-body">
        <div class="budget-display">{{ formatCurrency(budget) }}</div>
        <input type="range" class="budget-slider" min="0" max="500000" step="1000" v-model.number="budget" @input="onBudgetInput" />
        <div class="budget-bar-wrap">
          <div class="budget-bar-track">
            <div class="budget-bar-fill" :style="{ width: utilizationPct + '%' }"></div>
          </div>
          <span class="budget-bar-label">Projected Spend: {{ formatCurrency(totalCost) }} of {{ formatCurrency(budget) }}</span>
        </div>
      </div>
    </div>

    <!-- Success card — shown after placing order -->
    <div v-if="submittedOrder" class="card success-card">
      <div class="success-body">
        <div class="success-title">Restock Order Submitted</div>
        <div class="success-meta">Order: <strong>{{ submittedOrder.order_number }}</strong></div>
        <div class="success-meta">Expected Delivery: <strong>{{ formatDate(submittedOrder.expected_delivery) }}</strong></div>
        <router-link to="/orders" class="view-orders-link">View in Orders</router-link>
      </div>
    </div>

    <!-- Recommendations card -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
        <button
          class="place-order-btn"
          :disabled="recommendations.length === 0 || submitting"
          @click="placeOrder"
        >{{ submitting ? 'Submitting...' : 'Place Order' }}</button>
      </div>

      <div v-if="loading" class="loading-state">Loading recommendations...</div>
      <div v-else-if="recommendations.length === 0" class="empty-state">
        No items fit within this budget. Try increasing the budget.
      </div>
      <div v-else class="table-container">
        <table class="restock-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Item Name</th>
              <th>Trend</th>
              <th class="num-col">Current Demand</th>
              <th class="num-col">Forecasted</th>
              <th class="num-col">Restock Qty</th>
              <th class="num-col">Unit Cost</th>
              <th class="num-col">Line Total</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendations" :key="item.item_sku">
              <td><strong class="sku-cell">{{ item.item_sku }}</strong></td>
              <td>{{ item.item_name }}</td>
              <td><span :class="['badge', trendClass(item.trend)]">{{ item.trend }}</span></td>
              <td class="num-col">{{ item.current_demand.toLocaleString() }}</td>
              <td class="num-col">{{ item.forecasted_demand.toLocaleString() }}</td>
              <td class="num-col"><strong>{{ item.restock_quantity.toLocaleString() }}</strong></td>
              <td class="num-col">{{ formatCurrency(item.unit_cost) }}</td>
              <td class="num-col"><strong>{{ formatCurrency(item.line_total) }}</strong></td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="total-row">
              <td colspan="7" class="total-label">Total Cost</td>
              <td class="num-col total-value">{{ formatCurrency(totalCost) }}</td>
            </tr>
          </tfoot>
        </table>
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
    const budget = ref(50000)
    const recommendations = ref([])
    const loading = ref(false)
    const submitting = ref(false)
    const submittedOrder = ref(null)

    const totalCost = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.line_total, 0)
    )

    // Utilisation capped at 100% to prevent bar overflow
    const utilizationPct = computed(() => {
      if (!budget.value) return 0
      return Math.min(100, (totalCost.value / budget.value) * 100)
    })

    // Debounced fetch — manual timer, no external dependency
    let debounceTimer = null
    const fetchRecommendations = () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(async () => {
        try {
          loading.value = true
          const data = await api.getRestockRecommendations(budget.value)
          recommendations.value = data.recommendations
        } catch (err) {
          console.error('Failed to fetch recommendations:', err)
          recommendations.value = []
        } finally {
          loading.value = false
        }
      }, 400)
    }

    // Trigger fetch on every budget change; immediate: true loads on mount
    watch(budget, fetchRecommendations, { immediate: true })

    const onBudgetInput = (e) => {
      budget.value = Number(e.target.value)
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return
      try {
        submitting.value = true
        submittedOrder.value = await api.createRestockOrder({
          budget: budget.value,
          total_cost: totalCost.value,
          items: recommendations.value.map(r => ({
            item_sku: r.item_sku,
            item_name: r.item_name,
            quantity: r.restock_quantity,
            unit_cost: r.unit_cost,
          }))
        })
        recommendations.value = []
      } catch (err) {
        console.error('Failed to place restock order:', err)
      } finally {
        submitting.value = false
      }
    }

    const formatCurrency = (val) =>
      Number(val).toLocaleString('en-US', { style: 'currency', currency: 'USD' })

    const formatDate = (dateString) =>
      new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })

    // Map trend value to badge class
    const trendClass = (trend) => {
      if (trend === 'increasing') return 'success'
      if (trend === 'decreasing') return 'danger'
      return 'info'
    }

    return {
      budget, recommendations, loading, submitting, submittedOrder,
      totalCost, utilizationPct,
      onBudgetInput, placeOrder,
      formatCurrency, formatDate, trendClass
    }
  }
}
</script>

<style scoped>
/* Budget card body */
.budget-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.budget-display {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

/* Range slider */
.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
  height: 4px;
}

/* Utilisation bar */
.budget-bar-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-bar-track {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 4px;
  overflow: hidden;
}

.budget-bar-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.budget-bar-label {
  font-size: 0.813rem;
  color: #64748b;
}

/* Card header with action button */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

/* Place Order button */
.place-order-btn {
  background: #2563eb;
  color: #fff;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* SKU monospace */
.sku-cell {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 0.813rem;
}

/* Right-aligned numeric columns */
.num-col {
  text-align: right;
}

/* Table footer total row */
.total-row {
  background: #f8fafc;
  border-top: 2px solid #e2e8f0;
}

.total-label {
  text-align: right;
  font-weight: 600;
  color: #0f172a;
  padding-right: 1rem;
}

.total-value {
  font-weight: 700;
  color: #0f172a;
}

/* States */
.loading-state,
.empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

/* Success card */
.success-card {
  border-left: 4px solid #22c55e;
  background: #f0fdf4;
}

.success-body {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.success-title {
  font-weight: 700;
  color: #16a34a;
  font-size: 1rem;
}

.success-meta {
  font-size: 0.875rem;
  color: #15803d;
}

.view-orders-link {
  display: inline-block;
  margin-top: 0.5rem;
  color: #2563eb;
  font-weight: 600;
  font-size: 0.875rem;
  text-decoration: none;
}

.view-orders-link:hover {
  text-decoration: underline;
}

/* Restock table fixed layout */
.restock-table {
  width: 100%;
}
</style>
