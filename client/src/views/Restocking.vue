<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="orderPlaced" class="success-banner">
      {{ t('restocking.orderSuccess') }}
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>

      <!-- Budget Slider -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-display">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
        <input
          type="range"
          v-model.number="budget"
          min="0"
          max="500000"
          step="1000"
          class="budget-slider"
        />
        <div class="slider-labels">
          <span>{{ currencySymbol }}0</span>
          <span>{{ currencySymbol }}500,000</span>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <div v-if="recommendations.length > 0" class="budget-tracker">
            <span class="budget-tracker-label">
              {{ currencySymbol }}{{ totalCost.toLocaleString() }} / {{ currencySymbol }}{{ budget.toLocaleString() }}
            </span>
            <div class="budget-bar">
              <div
                class="budget-bar-fill"
                :style="{ width: Math.min(budgetPercent, 100) + '%' }"
                :class="{ overage: totalCost > budget }"
              ></div>
            </div>
          </div>
        </div>

        <div v-if="recommendations.length === 0" class="no-recs">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.subtotal') }}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, idx) in recommendations" :key="item.sku">
                <td>{{ item.name }}</td>
                <td><code class="sku-code">{{ item.sku }}</code></td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td>
                  <input
                    type="number"
                    v-model.number="item.quantity"
                    min="1"
                    class="qty-input"
                  />
                </td>
                <td>
                  <strong>{{ currencySymbol }}{{ (item.quantity * item.unit_cost).toLocaleString() }}</strong>
                </td>
                <td>
                  <button @click="removeItem(idx)" class="remove-btn">
                    {{ t('restocking.removeItem') }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="recommendations.length > 0" class="card-footer">
          <div class="footer-summary">
            <span>{{ t('restocking.total') }}: <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong></span>
            <span class="remaining-budget" :class="{ negative: remainingBudget < 0 }">
              {{ t('restocking.budgetRemaining') }}: <strong>{{ currencySymbol }}{{ Math.abs(remainingBudget).toLocaleString() }}</strong>
            </span>
          </div>
          <button
            @click="placeOrder"
            :disabled="placing || recommendations.length === 0"
            class="place-order-btn"
          >
            {{ placing ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
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
    const { t, currentCurrency } = useI18n()
    const { selectedLocation } = useFilters()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const orderPlaced = ref(false)

    const forecasts = ref([])
    const inventoryItems = ref([])
    const recommendations = ref([])
    const budget = ref(100000)

    // Map sku -> inventory item for fast lookups
    const inventoryMap = computed(() => {
      const map = {}
      for (const item of inventoryItems.value) {
        map[item.sku] = item
      }
      return map
    })

    const totalCost = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.quantity * r.unit_cost, 0)
    )

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const budgetPercent = computed(() =>
      budget.value > 0 ? (totalCost.value / budget.value) * 100 : 0
    )

    // Trend priority: increasing items are restocked first, then stable
    const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }

    const generateRecommendations = () => {
      if (budget.value <= 0 || forecasts.value.length === 0) {
        recommendations.value = []
        return
      }

      const sorted = [...forecasts.value].sort(
        (a, b) => (TREND_ORDER[a.trend] ?? 3) - (TREND_ORDER[b.trend] ?? 3)
      )

      let remaining = budget.value
      const recs = []

      for (const forecast of sorted) {
        const invItem = inventoryMap.value[forecast.item_sku]
        if (!invItem) continue // skip if no matching inventory item

        const unitCost = invItem.unit_cost
        if (unitCost > remaining) continue // can't afford even one unit

        // Cap at forecasted_demand — don't over-order beyond what's anticipated
        const maxAffordable = Math.floor(remaining / unitCost)
        const qty = Math.min(forecast.forecasted_demand, maxAffordable)
        if (qty <= 0) continue

        recs.push({
          sku: forecast.item_sku,
          name: forecast.item_name,
          trend: forecast.trend,
          unit_cost: unitCost,
          category: invItem.category,
          warehouse: invItem.warehouse,
          quantity: qty
        })

        remaining -= qty * unitCost
      }

      recommendations.value = recs
    }

    const removeItem = (idx) => {
      recommendations.value.splice(idx, 1)
    }

    const placeOrder = async () => {
      placing.value = true
      error.value = null
      try {
        // Use the active location filter as the warehouse, else fall back to the first recommendation's warehouse
        const warehouse =
          selectedLocation.value !== 'all'
            ? selectedLocation.value
            : (recommendations.value[0]?.warehouse || 'San Francisco')

        // Determine the primary category by frequency across recommendations
        const categoryCounts = {}
        for (const r of recommendations.value) {
          categoryCounts[r.category] = (categoryCounts[r.category] || 0) + 1
        }
        const category = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'Mixed'

        const payload = {
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.quantity,
            unit_price: r.unit_cost
          })),
          warehouse,
          category,
          customer: 'Internal Restock'
        }

        await api.createOrder(payload)
        orderPlaced.value = true
        recommendations.value = []
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    const loadData = async () => {
      try {
        loading.value = true
        const [forecastData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        forecasts.value = forecastData
        inventoryItems.value = inventoryData
        generateRecommendations()
      } catch (err) {
        error.value = 'Failed to load data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Regenerate recommendations whenever the budget slider moves
    watch(budget, generateRecommendations)

    onMounted(loadData)

    return {
      t,
      currencySymbol,
      loading,
      error,
      placing,
      orderPlaced,
      budget,
      recommendations,
      totalCost,
      remainingBudget,
      budgetPercent,
      removeItem,
      placeOrder
    }
  }
}
</script>

<style scoped>
/* Budget slider */
.budget-display {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.budget-slider {
  width: 100%;
  margin: 0.75rem 0 0.375rem;
  accent-color: #2563eb;
  cursor: pointer;
  height: 6px;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}

/* Budget progress bar */
.budget-tracker {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
  min-width: 220px;
}

.budget-tracker-label {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.budget-bar {
  width: 220px;
  height: 6px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}

.budget-bar-fill {
  height: 100%;
  background: #2563eb;
  border-radius: 999px;
  transition: width 0.3s ease, background-color 0.2s;
}

.budget-bar-fill.overage {
  background: #dc2626;
}

/* No recommendations state */
.no-recs {
  padding: 2rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.938rem;
}

/* SKU code style */
.sku-code {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.8rem;
  background: #f1f5f9;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  color: #475569;
}

/* Quantity input */
.qty-input {
  width: 80px;
  padding: 0.375rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #0f172a;
  text-align: right;
  transition: border-color 0.15s;
}

.qty-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
}

/* Remove button */
.remove-btn {
  padding: 0.25rem 0.625rem;
  font-size: 0.75rem;
  color: #dc2626;
  background: transparent;
  border: 1px solid #fecaca;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s;
}

.remove-btn:hover {
  background: #fef2f2;
  border-color: #dc2626;
}

/* Card footer with total and action */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 0.75rem 0;
  margin-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
}

.footer-summary {
  display: flex;
  gap: 1.5rem;
  font-size: 0.938rem;
  color: #334155;
}

.remaining-budget {
  color: #059669;
}

.remaining-budget.negative {
  color: #dc2626;
}

/* Place Order button */
.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  font-weight: 600;
  font-size: 0.938rem;
  border: none;
  border-radius: 8px;
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

/* Success banner */
.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-weight: 500;
  font-size: 0.938rem;
}
</style>
