<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget slider -->
      <div class="card budget-card">
        <div class="budget-row">
          <div class="budget-label">{{ t('restocking.budgetLabel') }}</div>
          <div class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <input
          type="range"
          class="budget-slider"
          min="0"
          :max="maxBudget"
          :step="sliderStep"
          v-model.number="budget"
        />
        <div class="budget-scale">
          <span>{{ formatCurrency(0, currentCurrency) }}</span>
          <span class="budget-hint">{{ t('restocking.budgetHint') }}</span>
          <span>{{ formatCurrency(maxBudget, currentCurrency) }}</span>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <span v-if="candidates.length" class="recommend-count">
            {{ t('restocking.itemsSelected', { count: recommendations.length }) }}
          </span>
        </div>

        <div v-if="!candidates.length" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>

        <template v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('demand.table.sku') }}</th>
                  <th>{{ t('demand.table.itemName') }}</th>
                  <th class="num">{{ t('demand.table.currentDemand') }}</th>
                  <th class="num">{{ t('demand.table.forecastedDemand') }}</th>
                  <th class="num">{{ t('restocking.qtyToOrder') }}</th>
                  <th class="num">{{ t('restocking.unitCost') }}</th>
                  <th class="num">{{ t('restocking.lineTotal') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations" :key="item.id">
                  <td><strong>{{ item.sku }}</strong></td>
                  <td>{{ item.name }}</td>
                  <td class="num">{{ item.current.toLocaleString() }}</td>
                  <td class="num"><strong>{{ item.forecasted.toLocaleString() }}</strong></td>
                  <td class="num">
                    <span class="badge increasing">+{{ item.gap.toLocaleString() }}</span>
                  </td>
                  <td class="num">
                    {{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}<span v-if="item.estimated" class="est-marker" :title="'Estimated price'">*</span>
                  </td>
                  <td class="num"><strong>{{ formatCurrency(item.lineCost, currentCurrency) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="order-summary">
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.selectedTotal') }}</span>
              <span class="summary-value">{{ formatCurrency(selectedTotal, currentCurrency) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">{{ t('restocking.remaining') }}</span>
              <span class="summary-value">{{ formatCurrency(remaining, currentCurrency) }}</span>
            </div>
            <button
              class="place-order-btn"
              :disabled="recommendations.length === 0"
              @click="placeOrder"
            >
              {{ t('restocking.placeOrder') }}
            </button>
          </div>

          <p v-if="hasEstimatedPrices" class="est-note">
            * {{ t('restocking.estimatedNote') }}
          </p>

          <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { useRestocking } from '../composables/useRestocking'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const LEAD_TIME_DAYS = 14

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()
    const { addSubmittedOrder } = useRestocking()

    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])
    const budget = ref(0)
    const successMessage = ref('')

    // Lookup of sku -> inventory item (only items matching the active filters,
    // which also scopes recommendations to the selected warehouse/category).
    const invBySku = computed(() => {
      const map = new Map()
      inventoryItems.value.forEach(item => map.set(item.sku, item))
      return map
    })

    // Fallback unit cost for forecast items that have no matching inventory SKU
    // (the demo's forecast and inventory data use largely disjoint SKUs), so
    // every recommended item can still be costed against the budget.
    const fallbackPrice = computed(() => {
      if (!inventoryItems.value.length) return 50
      const total = inventoryItems.value.reduce((sum, i) => sum + i.unit_cost, 0)
      return total / inventoryItems.value.length
    })

    // Items worth restocking: any positive demand gap, sorted largest gap first
    // so the budget funds the biggest shortfalls. Unit cost comes from a matching
    // inventory item when available, otherwise the fallback (estimated) price.
    const candidates = computed(() => {
      return allForecasts.value
        .filter(f => f.forecasted_demand - f.current_demand > 0)
        .map(f => {
          const inv = invBySku.value.get(f.item_sku)
          const gap = f.forecasted_demand - f.current_demand
          const unit_cost = inv ? inv.unit_cost : fallbackPrice.value
          return {
            id: f.id,
            sku: f.item_sku,
            name: f.item_name,
            current: f.current_demand,
            forecasted: f.forecasted_demand,
            gap,
            unit_cost,
            lineCost: gap * unit_cost,
            estimated: !inv
          }
        })
        .sort((a, b) => b.gap - a.gap)
    })

    // Total cost to fully fund every gap; drives the slider's upper bound.
    const maxBudget = computed(() => {
      const total = candidates.value.reduce((sum, c) => sum + c.lineCost, 0)
      return Math.ceil(total / 100) * 100
    })

    // Keep the slider granular regardless of the budget magnitude (~200 steps).
    const sliderStep = computed(() => Math.max(1, Math.round(maxBudget.value / 200)))

    // Greedily include items (largest gap first) while they fit the budget.
    const recommendations = computed(() => {
      const result = []
      let running = 0
      for (const c of candidates.value) {
        if (running + c.lineCost <= budget.value) {
          result.push(c)
          running += c.lineCost
        }
      }
      return result
    })

    const selectedTotal = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.lineCost, 0)
    )
    const remaining = computed(() => budget.value - selectedTotal.value)

    // True when any recommended item used the estimated fallback price.
    const hasEstimatedPrices = computed(() => recommendations.value.some(r => r.estimated))

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        const filters = getCurrentFilters()
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({ warehouse: filters.warehouse, category: filters.category })
        ])
        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Default the budget to fully fund all gaps whenever the data set changes.
    watch(maxBudget, (newMax) => {
      budget.value = newMax
    })

    // Reload (and re-scope) when the warehouse/category filters change.
    watch([selectedLocation, selectedCategory], () => {
      successMessage.value = ''
      loadData()
    })

    const placeOrder = () => {
      if (!recommendations.value.length) return

      const now = new Date()
      const expected = new Date(now.getTime() + LEAD_TIME_DAYS * 24 * 60 * 60 * 1000)
      const orderNumber = `RST-${now.getFullYear()}-${String(now.getTime()).slice(-4)}`

      addSubmittedOrder({
        id: `RESTOCK-${now.getTime()}`,
        order_number: orderNumber,
        customer: 'Internal Restock',
        items: recommendations.value.map(r => ({
          sku: r.sku,
          name: r.name,
          quantity: r.gap,
          unit_price: r.unit_cost
        })),
        status: 'Submitted',
        order_date: now.toISOString(),
        expected_delivery: expected.toISOString(),
        total_value: selectedTotal.value,
        warehouse: selectedLocation.value !== 'all' ? selectedLocation.value : null,
        category: selectedCategory.value !== 'all' ? selectedCategory.value : null,
        lead_time_days: LEAD_TIME_DAYS
      })

      successMessage.value = t('restocking.orderPlaced', { orderNumber })
    }

    onMounted(loadData)

    return {
      t,
      currentCurrency,
      loading,
      error,
      budget,
      maxBudget,
      sliderStep,
      candidates,
      recommendations,
      selectedTotal,
      remaining,
      hasEstimatedPrices,
      successMessage,
      placeOrder,
      formatCurrency,
      formatCurrencyWithDecimals
    }
  }
}
</script>

<style scoped>
.budget-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  appearance: none;
  -webkit-appearance: none;
  background: #e2e8f0;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: #94a3b8;
}

.budget-hint {
  color: #64748b;
  font-style: italic;
}

.recommend-count {
  font-size: 0.813rem;
  font-weight: 600;
  color: #2563eb;
}

.num {
  text-align: right;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.order-summary {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.place-order-btn {
  padding: 0.75rem 1.75rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
  transform: translateY(-1px);
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.est-marker {
  color: #d97706;
  font-weight: 700;
  margin-left: 2px;
}

.est-note {
  margin-top: 0.75rem;
  font-size: 0.75rem;
  color: #94a3b8;
  font-style: italic;
}

.success-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #d1fae5;
  color: #065f46;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
}
</style>
