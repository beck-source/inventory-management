<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Controls Card -->
      <div class="card controls-card">
        <div class="controls-row">
          <div class="control-group">
            <label class="control-label">
              {{ t('restocking.budget') }}
              <span class="control-value">{{ formatCurrency(budget) }}</span>
            </label>
            <div class="slider-wrapper">
              <span class="slider-bound">{{ formatCurrency(0) }}</span>
              <input
                type="range"
                class="budget-slider"
                :min="0"
                :max="maxBudget"
                :step="1000"
                v-model.number="budget"
              />
              <span class="slider-bound">{{ formatCurrency(maxBudget) }}</span>
            </div>
          </div>
          <div class="control-group control-group--narrow">
            <label class="control-label" for="lead-time">
              {{ t('restocking.leadTime') }}
            </label>
            <input
              id="lead-time"
              type="number"
              class="lead-time-input"
              min="1"
              v-model.number="leadTimeDays"
            />
          </div>
        </div>
      </div>

      <!-- Success Banner -->
      <div v-if="submitted" class="success-banner">
        {{ t('restocking.success') }}
      </div>

      <!-- Recommendations Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }}</h3>
          <div class="header-actions">
            <span class="summary-pill">
              {{ t('restocking.totalUnits') }}: <strong>{{ totalUnits }}</strong>
            </span>
            <span class="summary-pill">
              {{ t('restocking.totalCost') }}: <strong>{{ formatCurrency(totalCost) }}</strong>
            </span>
            <button
              class="place-order-btn"
              :disabled="!hasItemsWithinBudget || submitted"
              @click="placeOrder"
            >
              {{ t('restocking.placeOrder') }}
            </button>
          </div>
        </div>

        <div v-if="orderError" class="error">{{ orderError }}</div>

        <div v-if="recommendedItems.length === 0" class="empty-state">
          {{ t('restocking.noItems') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('demand.table.itemName') }}</th>
                <th>{{ t('demand.table.sku') }}</th>
                <th>{{ t('restocking.gap') }}</th>
                <th>{{ t('inventory.table.unitCost') }}</th>
                <th>{{ t('restocking.restockQty') }}</th>
                <th>{{ t('restocking.subtotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendedItems"
                :key="item.item_sku"
                :class="{ dimmed: !item.withinBudget }"
              >
                <td>{{ item.item_name }}</td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.demand_gap }}</td>
                <td>{{ formatCurrency(item.unit_cost) }}</td>
                <td>{{ item.restock_qty }}</td>
                <td>{{ formatCurrency(item.subtotal) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Summary Row -->
        <div v-if="recommendedItems.length > 0" class="summary-row">
          <span>{{ t('restocking.totalUnits') }}: <strong>{{ totalUnits }}</strong></span>
          <span>{{ t('restocking.totalCost') }}: <strong>{{ formatCurrency(totalCost) }}</strong></span>
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
    const { t, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const orderError = ref(null)
    const submitted = ref(false)

    const allForecasts = ref([])
    const inventoryItems = ref([])

    const leadTimeDays = ref(14)
    const budget = ref(0)

    // Build a fast lookup map: sku -> unit_cost
    const inventoryMap = computed(() => {
      const map = {}
      for (const item of inventoryItems.value) {
        map[item.sku] = item.unit_cost
      }
      return map
    })

    // Increasing-trend items sorted by demand gap descending, with computed fields
    const sortedIncreasingItems = computed(() => {
      return allForecasts.value
        .filter(f => f.trend === 'increasing')
        .map(f => {
          const demand_gap = f.forecasted_demand - f.current_demand
          const restock_qty = demand_gap
          const unit_cost = inventoryMap.value[f.item_sku] ?? 0
          const subtotal = restock_qty * unit_cost
          return { ...f, demand_gap, restock_qty, unit_cost, subtotal }
        })
        .sort((a, b) => b.demand_gap - a.demand_gap)
    })

    // Max budget = sum of all increasing items' subtotals, rounded up to nearest $10k
    const maxBudget = computed(() => {
      const total = sortedIncreasingItems.value.reduce((sum, item) => sum + item.subtotal, 0)
      return Math.ceil(total / 10000) * 10000 || 10000
    })

    // Greedy fill: mark each item withinBudget or not
    const recommendedItems = computed(() => {
      let running = 0
      return sortedIncreasingItems.value.map(item => {
        const withinBudget = running + item.subtotal <= budget.value
        if (withinBudget) running += item.subtotal
        return { ...item, withinBudget }
      })
    })

    const hasItemsWithinBudget = computed(() =>
      recommendedItems.value.some(i => i.withinBudget)
    )

    const totalUnits = computed(() =>
      recommendedItems.value
        .filter(i => i.withinBudget)
        .reduce((sum, i) => sum + i.restock_qty, 0)
    )

    const totalCost = computed(() =>
      recommendedItems.value
        .filter(i => i.withinBudget)
        .reduce((sum, i) => sum + i.subtotal, 0)
    )

    const formatCurrency = (value) => {
      const symbol = currentCurrency.value === 'JPY' ? '¥' : '$'
      return symbol + Number(value).toLocaleString()
    }

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData

        // Set default budget to midpoint of maxBudget after data loads
        // maxBudget is computed, so we read it after setting the raw data
        budget.value = Math.round(maxBudget.value / 2 / 1000) * 1000
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      orderError.value = null
      const items = recommendedItems.value
        .filter(i => i.withinBudget)
        .map(i => ({
          sku: i.item_sku,
          name: i.item_name,
          quantity: i.restock_qty,
          unit_cost: i.unit_cost
        }))

      try {
        await api.createRestockingOrder({ items, lead_time_days: leadTimeDays.value })
        submitted.value = true
      } catch (err) {
        orderError.value = 'Failed to place order: ' + (err.response?.data?.detail || err.message)
      }
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      orderError,
      submitted,
      budget,
      maxBudget,
      leadTimeDays,
      recommendedItems,
      hasItemsWithinBudget,
      totalUnits,
      totalCost,
      formatCurrency,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  /* inherits .main-content padding from App.vue */
}

/* Controls */
.controls-card {
  margin-bottom: 1.25rem;
}

.controls-row {
  display: flex;
  align-items: flex-end;
  gap: 2rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 240px;
}

.control-group--narrow {
  flex: 0 0 160px;
  min-width: 120px;
}

.control-label {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.control-value {
  font-size: 0.938rem;
  font-weight: 700;
  color: #2563eb;
  text-transform: none;
  letter-spacing: 0;
}

.slider-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.slider-bound {
  font-size: 0.75rem;
  color: #94a3b8;
  white-space: nowrap;
  flex-shrink: 0;
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
  transition: background 0.2s;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.35);
  transition: box-shadow 0.15s;
}

.budget-slider::-webkit-slider-thumb:hover {
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.5);
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 4px rgba(37, 99, 235, 0.35);
}

.budget-slider::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.lead-time-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.938rem;
  color: #0f172a;
  background: white;
  width: 100%;
  outline: none;
  transition: border-color 0.15s;
}

.lead-time-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

/* Card header actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.summary-pill {
  font-size: 0.813rem;
  color: #64748b;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0.313rem 0.75rem;
}

.summary-pill strong {
  color: #0f172a;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
  white-space: nowrap;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* Dimmed rows */
.dimmed {
  opacity: 0.4;
}

.dimmed:hover {
  background: transparent !important;
}

/* Summary row below table */
.summary-row {
  display: flex;
  gap: 2rem;
  padding: 0.875rem 0.75rem 0;
  margin-top: 0.5rem;
  border-top: 1px solid #e2e8f0;
  font-size: 0.875rem;
  color: #64748b;
}

.summary-row strong {
  color: #0f172a;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Success banner */
.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}
</style>
