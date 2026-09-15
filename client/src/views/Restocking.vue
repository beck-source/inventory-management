<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budgetTitle') }}</h3>
        <span class="budget-amount">{{ formatCurrency(budget) }}</span>
      </div>

      <div class="budget-control">
        <input
          id="restock-budget"
          v-model.number="budget"
          type="range"
          class="budget-slider"
          :min="BUDGET_MIN"
          :max="BUDGET_MAX"
          :step="BUDGET_STEP"
          :aria-label="t('restocking.budgetTitle')"
        />
        <div class="budget-scale">
          <span>{{ formatCurrency(BUDGET_MIN) }}</span>
          <span>{{ formatCurrency(BUDGET_MAX) }}</span>
        </div>
        <p class="budget-help">
          {{ t('restocking.fullCoverage', { amount: formatCurrency(plan ? plan.full_coverage_cost : 0) }) }}
        </p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="plan">
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.recommendedItems') }}</div>
          <div class="stat-value">{{ plan.item_count }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.recommendedUnits') }}</div>
          <div class="stat-value">{{ plan.total_units.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ formatCurrency(plan.total_cost) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: plan.lead_time_days }) }}</div>
        </div>
      </div>

      <div v-if="submitted" class="submit-banner">
        <div class="submit-banner-text">
          <strong>{{ t('restocking.orderPlaced', { orderNumber: submitted.order_number }) }}</strong>
          <span>
            {{ t('restocking.orderPlacedDetail', {
              units: submitted.total_units.toLocaleString(),
              amount: formatCurrency(submitted.total_value),
              days: submitted.lead_time_days
            }) }}
          </span>
        </div>
        <router-link to="/orders" class="submit-banner-link">
          {{ t('restocking.viewInOrders') }}
        </router-link>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            {{ t('restocking.recommendations') }} ({{ plan.recommendations.length }})
          </h3>
          <button
            class="place-order-btn"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <p v-if="plan.unpriced_skus.length" class="unpriced-notice">
          {{ t('restocking.unpricedNotice', {
            count: plan.unpriced_skus.length,
            skus: plan.unpriced_skus.join(', ')
          }) }}
        </p>

        <p v-if="submitError" class="error submit-error">{{ submitError }}</p>

        <div v-if="!plan.recommendations.length" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>

        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                <th class="col-category">{{ t('restocking.table.category') }}</th>
                <th class="col-num">{{ t('restocking.table.currentDemand') }}</th>
                <th class="col-num">{{ t('restocking.table.forecastedDemand') }}</th>
                <th class="col-num">{{ t('restocking.table.gap') }}</th>
                <th class="col-num">{{ t('restocking.table.quantity') }}</th>
                <th class="col-num">{{ t('restocking.table.unitCost') }}</th>
                <th class="col-num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="col-lead">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in plan.recommendations" :key="item.item_sku">
                <td class="col-sku"><strong>{{ item.item_sku }}</strong></td>
                <td class="col-name">{{ translateProductName(item.item_name) }}</td>
                <td class="col-category">{{ translateCategory(item.category) }}</td>
                <td class="col-num">{{ item.current_demand.toLocaleString() }}</td>
                <td class="col-num">{{ item.forecasted_demand.toLocaleString() }}</td>
                <td class="col-num gap-value">+{{ item.demand_gap.toLocaleString() }}</td>
                <td class="col-num">
                  <strong>{{ item.recommended_quantity.toLocaleString() }}</strong>
                  <span v-if="item.is_partial" class="badge warning partial-badge">
                    {{ t('restocking.partial') }}
                  </span>
                </td>
                <td class="col-num">{{ formatUnitCost(item.unit_cost) }}</td>
                <td class="col-num"><strong>{{ formatCurrency(item.line_total) }}</strong></td>
                <td class="col-lead">{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <p v-if="hasPartialLine" class="partial-note">{{ t('restocking.partialNote') }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import {
  formatCurrency as formatCurrencyUtil,
  formatCurrencyWithDecimals
} from '../utils/currency'

// Slider bounds in USD. The max sits just above the cost of closing every
// forecast gap (~$10.6K) so the top of the track means "fund everything"
// rather than trailing off into a range that changes nothing.
const BUDGET_MIN = 0
const BUDGET_MAX = 12000
const BUDGET_STEP = 100
const DEFAULT_BUDGET = 5000

// Dragging the slider fires an input event per step. Waiting for a short pause
// collapses a drag across the whole track into one request instead of ~120.
const BUDGET_DEBOUNCE_MS = 150

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    // All server amounts are USD; convert only at display time.
    const formatCurrency = (value) => formatCurrencyUtil(value, currentCurrency.value)

    // Unit costs are small enough that whole-dollar rounding misreports them
    // ($6.50 would render as $7), so they keep cents. Totals stay rounded.
    const formatUnitCost = (value) => formatCurrencyWithDecimals(value, currentCurrency.value, 2)

    // The API returns the raw catalog category ("Circuit Boards"); the locale files
    // key them in camelCase ("categories.circuitBoards"). t() returns the key itself
    // when a translation is missing, which is how the fallback to raw text works.
    const translateCategory = (category) => {
      const key = category
        .split(' ')
        .map((word, index) => (index === 0 ? word.toLowerCase() : word))
        .join('')
      const translated = t(`categories.${key}`)
      return translated === `categories.${key}` ? category : translated
    }

    const budget = ref(DEFAULT_BUDGET)
    const plan = ref(null)
    const loading = ref(true)
    const error = ref(null)
    const placing = ref(false)
    const submitError = ref(null)
    const submitted = ref(null)

    const hasPartialLine = computed(
      () => !!plan.value && plan.value.recommendations.some(item => item.is_partial)
    )

    const canPlaceOrder = computed(
      () => !placing.value && !!plan.value && plan.value.recommendations.length > 0
    )

    const loadPlan = async () => {
      try {
        loading.value = true
        error.value = null
        plan.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = t('restocking.loadFailed', { message: err.message })
      } finally {
        loading.value = false
      }
    }

    let debounceTimer = null
    watch(budget, () => {
      // A new budget invalidates the confirmation for the previous one.
      submitted.value = null
      submitError.value = null

      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(loadPlan, BUDGET_DEBOUNCE_MS)
    })

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return

      try {
        placing.value = true
        submitError.value = null

        // Send quantities only - the server re-prices every line from inventory.
        submitted.value = await api.createRestockOrder({
          budget: budget.value,
          lines: plan.value.recommendations.map(item => ({
            item_sku: item.item_sku,
            quantity: item.recommended_quantity
          }))
        })
      } catch (err) {
        const detail = err.response?.data?.detail
        submitError.value = t('restocking.submitFailed', { message: detail || err.message })
      } finally {
        placing.value = false
      }
    }

    onMounted(loadPlan)
    onUnmounted(() => clearTimeout(debounceTimer))

    return {
      t,
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      budget,
      plan,
      loading,
      error,
      placing,
      submitError,
      submitted,
      hasPartialLine,
      canPlaceOrder,
      placeOrder,
      formatCurrency,
      formatUnitCost,
      translateCategory,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-amount {
  font-size: 1.75rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  font-variant-numeric: tabular-nums;
}

.budget-control {
  padding-top: 0.25rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  appearance: none;
  -webkit-appearance: none;
  cursor: pointer;
  outline: none;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: transform 0.15s ease;
}

.budget-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #3b82f6;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  cursor: pointer;
}

.budget-slider:focus-visible {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 500;
}

.budget-help {
  margin-top: 0.75rem;
  font-size: 0.813rem;
  color: #64748b;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.25);
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.submit-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1.25rem;
}

.submit-banner-text {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  color: #065f46;
  font-size: 0.875rem;
}

.submit-banner-link {
  color: #047857;
  font-weight: 600;
  font-size: 0.875rem;
  text-decoration: none;
  white-space: nowrap;
}

.submit-banner-link:hover {
  text-decoration: underline;
}

.unpriced-notice {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 0.625rem 0.875rem;
  font-size: 0.813rem;
  color: #92400e;
  margin-bottom: 1rem;
}

.submit-error {
  margin-bottom: 1rem;
}

.empty-state {
  padding: 2.5rem 1rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

/* Fixed widths sum to 1100px, which fits the content area at the app's normal
   width; narrower viewports scroll via .table-container's overflow-x. */
.restock-table {
  table-layout: fixed;
  width: 100%;
  min-width: 1100px;
}

.col-sku {
  width: 100px;
}

.col-name {
  width: 180px;
}

.col-category {
  width: 120px;
}

.col-num {
  width: 100px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.col-lead {
  width: 100px;
  text-align: right;
}

.gap-value {
  color: #059669;
  font-weight: 600;
}

.partial-badge {
  margin-left: 0.5rem;
}

.partial-note {
  margin-top: 0.875rem;
  font-size: 0.813rem;
  color: #92400e;
}
</style>
