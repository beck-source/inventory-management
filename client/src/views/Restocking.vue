<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Success banner after an order is placed -->
      <div v-if="placedMessage" class="success-banner">{{ placedMessage }}</div>

      <!-- Budget slider -->
      <div class="card budget-card">
        <div class="budget-head">
          <div class="budget-label">{{ t('restocking.budgetLabel') }}</div>
          <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <input
          class="budget-slider"
          type="range"
          min="0"
          :max="maxBudget"
          :step="sliderStep"
          v-model.number="budget"
        />
        <div class="budget-scale">
          <span>{{ currencySymbol }}0</span>
          <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
        </div>
        <p class="budget-help">{{ t('restocking.budgetHelp') }}</p>
      </div>

      <!-- Summary stats -->
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatMoney(totalCost) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatMoney(remaining) }}</div>
        </div>
      </div>

      <!-- Recommendations -->
      <div class="card">
        <div class="card-header recommend-header">
          <h3 class="card-title">{{ t('restocking.recommended') }}</h3>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || placing"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.gap') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="recommendations.length === 0">
                <td colspan="7" class="empty-row">{{ t('restocking.noRecommendations') }}</td>
              </tr>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td>
                  <strong>{{ rec.sku }}</strong>
                  <div class="item-sub">{{ rec.name }}</div>
                </td>
                <td>
                  <span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span>
                </td>
                <td>{{ rec.gap }}</td>
                <td><strong>{{ rec.quantity }}</strong></td>
                <td>{{ currencySymbol }}{{ rec.unitCost.toFixed(2) }}</td>
                <td><strong>{{ currencySymbol }}{{ formatMoney(rec.lineCost) }}</strong></td>
                <td>{{ t('orders.leadTimeDays', { days: rec.leadTimeDays }) }}</td>
              </tr>
            </tbody>
          </table>
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

    // Match the Orders view convention: symbol only, raw amount (no FX conversion).
    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const budget = ref(0)
    const sliderStep = 100
    const placing = ref(false)
    const placedMessage = ref('')

    // A forecast item is a restock candidate only when forecast demand exceeds
    // current demand (a positive gap). Cost to fully close every gap sets the
    // slider ceiling, so the slider always spans "nothing" to "restock everything".
    const candidates = computed(() =>
      allForecasts.value
        .map(f => ({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          gap: f.forecasted_demand - f.current_demand,
          unitCost: f.unit_cost,
          leadTimeDays: f.lead_time_days
        }))
        .filter(c => c.gap > 0)
    )

    const maxBudget = computed(() => {
      const total = candidates.value.reduce((sum, c) => sum + c.gap * c.unitCost, 0)
      return Math.max(sliderStep, Math.ceil(total))
    })

    // Trend priority: fund rising demand first, then stable, then declining.
    const trendWeight = { increasing: 0, stable: 1, decreasing: 2 }

    // Greedy allocation: walk candidates by priority, buy up to the full gap for
    // each while budget lasts, so an item is never over-ordered beyond its gap.
    const recommendations = computed(() => {
      const sorted = [...candidates.value].sort((a, b) => {
        const w = (trendWeight[a.trend] ?? 1) - (trendWeight[b.trend] ?? 1)
        return w !== 0 ? w : b.gap - a.gap
      })
      let remainingBudget = budget.value
      const picks = []
      for (const c of sorted) {
        const affordable = Math.floor(remainingBudget / c.unitCost)
        const quantity = Math.min(c.gap, affordable)
        if (quantity > 0) {
          const lineCost = quantity * c.unitCost
          picks.push({ ...c, quantity, lineCost })
          remainingBudget -= lineCost
        }
      }
      return picks
    })

    const totalCost = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.lineCost, 0)
    )
    const remaining = computed(() => budget.value - totalCost.value)

    const formatMoney = (n) =>
      n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const loadForecasts = async () => {
      try {
        loading.value = true
        allForecasts.value = await api.getDemandForecasts()
        // Default the budget to ~40% of the full-restock cost as a sensible start.
        budget.value = Math.round((maxBudget.value * 0.4) / sliderStep) * sliderStep
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (recommendations.value.length === 0 || placing.value) return
      try {
        placing.value = true
        placedMessage.value = ''
        const payload = {
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.quantity,
            unit_price: r.unitCost
          })),
          customer: 'Internal Restock'
        }
        const order = await api.createOrder(payload)
        placedMessage.value = t('restocking.orderPlaced', {
          orderNumber: order.order_number,
          date: formatDate(order.expected_delivery)
        })
      } catch (err) {
        error.value = 'Failed to place order: ' + err.message
      } finally {
        placing.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      currencySymbol,
      budget,
      sliderStep,
      maxBudget,
      recommendations,
      totalCost,
      remaining,
      placing,
      placedMessage,
      formatMoney,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 2rem;
}

.budget-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
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
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
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
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}

.budget-help {
  font-size: 0.813rem;
  color: #64748b;
  margin: 0.75rem 0 0;
}

.recommend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.place-order-btn {
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
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

.item-sub {
  font-size: 0.813rem;
  color: #64748b;
  margin-top: 0.125rem;
}

.empty-row {
  text-align: center;
  color: #64748b;
  font-style: italic;
  padding: 1.5rem;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  border-radius: 8px;
  padding: 0.875rem 1.25rem;
  margin-bottom: 1.5rem;
  font-weight: 500;
}
</style>
