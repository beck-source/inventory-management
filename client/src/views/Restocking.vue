<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Recommended purchases based on forecasted demand, within your budget.</p>
    </div>

    <div class="card controls">
      <div class="control">
        <label for="restock-warehouse">Warehouse</label>
        <select id="restock-warehouse" v-model="warehouse">
          <option v-for="w in warehouses" :key="w" :value="w">{{ w }}</option>
        </select>
      </div>
      <div class="control budget-control">
        <label for="restock-budget">Budget</label>
        <div class="slider-row">
          <input
            id="restock-budget"
            type="range"
            min="0"
            max="500000"
            step="5000"
            v-model.number="budget"
          />
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
      </div>
    </div>

    <div v-if="orderMessage" class="notice success">{{ orderMessage }}</div>
    <div v-if="orderError" class="notice danger">{{ orderError }}</div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="result">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total Cost</div>
          <div class="stat-value">{{ formatCurrency(result.total_cost) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Remaining Budget</div>
          <div class="stat-value">{{ formatCurrency(result.remaining_budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Lead Time</div>
          <div class="stat-value">{{ result.lead_time_days }} days</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ result.items.length }})</h3>
          <button
            class="place-order"
            :disabled="result.items.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing...' : 'Place Order' }}
          </button>
        </div>
        <div v-if="result.items.length === 0" class="empty-state">
          No items are recommended for this warehouse and budget.
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th class="num">Current Stock</th>
                <th class="num">Forecasted Demand</th>
                <th class="num">Shortfall</th>
                <th class="num">Recommended Qty</th>
                <th class="num">Unit Cost</th>
                <th class="num">Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in result.items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td class="num">{{ item.current_stock.toLocaleString() }}</td>
                <td class="num">{{ item.forecasted_demand.toLocaleString() }}</td>
                <td class="num">{{ item.shortfall.toLocaleString() }}</td>
                <td class="num">{{ item.recommended_quantity.toLocaleString() }}</td>
                <td class="num">{{ formatCurrencyWithDecimals(item.unit_cost, 'USD', 2) }}</td>
                <td class="num"><strong>{{ formatCurrency(item.line_total) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const warehouses = ['San Francisco', 'London', 'Tokyo']
const warehouse = ref('San Francisco')
const budget = ref(100000)

const result = ref(null)
const loading = ref(false)
const error = ref(null)
const submitting = ref(false)
const orderMessage = ref('')
const orderError = ref('')

let requestId = 0
let debounceTimer = null

const loadRecommendations = async () => {
  const id = ++requestId
  loading.value = true
  error.value = null
  try {
    const data = await api.getRestockingRecommendations(warehouse.value, budget.value)
    if (id !== requestId) return
    result.value = data
  } catch (err) {
    if (id !== requestId) return
    result.value = null
    error.value = 'Failed to load recommendations: ' + (err.response?.data?.detail || err.message)
  } finally {
    if (id === requestId) loading.value = false
  }
}

watch([warehouse, budget], () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadRecommendations, 300)
})

const formatDate = (value) => {
  const d = new Date(value)
  if (isNaN(d.getTime())) return value
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

const placeOrder = async () => {
  if (!result.value || result.value.items.length === 0 || submitting.value) return
  submitting.value = true
  orderMessage.value = ''
  orderError.value = ''
  try {
    const order = await api.submitRestockingOrder({
      warehouse: warehouse.value,
      items: result.value.items.map(i => ({
        sku: i.sku,
        name: i.name,
        quantity: i.recommended_quantity,
        unit_price: i.unit_cost
      }))
    })
    orderMessage.value = `Order ${order.order_number} placed. Expected delivery: ${formatDate(order.expected_delivery)}.`
    loadRecommendations()
  } catch (err) {
    orderError.value = 'Failed to place order: ' + (err.response?.data?.detail || err.message)
  } finally {
    submitting.value = false
  }
}

onMounted(loadRecommendations)
onBeforeUnmount(() => clearTimeout(debounceTimer))
</script>

<style scoped>
.controls {
  display: flex;
  gap: 2rem;
  align-items: flex-end;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.control {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control label {
  font-size: 0.813rem;
  font-weight: 500;
  color: #64748b;
}

.control select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  color: #0f172a;
}

.budget-control {
  flex: 1;
  max-width: 480px;
}

/* Mobile: stack controls so the budget slider row fits the viewport */
@media (max-width: 767px) {
  .controls {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .budget-control {
    min-width: 0;
    max-width: 100%;
  }
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.slider-row input {
  flex: 1;
}

.budget-value {
  min-width: 90px;
  text-align: right;
  font-weight: 600;
  color: #0f172a;
}

.notice {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.notice.success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.notice.danger {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.place-order {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  background: #0f172a;
  color: white;
  font-weight: 500;
  cursor: pointer;
}

.place-order:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.num {
  text-align: right;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}
</style>
