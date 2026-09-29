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
            v-model.number="budget"
            :min="0"
            :max="maxBudget"
            :step="500"
            class="budget-slider"
          />
          <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendations.length }})</h3>
          <span :class="['badge', isWithinBudget ? 'success' : 'danger']">
            {{ isWithinBudget ? t('restocking.withinBudget') : t('restocking.overBudget') }}
          </span>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <template v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.forecastedGap') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.recommendedQty') }}</th>
                  <th>{{ t('restocking.table.subtotal') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="rec in recommendations" :key="rec.sku">
                  <td><strong>{{ rec.sku }}</strong></td>
                  <td>{{ rec.name }}</td>
                  <td>{{ rec.gap }}</td>
                  <td>{{ currencySymbol }}{{ rec.unit_cost.toFixed(2) }}</td>
                  <td>{{ rec.gap }}</td>
                  <td><strong>{{ currencySymbol }}{{ formatMoney(rec.subtotal) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="order-footer">
            <div class="running-total">
              <span class="running-total-label">{{ t('restocking.runningTotal') }}:</span>
              <span class="running-total-value">{{ currencySymbol }}{{ formatMoney(runningTotal) }}</span>
              <span class="running-total-sep">/</span>
              <span class="running-total-budget">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
            </div>
            <button
              class="place-order-btn"
              :disabled="recommendations.length === 0 || submitting"
              @click="placeOrder"
            >
              {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
            </button>
          </div>
        </template>

        <div v-if="submitSuccess" class="success-message">{{ t('restocking.orderSuccess') }}</div>
        <div v-if="submitError" class="error">{{ t('restocking.orderError') }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const inventoryItems = ref([])
    const demandForecasts = ref([])

    const budget = ref(25000)
    const submitting = ref(false)
    const submitSuccess = ref(false)
    const submitError = ref(false)

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        submitSuccess.value = false
        submitError.value = false

        const filters = getCurrentFilters()
        const [inventoryData, demandData] = await Promise.all([
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          }),
          api.getDemandForecasts()
        ])

        inventoryItems.value = inventoryData
        demandForecasts.value = demandData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Client-side join: match demand forecasts to inventory by SKU, compute gap
    const candidates = computed(() => {
      const inventoryBySku = new Map(inventoryItems.value.map(item => [item.sku, item]))

      const gapItems = []
      for (const forecast of demandForecasts.value) {
        const item = inventoryBySku.get(forecast.item_sku)
        if (!item) continue

        const gap = forecast.forecasted_demand - forecast.current_demand
        if (gap <= 0) continue

        gapItems.push({
          sku: item.sku,
          name: item.name,
          gap,
          unit_cost: item.unit_cost,
          subtotal: gap * item.unit_cost
        })
      }

      // Sort by gap descending
      return gapItems.sort((a, b) => b.gap - a.gap)
    })

    const maxBudget = computed(() => {
      const totalNeeded = candidates.value.reduce((sum, c) => sum + c.subtotal, 0)
      return Math.max(10000, Math.ceil(totalNeeded / 500) * 500)
    })

    // Greedy fill: strict break-on-first-miss (do NOT skip to a cheaper item)
    const recommendations = computed(() => {
      const result = []
      let total = 0

      for (const candidate of candidates.value) {
        const cost = candidate.subtotal
        if (total + cost > budget.value) break
        total += cost
        result.push(candidate)
      }

      return result
    })

    const runningTotal = computed(() => {
      return recommendations.value.reduce((sum, r) => sum + r.subtotal, 0)
    })

    const isWithinBudget = computed(() => runningTotal.value <= budget.value)

    const formatMoney = (value) => {
      return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    // Keep budget within the available slider range if the candidate set shrinks
    watch(maxBudget, (newMax) => {
      if (budget.value > newMax) {
        budget.value = newMax
      }
    })

    watch(budget, () => {
      submitSuccess.value = false
      submitError.value = false
    })

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadData()
    })

    const placeOrder = async () => {
      if (recommendations.value.length === 0) return

      submitting.value = true
      submitSuccess.value = false
      submitError.value = false

      try {
        const filters = getCurrentFilters()
        await api.createRestockingOrder({
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.gap,
            unit_cost: r.unit_cost
          })),
          warehouse: filters.warehouse,
          category: filters.category
        })
        submitSuccess.value = true
        await loadData()
      } catch (err) {
        submitError.value = true
        console.error('Failed to submit restocking order:', err)
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
      recommendations,
      runningTotal,
      isWithinBudget,
      currencySymbol,
      formatMoney,
      submitting,
      submitSuccess,
      submitError,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-control {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 120px;
  text-align: right;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #64748b;
  font-style: italic;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.running-total {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.938rem;
}

.running-total-label {
  color: #64748b;
  font-weight: 600;
}

.running-total-value {
  font-weight: 700;
  color: #0f172a;
  font-size: 1.125rem;
}

.running-total-sep {
  color: #94a3b8;
}

.running-total-budget {
  color: #64748b;
}

.place-order-btn {
  padding: 0.75rem 1.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, opacity 0.2s ease;
  white-space: nowrap;
}

.place-order-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-message {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 0.938rem;
}
</style>
