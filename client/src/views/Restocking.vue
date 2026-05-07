<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Recommend restocking quantities based on demand forecasts and available budget.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Budget</h3>
          <span class="budget-display">${{ budget.toLocaleString() }}</span>
        </div>
        <div class="budget-slider-row">
          <span class="slider-label">$0</span>
          <input
            type="range"
            v-model.number="budget"
            min="0"
            max="1000000"
            step="5000"
            class="budget-slider"
          />
          <span class="slider-label">$1,000,000</span>
        </div>
        <div class="budget-summary">
          <span class="budget-used">
            Allocated: <strong>${{ totalCost.toLocaleString() }}</strong>
          </span>
          <span class="budget-remaining">
            Remaining: <strong>${{ (budget - totalCost).toLocaleString() }}</strong>
          </span>
          <span class="budget-items">
            Items selected: <strong>{{ recommendedItems.length }}</strong>
          </span>
        </div>
      </div>

      <div v-if="orderSuccess" class="success-banner">
        Order placed successfully. Order number: <strong>{{ orderNumber }}</strong>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Restocking ({{ recommendedItems.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="recommendedItems.length === 0 || orderPlacing"
            @click="placeOrder"
          >
            {{ orderPlacing ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>
        <div v-if="recommendedItems.length === 0" class="empty-state">
          No items fit within the current budget. Increase the budget to see recommendations.
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>SKU</th>
                <th>Forecasted Demand</th>
                <th>Unit Cost</th>
                <th>Restock Qty</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendedItems" :key="item.sku">
                <td>{{ item.name }}</td>
                <td class="sku-cell">{{ item.sku }}</td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td>${{ item.unit_cost.toLocaleString() }}</td>
                <td>{{ item.restock_qty.toLocaleString() }}</td>
                <td><strong>${{ item.line_total.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="excludedItems.length > 0" class="card excluded-card">
        <div class="card-header">
          <h3 class="card-title excluded-title">Excluded — Does Not Fit Budget ({{ excludedItems.length }})</h3>
        </div>
        <div class="table-container">
          <table class="excluded-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>SKU</th>
                <th>Forecasted Demand</th>
                <th>Unit Cost</th>
                <th>Restock Qty</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in excludedItems" :key="item.sku" class="excluded-row">
                <td>{{ item.name }}</td>
                <td class="sku-cell">{{ item.sku }}</td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td>${{ item.unit_cost.toLocaleString() }}</td>
                <td>{{ item.restock_qty.toLocaleString() }}</td>
                <td>${{ item.line_total.toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
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
    const loading = ref(true)
    const error = ref(null)
    const demandForecasts = ref([])
    const inventoryItems = ref([])
    const budget = ref(50000)
    const orderPlacing = ref(false)
    const orderSuccess = ref(false)
    const orderNumber = ref('')

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        demandForecasts.value = forecasts
        inventoryItems.value = inventory
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    // Cross-reference increasing-trend demand items with inventory by SKU
    const candidates = computed(() => {
      const inventoryBySku = {}
      for (const inv of inventoryItems.value) {
        inventoryBySku[inv.sku] = inv
      }

      return demandForecasts.value
        .filter(f => f.trend === 'increasing')
        .map(f => {
          const inv = inventoryBySku[f.item_sku]
          if (!inv) return null
          const restock_qty = Math.max(1, f.forecasted_demand)
          const unit_cost = inv.unit_cost || 0
          const line_total = restock_qty * unit_cost
          return {
            sku: f.item_sku,
            name: f.item_name,
            forecasted_demand: f.forecasted_demand,
            unit_cost,
            restock_qty,
            line_total
          }
        })
        .filter(Boolean)
        .sort((a, b) => b.forecasted_demand - a.forecasted_demand)
    })

    // Greedy selection: pick items in order of forecasted_demand until budget is exhausted
    const recommendedItems = computed(() => {
      let remaining = budget.value
      const selected = []
      for (const item of candidates.value) {
        if (item.line_total <= remaining) {
          selected.push(item)
          remaining -= item.line_total
        }
      }
      return selected
    })

    const excludedItems = computed(() => {
      const selectedSkus = new Set(recommendedItems.value.map(i => i.sku))
      return candidates.value.filter(i => !selectedSkus.has(i.sku))
    })

    const totalCost = computed(() => {
      return recommendedItems.value.reduce((sum, i) => sum + i.line_total, 0)
    })

    const placeOrder = async () => {
      if (recommendedItems.value.length === 0) return
      orderPlacing.value = true
      orderSuccess.value = false
      try {
        const items = recommendedItems.value.map(i => ({
          sku: i.sku,
          name: i.name,
          quantity: i.restock_qty,
          unit_price: i.unit_cost
        }))
        const result = await api.createRestockingOrder({
          items,
          warehouse: 'all',
          category: 'all'
        })
        orderNumber.value = result.order_number || result.id || 'N/A'
        orderSuccess.value = true
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
        console.error(err)
      } finally {
        orderPlacing.value = false
      }
    }

    onMounted(loadData)

    return {
      loading,
      error,
      budget,
      recommendedItems,
      excludedItems,
      totalCost,
      orderPlacing,
      orderSuccess,
      orderNumber,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

.budget-card {
  margin-bottom: 1.25rem;
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.slider-label {
  font-size: 0.813rem;
  color: #64748b;
  white-space: nowrap;
}

.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-summary {
  display: flex;
  gap: 2rem;
  font-size: 0.875rem;
  color: #64748b;
}

.budget-summary strong {
  color: #0f172a;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.sku-cell {
  font-family: monospace;
  font-size: 0.813rem;
  color: #64748b;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
}

.excluded-card {
  opacity: 0.6;
}

.excluded-title {
  color: #64748b;
}

.excluded-row td {
  color: #94a3b8;
}
</style>
