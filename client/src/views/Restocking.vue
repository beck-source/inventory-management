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
          <h3 class="card-title">{{ t('restocking.budget.title') }}</h3>
          <span class="budget-value">{{ formatMoney(budget) }}</span>
        </div>
        <label for="restock-budget" class="budget-help">{{ t('restocking.budget.help') }}</label>
        <input
          id="restock-budget"
          v-model.number="budget"
          type="range"
          class="budget-slider"
          :min="MIN_BUDGET"
          :max="maxBudget"
          :step="BUDGET_STEP"
          :aria-valuetext="formatMoney(budget)"
        />
        <div class="budget-range">
          <span>{{ formatMoney(MIN_BUDGET) }}</span>
          <span>{{ t('restocking.budget.fullRestock', { amount: formatMoney(fullRestockCost) }) }}</span>
          <span>{{ formatMoney(maxBudget) }}</span>
        </div>
      </div>

      <div v-if="refreshError" class="error">{{ refreshError }}</div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
          <div class="stat-value">{{ formatMoney(summaryBudget) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.orderTotal') }}</div>
          <div class="stat-value">{{ formatMoney(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.remainingBudget') }}</div>
          <div class="stat-value">{{ formatMoney(remainingBudget) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.summary.itemCount') }}</div>
          <div class="stat-value">{{ items.length }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.recommendations') }}
            <span v-if="refreshing" class="updating">{{ t('restocking.updating') }}</span>
          </h3>
          <button
            type="button"
            class="btn-primary"
            :disabled="!canSubmit"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="lastOrder" class="order-success" role="status">
          <div>
            {{ t('restocking.orderSuccess', {
              orderNumber: lastOrder.order_number,
              date: formatDate(lastOrder.expected_delivery)
            }) }}
          </div>
          <router-link to="/orders" class="success-link">{{ t('restocking.viewOrders') }}</router-link>
        </div>
        <div v-if="submitError" class="error" role="alert">{{ submitError }}</div>

        <div v-if="items.length === 0" class="empty-state">
          {{ t('restocking.empty') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.forecast') }}</th>
                <th class="num">{{ t('restocking.table.onHand') }}</th>
                <th class="num">{{ t('restocking.table.recommendedQty') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="num">{{ item.forecasted_demand.toLocaleString() }}</td>
                <td class="num">{{ item.quantity_on_hand.toLocaleString() }}</td>
                <td class="num">
                  <strong>{{ item.recommended_quantity.toLocaleString() }}</strong>
                  <span
                    v-if="item.partial"
                    class="badge warning partial-badge"
                    :title="t('restocking.partialHint', { shortfall: item.shortfall.toLocaleString() })"
                  >{{ t('restocking.partial') }}</span>
                </td>
                <td class="num">{{ formatMoneyPrecise(item.unit_cost) }}</td>
                <td class="num"><strong>{{ formatMoney(item.line_total) }}</strong></td>
                <td class="num">{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
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

const MIN_BUDGET = 1000
const BUDGET_STEP = 1000
const DEFAULT_BUDGET = 25000
const MAX_ROUNDING = 10000
const PROBE_BUDGET = 1000000
const DEBOUNCE_MS = 300

export default {
  name: 'Restocking',
  setup() {
    const { t, currentLocale, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const refreshing = ref(false)
    const refreshError = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const lastOrder = ref(null)

    const budget = ref(DEFAULT_BUDGET)
    const maxBudget = ref(DEFAULT_BUDGET)
    const fullRestockCost = ref(0)
    const recommendation = ref(null)

    let debounceTimer = null
    let requestId = 0

    const items = computed(() => recommendation.value?.items || [])
    const summaryBudget = computed(() => recommendation.value?.budget ?? budget.value)
    const totalCost = computed(() => recommendation.value?.total_cost ?? 0)
    const remainingBudget = computed(() => recommendation.value?.remaining_budget ?? budget.value)

    // Recommendations are stale while a debounced refresh is pending or in flight
    const canSubmit = computed(() =>
      items.value.length > 0 && !submitting.value && !refreshing.value
    )

    const formatMoney = (amount) => formatCurrency(Number(amount) || 0, currentCurrency.value)
    const formatMoneyPrecise = (amount) =>
      formatCurrencyWithDecimals(Number(amount) || 0, currentCurrency.value, 2)

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (!dateString || isNaN(date.getTime())) return '-'
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const getErrorDetail = (err, fallbackKey) => {
      const detail = err?.response?.data?.detail
      return typeof detail === 'string' && detail ? detail : t(fallbackKey)
    }

    const fetchRecommendations = async () => {
      const id = ++requestId
      refreshing.value = true
      refreshError.value = null
      try {
        const data = await api.getRestockingRecommendations(budget.value)
        if (id !== requestId) return
        recommendation.value = data
        fullRestockCost.value = data.full_restock_cost || 0
      } catch (err) {
        if (id !== requestId) return
        console.error('Failed to load restocking recommendations:', err)
        refreshError.value = getErrorDetail(err, 'restocking.errors.loadRecommendations')
      } finally {
        if (id === requestId) refreshing.value = false
      }
    }

    const init = async () => {
      loading.value = true
      error.value = null
      try {
        // Probe with a large budget to learn the full restock cost for the slider range
        const probe = await api.getRestockingRecommendations(PROBE_BUDGET)
        fullRestockCost.value = probe.full_restock_cost || 0
        maxBudget.value = Math.max(
          Math.ceil(fullRestockCost.value / MAX_ROUNDING) * MAX_ROUNDING,
          MAX_ROUNDING
        )
        budget.value = Math.min(DEFAULT_BUDGET, maxBudget.value)
        recommendation.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        console.error('Failed to initialize restocking view:', err)
        error.value = getErrorDetail(err, 'restocking.errors.loadRecommendations')
      } finally {
        loading.value = false
      }
    }

    watch(budget, (newBudget, oldBudget) => {
      if (loading.value || newBudget === oldBudget) return
      submitError.value = null
      refreshing.value = true
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(fetchRecommendations, DEBOUNCE_MS)
    })

    const placeOrder = async () => {
      if (!canSubmit.value) return
      submitting.value = true
      submitError.value = null
      lastOrder.value = null
      try {
        lastOrder.value = await api.createRestockingOrder({
          budget: recommendation.value.budget,
          items: items.value.map(item => ({
            item_sku: item.item_sku,
            quantity: item.recommended_quantity
          }))
        })
      } catch (err) {
        console.error('Failed to place restocking order:', err)
        submitError.value = getErrorDetail(err, 'restocking.errors.placeOrder')
      } finally {
        submitting.value = false
      }
      // Ordered quantities now count as on order, so refresh to show only what is still short
      if (lastOrder.value) fetchRecommendations()
    }

    onMounted(init)
    onBeforeUnmount(() => clearTimeout(debounceTimer))

    return {
      t,
      MIN_BUDGET,
      BUDGET_STEP,
      loading,
      error,
      refreshing,
      refreshError,
      submitting,
      submitError,
      lastOrder,
      budget,
      maxBudget,
      fullRestockCost,
      items,
      summaryBudget,
      totalCost,
      remainingBudget,
      canSubmit,
      formatMoney,
      formatMoneyPrecise,
      formatDate,
      placeOrder,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-card .card-header {
  margin-bottom: 0.75rem;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  letter-spacing: -0.025em;
}

.budget-help {
  display: block;
  color: #64748b;
  font-size: 0.875rem;
  margin-bottom: 0.75rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-range {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 0.5rem;
  color: #64748b;
  font-size: 0.813rem;
}

.updating {
  margin-left: 0.5rem;
  font-size: 0.813rem;
  font-weight: 500;
  color: #64748b;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.order-success {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.938rem;
}

.success-link {
  color: #047857;
  font-weight: 600;
  white-space: nowrap;
}

.success-link:hover {
  color: #065f46;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.num {
  text-align: right;
  white-space: nowrap;
}

.partial-badge {
  margin-left: 0.5rem;
  padding: 0.125rem 0.5rem;
  cursor: help;
}
</style>
