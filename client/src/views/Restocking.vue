<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

const forecasts = ref([])
const loading = ref(true)
const error = ref(null)

// All money math is in USD; values are converted only when displayed.
const budget = ref(0)

// Per-row user edits, keyed by SKU. Absent key = use the recommendation default.
const qtyOverrides = ref({})
const selectedOverrides = ref({})

const submitting = ref(false)
const successMessage = ref('')
const submitError = ref('')

// Two decimals so unit costs like $3.20 and line totals add up on screen.
// The helper applies the USD->JPY rate itself, so pass the raw USD value.
const money = (usd) => formatCurrencyWithDecimals(usd, currentCurrency.value, 2)

// Items whose forecasted demand exceeds stock on hand, largest gap first.
const candidates = computed(() => {
  return forecasts.value
    // Units already on submitted restock orders count as covered; a missing on_order is 0.
    .map(f => ({ ...f, shortfall: f.forecasted_demand - f.quantity_on_hand - (f.on_order ?? 0) }))
    .filter(f => f.shortfall > 0 && f.unit_cost > 0)
    .sort((a, b) => b.shortfall - a.shortfall)
})

// Slider max: total cost of covering every shortfall, rounded up to the next 100.
const maxBudget = computed(() => {
  const total = candidates.value.reduce((sum, c) => sum + c.shortfall * c.unit_cost, 0)
  return Math.ceil(total / 100) * 100
})

// Greedy fill: biggest shortfalls first, buying as many units as the remaining budget allows.
const recommendation = computed(() => {
  let remaining = budget.value
  const lines = []
  for (const c of candidates.value) {
    const qty = Math.min(c.shortfall, Math.floor(remaining / c.unit_cost))
    if (qty > 0) {
      lines.push({ ...c, recommendedQty: qty })
      remaining -= qty * c.unit_cost
    }
  }
  return lines
})

// Recommendation merged with the user's manual edits.
const rows = computed(() => {
  return recommendation.value.map(line => {
    const override = qtyOverrides.value[line.item_sku]
    const quantity = override !== undefined ? override : line.recommendedQty
    const selected = selectedOverrides.value[line.item_sku] ?? true
    return { ...line, quantity, selected, lineCost: quantity * line.unit_cost }
  })
})

const orderLines = computed(() => rows.value.filter(r => r.selected && r.quantity > 0))
const orderTotal = computed(() => orderLines.value.reduce((sum, r) => sum + r.lineCost, 0))
// Clamped at zero: manual quantity edits can push the total past budget, and
// the over-budget state is already signalled by the 'over' class and message.
const remainingBudget = computed(() => Math.max(0, budget.value - orderTotal.value))
const isOverBudget = computed(() => orderTotal.value > budget.value)
const canSubmit = computed(() => !submitting.value && orderLines.value.length > 0 && !isOverBudget.value)

// A new budget produces a new recommendation, so discard stale manual edits.
watch(budget, () => {
  qtyOverrides.value = {}
  selectedOverrides.value = {}
})

const setQuantity = (sku, event) => {
  // Integer, never negative; empty/invalid input counts as 0.
  const parsed = Math.floor(Number(event.target.value))
  const qty = Number.isFinite(parsed) ? Math.max(0, parsed) : 0
  qtyOverrides.value = { ...qtyOverrides.value, [sku]: qty }
  event.target.value = qty
}

const setSelected = (sku, checked) => {
  selectedOverrides.value = { ...selectedOverrides.value, [sku]: checked }
}

