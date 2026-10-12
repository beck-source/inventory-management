<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Auto-recommend items below reorder point</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="planner-layout">
        <!-- Left column: budget controls + summary stats -->
        <div class="budget-panel">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Budget</h3>
            </div>

            <div class="budget-slider-section">
              <div class="budget-label">{{ formatCurrency(budget) }}</div>
              <input
                type="range"
                class="budget-slider"
                v-model.number="budget"
                min="0"
                max="500000"
                step="1000"
              />
              <div class="slider-range-labels">
                <span>$0</span>
                <span>$500,000</span>
              </div>
            </div>

            <div class="stats-section">
              <div class="stat-row">
                <span class="stat-row-label">Items below reorder</span>
                <span class="stat-row-value">{{ recommendedItems.length }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-row-label">Avg shortage</span>
                <span class="stat-row-value">{{ avgShortage }} units</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right column: recommendations table + actions -->
        <div class="recommendations-panel">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">Recommended Items</h3>
            </div>

            <div class="table-container">
              <table v-if="selectedItems.length > 0">
                <thead>
                  <tr>
                    <th>SKU</th>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Warehouse</th>
                    <th>Qty to Order</th>
                    <th>Unit Cost</th>
                    <th>Line Total</th>
                    <th>Demand Trend</th>
                  </tr>
                </thead>
                <tbody>
                  <!-- Use item.sku as key — SKUs are unique per inventory spec -->
                  <tr v-for="item in selectedItems" :key="item.sku">
                    <td><strong>{{ item.sku }}</strong></td>
                    <td>{{ item.name }}</td>
                    <td>{{ item.category }}</td>
                    <td>{{ item.warehouse }}</td>
                    <td>{{ item.shortageGap }}</td>
                    <td>{{ formatCurrency(item.unit_cost) }}</td>
                    <td>{{ formatCurrency(item.unit_cost * item.shortageGap) }}</td>
                    <td>
                      <span :class="['badge', item.trend]">{{ item.trend }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="empty-state">
                No items fit within the current budget.
              </div>
            </div>

            <div class="table-summary">
              <span>Items selected: <strong>{{ selectedItems.length }}</strong></span>
              <span>Total cost: <strong>{{ formatCurrency(totalCost) }}</strong></span>
              <span>Remaining budget: <strong>{{ formatCurrency(remainingBudget) }}</strong></span>
            </div>

            <div class="order-actions">
              <button
                class="place-order-btn"
                :disabled="selectedItems.length === 0 || isPlacingOrder"
                @click="placeOrder"
              >
                {{ isPlacingOrder ? 'Submitting...' : 'Place Order' }}
              </button>

              <div v-if="orderSuccess" class="order-success">
                Order submitted — check the Orders tab
              </div>
              <div v-if="orderError" class="error">{{ orderError }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

// Priority scores for demand trend used in sort — higher = order sooner
const TREND_PRIORITY = { increasing: 3, stable: 2, decreasing: 1 }

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)

    const inventoryItems = ref([])
    const demandForecasts = ref([])

    const budget = ref(100000)

    const isPlacingOrder = ref(false)
    const orderSuccess = ref(false)
    const orderError = ref(null)

    // Items below reorder point, enriched with demand trend and sorted by priority
    const recommendedItems = computed(() => {
      const belowReorder = inventoryItems.value.filter(
        item => item.quantity_on_hand <= item.reorder_point
      )

      const withTrend = belowReorder.map(item => {
        // Best-effort match: check if any forecast SKU contains the item SKU as a substring
        const forecast = demandForecasts.value.find(f =>
          f.item_sku.includes(item.sku) || item.sku.includes(f.item_sku)
        )
        const trend = forecast ? forecast.trend : 'stable'
        const priorityScore = TREND_PRIORITY[trend] ?? TREND_PRIORITY.stable
        const shortageGap = item.reorder_point - item.quantity_on_hand

        return { ...item, trend, priorityScore, shortageGap }
      })

      // Sort: highest priority first, then largest shortage gap first
      return withTrend.sort((a, b) => {
        if (b.priorityScore !== a.priorityScore) return b.priorityScore - a.priorityScore
        return b.shortageGap - a.shortageGap
      })
    })

    // Greedy selection: iterate sorted items and accumulate until budget is exhausted
    const selectedItems = computed(() => {
      let remaining = budget.value
      const result = []

      for (const item of recommendedItems.value) {
        const lineCost = item.unit_cost * item.shortageGap
        if (lineCost <= remaining) {
          result.push(item)
          remaining -= lineCost
        }
      }

      return result
    })

    const totalCost = computed(() =>
      selectedItems.value.reduce((sum, item) => sum + item.unit_cost * item.shortageGap, 0)
    )

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const avgShortage = computed(() => {
      if (recommendedItems.value.length === 0) return 0
      const total = recommendedItems.value.reduce((sum, item) => sum + item.shortageGap, 0)
      return Math.round(total / recommendedItems.value.length)
    })

    const formatCurrency = (value) =>
      value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [inventoryData, forecastData] = await Promise.all([
          api.getInventory({}),
          api.getDemandForecasts()
        ])
        inventoryItems.value = inventoryData
        demandForecasts.value = forecastData
      } catch (err) {
        error.value = 'Failed to load restocking data'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (selectedItems.value.length === 0) return

      isPlacingOrder.value = true
      orderSuccess.value = false
      orderError.value = null

      try {
        const orderItems = selectedItems.value.map(item => ({
          sku: item.sku,
          name: item.name,
          quantity: item.shortageGap,
          unit_price: item.unit_cost
        }))
        await api.createRestockOrder(orderItems)
        orderSuccess.value = true
      } catch (err) {
        orderError.value = 'Failed to submit order. Please try again.'
        console.error(err)
      } finally {
        isPlacingOrder.value = false
      }
    }

    onMounted(loadData)

    return {
      loading,
      error,
      budget,
      recommendedItems,
      selectedItems,
      totalCost,
      remainingBudget,
      avgShortage,
      isPlacingOrder,
      orderSuccess,
      orderError,
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

/* Two-column layout: fixed budget panel + flexible recommendations panel */
.planner-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1.5rem;
  align-items: start;
}

@media (max-width: 768px) {
  .planner-layout {
    grid-template-columns: 1fr;
  }
}

/* Budget panel */
.budget-slider-section {
  margin-bottom: 1.25rem;
}

.budget-label {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 0.75rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  height: 4px;
  cursor: pointer;
}

.slider-range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: #94a3b8;
}

.stats-section {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-row-label {
  font-size: 0.875rem;
  color: #64748b;
}

.stat-row-value {
  font-size: 0.938rem;
  font-weight: 700;
  color: #0f172a;
}

/* Empty state when no items fit in budget */
.empty-state {
  padding: 2.5rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Summary row below the table */
.table-summary {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  padding: 0.875rem 0;
  border-top: 1px solid #e2e8f0;
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: #475569;
}

/* Action row: button + messages */
.order-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  padding-top: 0.875rem;
  border-top: 1px solid #e2e8f0;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.938rem;
  border: none;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.order-success {
  font-size: 0.875rem;
  font-weight: 500;
  color: #065f46;
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  border-radius: 6px;
  padding: 0.5rem 0.875rem;
}
</style>
