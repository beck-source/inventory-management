<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()

const budget = ref(50000)
const forecasts = ref([])
const inventoryItems = ref([])
const loading = ref(true)
const error = ref(null)
const submitting = ref(false)
const submitted = ref(false)
const submittedOrder = ref(null)

// --- Data loading ---

const loadData = async () => {
  loading.value = true
  error.value = null
  try {
    const [forecastData, inventoryData] = await Promise.all([
      api.getDemandForecasts(),
      api.getInventory()
    ])
    forecasts.value = forecastData
    inventoryItems.value = inventoryData
  } catch (err) {
    error.value = 'Failed to load restocking data. Please try again.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(() => loadData())

// --- Recommendation algorithm ---

const trendPriority = { increasing: 0, stable: 1, decreasing: 2 }

const recommendations = computed(() => {
  const invMap = new Map(inventoryItems.value.map(inv => [inv.sku, inv]))

  const recs = []
  for (const forecast of forecasts.value) {
    const inv = invMap.get(forecast.item_sku)
    if (!inv) continue

    const restock_qty = Math.max(0, forecast.forecasted_demand - inv.quantity_on_hand)
    if (restock_qty <= 0) continue

    const item_total_cost = restock_qty * inv.unit_cost

    recs.push({
      sku: forecast.item_sku,
      name: forecast.item_name,
      trend: forecast.trend,
      current_demand: forecast.current_demand,
      forecasted_demand: forecast.forecasted_demand,
      quantity_on_hand: inv.quantity_on_hand,
      restock_qty,
      unit_cost: inv.unit_cost,
      item_total_cost,
      category: inv.category,
      warehouse: inv.warehouse,
      reorder_point: inv.reorder_point ?? 0
    })
  }

  recs.sort((a, b) => {
    const trendDiff = (trendPriority[a.trend] ?? 1) - (trendPriority[b.trend] ?? 1)
    if (trendDiff !== 0) return trendDiff
    const urgencyA = a.quantity_on_hand - a.reorder_point
    const urgencyB = b.quantity_on_hand - b.reorder_point
    return urgencyA - urgencyB
  })

  return recs
})

// --- Budget slider max ---

const maxBudget = computed(() => {
  const total = recommendations.value.reduce((sum, r) => sum + r.item_total_cost, 0)
  return total > 0 ? Math.ceil(total / 1000) * 1000 : 500000
})

// --- Greedy budget selection ---

const withinBudget = computed(() => {
  let accumulated = 0
  const selected = []
  for (const rec of recommendations.value) {
    if (accumulated + rec.item_total_cost <= budget.value) {
      accumulated += rec.item_total_cost
      selected.push(rec)
    }
  }
  return selected
})

const selectedTotal = computed(() =>
  withinBudget.value.reduce((sum, r) => sum + r.item_total_cost, 0)
)

const withinBudgetSkus = computed(() => new Set(withinBudget.value.map(r => r.sku)))

// --- Currency formatter ---

const formatCurrency = (value) =>
  value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

// --- Place Order ---

const placeOrder = async () => {
  if (submitting.value || withinBudget.value.length === 0) return

  submitting.value = true
  error.value = null
  try {
    const payload = {
      order_number: 'RST-' + Date.now(),
      customer: 'Internal Restocking',
      status: 'Restocking',
      order_date: new Date().toISOString(),
      expected_delivery: new Date(Date.now() + 14 * 86400000).toISOString(),
      total_value: selectedTotal.value,
      warehouse: null,
      category: null,
      items: withinBudget.value.map(r => ({
        sku: r.sku,
        name: r.name,
        quantity: r.restock_qty,
        unit_price: r.unit_cost
      }))
    }
    const result = await api.createOrder(payload)
    submittedOrder.value = result
    submitted.value = true
  } catch (err) {
    error.value = 'Failed to place order. Please try again.'
    console.error(err)
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  submitted.value = false
  submittedOrder.value = null
}

const formatDeliveryDate = (isoString) => {
  const date = new Date(isoString)
  if (isNaN(date.getTime())) return isoString
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<template>
  <div class="restocking">
    <!-- Page header -->
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Cross-reference demand forecasts with current inventory to build prioritized restock orders.</p>
    </div>

    <!-- Loading / error -->
    <div v-if="loading" class="loading">Loading restocking data...</div>
    <div v-else-if="error && !submitted" class="error">{{ error }}</div>

    <!-- Success state -->
    <div v-else-if="submitted && submittedOrder" class="success-card">
      <div class="success-icon-wrap">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
          <circle cx="16" cy="16" r="16" fill="#d1fae5"/>
          <path d="M9 16.5l4.5 4.5 9-9" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <h3 class="success-heading">Order Submitted</h3>
      <p class="success-detail">
        Order number: <strong>{{ submittedOrder.order_number }}</strong>
      </p>
      <p class="success-detail">
        Expected delivery: <strong>{{ formatDeliveryDate(submittedOrder.expected_delivery) }}</strong>
      </p>
      <div class="success-actions">
        <router-link to="/orders" class="btn-primary">View in Orders</router-link>
        <button class="btn-secondary" @click="resetForm">Place Another Order</button>
      </div>
    </div>

    <!-- Main content -->
    <div v-else>
      <!-- Budget card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
          <span class="budget-display">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="slider-wrap">
          <input
            type="range"
            v-model.number="budget"
            :min="0"
            :max="maxBudget"
            :step="1000"
            class="budget-slider"
          />
          <div class="slider-labels">
            <span>$0</span>
            <span>{{ formatCurrency(maxBudget) }}</span>
          </div>
        </div>
        <div class="budget-summary">
          <span class="budget-count">
            <strong>{{ withinBudget.length }}</strong> item{{ withinBudget.length !== 1 ? 's' : '' }} selected
          </span>
          <span class="budget-meta">
            {{ formatCurrency(selectedTotal) }} of {{ formatCurrency(budget) }} budget
          </span>
        </div>
      </div>

      <!-- Recommendations table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            Recommended Items
            <span class="card-count">({{ recommendations.length }} total, {{ withinBudget.length }} within budget)</span>
          </h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          No restocking recommendations at this time. All items have sufficient stock to meet forecasted demand.
        </div>

        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>Trend</th>
                <th>Current Stock</th>
                <th>Forecasted</th>
                <th>Restock Qty</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="rec in recommendations"
                :key="rec.sku"
                :class="{ 'row-excluded': !withinBudgetSkus.has(rec.sku) }"
              >
                <td>
                  <div class="item-name">{{ rec.name }}</div>
                  <div class="item-sku">{{ rec.sku }}</div>
                </td>
                <td>
                  <span
                    class="trend-badge"
                    :class="'trend-' + rec.trend"
                  >{{ rec.trend.charAt(0).toUpperCase() + rec.trend.slice(1) }}</span>
                </td>
                <td>{{ rec.quantity_on_hand.toLocaleString() }}</td>
                <td><strong>{{ rec.forecasted_demand.toLocaleString() }}</strong></td>
                <td><strong>{{ rec.restock_qty.toLocaleString() }}</strong></td>
                <td>{{ formatCurrency(rec.unit_cost) }}</td>
                <td>{{ formatCurrency(rec.item_total_cost) }}</td>
                <td class="status-cell">
                  <span v-if="withinBudgetSkus.has(rec.sku)" class="status-included" title="Within budget">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-label="Within budget">
                      <circle cx="8" cy="8" r="8" fill="#d1fae5"/>
                      <path d="M4.5 8.5l2.5 2.5 4.5-4.5" stroke="#059669" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </span>
                  <span v-else class="status-excluded">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Action area -->
        <div class="action-area">
          <div v-if="error" class="error action-error">{{ error }}</div>
          <button
            class="btn-primary btn-place-order"
            :disabled="submitting || withinBudget.length === 0"
            @click="placeOrder"
          >
            <span v-if="submitting">Placing order...</span>
            <span v-else-if="withinBudget.length === 0">No items selected</span>
            <span v-else>
              Place order for {{ withinBudget.length }} item{{ withinBudget.length !== 1 ? 's' : '' }} — {{ formatCurrency(selectedTotal) }}
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.restocking {
  /* inherits .main-content padding from App.vue */
}

/* Budget card */
.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.slider-wrap {
  margin: 0.75rem 0 0.5rem;
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
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.35);
  cursor: pointer;
  transition: box-shadow 0.15s;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.45);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #fff;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.35);
  cursor: pointer;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.375rem;
}

.budget-summary {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  margin-top: 0.75rem;
  padding-top: 0.875rem;
  border-top: 1px solid #f1f5f9;
}

.budget-count {
  font-size: 0.9375rem;
  color: #334155;
}

.budget-meta {
  font-size: 0.875rem;
  color: #64748b;
}

/* Card count label */
.card-count {
  font-size: 0.875rem;
  font-weight: 400;
  color: #64748b;
  margin-left: 0.5rem;
}

/* Item cell */
.item-name {
  font-weight: 600;
  color: #0f172a;
  font-size: 0.875rem;
}

.item-sku {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.125rem;
}

/* Trend badges */
.trend-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.trend-increasing {
  background: #d1fae5;
  color: #065f46;
}

.trend-stable {
  background: #e2e8f0;
  color: #334155;
}

.trend-decreasing {
  background: #fecaca;
  color: #991b1b;
}

/* Row dimming for excluded items */
.row-excluded {
  opacity: 0.4;
}

/* Status cell */
.status-cell {
  text-align: center;
}

.status-included {
  display: inline-flex;
  align-items: center;
}

.status-excluded {
  color: #cbd5e1;
  font-size: 1rem;
}

/* Empty state */
.empty-state {
  padding: 2.5rem 1.5rem;
  text-align: center;
  color: #64748b;
  font-size: 0.9375rem;
}

/* Action area */
.action-area {
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.75rem;
}

.action-error {
  width: 100%;
  margin: 0;
}

/* Buttons */
.btn-primary {
  display: inline-block;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 10px 20px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.15s, opacity 0.15s;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-place-order {
  min-width: 260px;
  text-align: center;
}

.btn-secondary {
  display: inline-block;
  background: #ffffff;
  color: #334155;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 10px 20px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, border-color 0.15s;
}

.btn-secondary:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

/* Success card */
.success-card {
  background: #ffffff;
  border: 1px solid #a7f3d0;
  border-left: 4px solid #10b981;
  border-radius: 10px;
  padding: 2.5rem 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.875rem;
  max-width: 520px;
  margin: 2rem auto;
}

.success-icon-wrap {
  margin-bottom: 0.25rem;
}

.success-heading {
  font-size: 1.375rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.success-detail {
  font-size: 0.9375rem;
  color: #334155;
}

.success-actions {
  display: flex;
  gap: 0.875rem;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 0.5rem;
}
</style>
