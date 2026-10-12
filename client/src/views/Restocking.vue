<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Pick a budget and place a restock order for the highest-priority items.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Budget</h3>
        </div>
        <div class="budget-controls">
          <input
            type="range"
            min="0"
            max="50000"
            step="500"
            v-model.number="budget"
            class="budget-slider"
          />
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
      </div>

      <div v-if="submittedOrder" class="success-banner">
        Order {{ submittedOrder.id }} placed. Expected delivery
        {{ formatDate(submittedOrder.expected_delivery_date) }}.
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">Budget</div>
          <div class="stat-value">{{ formatCurrency(budget) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">Allocated</div>
          <div class="stat-value">{{ formatCurrency(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">Remaining</div>
          <div class="stat-value">{{ formatCurrency(remainingBudget) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">Recommended Items ({{ recommendations.length }})</h3>
          <button
            class="btn-primary"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
          </button>
        </div>
        <div v-if="recommendations.length === 0" class="empty-state">
          No items need restocking at this budget.
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Trend</th>
                <th>Recommended Qty</th>
                <th>Unit Cost</th>
                <th>Estimated Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.item_sku">
                <td><strong>{{ rec.item_sku }}</strong></td>
                <td>{{ rec.item_name }}</td>
                <td><span class="badge" :class="rec.trend">{{ rec.trend }}</span></td>
                <td>{{ rec.recommended_quantity }}</td>
                <td>{{ formatCurrencyWithDecimals(rec.unit_cost, 'USD', 2) }}</td>
                <td>{{ formatCurrency(rec.estimated_cost) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const demandForecasts = ref([])
    const inventoryItems = ref([])

    const budget = ref(15000)
    const submitting = ref(false)
    const submittedOrder = ref(null)

    const loadData = async () => {
      try {
        loading.value = true
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        demandForecasts.value = forecasts
        inventoryItems.value = inventory
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const recommendations = computed(() => {
      const inventoryBySku = new Map(inventoryItems.value.map(item => [item.sku, item]))

      const candidates = demandForecasts.value
        .map(forecast => {
          const inventory = inventoryBySku.get(forecast.item_sku)
          if (!inventory) return null
          const recommended_quantity = Math.max(
            0,
            inventory.reorder_point - inventory.quantity_on_hand,
            forecast.forecasted_demand - inventory.quantity_on_hand
          )
          if (recommended_quantity <= 0) return null
          return {
            item_sku: inventory.sku,
            item_name: inventory.name,
            trend: forecast.trend,
            recommended_quantity,
            unit_cost: inventory.unit_cost,
            estimated_cost: recommended_quantity * inventory.unit_cost,
            stockGap: inventory.quantity_on_hand - inventory.reorder_point
          }
        })
        .filter(Boolean)
        .sort((a, b) => {
          const trendDiff = TREND_ORDER[a.trend] - TREND_ORDER[b.trend]
          if (trendDiff !== 0) return trendDiff
          return a.stockGap - b.stockGap
        })

      const result = []
      let remaining = budget.value
      for (const candidate of candidates) {
        if (candidate.estimated_cost <= remaining) {
          result.push(candidate)
          remaining -= candidate.estimated_cost
        }
      }
      return result
    })

    const totalCost = computed(() => recommendations.value.reduce((sum, r) => sum + r.estimated_cost, 0))
    const remainingBudget = computed(() => budget.value - totalCost.value)

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const placeOrder = async () => {
      submitting.value = true
      try {
        const payload = {
          budget: budget.value,
          items: recommendations.value.map(r => ({
            item_sku: r.item_sku,
            item_name: r.item_name,
            quantity: r.recommended_quantity,
            unit_cost: r.unit_cost
          }))
        }
        submittedOrder.value = await api.createRestockOrder(payload)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    watch(budget, () => {
      submittedOrder.value = null
    })

    onMounted(loadData)

    return {
      loading,
      error,
      budget,
      submitting,
      submittedOrder,
      recommendations,
      totalCost,
      remainingBudget,
      formatCurrency,
      formatCurrencyWithDecimals,
      formatDate,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-slider {
  flex: 1;
  accent-color: #2563eb;
}

.budget-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 90px;
  text-align: right;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  border: 1px solid #2563eb;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #93c5fd;
  border-color: #93c5fd;
  cursor: not-allowed;
}
</style>
