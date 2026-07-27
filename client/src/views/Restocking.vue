<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-slider-row">
          <input
            v-model.number="budget"
            type="range"
            min="0"
            max="10000"
            step="250"
            class="budget-slider"
          />
          <div class="budget-readout">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.recommendedItems') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card" :class="budgetRemaining >= 0 ? 'success' : 'danger'">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budgetRemaining.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
        </div>
        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.suggestedQuantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ translateProductName(rec.name) }}</td>
                <td>
                  <span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span>
                </td>
                <td>{{ rec.suggestedQuantity }}</td>
                <td>{{ currencySymbol }}{{ rec.unit_cost.toFixed(2) }}</td>
                <td><strong>{{ currencySymbol }}{{ rec.lineTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="place-order-row">
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || placingOrder"
            @click="placeOrder"
          >
            {{ placingOrder ? t('common.loading') : t('restocking.placeOrder') }}
          </button>
          <div v-if="orderSuccess" class="order-success">
            {{ t('restocking.orderSuccess', { orderNumber: orderSuccess.order_number }) }}
          </div>
          <div v-if="orderError" class="error">{{ orderError }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const inventoryItems = ref([])

    // Page-local budget state (not part of shared useFilters singleton)
    const budget = ref(3000)

    const placingOrder = ref(false)
    const orderSuccess = ref(null)
    const orderError = ref(null)

    // Join demand forecasts to inventory records via sku / item_sku
    const joinedItems = computed(() => {
      const inventoryBySku = new Map(inventoryItems.value.map(item => [item.sku, item]))
      return forecasts.value
        .map(forecast => {
          const inventoryItem = inventoryBySku.get(forecast.item_sku)
          if (!inventoryItem) return null
          return {
            sku: forecast.item_sku,
            name: forecast.item_name,
            trend: forecast.trend,
            forecasted_demand: forecast.forecasted_demand,
            current_demand: forecast.current_demand,
            quantity_on_hand: inventoryItem.quantity_on_hand,
            reorder_point: inventoryItem.reorder_point,
            unit_cost: inventoryItem.unit_cost
          }
        })
        .filter(item => item !== null)
    })

    // Recommendation algorithm: prioritize increasing trend, then largest stock deficit,
    // then greedily fill affordable quantities within the budget.
    const recommendations = computed(() => {
      const sortedItems = joinedItems.value
        .map(item => ({
          ...item,
          deficit: item.forecasted_demand - item.quantity_on_hand
        }))
        .sort((a, b) => {
          const aIncreasing = a.trend === 'increasing'
          const bIncreasing = b.trend === 'increasing'
          if (aIncreasing && !bIncreasing) return -1
          if (bIncreasing && !aIncreasing) return 1
          return b.deficit - a.deficit
        })

      const result = []
      let remainingBudget = budget.value

      for (const item of sortedItems) {
        const neededQuantity = Math.max(0, item.deficit)
        if (neededQuantity < 1) continue

        const affordableQuantity = Math.min(neededQuantity, Math.floor(remainingBudget / item.unit_cost))
        if (affordableQuantity < 1) continue

        const lineTotal = affordableQuantity * item.unit_cost
        result.push({
          sku: item.sku,
          name: item.name,
          trend: item.trend,
          unit_cost: item.unit_cost,
          suggestedQuantity: affordableQuantity,
          lineTotal
        })
        remainingBudget -= lineTotal
      }

      return result
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, rec) => sum + rec.lineTotal, 0)
    })

    const budgetRemaining = computed(() => {
      return budget.value - totalCost.value
    })

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        forecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      placingOrder.value = true
      orderSuccess.value = null
      orderError.value = null
      try {
        const payload = {
          items: recommendations.value.map(rec => ({
            sku: rec.sku,
            name: rec.name,
            quantity: rec.suggestedQuantity,
            unit_cost: rec.unit_cost
          })),
          budget: budget.value
        }
        orderSuccess.value = await api.createRestockOrder(payload)
      } catch (err) {
        orderError.value = 'Failed to place restock order: ' + err.message
      } finally {
        placingOrder.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      budget,
      recommendations,
      totalCost,
      budgetRemaining,
      placingOrder,
      orderSuccess,
      orderError,
      placeOrder,
      currencySymbol,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-readout {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 100px;
  text-align: right;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.place-order-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #f1f5f9;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
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

.order-success {
  color: #059669;
  font-weight: 600;
  font-size: 0.938rem;
}
</style>
