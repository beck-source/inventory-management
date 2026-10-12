<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Slider Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-controls">
          <div class="budget-display">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
          <div class="slider-row">
            <span class="slider-bound">{{ currencySymbol }}10,000</span>
            <input
              v-model.number="budget"
              type="range"
              min="10000"
              max="500000"
              step="5000"
              class="budget-slider"
            />
            <span class="slider-bound">{{ currencySymbol }}500,000</span>
          </div>
        </div>
      </div>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.itemsSelected') }}</div>
          <div class="stat-value">{{ recommendedItems.length }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.totalCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.budgetRemaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budgetRemaining.toLocaleString() }}</div>
        </div>
      </div>

      <!-- Recommendations Table -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <span class="card-subtitle">{{ t('restocking.recommendationsSubtitle') }}</span>
        </div>

        <div v-if="recommendedItems.length === 0" class="no-recommendations">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.forecastedQty') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendedItems" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
                <td>{{ item.quantity.toLocaleString() }}</td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ item.line_cost.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Place Order -->
        <div class="order-actions">
          <button
            class="place-order-btn"
            :disabled="recommendedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('common.loading') : t('restocking.placeOrder') }}
          </button>
          <span v-if="orderSuccess" class="order-success">{{ t('restocking.orderSuccess') }}</span>
          <span v-if="orderError" class="order-error">{{ orderError }}</span>
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
    const forecasts = ref([])
    const inventoryItems = ref([])
    const budget = ref(100000)
    const submitting = ref(false)
    const orderSuccess = ref(false)
    const orderError = ref(null)

    // Currency symbol derived from locale
    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    // Build a SKU → inventory item map for O(1) lookups in the algorithm
    const inventoryMap = computed(() => {
      const map = {}
      for (const item of inventoryItems.value) {
        map[item.sku] = item
      }
      return map
    })

    // Greedy budget-driven recommendation algorithm:
    // 1. Exclude decreasing trend items
    // 2. Sort: increasing first (rank 0), stable second (rank 1)
    // 3. Iterate all eligible items; skip any that don't fit the remaining budget
    //    (don't stop at first miss — keep going to fill remaining budget)
    const recommendedItems = computed(() => {
      const eligible = forecasts.value
        .filter(f => f.trend !== 'decreasing')
        .sort((a, b) => {
          const rank = { increasing: 0, stable: 1 }
          return (rank[a.trend] ?? 2) - (rank[b.trend] ?? 2)
        })

      let remaining = budget.value
      const selected = []

      for (const f of eligible) {
        const inv = inventoryMap.value[f.item_sku]
        if (!inv) continue // SKU not in inventory — skip

        const lineCost = f.forecasted_demand * inv.unit_cost
        if (lineCost > remaining) continue // doesn't fit — skip but keep iterating

        selected.push({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          quantity: f.forecasted_demand,
          unit_cost: inv.unit_cost,
          line_cost: lineCost
        })
        remaining -= lineCost
      }

      return selected
    })

    const totalCost = computed(() =>
      recommendedItems.value.reduce((sum, item) => sum + item.line_cost, 0)
    )

    const budgetRemaining = computed(() => budget.value - totalCost.value)

    const loadData = async () => {
      loading.value = true
      error.value = null
      try {
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        forecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
        console.error(err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendedItems.value.length === 0 || submitting.value) return

      submitting.value = true
      orderSuccess.value = false
      orderError.value = null

      try {
        await api.submitRestockingOrder({
          budget: budget.value,
          items: recommendedItems.value.map(({ sku, name, quantity, unit_cost }) => ({
            sku,
            name,
            quantity,
            unit_cost
          }))
        })
        orderSuccess.value = true
      } catch (err) {
        orderError.value = t('restocking.orderError')
        console.error(err)
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
      currencySymbol,
      recommendedItems,
      totalCost,
      budgetRemaining,
      submitting,
      orderSuccess,
      orderError,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  /* inherits page background from global styles */
}

/* Budget card controls */
.budget-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
}

.budget-display {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
}

.slider-bound {
  font-size: 0.813rem;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}

.budget-slider {
  flex: 1;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

/* Subtitle next to card title */
.card-subtitle {
  font-size: 0.875rem;
  color: #64748b;
}

/* Empty state */
.no-recommendations {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Place order footer */
.order-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem 0 0.25rem;
  border-top: 1px solid #e2e8f0;
  margin-top: 1rem;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease, opacity 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.order-success {
  color: #059669;
  font-size: 0.938rem;
  font-weight: 500;
}

.order-error {
  color: #dc2626;
  font-size: 0.938rem;
  font-weight: 500;
}
</style>
