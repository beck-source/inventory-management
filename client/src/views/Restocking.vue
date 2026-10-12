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
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-control">
          <input
            type="range"
            min="0"
            max="50000"
            step="500"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
      </div>

      <div v-if="submittedOrder" class="success-banner">
        <span>{{ t('restocking.orderSuccess', { orderNumber: submittedOrder.order_number }) }}</span>
        <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
      </div>

      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ rankedCandidates.length }})</h3>
        </div>

        <div v-if="!rankedCandidates.length" class="empty-state">{{ t('restocking.noItems') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-select">{{ t('restocking.table.select') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.currentStock') }}</th>
                <th>{{ t('restocking.table.reorderPoint') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.recommendedQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in rankedCandidates" :key="item.sku">
                <td class="col-select">
                  <input
                    type="checkbox"
                    :checked="selectedSkus.has(item.sku)"
                    @change="toggleSelection(item.sku)"
                  />
                </td>
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ item.category }}</td>
                <td>{{ translateWarehouse(item.warehouse) }}</td>
                <td>{{ item.quantity_on_hand }}</td>
                <td>{{ item.reorder_point }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>{{ item.restock_qty }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ item.line_cost.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="order-summary">
          <div class="summary-line">
            <span>{{ t('restocking.selectedTotal') }}</span>
            <strong>{{ currencySymbol }}{{ selectedTotal.toLocaleString() }}</strong>
          </div>
          <div class="summary-line">
            <span>{{ t('restocking.remainingBudget') }}</span>
            <strong :class="{ danger: remainingBudget < 0 }">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</strong>
          </div>
          <button class="btn-primary" :disabled="submitting" @click="placeOrder">
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    const budget = ref(20000)
    const selectedSkus = ref(new Set())
    const submitting = ref(false)
    const submitError = ref(null)
    const submittedOrder = ref(null)

    // Use shared filters (budget is page-local state, not part of the shared composable)
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
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

    // Join demand forecasts with inventory (by sku) and compute restock candidates
    const candidates = computed(() => {
      const invMap = new Map(inventoryItems.value.map(item => [item.sku, item]))
      const rows = []

      for (const forecast of allForecasts.value) {
        const inv = invMap.get(forecast.item_sku)
        if (!inv) continue

        const stock_gap = Math.max(inv.reorder_point - inv.quantity_on_hand, 0)
        const demand_growth = forecast.forecasted_demand - forecast.current_demand
        const growth_rate = forecast.current_demand > 0 ? demand_growth / forecast.current_demand : 0
        const restock_qty = stock_gap + Math.max(demand_growth, 0)

        if (restock_qty === 0) continue

        const line_cost = Math.round(restock_qty * forecast.unit_cost * 100) / 100

        rows.push({
          sku: forecast.item_sku,
          name: forecast.item_name,
          category: forecast.category,
          warehouse: forecast.warehouse,
          trend: forecast.trend,
          quantity_on_hand: inv.quantity_on_hand,
          reorder_point: inv.reorder_point,
          unit_cost: forecast.unit_cost,
          stock_gap,
          demand_growth,
          growth_rate,
          restock_qty,
          line_cost
        })
      }

      // Rank: stock_gap desc, then growth_rate desc (tiebreak), then sku asc (final tiebreak)
      rows.sort((a, b) => {
        if (b.stock_gap !== a.stock_gap) return b.stock_gap - a.stock_gap
        if (b.growth_rate !== a.growth_rate) return b.growth_rate - a.growth_rate
        return a.sku.localeCompare(b.sku)
      })

      return rows
    })

    // Greedy budget fill - walk the full ranked list once, keep walking past unaffordable items
    const rankedCandidates = computed(() => {
      let remaining = budget.value
      return candidates.value.map(item => {
        let recommended = false
        if (item.line_cost <= remaining) {
          recommended = true
          remaining -= item.line_cost
        }
        return { ...item, recommended }
      })
    })

    // Reset manual selection to the fresh recommendation whenever budget (or the candidate list) changes
    watch(rankedCandidates, (list) => {
      selectedSkus.value = new Set(list.filter(item => item.recommended).map(item => item.sku))
    }, { immediate: true })

    const toggleSelection = (sku) => {
      const next = new Set(selectedSkus.value)
      if (next.has(sku)) {
        next.delete(sku)
      } else {
        next.add(sku)
      }
      selectedSkus.value = next
    }

    const selectedItems = computed(() => {
      return rankedCandidates.value.filter(item => selectedSkus.value.has(item.sku))
    })

    const selectedTotal = computed(() => {
      return selectedItems.value.reduce((sum, item) => sum + item.line_cost, 0)
    })

    const remainingBudget = computed(() => budget.value - selectedTotal.value)

    const placeOrder = async () => {
      submitError.value = null
      submittedOrder.value = null

      if (selectedItems.value.length === 0) {
        submitError.value = t('restocking.noSelectionWarning')
        return
      }

      submitting.value = true
      try {
        const items = selectedItems.value.map(item => ({
          sku: item.sku,
          name: item.name,
          quantity: item.restock_qty,
          unit_cost: item.unit_cost,
          warehouse: item.warehouse,
          category: item.category
        }))

        submittedOrder.value = await api.submitRestockOrder({ items, budget: budget.value })
      } catch (err) {
        submitError.value = t('restocking.orderError') + ': ' + err.message
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
      selectedSkus,
      rankedCandidates,
      selectedItems,
      selectedTotal,
      remainingBudget,
      submitting,
      submitError,
      submittedOrder,
      toggleSelection,
      placeOrder,
      currencySymbol,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-control {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 120px;
  text-align: right;
}

.col-select {
  width: 60px;
  text-align: center;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.order-summary {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.summary-line {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #64748b;
}

.summary-line strong {
  font-size: 1.125rem;
  color: #0f172a;
}

.summary-line strong.danger {
  color: #dc2626;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.success-banner a {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}
</style>
