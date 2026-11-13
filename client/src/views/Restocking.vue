<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

const STEP = 100
const DEBOUNCE_MS = 250

const budget = ref(0)
const sliderMax = ref(0)
const recommendation = ref(null)
const trendBySku = ref({})
const loading = ref(true)
const refreshing = ref(false)
const error = ref(null)
// Separate from `error`: a failed slider refresh must keep the slider visible so the user can retry.
const initError = ref(false)

const placing = ref(false)
const placedOrder = ref(null)
const orderError = ref(null)

// --- AI recommendations panel (shares the slider's budget, own order flow) ---
const aiPlan = ref(null)
const aiLoading = ref(false)
const aiError = ref(null)
const aiPlacing = ref(false)
const aiPlacedOrder = ref(null)
const aiOrderError = ref(null)
// Same out-of-order guard as requestSeq: LLM calls are slow, so a second click
// must not let the first (older) response overwrite the newer plan.
let aiRequestSeq = 0

const aiItems = computed(() => aiPlan.value?.items ?? [])

// The slider can move after a plan is generated; the plan (and its order) stays
// tied to the budget it was generated for, so flag the mismatch instead of
// silently re-running a paid model call on every slider change.
const aiBudgetChanged = computed(() => aiPlan.value !== null && aiPlan.value.budget !== budget.value)
const canPlaceAIOrder = computed(() =>
  aiItems.value.length > 0 && !aiPlacing.value && !aiLoading.value && !aiPlacedOrder.value
)

const extractDetail = (err, fallback) => {
  const detail = err.response?.data?.detail
  return typeof detail === 'string' && detail ? detail : fallback
}

const formatDaysOfCover = (value) =>
  value === null || value === undefined || !Number.isFinite(value) ? t('restocking.ai.noValue') : Math.round(value).toLocaleString()

const generateAI = async () => {
  const seq = ++aiRequestSeq
  aiLoading.value = true
  aiError.value = null
  aiPlacedOrder.value = null
  aiOrderError.value = null
  // Clear the old plan: it must not be orderable while a new one is being generated.
  aiPlan.value = null
  try {
    const data = await api.getAIRestockRecommendations({ budget: budget.value })
    if (seq !== aiRequestSeq) return
    aiPlan.value = data
  } catch (err) {
    if (seq !== aiRequestSeq) return
    // 422 detail is an array of validation objects; show a generic message instead.
    aiError.value = err.response?.status === 422
      ? t('restocking.ai.invalidBudgetResponse')
      : extractDetail(err, t('restocking.ai.error'))
    console.error('AI restock recommendations error:', err)
  } finally {
    if (seq === aiRequestSeq) aiLoading.value = false
  }
}

const placeAIOrder = async () => {
  if (!canPlaceAIOrder.value) return
  const plan = aiPlan.value
  aiPlacing.value = true
  aiOrderError.value = null
  try {
    aiPlacedOrder.value = await api.createRestockOrder({
      // The budget the plan was generated for, not the slider's current value.
      budget: plan.budget,
      items: plan.items.map(i => ({ sku: i.sku, quantity: i.quantity }))
    })
  } catch (err) {
    aiOrderError.value = err.response?.status === 422 && Array.isArray(err.response?.data?.detail)
      ? err.response.data.detail.map(d => d.msg).join('; ')
      : extractDetail(err, t('restocking.ai.orderError'))
  } finally {
    aiPlacing.value = false
  }
}

let debounceTimer = null
// Monotonic id so only the latest request may write state; slider drags can
// make responses arrive out of order and show a stale budget's items.
let requestSeq = 0

const items = computed(() => recommendation.value?.items ?? [])

// Longest lead time bounds the whole order, since items ship in parallel.
const estimatedDeliveryDays = computed(() =>
  items.value.reduce((max, item) => Math.max(max, item.lead_time_days), 0)
)

// Block ordering while a debounce or fetch is pending so the user can't submit
// a list that no longer matches the slider position.
const canPlaceOrder = computed(() =>
  items.value.length > 0 && !placing.value && !refreshing.value && !error.value
)

// Budget label is whole-currency; money amounts use 2 decimals so a 3.20 unit
// cost doesn't render as "$3" beside a 320.00 line total.
const fmt = (amount) => formatCurrency(amount, currentCurrency.value)
const fmtExact = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)

