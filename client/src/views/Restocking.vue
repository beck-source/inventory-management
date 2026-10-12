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
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <div class="budget-value">{{ formatCurrency(budget) }}</div>
        </div>
        <div class="budget-controls">
          <input
            type="range"
            min="0"
            max="500000"
            step="5000"
            v-model.number="budget"
            class="budget-slider"
          />
          <input
            type="number"
            min="0"
            max="500000"
            step="5000"
            v-model.number="budget"
            class="budget-number"
          />
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.recommendedCost') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCost) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ formatCurrency(budgetRemaining) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemCount') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ longestLeadTime }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.title') }}</h3>
          <button class="place-order-btn" :disabled="recommendations.length === 0 || justSubmitted" @click="placeOrder">
            {{ t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.item') }}</th>
                <th>{{ t('restocking.sku') }}</th>
                <th>{{ t('restocking.demandGap') }}</th>
                <th>{{ t('restocking.recommendedQty') }}</th>
                <th>{{ t('restocking.unitCost') }}</th>
                <th>{{ t('restocking.lineCost') }}</th>
                <th>{{ t('restocking.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in recommendations" :key="row.sku">
                <td>{{ translateProductName(row.name) }}</td>
                <td>{{ row.sku }}</td>
                <td>{{ row.gap }}</td>
                <td>{{ row.quantity }}</td>
                <td>{{ formatCurrency(row.unit_cost) }}</td>
                <td>{{ formatCurrency(row.line_cost) }}</td>
                <td>{{ row.lead_time_days }}</td>
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
import { useSubmittedOrders } from '../composables/useSubmittedOrders'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()
    const { addSubmittedOrder } = useSubmittedOrders()

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(100000)
    const successMessage = ref('')
    const justSubmitted = ref(false)

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Gap priority, greedy fill: rank items by unmet demand (gap) descending, then
    // walk the list spending the budget. Each item ideally gets its full gap, but
    // if it doesn't fit we take the largest whole quantity the remaining budget can
    // afford (Math.floor) and keep going — a cheaper item further down the list may
    // still fit, so we don't stop at the first item we can't fully cover.
    const recommendations = computed(() => {
      const gapItems = forecasts.value
        .map(f => ({
          sku: f.item_sku,
          name: f.item_name,
          unit_cost: f.unit_cost,
          lead_time_days: f.lead_time_days,
          gap: f.forecasted_demand - f.current_demand
        }))
        // Skip items missing a numeric cost so budget math never yields NaN.
        .filter(item => item.gap > 0 && Number.isFinite(item.unit_cost))
        .sort((a, b) => b.gap - a.gap)

      let remainingBudget = budget.value
      const rows = []

      for (const item of gapItems) {
        let quantity = item.gap
        let lineCost = quantity * item.unit_cost

        if (remainingBudget - lineCost < 0) {
          // Partial fill: take whatever whole units still fit in the budget.
          quantity = Math.floor(remainingBudget / item.unit_cost)
          if (quantity < 1) continue
          lineCost = quantity * item.unit_cost
        }

        remainingBudget -= lineCost
        rows.push({
          sku: item.sku,
          name: item.name,
          gap: item.gap,
          quantity,
          unit_cost: item.unit_cost,
          lead_time_days: item.lead_time_days,
          line_cost: lineCost
        })
      }

      return rows
    })

    const totalCost = computed(() =>
      recommendations.value.reduce((sum, r) => sum + r.line_cost, 0)
    )
    const budgetRemaining = computed(() => budget.value - totalCost.value)
    const longestLeadTime = computed(() =>
      recommendations.value.reduce((max, r) => Math.max(max, r.lead_time_days), 0)
    )

    const formatCurrency = (value) =>
      `${currencySymbol.value}${Math.round(value).toLocaleString()}`

    const placeOrder = () => {
      if (recommendations.value.length === 0) return
      const order = addSubmittedOrder({
        budget: budget.value,
        items: recommendations.value.map(r => ({
          sku: r.sku,
          name: r.name,
          quantity: r.quantity,
          unit_cost: r.unit_cost,
          lead_time_days: r.lead_time_days
        }))
      })
      successMessage.value = t('restocking.orderSubmitted', { orderNumber: order.order_number })
      justSubmitted.value = true
      // Briefly disable the button so a double-click doesn't create duplicate orders.
      setTimeout(() => {
        justSubmitted.value = false
      }, 2000)
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      recommendations,
      totalCost,
      budgetRemaining,
      longestLeadTime,
      formatCurrency,
      placeOrder,
      successMessage,
      justSubmitted,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-slider {
  flex: 1;
}

.budget-number {
  width: 140px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #0f172a;
}

.budget-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #2563eb;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-message {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
