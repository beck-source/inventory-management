<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget control -->
      <div class="card">
        <div class="budget-label">{{ t('restocking.budgetLabel') }}</div>
        <div class="budget-display">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        <input
          type="range"
          v-model.number="budget"
          :min="0"
          :max="maxBudget"
          :step="100"
          class="budget-slider"
        />
        <div class="slider-ends">
          <span>{{ currencySymbol }}0</span>
          <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
        </div>
      </div>

      <!-- Summary -->
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ remaining.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemCount') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noItems') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.item') }}</th>
                <th>{{ t('restocking.sku') }}</th>
                <th>{{ t('restocking.current') }}</th>
                <th>{{ t('restocking.forecasted') }}</th>
                <th>{{ t('restocking.shortfall') }}</th>
                <th>{{ t('restocking.unitCost') }}</th>
                <th>{{ t('restocking.lineCost') }}</th>
                <th>{{ t('restocking.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in recommendations" :key="f.id">
                <td>{{ translateProductName(f.item_name) }}</td>
                <td><strong>{{ f.item_sku }}</strong></td>
                <td>{{ f.current_demand }}</td>
                <td>{{ f.forecasted_demand }}</td>
                <td><strong>{{ f.shortfall }}</strong></td>
                <td>{{ currencySymbol }}{{ f.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ f.lineCost.toLocaleString() }}</strong></td>
                <td>{{ f.lead_time_days }} {{ t('days') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Success banner -->
      <div v-if="placedOrder" class="success-banner">
        <div>{{ t('restocking.orderPlaced') }} {{ placedOrder.order_number }}</div>
        <router-link to="/orders">{{ t('restocking.viewInOrders') }}</router-link>
      </div>

      <!-- Place order -->
      <button
        class="place-order-btn"
        :disabled="recommendations.length === 0 || submitting"
        @click="placeOrder"
      >
        {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
      </button>
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
    const { t, currentCurrency, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(0)
    const submitting = ref(false)
    const placedOrder = ref(null)

    // Maximum budget = total cost to fully cover every item's shortfall,
    // rounded up to the nearest 1000 so the slider has a clean upper bound.
    const maxBudget = computed(() => {
      if (forecasts.value.length === 0) return 0
      const total = forecasts.value.reduce((sum, f) => {
        const shortfall = Math.max(0, f.forecasted_demand - f.current_demand)
        return sum + shortfall * f.unit_cost
      }, 0)
      return Math.ceil(total / 1000) * 1000
    })

    // Greedy, priority-first budget allocation:
    //  1. Only items with a positive shortfall (forecasted > current) are candidates.
    //  2. Candidates are prioritized by largest shortfall first (most urgent to restock).
    //  3. Walk the prioritized list keeping a running total; include a candidate only if
    //     adding its full line cost still fits within the budget. If it doesn't fit, skip it
    //     and continue — a cheaper later item may still fit (first-fit by priority).
    const recommendations = computed(() => {
      const candidates = forecasts.value
        .filter(f => f.forecasted_demand - f.current_demand > 0)
        .map(f => {
          const shortfall = f.forecasted_demand - f.current_demand
          return { ...f, shortfall, lineCost: shortfall * f.unit_cost }
        })
        .sort((a, b) => b.shortfall - a.shortfall)

      const included = []
      let runningTotal = 0
      for (const c of candidates) {
        if (runningTotal + c.lineCost <= budget.value) {
          included.push(c)
          runningTotal += c.lineCost
        }
      }
      return included
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, f) => sum + f.lineCost, 0)
    })

    const remaining = computed(() => budget.value - totalCost.value)

    const placeOrder = async () => {
      try {
        submitting.value = true
        error.value = null
        const payload = {
          items: recommendations.value.map(f => ({
            sku: f.item_sku,
            name: f.item_name,
            quantity: f.shortfall,
            unit_price: f.unit_cost
          })),
          total_value: totalCost.value,
          // Use the longest lead time across all line items: the order can only be
          // considered fully fulfilled once its slowest-arriving item has landed.
          lead_time_days: Math.max(...recommendations.value.map(f => f.lead_time_days))
        }
        const order = await api.createOrder(payload)
        placedOrder.value = order
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(async () => {
      try {
        loading.value = true
        forecasts.value = await api.getDemandForecasts()
        // Default the budget to half of the maximum so recommendations are populated on load.
        budget.value = Math.round(maxBudget.value / 2)
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    })

    return {
      t,
      currencySymbol,
      translateProductName,
      loading,
      error,
      forecasts,
      budget,
      maxBudget,
      recommendations,
      totalCost,
      remaining,
      submitting,
      placedOrder,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  display: flex;
  flex-direction: column;
}

.budget-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.5rem;
}

.budget-display {
  font-size: 2.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 1rem;
}

.budget-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 999px;
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

.slider-ends {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.place-order-btn {
  align-self: flex-start;
  background: #2563eb;
  color: #fff;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.success-banner {
  background: #f0fdf4;
  border-left: 4px solid #16a34a;
  color: #166534;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.938rem;
  font-weight: 500;
}

.success-banner a {
  color: #16a34a;
  font-weight: 600;
  text-decoration: underline;
  width: fit-content;
}
</style>
