<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="placedOrder" class="confirmation">
        <div>
          <div class="confirmation-title">
            {{ t('restocking.orderPlaced', { orderNumber: placedOrder.order_number }) }}
          </div>
          <div class="confirmation-detail">
            {{ t('restocking.orderPlacedDetail', {
              total: formatCurrency(placedOrder.total_value, currentCurrency),
              date: formatDate(placedOrder.estimated_delivery)
            }) }}
          </div>
        </div>
        <router-link to="/orders" class="confirmation-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <div class="budget-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="budgetMax"
          :step="BUDGET_STEP"
          :disabled="candidates.length === 0"
          :aria-label="t('restocking.budget')"
        />
        <div class="budget-scale">
          <span>{{ formatCurrency(0, currentCurrency) }}</span>
          <span>{{ formatCurrency(budgetMax, currentCurrency) }}</span>
        </div>
        <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.itemsSelected') }}</div>
          <div class="stat-value">{{ selected.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCost, currentCurrency) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.budgetRemaining') }}</div>
          <div class="stat-value">{{ formatCurrency(budgetRemaining, currentCurrency) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.leadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: orderLeadTime }) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ selected.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="selected.length === 0 || submitting || justPlaced"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>
        <div v-if="submitError" class="error">{{ submitError }}</div>
        <div v-if="candidates.length === 0" class="empty-state">{{ t('restocking.noCandidates') }}</div>
        <div v-else-if="selected.length === 0" class="empty-state">{{ t('restocking.noneSelected') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selected" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="num">{{ item.qty.toLocaleString() }}</td>
                <td class="num">{{ formatCurrencyWithDecimals(item.unitCost, currentCurrency, 2) }}</td>
                <td class="num"><strong>{{ formatCurrency(item.lineCost, currentCurrency) }}</strong></td>
                <td class="num">{{ t('restocking.days', { count: item.leadTimeDays }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="notRecommended.length > 0" class="card muted-card">
        <div class="card-header">
          <h3 class="card-title muted-title">{{ t('restocking.notRecommended') }} ({{ notRecommended.length }})</h3>
        </div>
        <ul class="not-recommended-list">
          <li v-for="item in notRecommended" :key="item.sku" class="not-recommended-item">
            <span class="nr-sku">{{ item.sku }}</span>
            <span class="nr-name">{{ translateProductName(item.name) }}</span>
            <span class="nr-reason">{{ t(`restocking.reasons.${item.reason}`) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const BUDGET_STEP = 500
const BUDGET_ROUND = 5000

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const inventoryItems = ref([])

    // Budget is always held in USD; formatCurrency converts for display only
    const budget = ref(0)

    const submitting = ref(false)
    const submitError = ref(null)
    const placedOrder = ref(null)
    // True right after a successful submit; blocks re-submitting the same selection
    const justPlaced = ref(false)

    // Total on-hand stock per SKU, summed across all warehouses
    const onHandBySku = computed(() => {
      const map = new Map()
      for (const item of inventoryItems.value) {
        map.set(item.sku, (map.get(item.sku) || 0) + (Number(item.quantity_on_hand) || 0))
      }
      return map
    })

    // Every forecast evaluated once: either a restock candidate or excluded with a reason
    const evaluated = computed(() => {
      return forecasts.value.map(f => {
        const onHand = onHandBySku.value.get(f.item_sku) || 0
        const shortfall = Math.max(0, f.forecasted_demand - onHand)
        // Guard against divide-by-zero when current demand is 0
        const growth = f.current_demand > 0
          ? (f.forecasted_demand - f.current_demand) / f.current_demand * 100
          : 0
        const unitCost = Number(f.unit_cost) || 0
        let reason = null
        if (f.trend === 'decreasing') reason = 'decreasing'
        else if (shortfall === 0) reason = 'sufficient'
        return {
          sku: f.item_sku,
          name: f.item_name,
          trend: f.trend,
          growth,
          qty: shortfall,
          unitCost,
          // Rounded to cents per line so the client total matches the server's per-line rounding
          lineCost: Math.round(shortfall * unitCost * 100) / 100,
          leadTimeDays: Number(f.lead_time_days) || 0,
          reason
        }
      })
    })

    // Ranking: increasing trend first, then highest growth %, then cheapest line as tiebreak
    const candidates = computed(() => {
      return evaluated.value
        .filter(c => c.reason === null)
        .sort((a, b) => {
          const aInc = a.trend === 'increasing' ? 0 : 1
          const bInc = b.trend === 'increasing' ? 0 : 1
          if (aInc !== bInc) return aInc - bInc
          if (b.growth !== a.growth) return b.growth - a.growth
          return a.lineCost - b.lineCost
        })
    })

    // Slider max: total cost of every candidate, rounded UP to the next 5,000 (never below 5,000).
    // With no candidates there is nothing to buy, so the max is 0 and the slider is disabled.
    const budgetMax = computed(() => {
      if (candidates.value.length === 0) return 0
      const total = candidates.value.reduce((sum, c) => sum + c.lineCost, 0)
      return Math.max(BUDGET_ROUND, Math.ceil(total / BUDGET_ROUND) * BUDGET_ROUND)
    })

    // Greedy whole-item fill: an item that doesn't fit is skipped (not split), and scanning
    // continues so cheaper lower-ranked items can still use the remaining budget.
    const allocation = computed(() => {
      let remaining = budget.value
      const picked = []
      const skipped = []
      for (const c of candidates.value) {
        if (c.lineCost <= remaining) {
          picked.push(c)
          remaining -= c.lineCost
        } else {
          skipped.push({ ...c, reason: 'overBudget' })
        }
      }
      return { picked, skipped }
    })

    const selected = computed(() => allocation.value.picked)

    const notRecommended = computed(() => [
      ...allocation.value.skipped,
      ...evaluated.value.filter(c => c.reason !== null)
    ])

    const totalCost = computed(() => selected.value.reduce((sum, i) => sum + i.lineCost, 0))
    const budgetRemaining = computed(() => Math.max(0, budget.value - totalCost.value))
    // The order arrives when its slowest line arrives
    const orderLeadTime = computed(() =>
      selected.value.reduce((max, i) => Math.max(max, i.leadTimeDays), 0)
    )

    const loadData = async () => {
      try {
        loading.value = true
        error.value = null
        // Inventory loaded unfiltered: restocking plans against total stock, not the filter bar
        const [forecastData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        forecasts.value = forecastData
        inventoryItems.value = inventoryData
        // Default budget is set once, after data loads, to ~50% of max snapped to the slider step
        // (budgetMax is 0 when there are no candidates, giving a default of 0)
        budget.value = Math.round((budgetMax.value * 0.5) / BUDGET_STEP) * BUDGET_STEP
      } catch (err) {
        error.value = t('restocking.loadError') + ': ' + err.message
        console.error('Restocking load error:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (selected.value.length === 0 || submitting.value || justPlaced.value) return
      try {
        submitting.value = true
        submitError.value = null
        placedOrder.value = null
        // Only SKU and quantity are sent; the server prices the order itself
        placedOrder.value = await api.createRestockingOrder({
          items: selected.value.map(i => ({ sku: i.sku, quantity: i.qty }))
        })
        justPlaced.value = true
      } catch (err) {
        const detail = err.response?.data?.detail
        submitError.value = t('restocking.submitError') +
          (typeof detail === 'string' ? ': ' + detail : err.message ? ': ' + err.message : '')
        console.error('Restocking submit error:', err)
      } finally {
        submitting.value = false
      }
    }

    // The server has no idempotency, so after a successful submit Place Order stays disabled
    // until the budget changes (a new selection). Changing the budget also clears the
    // confirmation banner, which would otherwise describe a selection no longer on screen.
    watch(budget, () => {
      justPlaced.value = false
      placedOrder.value = null
    })

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString || ''
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    onMounted(loadData)

    return {
      t,
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      formatDate,
      BUDGET_STEP,
      loading,
      error,
      budget,
      budgetMax,
      candidates,
      selected,
      notRecommended,
      totalCost,
      budgetRemaining,
      orderLeadTime,
      submitting,
      submitError,
      placedOrder,
      justPlaced,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.budget-hint {
  margin-top: 0.75rem;
  font-size: 0.813rem;
  color: #64748b;
}

.num {
  text-align: right;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
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

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.875rem;
}

.confirmation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
}

.confirmation-title {
  font-weight: 700;
  color: #065f46;
}

.confirmation-detail {
  font-size: 0.875rem;
  color: #047857;
  margin-top: 0.25rem;
}

.confirmation-link {
  color: #065f46;
  font-weight: 600;
  font-size: 0.875rem;
  white-space: nowrap;
}

.muted-card {
  background: #f8fafc;
}

.muted-title {
  color: #64748b;
}

.not-recommended-list {
  list-style: none;
}

.not-recommended-item {
  display: grid;
  grid-template-columns: 120px 1fr auto;
  gap: 1rem;
  padding: 0.5rem 0.75rem;
  border-top: 1px solid #e2e8f0;
  font-size: 0.875rem;
  color: #64748b;
}

.not-recommended-item:first-child {
  border-top: none;
}

.nr-sku {
  font-weight: 600;
}

.nr-reason {
  font-style: italic;
}
</style>
