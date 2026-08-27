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
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
        </div>
        <div class="budget-body">
          <div class="budget-amount">{{ formatCurrency(budget, currentCurrency) }}</div>
          <input
            type="range"
            :min="SLIDER_MIN"
            :max="SLIDER_MAX"
            :step="SLIDER_STEP"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-scale">
            <span>{{ formatCurrency(SLIDER_MIN, currentCurrency) }}</span>
            <span class="full-coverage-marker" :style="{ left: fullCoveragePercent + '%' }">
              {{ t('restocking.fullCoverage') }}: {{ formatCurrencyWithDecimals(fullCoverageCost, currentCurrency, 2) }}
            </span>
            <span>{{ formatCurrency(SLIDER_MAX, currentCurrency) }}</span>
          </div>
          <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
        </div>
      </div>

      <div v-if="noShortfallCandidates" class="empty-state card">
        {{ t('restocking.noShortfall') }}
      </div>
      <div v-else>
        <div class="stats-grid">
          <div class="stat-card info">
            <div class="stat-label">{{ t('restocking.allocated') }}</div>
            <div class="stat-value">{{ formatCurrencyWithDecimals(allocatedTotal, currentCurrency, 2) }}</div>
          </div>
          <div class="stat-card success">
            <div class="stat-label">{{ t('restocking.remaining') }}</div>
            <div class="stat-value">{{ formatCurrencyWithDecimals(remainingBudget, currentCurrency, 2) }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">{{ t('restocking.itemsSelected') }}</div>
            <div class="stat-value">{{ recommendedItems.length }}</div>
          </div>
          <div class="stat-card warning">
            <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
            <div class="stat-value">{{ t('restocking.days', { count: longestLeadTime }) }}</div>
          </div>
        </div>

        <div v-if="nothingAffordable" class="empty-state card">
          {{ t('restocking.nothingAffordable') }}
        </div>

        <div v-else class="card">
          <div class="card-header">
            <h3 class="card-title">
              {{ t('restocking.recommended') }} —
              {{ t('restocking.recommendedCount', { count: recommendedItems.length, total: candidates.length }) }}
            </h3>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.table.shortfall') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.quantity') }}</th>
                  <th>{{ t('restocking.table.lineTotal') }}</th>
                  <th>{{ t('restocking.table.leadTime') }}</th>
                  <th>{{ t('restocking.table.coverage') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendedItems" :key="item.item_sku">
                  <td><strong>{{ item.item_sku }}</strong></td>
                  <td>{{ item.item_name }}</td>
                  <td>{{ item.shortfall }}</td>
                  <td>{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                  <td><strong>{{ item.quantity }}</strong></td>
                  <td>{{ formatCurrencyWithDecimals(item.lineTotal, currentCurrency, 2) }}</td>
                  <td>{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
                  <td>
                    <span :class="['badge', item.coverage === 'full' ? 'success' : 'warning']">
                      {{ item.coverage === 'full' ? t('restocking.fullHint') : t('restocking.partial') }}
                    </span>
                    <div v-if="item.coverage === 'partial'" class="coverage-hint">
                      {{ t('restocking.partialHint', { quantity: item.quantity, needed: item.shortfall }) }}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="excludedItems.length" class="card excluded-card">
          <div class="card-header">
            <h3 class="card-title">{{ t('restocking.excluded') }}</h3>
          </div>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.itemName') }}</th>
                  <th>{{ t('restocking.excluded') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in excludedItems" :key="item.item_sku" class="excluded-row">
                  <td>{{ item.item_sku }}</td>
                  <td>{{ item.item_name }}</td>
                  <td class="muted">{{ item.reasonText }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="submit-section">
          <button
            class="place-order-btn"
            :disabled="submitting || recommendedItems.length === 0"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>

          <div v-if="submitError" class="error submit-error">{{ submitError }}</div>

          <div v-if="submittedOrder" class="order-confirmation">
            {{ t('restocking.orderPlaced', { orderNumber: submittedOrder.order_number, date: formatDate(submittedOrder.expected_delivery) }) }}
            <router-link to="/orders" class="view-in-orders-link">
              {{ t('restocking.viewInOrders') }}
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])

    const budget = ref(5000)
    const submitting = ref(false)
    const submitError = ref(null)
    const submittedOrder = ref(null)

    const SLIDER_MIN = 0
    const SLIDER_MAX = 10000
    const SLIDER_STEP = 250

    // Cent-safe rounding helper to avoid IEEE-754 drift when
    // repeatedly adding/subtracting money values.
    const roundToCents = (value) => Math.round(value * 100) / 100

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

    // Candidates: forecasts with positive shortfall, sorted deterministically
    const candidates = computed(() => {
      return forecasts.value
        .map(f => ({
          ...f,
          shortfall: f.forecasted_demand - f.current_demand
        }))
        .filter(f => f.shortfall > 0)
        .sort((a, b) => {
          if (b.shortfall !== a.shortfall) return b.shortfall - a.shortfall
          if (b.unit_cost !== a.unit_cost) return b.unit_cost - a.unit_cost
          return a.item_sku.localeCompare(b.item_sku)
        })
    })

    const noShortfallCandidates = computed(() => candidates.value.length === 0)

    // Full-coverage cost: cent-rounded sum of every candidate's full shortfall
    // cost, derived from the loaded forecasts so it never drifts from the
    // actual fixture data.
    const fullCoverageCost = computed(() => {
      return roundToCents(
        candidates.value.reduce((sum, item) => sum + item.shortfall * item.unit_cost, 0)
      )
    })

    const fullCoveragePercent = computed(() => {
      return Math.min(100, (fullCoverageCost.value / SLIDER_MAX) * 100)
    })

    // Greedy allocation computed from budget + candidates
    const allocation = computed(() => {
      let remaining = roundToCents(budget.value)
      const recommended = []
      const excluded = []

      for (const item of candidates.value) {
        // Round to cents so a running total that should exactly equal an
        // item's cost isn't off by IEEE-754 float drift.
        const fullCost = roundToCents(item.shortfall * item.unit_cost)
        let quantity
        let coverage

        if (remaining >= fullCost) {
          quantity = item.shortfall
          coverage = 'full'
        } else {
          quantity = Math.floor(remaining / item.unit_cost)
          coverage = 'partial'
        }

        if (quantity < 1) {
          excluded.push({
            ...item,
            reason: 'excludedNoBudget',
            reasonText: t('restocking.excludedNoBudget')
          })
          continue
        }

        const lineTotal = roundToCents(quantity * item.unit_cost)
        remaining = roundToCents(remaining - lineTotal)
        recommended.push({
          ...item,
          quantity,
          coverage,
          lineTotal
        })
      }

      // Avoid rendering -0 or leftover float noise on the remaining budget.
      if (Object.is(remaining, -0)) remaining = 0

      return { recommended, excluded, remaining }
    })

    const recommendedItems = computed(() => allocation.value.recommended)

    const excludedItems = computed(() => {
      // MTR-304-style items (no positive shortfall) plus budget-exhausted items
      const noShortfall = forecasts.value
        .map(f => ({ ...f, shortfall: f.forecasted_demand - f.current_demand }))
        .filter(f => f.shortfall <= 0)
        .map(f => ({
          ...f,
          reason: 'excludedNoShortfall',
          reasonText: t('restocking.excludedNoShortfall')
        }))

      return [...noShortfall, ...allocation.value.excluded]
    })

    const allocatedTotal = computed(() => {
      return roundToCents(recommendedItems.value.reduce((sum, item) => sum + item.lineTotal, 0))
    })

    const remainingBudget = computed(() => {
      let remaining = roundToCents(budget.value - allocatedTotal.value)
      if (Object.is(remaining, -0)) remaining = 0
      return remaining
    })

    const longestLeadTime = computed(() => {
      if (recommendedItems.value.length === 0) return 0
      return Math.max(...recommendedItems.value.map(item => item.lead_time_days))
    })

    const nothingAffordable = computed(() => {
      return !noShortfallCandidates.value && recommendedItems.value.length === 0
    })

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const placeOrder = async () => {
      submitError.value = null
      submittedOrder.value = null
      submitting.value = true
      try {
        const payload = {
          budget: budget.value,
          items: recommendedItems.value.map(item => ({
            item_sku: item.item_sku,
            item_name: item.item_name,
            quantity: item.quantity,
            unit_cost: item.unit_cost,
            lead_time_days: item.lead_time_days
          }))
        }
        submittedOrder.value = await api.createRestockOrder(payload)
      } catch (err) {
        submitError.value = err.response?.data?.detail || 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      currentCurrency,
      loading,
      error,
      budget,
      SLIDER_MIN,
      SLIDER_MAX,
      SLIDER_STEP,
      fullCoverageCost,
      fullCoveragePercent,
      candidates,
      noShortfallCandidates,
      recommendedItems,
      excludedItems,
      allocatedTotal,
      remainingBudget,
      longestLeadTime,
      nothingAffordable,
      submitting,
      submitError,
      submittedOrder,
      formatCurrency,
      formatCurrencyWithDecimals,
      formatDate,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-amount {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.budget-scale {
  position: relative;
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  padding-top: 0.25rem;
  min-height: 1.5rem;
}

.full-coverage-marker {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  color: #ea580c;
  font-weight: 600;
  white-space: nowrap;
}

.budget-hint {
  color: #64748b;
  font-size: 0.875rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.excluded-card .muted {
  color: #94a3b8;
}

.excluded-row:hover {
  background: transparent !important;
}

.coverage-hint {
  font-size: 0.75rem;
  color: #92400e;
  margin-top: 0.25rem;
}

.submit-section {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: flex-start;
}

.place-order-btn {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.938rem;
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

.submit-error {
  margin: 0;
}

.order-confirmation {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.938rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.view-in-orders-link {
  color: #065f46;
  font-weight: 600;
  text-decoration: underline;
}
</style>
