<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Allocate your budget across high-demand items and submit a restocking order.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Success banner -->
      <div v-if="orderPlaced" class="success-banner">
        Order {{ lastOrderNumber }} submitted. Expected delivery: {{ lastDeliveryDate }}.
      </div>

      <!-- Budget section -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Available Budget</h3>
        </div>
        <div class="budget-body">
          <div class="stat-value budget-display">{{ formattedBudget }}</div>
          <div class="slider-wrapper">
            <input
              type="range"
              min="0"
              max="500000"
              step="1000"
              v-model.number="budget"
              class="budget-slider"
            />
            <div class="slider-labels">
              <span class="stat-label">{{ currencySymbol }}0</span>
              <span class="stat-label">{{ currencySymbol }}500,000</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recommendations section -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items</h3>
          <span class="summary-badge">
            {{ recommendedItems.length }} items &middot; Total: {{ formattedTotalCost }}
          </span>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Trend</th>
                <th>Qty to Order</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="recommendedItems.length === 0">
                <td colspan="6" class="empty-state">No items fit within the current budget. Increase the budget to see recommendations.</td>
              </tr>
              <tr v-for="item in recommendedItems" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
                <td>{{ item.qty_to_order }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td>{{ formatCurrency(item.item_total) }}</td>
              </tr>
            </tbody>
            <tfoot v-if="recommendedItems.length > 0">
              <tr class="total-row">
                <td colspan="5" class="total-label">Total Cost</td>
                <td class="total-value">{{ formattedTotalCost }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
        <div class="card-footer">
          <button
            class="btn-primary"
            :disabled="recommendedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Submitting...' : 'Place Order' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { useRestockingOrders } from '../composables/useRestockingOrders'

const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    const { submitOrder } = useRestockingOrders()
    const { currentCurrency } = useI18n()
    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const inventoryItems = ref([])
    const budget = ref(50000)
    const submitting = ref(false)
    const orderPlaced = ref(false)
    const lastOrderNumber = ref('')
    const lastDeliveryDate = ref('')

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        forecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const recommendedItems = computed(() => {
      // Build a unit_cost lookup from inventory keyed by SKU
      const costMap = {}
      for (const inv of inventoryItems.value) {
        costMap[inv.sku] = inv.unit_cost
      }

      // Enrich forecasts with cost data and quantities
      const enriched = []
      for (const forecast of forecasts.value) {
        const unit_cost = costMap[forecast.item_sku]
        if (unit_cost == null) continue
        const qty_to_order = Math.max(1, forecast.forecasted_demand - forecast.current_demand)
        const item_total = qty_to_order * unit_cost
        enriched.push({
          ...forecast,
          unit_cost,
          qty_to_order,
          item_total
        })
      }

      // Sort: trend priority first, then item_total ascending within same trend
      enriched.sort((a, b) => {
        const trendDiff = (TREND_ORDER[a.trend] ?? 99) - (TREND_ORDER[b.trend] ?? 99)
        if (trendDiff !== 0) return trendDiff
        return a.item_total - b.item_total
      })

      // Greedy fill within budget
      const result = []
      let running_total = 0
      for (const item of enriched) {
        if (running_total + item.item_total <= budget.value) {
          result.push(item)
          running_total += item.item_total
        }
      }
      return result
    })

    const totalCost = computed(() =>
      recommendedItems.value.reduce((sum, item) => sum + item.item_total, 0)
    )

    const formatCurrency = (value) => {
      if (currentCurrency.value === 'JPY') {
        return '¥' + Math.round(value).toLocaleString()
      }
      return '$' + value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    const formattedBudget = computed(() => formatCurrency(budget.value))
    const formattedTotalCost = computed(() => formatCurrency(totalCost.value))

    const placeOrder = async () => {
      if (recommendedItems.value.length === 0 || submitting.value) return
      submitting.value = true

      const now = Date.now()
      const deliveryDate = (() => {
        const d = new Date()
        d.setDate(d.getDate() + 7)
        return d.toISOString().split('T')[0]
      })()

      const order = {
        id: 'RST-' + now,
        order_number: 'RST-' + String(now).slice(-6),
        customer: 'Internal Restocking',
        items: recommendedItems.value.map(item => ({
          sku: item.item_sku,
          name: item.item_name,
          quantity: item.qty_to_order,
          unit_price: item.unit_cost
        })),
        status: 'Processing',
        order_date: new Date().toISOString().split('T')[0],
        expected_delivery: deliveryDate,
        total_value: totalCost.value
      }

      submitOrder(order)

      lastOrderNumber.value = order.order_number
      lastDeliveryDate.value = deliveryDate
      orderPlaced.value = true
      submitting.value = false

      setTimeout(() => {
        orderPlaced.value = false
      }, 4000)
    }

    onMounted(loadData)

    return {
      loading,
      error,
      budget,
      submitting,
      orderPlaced,
      lastOrderNumber,
      lastDeliveryDate,
      currencySymbol,
      recommendedItems,
      totalCost,
      formattedBudget,
      formattedTotalCost,
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
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  border-radius: 8px;
  padding: 0.875rem 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
  margin-bottom: 1.25rem;
}

.budget-body {
  padding-top: 0.5rem;
}

.budget-display {
  font-size: 2.5rem;
  margin-bottom: 1.25rem;
}

.slider-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: #e2e8f0;
  border-radius: 4px;
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
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  transition: transform 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.25rem;
}

.summary-badge {
  display: inline-block;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #334155;
  font-size: 0.813rem;
  font-weight: 600;
  padding: 0.375rem 0.875rem;
  border-radius: 6px;
}

.empty-state {
  text-align: center;
  color: #64748b;
  font-style: italic;
  padding: 2rem 1rem;
}

.total-row {
  background: #f8fafc;
  border-top: 2px solid #e2e8f0;
}

.total-label {
  font-weight: 600;
  color: #475569;
  text-align: right;
  font-size: 0.875rem;
}

.total-value {
  font-weight: 700;
  color: #0f172a;
  font-size: 0.938rem;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 1rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.5rem;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
