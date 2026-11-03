<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil, formatCurrencyWithDecimals } from '../utils/currency'

// NOTE: This view intentionally does NOT use useFilters / watch the global FilterBar.
// Restocking is driven only by the budget slider: recommendations are computed server-side
// across all warehouses/categories, so warehouse/category/month/status filters do not apply.

const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

const DEBOUNCE_MS = 200

// Raw data lives in refs; everything shown in totals is derived with computed()
const loading = ref(true)          // initial page load
const ready = ref(false)           // true once max_budget is known
const error = ref(null)
const maxBudget = ref(0)
const sliderValue = ref(0)
const items = ref([])
const selectedSkus = ref([])       // SKUs currently checked
const recsLoading = ref(false)

const submitting = ref(false)
const orderError = ref(null)
const orderResult = ref(null)

// Slider step: 100 for realistic budgets, 1 when the whole range is small
const step = computed(() => (maxBudget.value >= 1000 ? 100 : 1))

// The slider can only land on multiples of `step`, so round its max up to a step boundary;
// the budget actually used is clamped back to the true max_budget so "cover everything"
// is reachable even when max_budget is not a multiple of the step.
const sliderMax = computed(() => Math.ceil(maxBudget.value / step.value) * step.value)
const budget = computed(() => Math.min(sliderValue.value, maxBudget.value))

const selectedSet = computed(() => new Set(selectedSkus.value))
const selectedItems = computed(() => items.value.filter(i => selectedSet.value.has(i.sku)))

// Round to cents to avoid float drift when summing line costs
const round2 = (n) => Math.round(n * 100) / 100
const selectedTotal = computed(() => round2(selectedItems.value.reduce((sum, i) => sum + i.line_cost, 0)))
const selectedShortfall = computed(() => selectedItems.value.reduce((sum, i) => sum + i.shortfall, 0))
const selectedQuantity = computed(() => selectedItems.value.reduce((sum, i) => sum + i.quantity, 0))
const remaining = computed(() => round2(budget.value - selectedTotal.value))

// Lead time is the MAX across checked items, not the sum: suppliers ship in parallel,
// so the order is only complete when its slowest line item arrives.
const orderLeadTime = computed(() =>
  selectedItems.value.reduce((max, i) => Math.max(max, i.lead_time_days), 0)
)

const allSelected = computed(() => items.value.length > 0 && selectedItems.value.length === items.value.length)
const someSelected = computed(() => selectedItems.value.length > 0 && !allSelected.value)
const canPlaceOrder = computed(() => selectedItems.value.length > 0 && !submitting.value)

const formatCurrency = (value) => formatCurrencyUtil(value, currentCurrency.value)
const formatMoney = (value) => formatCurrencyWithDecimals(value, currentCurrency.value, 2)

const formatDate = (dateString) => {
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

// Turn FastAPI errors into readable text: `detail` is a string for 400s and an array of
// { loc, msg } objects for 422 validation errors.
const extractErrorMessage = (err) => {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string' && detail) return detail
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map(d => {
        if (typeof d === 'string') return d
        const field = Array.isArray(d.loc) ? d.loc.filter(p => p !== 'body').join('.') : ''
        return field ? `${field}: ${d.msg}` : d.msg
      })
      .join('; ')
  }
  return t('restocking.errorFallback')
}

// Stale-response guard: every request gets an increasing id and only the latest one may
// write state. Without this, a slow response for an earlier slider position could arrive
// after a newer one and overwrite it.
let requestCounter = 0
let debounceTimer = null

const fetchRecommendations = async () => {
  const requestId = ++requestCounter
  recsLoading.value = true
  error.value = null
  try {
    const data = await api.getRestockRecommendations(budget.value)
    if (requestId !== requestCounter) return // superseded by a newer request
    items.value = data.items
    // Every new recommendation set starts fully checked
    selectedSkus.value = data.items.map(i => i.sku)
  } catch (err) {
    if (requestId !== requestCounter) return
    error.value = t('restocking.loadError') + ': ' + err.message
    console.error(err)
  } finally {
    if (requestId === requestCounter) recsLoading.value = false
  }
}

// Debounce while dragging so we send one request per ~200 ms pause instead of one per tick
const onSliderInput = (event) => {
  sliderValue.value = Number(event.target.value)
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchRecommendations, DEBOUNCE_MS)
}

const toggleItem = (sku) => {
  if (selectedSet.value.has(sku)) {
    selectedSkus.value = selectedSkus.value.filter(s => s !== sku)
  } else {
    selectedSkus.value = [...selectedSkus.value, sku]
  }
}

const toggleAll = () => {
  selectedSkus.value = allSelected.value ? [] : items.value.map(i => i.sku)
}

const loadInitial = async () => {
  loading.value = true
  error.value = null
  try {
    // budget=0 is only used to learn max_budget (cost of covering every shortfall),
    // which becomes the slider's upper bound.
    const base = await api.getRestockRecommendations(0)
    maxBudget.value = base.max_budget
    const s = base.max_budget >= 1000 ? 100 : 1
    sliderValue.value = Math.round(base.max_budget / 2 / s) * s // default to ~half
    ready.value = true
    await fetchRecommendations()
  } catch (err) {
    error.value = t('restocking.loadError') + ': ' + err.message
    console.error(err)
  } finally {
    loading.value = false
  }
}

