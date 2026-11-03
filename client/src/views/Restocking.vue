<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
      <p class="filters-notice">{{ t('restocking.filtersNotice') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-header">
        <label class="budget-label" for="restocking-budget">{{ t('restocking.budgetLabel') }}</label>
        <div class="budget-value">{{ formatMoney(budget) }}</div>
      </div>
      <input
        id="restocking-budget"
        v-model.number="budget"
        class="budget-slider"
        type="range"
        :min="BUDGET_MIN"
        :max="BUDGET_MAX"
        :step="BUDGET_STEP"
        :style="{ '--fill': sliderFill }"
        :aria-label="t('restocking.budgetLabel')"
      />
      <div class="budget-scale">
        <span>{{ formatMoney(BUDGET_MIN) }}</span>
        <span>{{ formatMoney(BUDGET_MAX) }}</span>
      </div>
      <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card info">
        <div class="stat-label">{{ t('restocking.stats.budget') }}</div>
        <div class="stat-value">{{ formatMoney(budget) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.stats.recommendedSpend') }}</div>
        <div class="stat-value">{{ formatMoney(totalCost) }}</div>
      </div>
      <div class="stat-card success">
        <div class="stat-label">{{ t('restocking.stats.remainingBudget') }}</div>
        <div class="stat-value">{{ formatMoney(remainingBudget) }}</div>
      </div>
    </div>

    <div v-if="orderSuccess" class="success-banner" role="status">
      <span>{{ t('restocking.orderSuccess', { orderNumber: orderSuccess.order_number, days: orderSuccess.lead_time_days }) }}</span>
      <router-link to="/orders" class="success-link">{{ t('restocking.viewInOrders') }}</router-link>
    </div>
    <div v-if="orderError" class="error" role="alert">{{ orderError }}</div>

    <div v-if="loading && !hasData" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="card" :class="{ refreshing: loading || pending }">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ items.length }})</h3>
        <button
          type="button"
          class="btn-primary"
          :disabled="!canPlaceOrder"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="items.length === 0" class="empty-state">
        {{ t('restocking.noRecommendations') }}
      </div>
      <div v-else class="table-container">
        <table>
          <thead>
            <tr>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.name') }}</th>
              <th>{{ t('restocking.table.category') }}</th>
              <th>{{ t('restocking.table.warehouse') }}</th>
              <th class="num">{{ t('restocking.table.onHand') }}</th>
              <th class="num">{{ t('restocking.table.reorderPoint') }}</th>
              <th class="num">{{ t('restocking.table.forecastedDemand') }}</th>
              <th class="num">{{ t('restocking.table.recommendedQty') }}</th>
              <th class="num">{{ t('restocking.table.unitCost') }}</th>
              <th class="num">{{ t('restocking.table.lineTotal') }}</th>
              <th>{{ t('restocking.table.leadTime') }}</th>
              <th>{{ t('restocking.table.reason') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.sku">
              <td><strong>{{ item.sku }}</strong></td>
              <td>{{ translateProductName(item.name) }}</td>
              <td>{{ translateCategory(item.category) }}</td>
              <td>{{ translateWarehouse(item.warehouse) }}</td>
              <td class="num">{{ item.quantity_on_hand.toLocaleString() }}</td>
              <td class="num">{{ item.reorder_point.toLocaleString() }}</td>
              <td class="num">{{ item.forecasted_demand.toLocaleString() }}</td>
              <td class="num"><strong>{{ item.recommended_quantity.toLocaleString() }}</strong></td>
              <td class="num">{{ formatMoneyWithDecimals(item.unit_cost) }}</td>
              <td class="num"><strong>{{ formatMoney(item.line_total) }}</strong></td>
              <td>{{ t('restocking.leadDays', { count: item.lead_time_days }) }}</td>
              <td>
                <span :class="['badge', isBelowReorder(item) ? 'danger' : 'info']">
                  {{ isBelowReorder(item) ? t('restocking.badge.belowReorder') : t('restocking.badge.forecastDemand') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil, formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_MIN = 0
const BUDGET_MAX = 500000
const BUDGET_STEP = 5000
const DEBOUNCE_MS = 250

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    // Slider value is always in USD; only display is converted
    const budget = ref(100000)

    // Raw API response
    const recommendations = ref(null)
    const loading = ref(true)
    const error = ref(null)
    const pending = ref(false)

    // Order submission state
    const submitting = ref(false)
    const orderSuccess = ref(null)
    const orderError = ref(null)

    let debounceTimer = null
    let requestId = 0

    const items = computed(() => recommendations.value?.items ?? [])
    const hasData = computed(() => recommendations.value !== null)
    const totalCost = computed(() => recommendations.value?.total_cost ?? 0)
    const remainingBudget = computed(() => recommendations.value?.remaining_budget ?? budget.value)

    const sliderFill = computed(() => {
      const pct = ((budget.value - BUDGET_MIN) / (BUDGET_MAX - BUDGET_MIN)) * 100
      return `${Math.min(100, Math.max(0, pct))}%`
    })

    const canPlaceOrder = computed(() =>
      items.value.length > 0 && !submitting.value && !loading.value && !pending.value
    )

    const formatMoney = (value) => formatCurrencyUtil(value, currentCurrency.value)
    const formatMoneyWithDecimals = (value) => formatCurrencyWithDecimals(value, currentCurrency.value, 2)

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    const isBelowReorder = (item) => item.quantity_on_hand <= item.reorder_point

    // Latest request wins: stale responses are ignored
    const loadRecommendations = async () => {
      const currentRequest = ++requestId
      loading.value = true
      error.value = null
      try {
        const data = await api.getRestockingRecommendations(budget.value)
        if (currentRequest !== requestId) return
        recommendations.value = data
      } catch (err) {
        if (currentRequest !== requestId) return
        recommendations.value = null
        error.value = t('restocking.loadError')
        console.error('Failed to load restocking recommendations:', err)
      } finally {
        if (currentRequest === requestId) {
          loading.value = false
        }
      }
    }

    watch(budget, () => {
      pending.value = true
      orderSuccess.value = null
      orderError.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        pending.value = false
        loadRecommendations()
      }, DEBOUNCE_MS)
    })

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      submitting.value = true
      orderSuccess.value = null
      orderError.value = null
      try {
        const payload = {
          // Use the budget the recommendations were computed for
          budget: recommendations.value.budget,
          items: items.value.map(item => ({
            sku: item.sku,
            quantity: item.recommended_quantity
          }))
        }
        orderSuccess.value = await api.createRestockingOrder(payload)
        await loadRecommendations()
      } catch (err) {
        orderError.value = err.response?.data?.detail || t('restocking.orderError')
        console.error('Failed to place restocking order:', err)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    onBeforeUnmount(() => {
      clearTimeout(debounceTimer)
      requestId++
    })

    return {
      t,
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      budget,
      items,
      hasData,
      totalCost,
      remainingBudget,
      sliderFill,
      loading,
      pending,
      error,
      submitting,
      orderSuccess,
      orderError,
      canPlaceOrder,
      formatMoney,
      formatMoneyWithDecimals,
      translateProductName,
      translateWarehouse,
      translateCategory,
      isBelowReorder,
      placeOrder
    }
  }
}
</script>

<style scoped>
.filters-notice {
  margin-top: 0.25rem;
  font-size: 0.813rem;
}

/* Budget slider card */
.budget-card {
  padding: var(--space-5);
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
}

.budget-label {
  color: var(--text-muted);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.budget-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: -0.025em;
}

.budget-slider {
  --fill: 0%;
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 20px;
  background: transparent;
  cursor: pointer;
}

.budget-slider:focus {
  outline: none;
}

/* WebKit track */
.budget-slider::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 3px;
  background: linear-gradient(to right, var(--accent) 0%, var(--accent) var(--fill), var(--border) var(--fill), var(--border) 100%);
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  margin-top: -7px;
  border-radius: 50%;
  background: var(--bg-surface);
  border: 2px solid var(--accent);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.2);
  transition: box-shadow 0.15s ease;
}

