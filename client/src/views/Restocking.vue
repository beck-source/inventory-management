<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Recommend items to restock based on demand forecasts and your available budget.</p>
    </div>

    <!-- Budget card -->
    <div class="card">
      <div class="card-header">
        <span class="card-title">Available Budget</span>
        <span class="budget-value">${{ budget.toLocaleString() }}</span>
      </div>
      <input
        type="range"
        class="budget-slider"
        v-model.number="budget"
        min="1000"
        max="500000"
        step="1000"
      />
      <div class="budget-bar-track">
        <div class="budget-bar-fill" :style="{ width: budgetUsedPct + '%' }"></div>
      </div>
      <div class="budget-meta">
        <span>Allocated: ${{ totalCost.toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</span>
        <span>Remaining: ${{ (budget - totalCost).toLocaleString(undefined, { maximumFractionDigits: 0 }) }}</span>
      </div>
    </div>

    <!-- Loading / error states -->
    <div v-if="loading" class="loading">Loading demand forecasts...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <template v-else>
      <!-- Success banner -->
      <div v-if="successMessage" class="success-banner">{{ successMessage }}</div>

      <!-- Unmatched notice -->
      <div v-if="unmatchedForecasts.length" class="info-notice">
        {{ unmatchedForecasts.length }} forecast item(s) could not be matched to inventory and were excluded.
      </div>

      <!-- Recommendations card -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">Recommended Restocking ({{ recommendations.length }} items)</span>
          <button
            class="place-order-btn"
            @click="placeOrder"
            :disabled="!recommendations.length || placing"
          >
            {{ placing ? 'Placing...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="!recommendations.length" class="empty-state">
          No items fit within the current budget. Try increasing the budget slider.
        </div>

        <div v-else class="table-container">
          <table class="recommendations-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Trend</th>
                <th>Demand Gap</th>
                <th>Unit Cost</th>
                <th>Rec. Qty</th>
                <th>Line Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.forecast.item_sku">
                <td class="sku-cell">{{ rec.forecast.item_sku }}</td>
                <td>{{ rec.forecast.item_name }}</td>
                <td><span :class="['badge', rec.forecast.trend]">{{ rec.forecast.trend }}</span></td>
                <td>+{{ rec.qty }}</td>
                <td>${{ rec.inv.unit_cost.toFixed(2) }}</td>
                <td class="qty-cell">{{ rec.qty }}</td>
                <td class="total-cell">${{ rec.lineTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="total-row">
                <td colspan="6" class="total-label">Total</td>
                <td class="total-cell">${{ totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(50000)
    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const successMessage = ref('')
    const forecasts = ref([])
    const inventoryBySku = ref({})

    const recommendations = computed(() => {
      let remaining = budget.value
      const result = []

      const sorted = [...forecasts.value]
        .filter(f => {
          const inv = inventoryBySku.value[f.item_sku]
          return inv && (f.forecasted_demand - f.current_demand) > 0
        })
        .sort((a, b) => {
          const trendDiff = (TREND_ORDER[a.trend] ?? 99) - (TREND_ORDER[b.trend] ?? 99)
          if (trendDiff !== 0) return trendDiff
          return (b.forecasted_demand - b.current_demand) - (a.forecasted_demand - a.current_demand)
        })

      for (const forecast of sorted) {
        const inv = inventoryBySku.value[forecast.item_sku]
        const qty = forecast.forecasted_demand - forecast.current_demand
        const lineTotal = qty * inv.unit_cost
        if (remaining >= lineTotal) {
          result.push({ forecast, inv, qty, lineTotal })
          remaining -= lineTotal
        }
      }
      return result
    })

    const totalCost = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.lineTotal, 0)
    )

    const budgetUsedPct = computed(() =>
      Math.min((totalCost.value / budget.value) * 100, 100)
    )

    const unmatchedForecasts = computed(() =>
      forecasts.value.filter(f => !inventoryBySku.value[f.item_sku])
    )

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        forecasts.value = forecastsData
        inventoryBySku.value = inventoryData.reduce((map, item) => {
          map[item.sku] = item
          return map
        }, {})
      } catch (err) {
        error.value = 'Failed to load data. Please try again.'
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (!recommendations.value.length) return
      placing.value = true
      successMessage.value = ''
      try {
        for (const { forecast, inv, qty } of recommendations.value) {
          await api.createRestockingOrder({
            item_sku: forecast.item_sku,
            item_name: forecast.item_name,
            quantity: qty,
            unit_cost: inv.unit_cost
          })
        }
        successMessage.value = `${recommendations.value.length} restocking order${recommendations.value.length > 1 ? 's' : ''} placed successfully. View them in the Orders tab.`
      } catch (err) {
        error.value = 'Failed to place orders. Please try again.'
        console.error(err)
      } finally {
        placing.value = false
      }
    }

    onMounted(() => loadData())

    return {
      budget,
      loading,
      error,
      placing,
      successMessage,
      recommendations,
      totalCost,
      budgetUsedPct,
      unmatchedForecasts,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--sidebar-active-border);
}

.budget-slider {
  width: 100%;
  margin: var(--space-4) 0 var(--space-3);
  accent-color: var(--sidebar-active-border);
  cursor: pointer;
}

.budget-bar-track {
  height: 6px;
  background: var(--surface-border);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: var(--space-2);
}

.budget-bar-fill {
  height: 100%;
  background: var(--sidebar-active-border);
  border-radius: 999px;
  transition: width 0.2s ease;
}

.budget-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-6);
  font-size: 0.875rem;
}

.info-notice {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  color: #1e40af;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
  font-size: 0.8rem;
}

.empty-state {
  padding: var(--space-10);
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.place-order-btn {
  padding: var(--space-2) var(--space-5);
  background: var(--sidebar-active-border);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

.place-order-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.place-order-btn:not(:disabled):hover {
  opacity: 0.88;
}

.sku-cell {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
  color: var(--text-secondary);
}

.qty-cell,
.total-cell {
  font-weight: 600;
}

.total-row td {
  border-top: 2px solid var(--surface-border);
  font-weight: 700;
  padding-top: var(--space-3);
}

.total-label {
  color: var(--text-secondary);
}
</style>