const placeOrder = async () => {
  if (!canPlaceOrder.value) return
  // Drop any pending debounced fetch so the slider can't swap the list out right after
  // the order is placed; the order payload below is built from the set currently shown.
  clearTimeout(debounceTimer)
  submitting.value = true
  orderError.value = null
  orderResult.value = null
  try {
    const order = await api.createRestockOrder({
      budget: budget.value,
      items: selectedItems.value.map(i => ({ sku: i.sku, quantity: i.quantity }))
    })
    orderResult.value = order
    await fetchRecommendations()
  } catch (err) {
    orderError.value = extractErrorMessage(err)
    console.error(err)
  } finally {
    submitting.value = false
  }
}

onMounted(loadInitial)

onBeforeUnmount(() => {
  clearTimeout(debounceTimer)
  requestCounter++ // ignore any response that lands after unmount
})
</script>

<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="!ready" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetTitle') }}</h3>
        </div>
        <div class="budget-readout" aria-live="polite">{{ formatCurrency(budget) }}</div>
        <input
          class="budget-slider"
          type="range"
          min="0"
          :max="sliderMax"
          :step="step"
          :value="sliderValue"
          :disabled="maxBudget === 0"
          :aria-label="t('restocking.budgetLabel')"
          @input="onSliderInput"
        />
        <div class="budget-scale">
          <span>{{ t('restocking.budgetMin') }}: {{ formatCurrency(0) }}</span>
          <span>{{ t('restocking.budgetMax') }}: {{ formatCurrency(maxBudget) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.selectedTotal') }}</div>
          <div class="stat-value">{{ formatMoney(selectedTotal) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.remaining') }}</div>
          <div class="stat-value">{{ formatMoney(remaining) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.summary.leadTime') }}</div>
          <div class="stat-value">
            {{ selectedItems.length ? t('restocking.days', { count: orderLeadTime }) : '-' }}
          </div>
        </div>
      </div>

      <div v-if="orderResult" class="success-banner" role="status">
        <span>
          {{ t('restocking.success', {
            orderNumber: orderResult.order_number,
            total: formatMoney(orderResult.total_value),
            date: formatDate(orderResult.expected_delivery)
          }) }}
        </span>
        <router-link to="/orders" class="banner-link">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="orderError" class="error" role="alert">{{ orderError }}</div>
      <div v-if="error" class="error" role="alert">{{ error }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendationsTitle') }} ({{ items.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="items.length === 0" class="empty-state">
          {{ recsLoading ? t('common.loading') : t('restocking.empty') }}
        </div>
        <div v-else class="table-container" :class="{ stale: recsLoading }">
          <table>
            <thead>
              <tr>
                <th class="col-check">
                  <input
                    type="checkbox"
                    :checked="allSelected"
                    :indeterminate.prop="someSelected"
                    :aria-label="t('restocking.selectAll')"
                    @change="toggleAll"
                  />
                </th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.shortfall') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.sku" :class="{ unchecked: !selectedSet.has(item.sku) }">
                <td class="col-check">
                  <input
                    type="checkbox"
                    :checked="selectedSet.has(item.sku)"
                    :aria-label="`${t('restocking.table.include')} ${item.sku}`"
                    @change="toggleItem(item.sku)"
                  />
                </td>
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
                </td>
                <td class="num">{{ item.shortfall.toLocaleString() }}</td>
                <td class="num"><strong>{{ item.quantity.toLocaleString() }}</strong></td>
                <td class="num">{{ formatMoney(item.unit_cost) }}</td>
                <td class="num"><strong>{{ formatMoney(item.line_cost) }}</strong></td>
                <td class="num">{{ item.lead_time_days }}</td>
              </tr>
            </tbody>
            <!-- Totals cover CHECKED items only -->
            <tfoot>
              <tr>
                <td></td>
                <td colspan="3"><strong>{{ t('restocking.totals') }} ({{ selectedItems.length }})</strong></td>
                <td class="num"><strong>{{ selectedShortfall.toLocaleString() }}</strong></td>
                <td class="num"><strong>{{ selectedQuantity.toLocaleString() }}</strong></td>
                <td></td>
                <td class="num"><strong>{{ formatMoney(selectedTotal) }}</strong></td>
                <td class="num"><strong>{{ selectedItems.length ? orderLeadTime : '-' }}</strong></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget-readout {
  font-size: 3rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  margin-bottom: 1rem;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-slider:disabled {
  cursor: not-allowed;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: #64748b;
}

.success-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  background: #d1fae5;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
  font-weight: 500;
}

.banner-link {
  color: #065f46;
  font-weight: 700;
  text-decoration: underline;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.625rem 1.25rem;
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
  color: #64748b;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Dim the table while a newer recommendation set is loading */
.stale {
  opacity: 0.6;
}

th.num,
td.num {
  text-align: right;
}

.col-check {
  width: 48px;
}

tr.unchecked td:not(.col-check) {
  color: #94a3b8;
}

tfoot td {
  border-top: 2px solid #e2e8f0;
  background: #f8fafc;
  color: #0f172a;
}
</style>