.budget-slider:hover::-webkit-slider-thumb {
  box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.12);
}

.budget-slider:focus-visible::-webkit-slider-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.3);
}

/* Firefox track */
.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 3px;
  background: var(--border);
}

.budget-slider::-moz-range-progress {
  height: 6px;
  border-radius: 3px;
  background: var(--accent);
}

.budget-slider::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--bg-surface);
  border: 2px solid var(--accent);
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.2);
}

.budget-slider:hover::-moz-range-thumb {
  box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.12);
}

.budget-slider:focus-visible::-moz-range-thumb {
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.3);
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.375rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.budget-hint {
  margin-top: 0.75rem;
  font-size: 0.813rem;
  color: var(--text-muted);
}

/* Primary button */
.btn-primary {
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}

.btn-primary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-primary:disabled {
  background: var(--border);
  border-color: var(--border);
  color: #94a3b8;
  cursor: not-allowed;
}

/* Success banner */
.success-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: var(--radius-md);
  margin: 0 0 var(--space-5);
  font-size: 0.938rem;
}

.success-link {
  color: var(--accent);
  font-weight: 600;
  text-decoration: none;
}

.success-link:hover {
  text-decoration: underline;
}

/* Table */
th.num,
td.num {
  text-align: right;
  white-space: nowrap;
}

.refreshing .table-container {
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.empty-state {
  text-align: center;
  padding: 2.5rem 1rem;
  color: var(--text-muted);
  font-size: 0.938rem;
}
</style>