const formatDate = (dateString) => {
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

const fetchRecommendations = async (value) => {
  const seq = ++requestSeq
  refreshing.value = true
  try {
    const data = await api.getRestockRecommendations(value)
    if (seq !== requestSeq) return
    recommendation.value = data
    error.value = null
  } catch (err) {
    if (seq !== requestSeq) return
    error.value = t('restocking.loadError')
    // Drop the old list: it belongs to a different budget and must not be orderable.
    recommendation.value = null
    console.error('Restock recommendations error:', err)
  } finally {
    if (seq === requestSeq) refreshing.value = false
  }
}

const onBudgetInput = () => {
  placedOrder.value = null
  orderError.value = null
  // Mark as refreshing immediately so Place Order is disabled during debounce.
  refreshing.value = true
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => fetchRecommendations(budget.value), DEBOUNCE_MS)
}

const init = async () => {
  try {
    loading.value = true
    // Trend lives in the demand forecast data, not the recommendation payload.
    const [probe, forecasts] = await Promise.all([
      api.getRestockRecommendations(0),
      api.getDemandForecasts().catch(() => [])
    ])
    trendBySku.value = Object.fromEntries(forecasts.map(f => [f.item_sku, f.trend]))
    // Round up so the slider can always reach the full max_useful_budget.
    sliderMax.value = Math.ceil(probe.max_useful_budget / STEP) * STEP
    budget.value = Math.floor(sliderMax.value / 2 / STEP) * STEP
    await fetchRecommendations(budget.value)
  } catch (err) {
    error.value = t('restocking.loadError')
    initError.value = true
    console.error('Restocking init error:', err)
  } finally {
    loading.value = false
  }
}

const placeOrder = async () => {
  if (!canPlaceOrder.value) return
  placing.value = true
  orderError.value = null
  placedOrder.value = null
  try {
    placedOrder.value = await api.createRestockOrder({
      budget: recommendation.value.budget,
      items: items.value.map(i => ({ sku: i.sku, quantity: i.quantity }))
    })
  } catch (err) {
    const detail = err.response?.data?.detail
    // 422 detail can be an array of validation objects; flatten to readable text.
    orderError.value = Array.isArray(detail)
      ? detail.map(d => d.msg).join('; ')
      : (detail || t('restocking.orderError'))
  } finally {
    placing.value = false
  }
}

onMounted(init)
onBeforeUnmount(() => clearTimeout(debounceTimer))
</script>

