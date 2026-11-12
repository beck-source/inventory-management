<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading && !recommendation" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="recommendation">
      <div class="card budget-card">
        <div class="budget-row">
          <label for="budget-slider" class="budget-label">{{ t('restocking.budget') }}</label>
          <span class="budget-value">{{ money(budget) }}</span>
        </div>
        <input
          id="budget-slider"
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          :max="maxBudget"
          :step="BUDGET_STEP"
          :aria-valuetext="money(budget)"
        />
        <div class="budget-scale">
          <span>{{ money(0) }}</span>
          <span>{{ money(maxBudget) }}</span>
        </div>
        <p class="hint">{{ t('restocking.howItWorks') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ money(recommendation.budget) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ money(recommendation.total_cost) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ money(recommendation.remaining) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.itemsToRestock') }}</div>
          <div class="stat-value">{{ recommendation.items.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
          <button
            class="btn-primary"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="confirmation" class="success-banner">
          {{ t('restocking.orderPlaced', { id: confirmation.id, date: formatDate(confirmation.expected_delivery), days: confirmation.lead_time_days }) }}
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </div>
        <div v-if="submitError" class="error">{{ submitError }}</div>

        <div v-if="!recommendation.items.length" class="empty">{{ t('restocking.noRecommendations') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.demand') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendation.items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td><span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span></td>
                <td>{{ item.current_demand }} → {{ item.forecasted_demand }}</td>
                <td class="num">{{ item.quantity }}</td>
                <td class="num">{{ moneyExact(item.unit_cost) }}</td>
                <td class="num"><strong>{{ moneyExact(item.line_total) }}</strong></td>
                <td class="num">{{ t('orders.leadTimeDays', { days: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_STEP = 500
const DEBOUNCE_MS = 250

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const recommendation = ref(null)
    const budget = ref(0)
    const maxBudget = ref(0)
    const submitting = ref(false)
    const submitError = ref(null)
    const confirmation = ref(null)

    const money = (amount) => formatCurrency(amount, currentCurrency.value)
    const moneyExact = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

    // Dates from the API are date-only ("2026-11-19"); new Date() would read them as UTC
    // midnight and show the previous day west of UTC, so parse them as local dates.
    const formatDate = (dateString) => {
      const d = /^\d{4}-\d{2}-\d{2}$/.test(dateString) ? new Date(`${dateString}T00:00:00`) : new Date(dateString)
      if (isNaN(d.getTime())) return dateString
      return d.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric', month: 'short', day: 'numeric'
      })
    }

    // Each fetch gets a sequence number; only the newest response is applied, so a slow
    // earlier request can never overwrite the plan for the budget currently on the slider.
    let latestRequest = 0
    const loadRecommendations = async () => {
      const requestId = ++latestRequest
      try {
        loading.value = true
        error.value = null
        const result = await api.getRestockRecommendations(budget.value)
        if (requestId !== latestRequest) return
        recommendation.value = result
        maxBudget.value = result.max_budget
      } catch (err) {
        if (requestId === latestRequest) error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        if (requestId === latestRequest) loading.value = false
      }
    }

    // Debounce slider drags so we don't fire a request for every pixel moved.
    // `loading` is set immediately so Place Order is disabled while a fetch is pending.
    let timer = null
    let skipNextWatch = false
    watch(budget, () => {
      confirmation.value = null
      submitError.value = null
      clearTimeout(timer)
      if (skipNextWatch) {
        skipNextWatch = false
        return
      }
      loading.value = true
      timer = setTimeout(loadRecommendations, DEBOUNCE_MS)
    })
    onBeforeUnmount(() => clearTimeout(timer))

    // First load: learn the data-driven maximum, start the slider at half of it (rounded to
    // the slider step) and fetch that plan right away, staying in the loading state throughout
    // so the user never sees a transient "$0 / nothing fits" screen.
    const init = async () => {
      try {
        loading.value = true
        const { max_budget: max } = await api.getRestockRecommendations(0)
        maxBudget.value = max
        const start = Math.round(max / 2 / BUDGET_STEP) * BUDGET_STEP
        // Only skip the watcher if the value actually changes (otherwise it never fires)
        skipNextWatch = start !== budget.value
        budget.value = start
        await loadRecommendations()
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
        loading.value = false
      }
    }

    // Only allow ordering the plan that matches the slider, once, and not mid-request
    const canPlaceOrder = computed(() =>
      !!recommendation.value?.items.length &&
      recommendation.value.budget === budget.value &&
      !loading.value && !submitting.value && !confirmation.value
    )

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      try {
        submitting.value = true
        submitError.value = null
        confirmation.value = await api.createRestockOrder({
          budget: recommendation.value.budget,
          items: recommendation.value.items.map(i => ({ item_sku: i.item_sku, quantity: i.quantity }))
        })
      } catch (err) {
        submitError.value = 'Failed to place order: ' + (err.response?.data?.detail || err.message)
      } finally {
        submitting.value = false
      }
    }

    onMounted(init)

    return {
      t,
      BUDGET_STEP,
      loading,
      error,
      recommendation,
      budget,
      maxBudget,
      submitting,
      submitError,
      confirmation,
      money,
      moneyExact,
      formatDate,
      canPlaceOrder,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-weight: 600;
  color: #0f172a;
}

.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.hint {
  margin: 0.75rem 0 0;
  font-size: 0.85rem;
  color: #64748b;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.btn-primary {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 0.55rem 1.1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

.success-banner {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
}

.success-banner a {
  margin-left: 0.5rem;
  font-weight: 600;
  color: #047857;
}

.empty {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.num {
  text-align: right;
}
</style>
