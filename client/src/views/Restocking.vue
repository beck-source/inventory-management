<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking Planner</h2>
      <p>Allocate your restocking budget across forecasted demand using priority-ranked recommendations.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="showSuccess" class="success-banner" @click="showSuccess = false">
        <div class="success-content">
          <strong>Order placed!</strong>
          Order ID: {{ lastOrder.id }} | Expected delivery: {{ lastOrder.expected_delivery }}
        </div>
        <button class="dismiss-btn" @click.stop="showSuccess = false">Dismiss</button>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Budget Allocation</span>
          <span class="budget-display">${{ budget.toLocaleString() }}</span>
        </div>
        <input
          type="range"
          v-model.number="budget"
          :min="0"
          :max="maxBudget"
          :step="1000"
        />
        <div class="budget-meta">
          Total budget utilized: ${{ totalCost.toLocaleString() }} / ${{ budget.toLocaleString() }}
          <span class="utilization-pct" v-if="budget > 0">
            ({{ Math.round((totalCost / budget) * 100) }}%)
          </span>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <span class="card-title">Recommended Items</span>
          <span class="badge info">{{ recommendedItems.length }} items</span>
        </div>
        <div v-if="recommendedItems.length === 0" class="empty-state">
          No items fit within this budget
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Item Name</th>
                <th>Trend</th>
                <th>Forecasted Qty</th>
                <th>Unit Cost</th>
                <th>Total Cost</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendedItems" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span :class="['badge', trendBadgeClass(item.trend)]">
                    {{ item.trend }}
                  </span>
                </td>
                <td>{{ item.forecasted_demand.toLocaleString() }}</td>
                <td>${{ getUnitCost(item.item_sku).toLocaleString() }}</td>
                <td><strong>${{ getItemCost(item).toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card order-summary">
        <div class="order-summary-row">
          <div class="order-summary-meta">
            <span>Total items: {{ recommendedItems.length }}</span>
            <span class="separator">|</span>
            <span class="stat-value">${{ totalCost.toLocaleString() }}</span>
          </div>
          <button
            class="btn-primary"
            :disabled="recommendedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Placing Order...' : 'Place Order' }}
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

export default {
  name: 'Restocking',
  setup() {
    const { t } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const inventoryBySku = ref({})
    const budget = ref(50000)
    const submitting = ref(false)
    const lastOrder = ref(null)
    const showSuccess = ref(false)

    const maxBudget = computed(() => {
      return forecasts.value.reduce((sum, item) => {
        return sum + getItemCost(item)
      }, 0)
    })

    const sortedForecasts = computed(() => {
      const trendPriority = { increasing: 0, stable: 1, decreasing: 2 }
      return [...forecasts.value].sort((a, b) => {
        const trendDiff = (trendPriority[a.trend] ?? 1) - (trendPriority[b.trend] ?? 1)
        if (trendDiff !== 0) return trendDiff
        return b.forecasted_demand - a.forecasted_demand
      })
    })

    const recommendedItems = computed(() => {
      let remaining = budget.value
      const result = []
      for (const item of sortedForecasts.value) {
        const cost = getItemCost(item)
        if (cost <= remaining) {
          result.push(item)
          remaining -= cost
        }
      }
      return result
    })

    const totalCost = computed(() => {
      return recommendedItems.value.reduce((sum, item) => sum + getItemCost(item), 0)
    })

    const getUnitCost = (sku) => {
      return inventoryBySku.value[sku]?.unit_cost ?? 0
    }

    const getItemCost = (item) => {
      const unitCost = inventoryBySku.value[item.item_sku]?.unit_cost ?? 0
      return item.forecasted_demand * unitCost
    }

    const trendBadgeClass = (trend) => {
      const map = { increasing: 'increasing', stable: 'stable', decreasing: 'decreasing' }
      return map[trend] ?? 'info'
    }

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        forecasts.value = forecastsData
        const bySkuMap = {}
        for (const inv of inventoryData) {
          bySkuMap[inv.sku] = inv
        }
        inventoryBySku.value = bySkuMap
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      try {
        const payload = {
          items: recommendedItems.value.map(item => ({
            sku: item.item_sku,
            item_name: item.item_name,
            quantity: item.forecasted_demand,
            unit_cost: inventoryBySku.value[item.item_sku]?.unit_cost ?? 0
          })),
          notes: `Auto-generated restocking order. Budget: $${budget.value}`
        }
        const order = await api.createRestockingOrder(payload)
        lastOrder.value = order
        showSuccess.value = true
        setTimeout(() => { showSuccess.value = false }, 5000)
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      budget,
      maxBudget,
      recommendedItems,
      totalCost,
      submitting,
      lastOrder,
      showSuccess,
      getUnitCost,
      getItemCost,
      trendBadgeClass,
      placeOrder
    }
  }
}
</script>

<style scoped>
input[type="range"] {
  width: 100%;
  accent-color: var(--accent);
  margin: 0.75rem 0;
}

.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent);
}

.budget-meta {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.utilization-pct {
  font-weight: 600;
  color: var(--accent);
  margin-left: 0.25rem;
}

.empty-state {
  padding: 2.5rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.938rem;
}

.order-summary .order-summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.order-summary-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.938rem;
  color: var(--text-primary);
  font-weight: 500;
}

.separator {
  color: var(--border);
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm, 6px);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover, #1d4ed8);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-banner {
  background: #dcfce7;
  border: 1px solid #86efac;
  color: #16a34a;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-md, 8px);
  margin-bottom: 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.success-content {
  font-size: 0.938rem;
}

.dismiss-btn {
  background: none;
  border: 1px solid #059669;
  color: #065f46;
  border-radius: 5px;
  padding: 0.25rem 0.75rem;
  font-size: 0.813rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}

.dismiss-btn:hover {
  background: #a7f3d0;
}
</style>
