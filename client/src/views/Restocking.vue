<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="budget-header">
          <span class="budget-label">{{ t('restocking.budget') }}</span>
          <span class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</span>
        </div>
        <input
          type="range"
          min="0"
          :max="maxBudget"
          step="1000"
          v-model.number="budget"
          class="budget-slider"
        />
        <div class="budget-range-labels">
          <span>{{ formatCurrency(0, currentCurrency) }}</span>
          <span>{{ formatCurrency(maxBudget, currentCurrency) }}</span>
        </div>
        <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ itemsRecommended }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.unitsRecommended') }}</div>
          <div class="stat-value">{{ unitsRecommended }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCost, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ formatCurrency(budgetRemaining, currentCurrency) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }} ({{ recommendations.length }})</h3>
        </div>

        <div v-if="shortfallItems.length === 0" class="empty-state">
          <p>{{ t('restocking.noShortfall') }}</p>
        </div>
        <div v-else-if="recommendations.length === 0" class="empty-state">
          <p>{{ t('restocking.noRecommendations') }}</p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.shortfall') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.itemName) }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td>
                  <span class="badge warning">{{ t('restocking.shortBy', { count: item.shortfall }) }}</span>
                </td>
                <td><strong>{{ item.quantity }}</strong></td>
                <!-- Unit costs carry cents (e.g. 12.75), so they need decimals -
                     formatCurrency rounds to whole units and would misreport them. -->
                <td>{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                <td><strong>{{ formatCurrency(item.lineTotal, currentCurrency) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="submitError" class="error">{{ submitError }}</div>
        <div v-if="submitSuccess" class="success-message">{{ submitSuccess }}</div>

        <div class="card-footer">
          <span class="orders-across">{{ t('restocking.ordersAcross', { count: warehouseCount }) }}</span>
          <button
            class="place-order-btn"
            :disabled="submitting || recommendations.length === 0"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    // Use shared filters (inventory/demand only support warehouse + category)
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Join forecasts to inventory by SKU, keep only items where forecasted demand
    // outstrips what's on hand, ranked worst-shortfall-first so the budget greedily
    // covers the most urgent gaps first.
    const shortfallItems = computed(() => {
      const inventoryBySku = new Map(inventoryItems.value.map(item => [item.sku, item]))
      const items = []

      for (const forecast of allForecasts.value) {
        const inv = inventoryBySku.get(forecast.item_sku)
        if (!inv) continue // no matching inventory item under the current filters

        const shortfall = forecast.forecasted_demand - inv.quantity_on_hand
        if (shortfall > 0) {
          items.push({
            sku: inv.sku,
            itemName: inv.name,
            warehouse: inv.warehouse,
            shortfall,
            unit_cost: inv.unit_cost
          })
        }
      }

      return items.sort((a, b) => b.shortfall - a.shortfall)
    })

    // Cost of fully covering every shortfall, rounded up to the nearest $5,000 so the
    // slider has a round, generous ceiling rather than an oddly specific max.
    const maxBudget = computed(() => {
      if (shortfallItems.value.length === 0) return 0
      const total = shortfallItems.value.reduce((sum, item) => sum + item.shortfall * item.unit_cost, 0)
      return Math.ceil(total / 5000) * 5000
    })

    const budget = ref(0)

    // Reset the budget to 25% of the new ceiling whenever the ceiling changes
    // (e.g. filters change the shortfall set), so the slider never gets stuck
    // above/below the new range.
    watch(maxBudget, (newMax) => {
      budget.value = Math.round(newMax * 0.25)
    })

    // Any manual or automatic budget change invalidates a previously shown
    // success message from placing an order.
    watch(budget, () => {
      submitSuccess.value = null
    })

    // Greedy fill: walk shortfalls worst-first, buy as many units of the current
    // item as the remaining budget allows, then move on. This maximizes the number
    // of the most urgent shortfalls that get at least partially addressed.
    const recommendations = computed(() => {
      let left = budget.value
      const out = []

      for (const item of shortfallItems.value) {
        const qty = Math.min(item.shortfall, Math.floor(left / item.unit_cost))
        if (qty >= 1) {
          out.push({ ...item, quantity: qty, lineTotal: qty * item.unit_cost })
          left -= qty * item.unit_cost
        }
      }

      return out
    })

    const itemsRecommended = computed(() => recommendations.value.length)
    const unitsRecommended = computed(() => recommendations.value.reduce((sum, item) => sum + item.quantity, 0))
    const totalCost = computed(() => recommendations.value.reduce((sum, item) => sum + item.lineTotal, 0))
    const budgetRemaining = computed(() => budget.value - totalCost.value)

    const groupedByWarehouse = computed(() => {
      const map = new Map()
      for (const item of recommendations.value) {
        if (!map.has(item.warehouse)) map.set(item.warehouse, [])
        map.get(item.warehouse).push(item)
      }
      return map
    })

    const warehouseCount = computed(() => groupedByWarehouse.value.size)

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const filters = getCurrentFilters()
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadData()
    })

    const submitting = ref(false)
    const submitError = ref(null)
    const submitSuccess = ref(null)

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      try {
        const entries = Array.from(groupedByWarehouse.value.entries())
        await Promise.all(entries.map(([warehouse, items]) =>
          api.createRestockingOrder({
            warehouse,
            items: items.map(item => ({
              sku: item.sku,
              name: item.itemName,
              quantity: item.quantity,
              unit_price: item.unit_cost
            }))
          })
        ))
        submitSuccess.value = t('restocking.orderPlaced', { count: entries.length })
      } catch (err) {
        submitError.value = t('restocking.orderFailed')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      currentCurrency,
      formatCurrency,
      formatCurrencyWithDecimals,
      translateProductName,
      translateWarehouse,
      loading,
      error,
      budget,
      maxBudget,
      shortfallItems,
      recommendations,
      itemsRecommended,
      unitsRecommended,
      totalCost,
      budgetRemaining,
      warehouseCount,
      submitting,
      submitError,
      submitSuccess,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 20px;
  background: transparent;
  cursor: pointer;
  margin: 0.25rem 0;
}

.budget-slider:focus {
  outline: none;
}

.budget-slider::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  margin-top: -7px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: box-shadow 0.15s ease;
}

.budget-slider:focus::-webkit-slider-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.25);
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 3px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: box-shadow 0.15s ease;
}

.budget-slider:focus::-moz-range-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.25);
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.budget-hint {
  font-size: 0.813rem;
  color: #94a3b8;
  font-style: italic;
}

.empty-state {
  padding: 3rem;
  text-align: center;
  color: #64748b;
}

.success-message {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.938rem;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.orders-across {
  font-size: 0.875rem;
  color: #64748b;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
