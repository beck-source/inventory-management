<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="lastSubmitted" class="submit-banner">
      <div class="submit-banner-text">
        <strong>{{ t('restocking.submitted.heading', { orderNumber: lastSubmitted.order_number }) }}</strong>
        <span>
          {{ t('restocking.submitted.detail', {
            count: lastSubmitted.item_count,
            units: lastSubmitted.total_units,
            days: lastSubmitted.max_lead_time_days
          }) }}
        </span>
      </div>
      <router-link to="/orders" class="submit-banner-link">
        {{ t('restocking.submitted.viewInOrders') }}
      </router-link>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budget.title') }}</h3>
        <span class="budget-readout">{{ formatMoney(budget) }}</span>
      </div>
      <div class="budget-body">
        <input
          type="range"
          class="budget-slider"
          :min="BUDGET_MIN"
          :max="BUDGET_MAX"
          :step="BUDGET_STEP"
          v-model.number="budget"
          :aria-label="t('restocking.budget.title')"
        />
        <div class="budget-scale">
          <span>{{ formatMoney(BUDGET_MIN) }}</span>
          <span>{{ formatMoney(BUDGET_MAX) }}</span>
        </div>
        <p class="budget-hint">
          {{ t('restocking.budget.totalNeed', { amount: formatMoney(plan.total_need) }) }}
        </p>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card info">
        <div class="stat-label">{{ t('restocking.stats.allocated') }}</div>
        <div class="stat-value">{{ formatMoney(plan.total_cost) }}</div>
      </div>
      <div class="stat-card success">
        <div class="stat-label">{{ t('restocking.stats.remaining') }}</div>
        <div class="stat-value">{{ formatMoney(plan.remaining_budget) }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ t('restocking.stats.itemsRecommended') }}</div>
        <div class="stat-value">{{ plan.items_recommended }}</div>
      </div>
      <div class="stat-card warning">
        <div class="stat-label">{{ t('restocking.stats.leadTime') }}</div>
        <div class="stat-value">{{ plan.max_lead_time_days }}{{ t('restocking.daysSuffix') }}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">
          {{ t('restocking.recommendations.title') }} ({{ plan.recommendations.length }})
        </h3>
        <button
          class="place-order-btn"
          :disabled="!canPlaceOrder"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>

      <div v-else-if="plan.recommendations.length === 0" class="empty-state">
        {{ t('restocking.recommendations.empty') }}
      </div>

      <div v-else class="table-container">
        <table class="restock-table">
          <thead>
            <tr>
              <th class="col-sku">{{ t('restocking.table.sku') }}</th>
              <th class="col-item">{{ t('restocking.table.itemName') }}</th>
              <th class="col-supplier">{{ t('restocking.table.supplier') }}</th>
              <th class="col-trend">{{ t('restocking.table.trend') }}</th>
              <th class="col-num">{{ t('restocking.table.demandGap') }}</th>
              <th class="col-num">{{ t('restocking.table.quantity') }}</th>
              <th class="col-num">{{ t('restocking.table.unitCost') }}</th>
              <th class="col-num">{{ t('restocking.table.lineTotal') }}</th>
              <th class="col-num">{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in plan.recommendations" :key="item.item_sku">
              <td class="col-sku"><strong>{{ item.item_sku }}</strong></td>
              <td class="col-item">{{ translateProductName(item.item_name) }}</td>
              <td class="col-supplier">{{ item.supplier }}</td>
              <td class="col-trend">
                <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
              </td>
              <td class="col-num">{{ item.demand_gap.toLocaleString() }}</td>
              <td class="col-num">{{ item.recommended_quantity.toLocaleString() }}</td>
              <td class="col-num">{{ formatMoneyExact(item.unit_cost) }}</td>
              <td class="col-num"><strong>{{ formatMoney(item.line_total) }}</strong></td>
              <td class="col-num">{{ item.lead_time_days }}{{ t('restocking.daysSuffix') }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="7" class="foot-label">{{ t('restocking.table.total') }}</td>
              <td class="col-num"><strong>{{ formatMoney(plan.total_cost) }}</strong></td>
              <td class="col-num">{{ plan.max_lead_time_days }}{{ t('restocking.daysSuffix') }}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>

    <div v-if="plan.skipped.length > 0" class="card">
      <div class="card-header">
        <h3 class="card-title">
          {{ t('restocking.skipped.title') }} ({{ plan.skipped.length }})
        </h3>
      </div>
      <p class="skipped-note">{{ t('restocking.skipped.note') }}</p>
      <div class="table-container">
        <table class="restock-table">
          <thead>
            <tr>
              <th class="col-sku">{{ t('restocking.table.sku') }}</th>
              <th class="col-item">{{ t('restocking.table.itemName') }}</th>
              <th class="col-trend">{{ t('restocking.table.trend') }}</th>
              <th class="col-num">{{ t('restocking.table.quantity') }}</th>
              <th class="col-num">{{ t('restocking.table.lineTotal') }}</th>
              <th class="col-num">{{ t('restocking.skipped.shortBy') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in plan.skipped" :key="item.item_sku">
              <td class="col-sku"><strong>{{ item.item_sku }}</strong></td>
              <td class="col-item">{{ translateProductName(item.item_name) }}</td>
              <td class="col-trend">
                <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
              </td>
              <td class="col-num">{{ item.recommended_quantity.toLocaleString() }}</td>
              <td class="col-num">{{ formatMoney(item.line_total) }}</td>
              <td class="col-num shortfall">
                {{ formatMoney(Math.max(0, item.line_total - plan.remaining_budget)) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Slider bounds are chosen so the default sits below total demand need, which keeps the
// budget constraint visible on first load instead of funding every item immediately.
const BUDGET_MIN = 1000
const BUDGET_MAX = 12000
const BUDGET_STEP = 250
const BUDGET_DEFAULT = 5000

// A range input emits a value for every step it passes through, so dragging across the
// full track would fire ~44 requests. Wait for the slider to settle before asking the
// server to recompute the plan.
const BUDGET_DEBOUNCE_MS = 250

const emptyPlan = () => ({
  budget: 0,
  recommendations: [],
  skipped: [],
  total_cost: 0,
  remaining_budget: 0,
  total_need: 0,
  items_recommended: 0,
  items_skipped: 0,
  total_units: 0,
  max_lead_time_days: 0
})

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const budget = ref(BUDGET_DEFAULT)
    const plan = ref(emptyPlan())
    const loading = ref(true)
    const submitting = ref(false)
    const error = ref(null)
    const lastSubmitted = ref(null)

    const formatMoney = (amount) => formatCurrency(amount || 0, currentCurrency.value)
    const formatMoneyExact = (amount) => formatCurrencyWithDecimals(amount || 0, currentCurrency.value, 2)

    // True between a slider move and the debounced fetch that follows it. While pending,
    // the plan on screen belongs to an older budget, so it must not be submittable.
    const planPending = ref(false)

    const canPlaceOrder = computed(() => {
      return !submitting.value &&
             !loading.value &&
             !planPending.value &&
             plan.value.recommendations.length > 0
    })

    const loadPlan = async () => {
      try {
        loading.value = true
        error.value = null
        plan.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = t('restocking.errors.load') + ' ' + err.message
        plan.value = emptyPlan()
      } finally {
        loading.value = false
        planPending.value = false
      }
    }

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return

      try {
        submitting.value = true
        error.value = null

        // The server recomputes nothing on submit, so the recommended quantity is sent
        // explicitly as the ordered quantity.
        const items = plan.value.recommendations.map(rec => ({
          item_sku: rec.item_sku,
          item_name: rec.item_name,
          supplier: rec.supplier,
          quantity: rec.recommended_quantity,
          unit_cost: rec.unit_cost,
          line_total: rec.line_total,
          lead_time_days: rec.lead_time_days
        }))

        lastSubmitted.value = await api.submitRestockOrder({
          budget: plan.value.budget,
          items
        })
      } catch (err) {
        error.value = t('restocking.errors.submit') + ' ' + err.message
      } finally {
        submitting.value = false
      }
    }

    // Re-request the plan whenever the slider settles on a new value. The budget is the
    // only input, so the whole plan is recomputed server-side rather than filtered here.
    let budgetTimer = null

    watch(budget, () => {
      // The confirmation banner describes the plan that was submitted, so a new budget
      // makes it stale - drop it rather than let it sit above a different plan.
      lastSubmitted.value = null
      planPending.value = true

      if (budgetTimer) clearTimeout(budgetTimer)
      budgetTimer = setTimeout(loadPlan, BUDGET_DEBOUNCE_MS)
    })

    onMounted(loadPlan)

    // Leaving the view mid-drag would otherwise fire a fetch against a dead component.
    onUnmounted(() => {
      if (budgetTimer) clearTimeout(budgetTimer)
    })

    return {
      t,
      BUDGET_MIN,
      BUDGET_MAX,
      BUDGET_STEP,
      budget,
      plan,
      loading,
      submitting,
      planPending,
      error,
      lastSubmitted,
      canPlaceOrder,
      placeOrder,
      formatMoney,
      formatMoneyExact,
      translateProductName
    }
  }
}
</script>

<style scoped>
/* Budget slider */
.budget-body {
  padding: 0.5rem 0 0.25rem;
}

.budget-readout {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  appearance: none;
  -webkit-appearance: none;
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
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  cursor: pointer;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.3);
  cursor: pointer;
}

.budget-slider:focus-visible {
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.budget-hint {
  margin: 0.75rem 0 0;
  font-size: 0.875rem;
  color: #64748b;
}

/* Place order button */
.place-order-btn {
  background: #2563eb;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1.125rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

/* Submission confirmation */
.submit-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-left: 3px solid #16a34a;
  border-radius: 8px;
  padding: 0.875rem 1.125rem;
  margin-bottom: 1.5rem;
}

.submit-banner-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #0f172a;
}

.submit-banner-text span {
  color: #64748b;
}

.submit-banner-link {
  font-size: 0.875rem;
  font-weight: 600;
  color: #16a34a;
  text-decoration: none;
  white-space: nowrap;
}

.submit-banner-link:hover {
  text-decoration: underline;
}

/* Tables */
.restock-table {
  width: 100%;
}

.col-sku {
  width: 110px;
}

.col-supplier {
  width: 180px;
}

.col-trend {
  width: 110px;
}

.col-num {
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.restock-table tfoot td {
  border-top: 2px solid #e2e8f0;
  border-bottom: none;
  font-weight: 600;
}

.foot-label {
  text-align: right;
  color: #64748b;
}

.shortfall {
  color: #dc2626;
}

.skipped-note {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  color: #64748b;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
