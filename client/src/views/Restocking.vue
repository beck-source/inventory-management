<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-if="successMessage" class="success-banner" role="status">{{ successMessage }}</div>

      <div class="card budget-card">
        <div class="budget-header">
          <label for="budget-slider" class="budget-label">{{ t('restocking.budget') }}</label>
          <span class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</span>
        </div>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="sliderMax"
          :step="step"
        />
        <div class="budget-max">{{ t('restocking.budgetMax', { amount: formatCurrency(maxBudget, currentCurrency) }) }}</div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ formatCurrency(result.total_cost, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ formatCurrency(result.remaining_budget, currentCurrency) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: result.lead_time_days }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header recs-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ result.items.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="result.items.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="result.items.length === 0" class="empty-state">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.shortfall') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in result.items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td>{{ item.shortfall }}</td>
                <td><strong>{{ item.quantity }}</strong></td>
                <td>{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                <td><strong>{{ formatCurrencyWithDecimals(item.line_total, currentCurrency, 2) }}</strong></td>
                <td>{{ item.lead_time_days }}</td>
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
import { parseLocalDate } from '../utils/date'

const DEBOUNCE_MS = 250

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const loading = ref(true)
    const submitting = ref(false)
    const error = ref(null)
    const successMessage = ref(null)

    const budget = ref(0)
    const maxBudget = ref(0)
    const result = ref({ items: [], total_cost: 0, remaining_budget: 0, lead_time_days: 0 })

    // Slider granularity scales with the range (~100 steps, rounded to a power of 10)
    const step = computed(() => {
      if (maxBudget.value <= 100) return 1
      return Math.pow(10, Math.floor(Math.log10(maxBudget.value / 100)))
    })

    // The slider max is the full cost rounded UP to a step multiple. Otherwise
    // (e.g. 24143.10 with step 100) the thumb tops out at 24100 and one item is
    // under-ordered. A budget above the full cost is fine: the backend only
    // fills up to the shortfall. maxBudget keeps the real cost for the label.
    const sliderMax = computed(() => Math.ceil(maxBudget.value / step.value) * step.value)

    // Each request gets an id; only the latest one may update state, so slow
    // responses for an older slider position never overwrite newer data.
    let requestSeq = 0
    let debounceTimer = null
    // Set when the budget is changed programmatically so the watcher does not
    // schedule a duplicate fetch.
    let skipNextWatch = false

    const fetchRecommendations = async (amount) => {
      const seq = ++requestSeq
      try {
        const data = await api.getRestockingRecommendations(amount)
        if (seq !== requestSeq) return false
        result.value = data
        maxBudget.value = data.full_restock_cost
        error.value = null
        return true
      } catch (err) {
        if (seq !== requestSeq) return false
        error.value = t('restocking.loadError') + ': ' + err.message
        return false
      }
    }

    const init = async () => {
      // The slider max comes from the API, so probe with 0 first, then load
      // the full-restock view as the default position.
      await fetchRecommendations(0)
      if (sliderMax.value !== budget.value) {
        skipNextWatch = true
        budget.value = sliderMax.value
      }
      await fetchRecommendations(budget.value)
      loading.value = false
    }

    watch(budget, (value) => {
      if (skipNextWatch) {
        skipNextWatch = false
        return
      }
      successMessage.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => fetchRecommendations(value), DEBOUNCE_MS)
    })

    const formatDate = (dateString) => {
      // expected_delivery is a plain 'YYYY-MM-DD'; parse as local to avoid a one-day-early shift
      const date = parseLocalDate(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const placeOrder = async () => {
      if (submitting.value || result.value.items.length === 0) return
      // Cancel any pending slider fetch so the order matches what is displayed
      clearTimeout(debounceTimer)
      submitting.value = true
      error.value = null
      successMessage.value = null
      try {
        const order = await api.createRestockingOrder({
          items: result.value.items.map(i => ({ sku: i.sku, quantity: i.quantity })),
          budget: budget.value
        })
        successMessage.value = t('restocking.orderSuccess', {
          orderNumber: order.order_number,
          date: formatDate(order.expected_delivery)
        })
        await fetchRecommendations(budget.value)
        // Placed orders may shrink the full-restock cost; keep slider in range
        if (budget.value > sliderMax.value) {
          skipNextWatch = true
          budget.value = sliderMax.value
        }
      } catch (err) {
        const detail = err.response && err.response.data && err.response.data.detail
        error.value = t('restocking.orderError') + ': ' + (typeof detail === 'string' ? detail : err.message)
      } finally {
        submitting.value = false
      }
    }

    onMounted(init)
    onBeforeUnmount(() => {
      clearTimeout(debounceTimer)
      requestSeq++ // invalidate in-flight requests
    })

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      loading,
      submitting,
      error,
      successMessage,
      budget,
      maxBudget,
      sliderMax,
      step,
      result,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.budget-header {
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
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-slider:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  border-radius: 4px;
}

.budget-max {
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.success-banner {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
}

.recs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.place-order-btn {
  background: #0f172a;
  color: white;
  border: 1px solid #0f172a;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1e293b;
}

.place-order-btn:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.place-order-btn:disabled {
  background: #e2e8f0;
  border-color: #e2e8f0;
  color: #94a3b8;
  cursor: not-allowed;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}
</style>