const trendLabel = (trend) => {
  const key = `trends.${trend}`
  const label = t(key)
  return label === key ? trend : label
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

const loadForecasts = async () => {
  loading.value = true
  error.value = null
  try {
    forecasts.value = await api.getDemandForecasts()
    // Start at roughly half the full cost so the slider visibly changes the list.
    budget.value = Math.round(maxBudget.value / 2 / 100) * 100
  } catch (err) {
    error.value = 'Failed to load forecasts: ' + err.message
    console.error(err)
  } finally {
    loading.value = false
  }
}

// Plain (non-reactive) flag: it flips synchronously, so a second click fired
// before Vue re-renders the disabled button is still rejected.
let submitInFlight = false

const placeOrder = async () => {
  if (submitInFlight) return
  if (!canSubmit.value) return
  submitInFlight = true
  submitting.value = true
  successMessage.value = ''
  submitError.value = ''
  try {
    const order = await api.submitRestockOrder({
      items: orderLines.value.map(r => ({ sku: r.item_sku, quantity: r.quantity }))
    })
    successMessage.value = t('restocking.orderPlaced', {
      orderNumber: order.order_number,
      days: order.lead_time_days,
      date: formatDate(order.expected_delivery)
    })
    // Clear the selection. Budget 0 yields an empty recommendation, so no rows
    // stay selected (the budget watcher also drops manual edits).
    budget.value = 0
    qtyOverrides.value = {}
    selectedOverrides.value = {}
    // Refresh so shortfall reflects the new on_order. Done without the page-level
    // loading state (no flicker) and without resetting the budget. A refresh
    // failure must not look like an order failure: the order was already placed.
    try {
      forecasts.value = await api.getDemandForecasts()
    } catch (reloadErr) {
      console.error(reloadErr)
    }
  } catch (err) {
    // Prefer the server's explanation (HTTP 400 detail) when present.
    const detail = err.response?.data?.detail
    submitError.value = typeof detail === 'string' ? detail : t('restocking.orderFailed')
    console.error(err)
  } finally {
    submitting.value = false
    submitInFlight = false
  }
}

onMounted(loadForecasts)
</script>

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
          step="100"
          :max="maxBudget"
        />
      </div>

      <div v-if="successMessage" class="notice notice-success" role="status">{{ successMessage }}</div>
      <div v-if="submitError" class="notice notice-error" role="alert">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommended') }} ({{ rows.length }})</h3>
        </div>

        <p v-if="rows.length === 0" class="empty">{{ t('restocking.noRecommendations') }}</p>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th class="col-select">{{ t('restocking.table.select') }}</th>
                <th>{{ t('restocking.table.item') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.shortfall') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.item_sku" :class="{ dimmed: !row.selected }">
                <td class="col-select">
                  <input
                    type="checkbox"
                    :checked="row.selected"
                    :aria-label="t('restocking.table.select')"
                    @change="setSelected(row.item_sku, $event.target.checked)"
                  />
                </td>
                <td>
                  <div class="item-name">{{ translateProductName(row.item_name) }}</div>
                  <div class="item-sku">{{ row.item_sku }}</div>
                </td>
                <td>
                  <span :class="['badge', row.trend]">{{ trendLabel(row.trend) }}</span>
                </td>
                <td class="num">{{ row.shortfall.toLocaleString() }}</td>
                <td class="num">
                  <input
                    class="qty-input"
                    type="number"
                    min="0"
                    step="1"
                    :value="row.quantity"
                    @change="setQuantity(row.item_sku, $event)"
                  />
                </td>
                <td class="num">{{ money(row.unit_cost) }}</td>
                <td class="num">{{ money(row.lineCost) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="footer">
          <div class="totals">
            <div class="total-item">
              <span class="total-label">{{ t('restocking.totalCost') }}</span>
              <span :class="['total-value', { over: isOverBudget }]">{{ money(orderTotal) }}</span>
            </div>
            <div class="total-item">
              <span class="total-label">{{ t('restocking.budgetRemaining') }}</span>
              <span :class="['total-value', { over: isOverBudget }]">{{ money(remainingBudget) }}</span>
            </div>
          </div>
          <div class="actions">
            <span v-if="isOverBudget" class="helper helper-error">{{ t('restocking.overBudget') }}</span>
            <span v-else-if="orderLines.length === 0" class="helper">{{ t('restocking.selectItems') }}</span>
            <button type="button" class="place-order" :disabled="!canSubmit" @click="placeOrder">
              {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget-card {
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
}

.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
  accent-color: #0f172a;
}

.notice {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  font-size: 0.875rem;
  border: 1px solid;
}

.notice-success {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}

.notice-error {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.empty {
  padding: 2rem 1.5rem;
  text-align: center;
  color: #64748b;
}

.restock-table {
  width: 100%;
}

.restock-table .num {
  text-align: right;
}

.col-select {
  width: 72px;
  text-align: center;
}

.dimmed {
  opacity: 0.5;
}

.item-name {
  font-weight: 500;
  color: #0f172a;
}

.item-sku {
  font-size: 0.75rem;
  color: #64748b;
}

.qty-input {
  width: 88px;
  padding: 0.25rem 0.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  text-align: right;
  font-size: 0.875rem;
  color: #0f172a;
}

.footer {
  display: grid;
  grid-template-columns: 1fr auto;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.totals {
  display: flex;
  gap: 2rem;
}

.total-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.total-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.total-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.total-value.over {
  color: #dc2626;
}

.actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.helper {
  font-size: 0.813rem;
  color: #64748b;
}

.helper-error {
  color: #dc2626;
}

.place-order {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
}

.place-order:hover:not(:disabled) {
  background: #1e293b;
}

.place-order:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}
</style>
