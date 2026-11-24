<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="confirmation" class="banner banner-success" role="status">
        <span>{{ t('restocking.success', { orderNumber: confirmation.order_number }) }}</span>
        <router-link to="/orders" class="banner-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="submitError" class="banner banner-error" role="alert">{{ submitError }}</div>

      <div class="card budget-card">
        <label class="budget-label" for="budget-slider">
          <span>{{ t('restocking.budget') }}</span>
          <strong class="budget-value">{{ formatMoney(budget, 0) }}</strong>
        </label>
        <input
          id="budget-slider"
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          max="100000"
          step="1000"
        />
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatMoney(budget, 0) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.allocated') }}</div>
          <div class="stat-value">{{ formatMoney(allocated) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatMoney(remaining) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ longestLeadTime }} {{ t('restocking.days') }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendationsTitle') }} ({{ recommendations.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting || !!confirmation"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">{{ t('restocking.noRecommendations') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.gap') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ translateProductName(rec.name) }}</td>
                <td>
                  <span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span>
                </td>
                <td>{{ rec.gap }}</td>
                <td><strong>{{ rec.quantity }}</strong></td>
                <td>{{ formatMoney(rec.unit_cost) }}</td>
                <td><strong>{{ formatMoney(rec.line_total) }}</strong></td>
                <td>{{ rec.lead_time_days }}</td>
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
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(25000)
    const submitting = ref(false)
    const submitError = ref(null)
    const confirmation = ref(null)

    // A changed budget means a new recommendation set, so the banner for the
    // previous order would be stale and misleading.
    watch(budget, () => {
      confirmation.value = null
      submitError.value = null
    })

    // Amounts are USD from the API; the formatter converts for the JPY locale.
    const formatMoney = (amount, decimals = 2) =>
      formatCurrencyWithDecimals(amount, currentCurrency.value, decimals)

    // Greedy budget allocation:
    // 1. Only items whose forecast exceeds current demand need stock (gap > 0).
    // 2. Rank by relative growth (gap / current demand) so fast-growing items are funded
    //    first, regardless of absolute volume.
    // 3. Walk the ranking, buying min(gap, what the remaining budget affords). A partial
    //    fill does not stop the walk: the leftover may still fit cheaper items later.
    // Money is tracked in integer cents so repeated float subtraction cannot drift
    // (e.g. leaving 0.0000001 that wrongly affords or blocks a unit).
    const recommendations = computed(() => {
      const candidates = forecasts.value
        .map(f => ({ ...f, gap: f.forecasted_demand - f.current_demand }))
        .filter(f => f.gap > 0 && f.unit_cost > 0)
        // current_demand of 0 means unbounded growth; rank it first and avoid divide-by-zero
        .map(f => ({ ...f, growth: f.current_demand > 0 ? f.gap / f.current_demand : Infinity }))
        .sort((a, b) => b.growth - a.growth)

      let remainingCents = Math.round(budget.value * 100)
      const result = []

      for (const f of candidates) {
        const unitCents = Math.round(f.unit_cost * 100)
        const quantity = Math.min(f.gap, Math.floor(remainingCents / unitCents))
        if (quantity <= 0) continue

        const lineCents = quantity * unitCents
        remainingCents -= lineCents
        result.push({
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          gap: f.gap,
          quantity,
          unit_cost: f.unit_cost,
          line_total: lineCents / 100,
          lead_time_days: f.lead_time_days
        })
      }
      return result
    })

    const allocated = computed(() =>
      Math.round(recommendations.value.reduce((sum, r) => sum + Math.round(r.line_total * 100), 0)) / 100
    )
    const remaining = computed(() => Math.round(budget.value * 100 - allocated.value * 100) / 100)
    const longestLeadTime = computed(() =>
      recommendations.value.reduce((max, r) => Math.max(max, r.lead_time_days), 0)
    )

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

    const placeOrder = async () => {
      // Block repeat submits of the same recommendation set; changing the budget clears confirmation.
      if (recommendations.value.length === 0 || submitting.value || confirmation.value) return
      submitting.value = true
      submitError.value = null
      confirmation.value = null
      try {
        confirmation.value = await api.createRestockOrder({
          budget: budget.value,
          items: recommendations.value.map(r => ({ sku: r.sku, quantity: r.quantity }))
        })
      } catch (err) {
        // 400s carry a string detail; 422 validation errors carry an array of
        // objects, which would render as "[object Object]", so fall back for those.
        const detail = err.response?.data?.detail
        submitError.value = typeof detail === 'string' ? detail : t('restocking.error')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      recommendations,
      allocated,
      remaining,
      longestLeadTime,
      submitting,
      submitError,
      confirmation,
      formatMoney,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.budget-label {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-value {
  font-size: 1.5rem;
  color: #0f172a;
  text-transform: none;
  letter-spacing: normal;
}

.budget-slider {
  width: 100%;
  accent-color: #0f172a;
  cursor: pointer;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  padding: 0.875rem 1.25rem;
  margin-bottom: 1.5rem;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
}

.banner-success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.banner-error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.banner-link {
  color: inherit;
  font-weight: 600;
  text-decoration: underline;
}

.empty-state {
  padding: 2rem;
  color: #64748b;
  text-align: center;
}
</style>
