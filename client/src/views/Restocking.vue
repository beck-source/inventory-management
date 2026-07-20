<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>

      <!-- Budget Card -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
        </div>
        <div class="budget-body">
          <div class="budget-amount">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
          <input
            type="range"
            class="budget-slider"
            :min="0"
            :max="500000"
            :step="500"
            v-model.number="budget"
          />
          <div class="budget-utilization">
            <span>
              Total selected: {{ currencySymbol }}{{ totalCost.toLocaleString() }}
              ({{ budgetPercent }}% {{ t('restocking.budgetUsed') }})
            </span>
            <span :class="['budget-status-label', budgetPercent > 100 ? 'over' : 'within']">
              {{ budgetPercent > 100 ? t('restocking.overBudget') : t('restocking.withinBudget') }}
            </span>
          </div>
          <div class="progress-bar-track">
            <div
              class="progress-bar-fill"
              :style="{ width: Math.min(budgetPercent, 100) + '%' }"
              :class="{ 'over-budget': budgetPercent > 100 }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Recommended Items Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendations.length }})</h3>
          <div class="header-actions">
            <button class="btn-text" @click="selectAll">{{ t('restocking.selectAll') }}</button>
            <button class="btn-text" @click="clearAll">{{ t('restocking.clearAll') }}</button>
          </div>
        </div>

        <div v-if="recommendations.length === 0" class="no-data">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table class="restock-items-table">
            <thead>
              <tr>
                <th class="col-check"></th>
                <th>Item Name</th>
                <th>SKU</th>
                <th>{{ t('restocking.trend') }}</th>
                <th>{{ t('restocking.currentStock') }}</th>
                <th>{{ t('restocking.reorderPoint') }}</th>
                <th>{{ t('restocking.quantity') }}</th>
                <th>{{ t('restocking.estimatedCost') }}</th>
                <th>{{ t('restocking.withinBudget') }}?</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in recommendations"
                :key="item.sku"
                :class="{ 'row-dimmed': !isWithinBudget(item) && !isSelected(item.sku) }"
              >
                <td class="col-check">
                  <input
                    v-if="isSelected(item.sku) || isWithinBudget(item)"
                    type="checkbox"
                    :checked="isSelected(item.sku)"
                    @change="toggleItem(item.sku)"
                  />
                  <span v-else class="over-budget-icon" title="Over budget">-</span>
                </td>
                <td><strong>{{ item.name }}</strong></td>
                <td class="sku-cell">{{ item.sku }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
                <td>{{ item.current_stock }}</td>
                <td>{{ item.reorder_point }}</td>
                <td>{{ item.quantity_to_order }}</td>
                <td>{{ currencySymbol }}{{ item.estimated_cost.toLocaleString() }}</td>
                <td>
                  <span v-if="isSelected(item.sku)" class="badge success">{{ t('restocking.withinBudget') }}</span>
                  <span v-else-if="isWithinBudget(item)" class="badge info">{{ t('restocking.withinBudget') }}</span>
                  <span v-else class="badge danger">{{ t('restocking.overBudget') }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Footer / Order Actions -->
        <div class="order-footer">
          <div class="order-summary">
            <span class="selected-count">{{ selectedSkus.size }} {{ t('restocking.selectedItems') }}</span>
            <span class="total-cost">{{ t('restocking.totalCost') }}: <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong></span>
          </div>
          <div class="order-actions">
            <div v-if="orderSuccess" class="success-message">
              {{ t('restocking.successMessage') }}
            </div>
            <button
              class="btn-primary"
              :disabled="placing || selectedSkus.size === 0"
              @click="placeOrder"
            >
              {{ placing ? t('restocking.orderPlaced') + '...' : t('restocking.placeOrder') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Submitted Restocking Orders -->
      <div v-if="restockOrders.length > 0" class="card submitted-orders-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.submittedOrders') }} ({{ restockOrders.length }})</h3>
        </div>
        <div class="table-container">
          <table class="submitted-orders-table">
            <thead>
              <tr>
                <th>{{ t('restocking.orderNumber') }}</th>
                <th>{{ t('orders.table.items') }}</th>
                <th>{{ t('restocking.placedDate') }}</th>
                <th>{{ t('restocking.expectedDelivery') }}</th>
                <th>{{ t('orders.table.totalValue') }}</th>
                <th>{{ t('orders.table.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in restockOrders" :key="order.id">
                <td><strong>{{ order.order_number }}</strong></td>
                <td>{{ t('orders.itemsCount', { count: order.items.length }) }}</td>
                <td>{{ formatDate(order.order_date) }}</td>
                <td>{{ formatDate(order.expected_delivery) }}</td>
                <td><strong>{{ currencySymbol }}{{ order.total_value.toLocaleString() }}</strong></td>
                <td><span class="badge warning">{{ order.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const demandForecasts = ref([])
    const inventoryItems = ref([])
    const restockOrders = ref([])
    const budget = ref(50000)
    const selectedSkus = ref(new Set())
    const placing = ref(false)
    const orderSuccess = ref(false)

    // Build recommendations from demand forecasts + inventory
    const recommendations = computed(() => {
      const inventoryMap = {}
      inventoryItems.value.forEach(item => {
        inventoryMap[item.sku] = item
      })

      const result = []
      demandForecasts.value.forEach(forecast => {
        if (forecast.trend === 'decreasing') return

        const inventoryItem = inventoryMap[forecast.item_sku]
        const quantity_to_order = Math.max(forecast.forecasted_demand - forecast.current_demand, 1)
        const unit_cost = inventoryItem?.unit_cost ?? 25.00
        const estimated_cost = quantity_to_order * unit_cost

        result.push({
          sku: forecast.item_sku,
          name: forecast.item_name,
          trend: forecast.trend,
          current_stock: inventoryItem?.quantity_on_hand ?? 'N/A',
          reorder_point: inventoryItem?.reorder_point ?? 'N/A',
          quantity_to_order,
          unit_cost,
          estimated_cost
        })
      })

      // Sort: increasing first, then stable; ties by estimated_cost descending
      result.sort((a, b) => {
        if (a.trend === b.trend) {
          return b.estimated_cost - a.estimated_cost
        }
        if (a.trend === 'increasing') return -1
        if (b.trend === 'increasing') return 1
        return 0
      })

      return result
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, item) => {
        if (selectedSkus.value.has(item.sku)) {
          return sum + item.estimated_cost
        }
        return sum
      }, 0)
    })

    const budgetPercent = computed(() => {
      if (budget.value === 0) return 0
      return Math.round((totalCost.value / budget.value) * 100)
    })

    const isSelected = (sku) => {
      return selectedSkus.value.has(sku)
    }

    const isWithinBudget = (item) => {
      const currentTotal = totalCost.value
      if (selectedSkus.value.has(item.sku)) return true
      return (currentTotal + item.estimated_cost) <= budget.value
    }

    // Greedily select items that fit within budget
    const applyBudgetSelection = () => {
      const newSet = new Set()
      let cumulative = 0
      for (const item of recommendations.value) {
        if (cumulative + item.estimated_cost <= budget.value) {
          newSet.add(item.sku)
          cumulative += item.estimated_cost
        }
      }
      selectedSkus.value = newSet
    }

    const toggleItem = (sku) => {
      const newSet = new Set(selectedSkus.value)
      if (newSet.has(sku)) {
        newSet.delete(sku)
      } else {
        newSet.add(sku)
      }
      selectedSkus.value = newSet
    }

    const selectAll = () => {
      const newSet = new Set(recommendations.value.map(item => item.sku))
      selectedSkus.value = newSet
    }

    const clearAll = () => {
      selectedSkus.value = new Set()
    }

    const loadRestockOrders = async () => {
      try {
        restockOrders.value = await api.getRestockOrders()
      } catch (err) {
        console.error('Failed to load restock orders:', err)
      }
    }

    const placeOrder = async () => {
      if (placing.value || selectedSkus.value.size === 0) return
      placing.value = true
      orderSuccess.value = false

      const selectedItems = recommendations.value
        .filter(item => selectedSkus.value.has(item.sku))
        .map(item => ({
          sku: item.sku,
          name: item.name,
          quantity: item.quantity_to_order,
          unit_cost: item.unit_cost
        }))

      try {
        await api.createRestockOrder({
          items: selectedItems,
          total_value: totalCost.value,
          warehouse: 'San Francisco'
        })
        orderSuccess.value = true
        selectedSkus.value = new Set()
        await loadRestockOrders()
      } catch (err) {
        console.error('Failed to place restock order:', err)
        error.value = 'Failed to place restocking order. Please try again.'
      } finally {
        placing.value = false
      }
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    // When budget changes, recompute greedy selection
    watch(budget, () => {
      applyBudgetSelection()
    })

    // After recommendations load, apply initial budget selection
    watch(recommendations, (newVal) => {
      if (newVal.length > 0 && selectedSkus.value.size === 0) {
        applyBudgetSelection()
      }
    })

    onMounted(async () => {
      loading.value = true
      error.value = null
      try {
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        demandForecasts.value = forecasts
        inventoryItems.value = inventory
        await loadRestockOrders()
        applyBudgetSelection()
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    })

    return {
      t,
      currencySymbol,
      loading,
      error,
      recommendations,
      budget,
      selectedSkus,
      totalCost,
      budgetPercent,
      placing,
      orderSuccess,
      restockOrders,
      isSelected,
      isWithinBudget,
      toggleItem,
      selectAll,
      clearAll,
      placeOrder,
      formatDate
    }
  }
}
</script>

<style scoped>
.restocking {
  padding: 0;
}

/* Budget Card */
.budget-card .budget-body {
  padding: 0.5rem 0;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 0.75rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  margin-bottom: 0.75rem;
  cursor: pointer;
  height: 4px;
}

.budget-utilization {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.budget-status-label {
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
}

.budget-status-label.within {
  background: #d1fae5;
  color: #065f46;
}

.budget-status-label.over {
  background: #fecaca;
  color: #991b1b;
}

.progress-bar-track {
  height: 6px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 999px;
  transition: width 0.3s ease;
}

.progress-bar-fill.over-budget {
  background: #dc2626;
}

/* Header actions */
.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-text {
  background: none;
  border: 1px solid #e2e8f0;
  color: #2563eb;
  font-size: 0.813rem;
  font-weight: 500;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-text:hover {
  background: #eff6ff;
  border-color: #2563eb;
}

/* Table */
.restock-items-table {
  width: 100%;
  border-collapse: collapse;
}

.col-check {
  width: 40px;
  text-align: center;
}

.sku-cell {
  font-family: monospace;
  font-size: 0.813rem;
  color: #64748b;
}

.row-dimmed {
  opacity: 0.45;
}

.over-budget-icon {
  display: inline-block;
  color: #94a3b8;
  font-weight: 700;
  font-size: 1rem;
}

/* No data */
.no-data {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Order footer */
.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0 0;
  margin-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
  gap: 1rem;
}

.order-summary {
  display: flex;
  gap: 1.5rem;
  align-items: center;
  font-size: 0.875rem;
  color: #64748b;
}

.selected-count {
  font-weight: 600;
  color: #0f172a;
}

.total-cost {
  color: #64748b;
}

.order-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.success-message {
  background: #d1fae5;
  color: #065f46;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid #a7f3d0;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* Submitted orders card */
.submitted-orders-card {
  border-top: 3px solid #2563eb;
}

.submitted-orders-table {
  width: 100%;
  border-collapse: collapse;
}
</style>