<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="initError" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget.title') }}</h3>
        </div>
        <div class="budget-body">
          <div class="budget-value">
            <span class="budget-label">{{ t('restocking.budget.selected') }}</span>
            <strong>{{ fmt(budget) }}</strong>
          </div>
          <input
            v-model.number="budget"
            type="range"
            class="budget-slider"
            min="0"
            :max="sliderMax"
            :step="STEP"
            :aria-label="t('restocking.budget.selected')"
            @input="onBudgetInput"
          />
          <div class="budget-scale">
            <span>{{ fmt(0) }}</span>
            <span>{{ t('restocking.budget.max') }}: {{ fmt(sliderMax) }}</span>
          </div>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div v-if="recommendation" class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.totalCost') }}</div>
          <div class="stat-value">{{ fmtExact(recommendation.total_cost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.remainingBudget') }}</div>
          <div class="stat-value">{{ fmtExact(recommendation.remaining_budget) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.summary.estimatedDelivery') }}</div>
          <div class="stat-value">{{ items.length ? t('restocking.days', { count: estimatedDeliveryDays }) : '-' }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header header-row">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ items.length }})</h3>
          <button
            type="button"
            class="place-order-btn"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="placedOrder" class="notice notice-success" role="status">
          {{ t('restocking.orderPlaced', { orderNumber: placedOrder.order_number }) }}
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </div>
        <div v-if="orderError" class="notice notice-error" role="alert">{{ orderError }}</div>

        <div v-if="items.length === 0" class="empty-state">
          {{ sliderMax === 0 ? t('restocking.noGaps') : t('restocking.empty') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>
                  <span v-if="trendBySku[item.sku]" :class="['badge', trendBySku[item.sku]]">
                    {{ t(`trends.${trendBySku[item.sku]}`) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td class="num">{{ item.quantity.toLocaleString() }}</td>
                <td class="num">{{ fmtExact(item.unit_cost) }}</td>
                <td class="num"><strong>{{ fmtExact(item.line_total) }}</strong></td>
                <td class="num">{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card ai-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.ai.title') }}</h3>
          <p v-if="aiPlan" class="ai-note">{{ t('restocking.ai.note', { model: aiPlan.model }) }}</p>
        </div>

        <div class="ai-controls">
          <span class="ai-budget">{{ t('restocking.ai.usesBudget', { amount: fmt(budget) }) }}</span>
          <button type="button" class="place-order-btn" :disabled="aiLoading" @click="generateAI">
            {{ aiLoading ? t('restocking.ai.analyzing') : t('restocking.ai.generate') }}
          </button>
        </div>
        <div v-if="aiBudgetChanged" class="notice" role="status">
          {{ t('restocking.ai.budgetChanged', { amount: fmt(aiPlan.budget) }) }}
        </div>
        <div v-if="aiError" class="notice notice-error" role="alert">{{ aiError }}</div>

        <template v-if="aiPlan">
          <p v-if="aiPlan.summary" class="ai-summary">{{ aiPlan.summary }}</p>

          <div v-if="aiItems.length === 0" class="empty-state">{{ t('restocking.ai.empty') }}</div>
          <template v-else>
            <div class="table-container">
              <table>
                <thead>
                  <tr>
                    <th>{{ t('restocking.ai.table.sku') }}</th>
                    <th>{{ t('restocking.ai.table.name') }}</th>
                    <th class="num">{{ t('restocking.ai.table.onHand') }}</th>
                    <th class="num">{{ t('restocking.ai.table.reorderPoint') }}</th>
                    <th class="num">{{ t('restocking.ai.table.daysOfCover') }}</th>
                    <th class="num">{{ t('restocking.ai.table.quantity') }}</th>
                    <th class="num">{{ t('restocking.ai.table.lineTotal') }}</th>
                    <th>{{ t('restocking.ai.table.priority') }}</th>
                    <th class="ai-reason-col">{{ t('restocking.ai.table.reason') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in aiItems" :key="item.sku">
                    <td><strong>{{ item.sku }}</strong></td>
                    <td>{{ translateProductName(item.name) }}</td>
                    <td class="num">{{ item.quantity_on_hand.toLocaleString() }}</td>
                    <td class="num">{{ item.reorder_point.toLocaleString() }}</td>
                    <td class="num">{{ formatDaysOfCover(item.days_of_cover) }}</td>
                    <td class="num">{{ item.quantity.toLocaleString() }}</td>
                    <td class="num"><strong>{{ fmtExact(item.line_total) }}</strong></td>
                    <td>
                      <span :class="['badge', item.priority]">{{ t(`restocking.ai.priority.${item.priority}`) }}</span>
                    </td>
                    <td class="ai-reason">{{ item.reason }}</td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr>
                    <td colspan="6" class="num"><strong>{{ t('restocking.ai.total') }}</strong></td>
                    <td class="num"><strong>{{ fmtExact(aiPlan.total_cost) }}</strong></td>
                    <td colspan="2"></td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div class="ai-footer">
              <button type="button" class="place-order-btn" :disabled="!canPlaceAIOrder" @click="placeAIOrder">
                {{ aiPlacing ? t('restocking.ai.placing') : t('restocking.ai.placeOrder') }}
              </button>
            </div>
            <div v-if="aiPlacedOrder" class="notice notice-success" role="status">
              {{ t('restocking.ai.orderPlaced', { orderNumber: aiPlacedOrder.order_number }) }}
              <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
            </div>
            <div v-if="aiOrderError" class="notice notice-error" role="alert">{{ aiOrderError }}</div>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget-body {
  padding: 1rem 1.25rem 1.25rem;
}

.budget-value {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.budget-label {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 600;
}

.budget-value strong {
  font-size: 1.75rem;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.25rem;
  font-size: 0.813rem;
  color: #64748b;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.place-order-btn {
  padding: 0.5rem 1rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.num {
  text-align: right;
}

.notice {
  margin: 0.75rem 1.25rem;
  padding: 0.625rem 0.875rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.notice-success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.notice-success a {
  margin-left: 0.5rem;
  color: #166534;
  font-weight: 600;
}

.notice-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

.ai-card { margin-top: 1.5rem; }

.ai-note {
  margin: 0.25rem 0 0;
  font-size: 0.813rem;
  color: #64748b;
}

.ai-controls {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 1rem 1.25rem;
}

.ai-budget {
  font-size: 0.875rem;
  color: #64748b;
}

.ai-summary {
  margin: 0;
  padding: 0 1.25rem 1rem;
  color: #0f172a;
  line-height: 1.5;
}

/* Table scrolls horizontally on narrow screens instead of squeezing the reason text. */
.ai-card .table-container { overflow-x: auto; }

.ai-reason-col { min-width: 16rem; }

.ai-reason {
  min-width: 16rem;
  white-space: normal;
  color: #64748b;
}

.ai-card tfoot td { border-top: 2px solid #e2e8f0; }

.ai-footer {
  display: flex;
  justify-content: flex-end;
  padding: 1rem 1.25rem 0.5rem;
}

/* Spec asks for yellow medium; the global .badge.medium is orange. */
.badge.medium {
  background: #fef3c7;
  color: #92400e;
}
</style>
