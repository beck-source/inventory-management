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

const PRESETS = [
  { key: 'quarter', pct: 0.25 },
  { key: 'half', pct: 0.5 },
  { key: 'threeQuarters', pct: 0.75 },
  { key: 'max', pct: 1 }
]
const presetValue = (pct) => Math.round(sliderMax.value * pct / STEP) * STEP

// Single entry point for slider, number input and presets so every path clamps,
// snaps to STEP and triggers the same debounce/seq/placedOrder reset.
const setBudget = (raw) => {
  // Number('') is 0, which would silently zero the budget on an empty field.
  if (raw === '' || raw === null || raw === undefined) return false
  const n = Number(raw)
  if (!Number.isFinite(n)) return false
  const next = Math.min(sliderMax.value, Math.max(0, Math.round(n / STEP) * STEP))
  if (next === budget.value) return true
  budget.value = next
  onBudgetInput()
  return true
}

// Commit on change/blur (not per keystroke) so partial typing like "1" doesn't fire requests;
// always rewrite the DOM value because a clamped/unchanged budget won't re-render the input.
const commitBudgetInput = (event) => {
  setBudget(event.target.value)
  event.target.value = budget.value
}

const activePreset = computed(() =>
  PRESETS.find(p => presetValue(p.pct) === budget.value)?.key ?? null
)

// total_cost can never exceed the budget server-side, but guard budget 0 and clamp defensively.
const utilizationPercent = computed(() => {
  const r = recommendation.value
  if (!r || !r.budget) return 0
  return Math.min(100, Math.max(0, Math.round((r.total_cost / r.budget) * 100)))
})

const orderHint = computed(() => {
  if (refreshing.value) return t('restocking.updatingHint')
  if (items.value.length === 0) return t('restocking.noItemsHint')
  return ''
})

// Text for the visually-hidden live region.
const aiStatus = computed(() => {
  if (aiLoading.value) return t('restocking.ai.loadingStatus')
  if (aiError.value) return aiError.value
  if (aiPlan.value) {
    return t('restocking.ai.readyStatus', { count: aiItems.value.length, amount: fmtExact(aiPlan.value.total_cost) })
  }
  return ''
})

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
            :value="budget"
            type="range"
            class="budget-slider"
            min="0"
            :max="sliderMax"
            :step="STEP"
            :aria-label="t('restocking.budget.selected')"
            :aria-valuetext="fmt(budget)"
            @input="setBudget($event.target.value)"
          />
          <div class="budget-scale">
            <span>{{ fmt(0) }}</span>
            <span>{{ t('restocking.budget.max') }}: {{ fmt(sliderMax) }}</span>
          </div>
          <div class="budget-controls">
            <input
              :value="budget"
              type="number"
              class="budget-number"
              min="0"
              :max="sliderMax"
              :step="STEP"
              inputmode="numeric"
              :aria-label="t('restocking.budget.input')"
              @change="commitBudgetInput"
            />
            <div class="preset-group">
              <button
                v-for="p in PRESETS"
                :key="p.key"
                type="button"
                class="btn btn-secondary"
                :aria-pressed="activePreset === p.key"
                @click="setBudget(presetValue(p.pct))"
              >
                {{ t(`restocking.budget.presets.${p.key}`) }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <template v-if="recommendation">
        <div class="stats-grid">
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

        <div class="utilization">
          <div
            class="meter-track"
            role="meter"
            :aria-valuenow="utilizationPercent"
            aria-valuemin="0"
            aria-valuemax="100"
            :aria-valuetext="t('restocking.budget.utilization', { percent: utilizationPercent })"
            :aria-label="t('restocking.budget.utilization', { percent: utilizationPercent })"
          >
            <div
              :class="['meter-fill', utilizationPercent >= 90 ? 'meter-warn' : 'meter-ok']"
              :style="{ width: utilizationPercent + '%' }"
            ></div>
          </div>
          <span class="meter-label">{{ t('restocking.budget.utilization', { percent: utilizationPercent }) }}</span>
        </div>
      </template>

      <div class="card">
        <div class="card-header header-row">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ items.length }})</h3>
          <div class="action-group">
            <span v-if="orderHint" id="place-order-hint" class="hint">{{ orderHint }}</span>
            <button
              type="button"
              class="btn btn-primary"
              :disabled="!canPlaceOrder"
              :aria-describedby="orderHint ? 'place-order-hint' : null"
              @click="placeOrder"
            >
              {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
            </button>
          </div>
        </div>

        <div v-if="placedOrder" class="notice notice-success" role="status">
          {{ t('restocking.orderPlaced', { orderNumber: placedOrder.order_number }) }}
          <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
        </div>
        <div v-if="orderError" class="notice notice-error" role="alert">{{ orderError }}</div>

        <div v-if="items.length === 0" class="empty-state">
          {{ sliderMax === 0 ? t('restocking.noGaps') : t('restocking.empty') }}
        </div>
        <div v-else :class="['table-container', { 'is-refreshing': refreshing }]" :aria-busy="refreshing">
          <!-- Explicit roles: the mobile card layout uses display:block, which strips native table semantics. -->
          <table class="stack-table" role="table">
            <thead role="rowgroup">
              <tr role="row">
                <th role="columnheader">{{ t('restocking.table.sku') }}</th>
                <th role="columnheader">{{ t('restocking.table.name') }}</th>
                <th role="columnheader">{{ t('restocking.table.trend') }}</th>
                <th role="columnheader" class="num">{{ t('restocking.table.quantity') }}</th>
                <th role="columnheader" class="num">{{ t('restocking.table.unitCost') }}</th>
                <th role="columnheader" class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th role="columnheader" class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody role="rowgroup">
              <tr v-for="item in items" :key="item.sku" role="row">
                <td role="cell" class="c-sku" :data-label="t('restocking.table.sku')"><strong>{{ item.sku }}</strong></td>
                <td role="cell" class="c-name" :data-label="t('restocking.table.name')">{{ translateProductName(item.name) }}</td>
                <td role="cell" class="c-badge" :data-label="t('restocking.table.trend')">
                  <span v-if="trendBySku[item.sku]" :class="['badge', trendBySku[item.sku]]">
                    {{ t(`trends.${trendBySku[item.sku]}`) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td role="cell" class="num" :data-label="t('restocking.table.quantity')">{{ item.quantity.toLocaleString() }}</td>
                <td role="cell" class="num" :data-label="t('restocking.table.unitCost')">{{ fmtExact(item.unit_cost) }}</td>
                <td role="cell" class="num" :data-label="t('restocking.table.lineTotal')"><strong>{{ fmtExact(item.line_total) }}</strong></td>
                <td role="cell" class="num" :data-label="t('restocking.table.leadTime')">{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card ai-card" :aria-busy="aiLoading">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.ai.title') }}</h3>
        </div>

        <div class="ai-controls">
          <span class="ai-budget">{{ t('restocking.ai.usesBudget', { amount: fmt(budget) }) }}</span>
          <button type="button" class="btn btn-primary" :disabled="aiLoading" @click="generateAI">
            <span v-if="aiLoading" class="spinner" aria-hidden="true"></span>
            {{ aiLoading ? t('restocking.ai.analyzing') : t('restocking.ai.generate') }}
          </button>
        </div>
        <p v-if="aiPlan" class="ai-note">{{ t('restocking.ai.note', { model: aiPlan.model }) }}</p>

        <!-- Announces progress/result to screen readers; the visual states are the skeleton and table. -->
        <div class="sr-only" aria-live="polite" role="status">{{ aiStatus }}</div>

        <div v-if="aiError" class="notice notice-error" role="alert">{{ aiError }}</div>

        <div v-if="aiLoading" class="skeleton-list" aria-hidden="true">
          <div v-for="n in 4" :key="n" class="skeleton-row"></div>
        </div>

        <template v-if="aiPlan">
          <p v-if="aiPlan.summary" class="ai-summary">{{ aiPlan.summary }}</p>

          <div v-if="aiItems.length === 0" class="empty-state">{{ t('restocking.ai.empty') }}</div>
          <template v-else>
            <div v-if="aiBudgetChanged" class="notice" role="status">
              {{ t('restocking.ai.budgetChanged', { amount: fmt(aiPlan.budget) }) }}
            </div>
            <div class="table-container">
              <table class="stack-table ai-table" role="table">
                <thead role="rowgroup">
                  <tr role="row">
                    <th role="columnheader">{{ t('restocking.ai.table.sku') }}</th>
                    <th role="columnheader">{{ t('restocking.ai.table.name') }}</th>
                    <th role="columnheader" class="num">{{ t('restocking.ai.table.onHand') }}</th>
                    <th role="columnheader" class="num">{{ t('restocking.ai.table.reorderPoint') }}</th>
                    <th role="columnheader" class="num">{{ t('restocking.ai.table.daysOfCover') }}</th>
                    <th role="columnheader" class="num">{{ t('restocking.ai.table.quantity') }}</th>
                    <th role="columnheader" class="num">{{ t('restocking.ai.table.lineTotal') }}</th>
                    <th role="columnheader">{{ t('restocking.ai.table.priority') }}</th>
                    <th role="columnheader" class="ai-reason-col">{{ t('restocking.ai.table.reason') }}</th>
                  </tr>
                </thead>
                <tbody role="rowgroup">
                  <tr v-for="item in aiItems" :key="item.sku" role="row">
                    <td role="cell" class="c-sku" :data-label="t('restocking.ai.table.sku')"><strong>{{ item.sku }}</strong></td>
                    <td role="cell" class="c-name" :data-label="t('restocking.ai.table.name')">{{ translateProductName(item.name) }}</td>
                    <td role="cell" class="num" :data-label="t('restocking.ai.table.onHand')">{{ item.quantity_on_hand.toLocaleString() }}</td>
                    <td role="cell" class="num" :data-label="t('restocking.ai.table.reorderPoint')">{{ item.reorder_point.toLocaleString() }}</td>
                    <td role="cell" class="num" :data-label="t('restocking.ai.table.daysOfCover')">{{ formatDaysOfCover(item.days_of_cover) }}</td>
                    <td role="cell" class="num" :data-label="t('restocking.ai.table.quantity')">{{ item.quantity.toLocaleString() }}</td>
                    <td role="cell" class="num" :data-label="t('restocking.ai.table.lineTotal')"><strong>{{ fmtExact(item.line_total) }}</strong></td>
                    <td role="cell" class="c-badge" :data-label="t('restocking.ai.table.priority')">
                      <span :class="['badge', item.priority]">{{ t(`restocking.ai.priority.${item.priority}`) }}</span>
                    </td>
                    <td role="cell" class="ai-reason" :data-label="t('restocking.ai.table.reason')">{{ item.reason }}</td>
                  </tr>
                </tbody>
                <tfoot role="rowgroup">
                  <tr role="row" class="tfoot-row">
                    <td role="cell" colspan="6" class="num tfoot-label"><strong>{{ t('restocking.ai.total') }}</strong></td>
                    <td role="cell" class="num"><strong>{{ fmtExact(aiPlan.total_cost) }}</strong></td>
                    <td role="cell" colspan="2" class="tfoot-spacer"></td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <div class="ai-footer">
              <button type="button" class="btn btn-primary" :disabled="!canPlaceAIOrder" @click="placeAIOrder">
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
  font-variant-numeric: tabular-nums;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.budget-slider:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 4px;
  border-radius: 4px;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 0.25rem;
  font-size: 0.813rem;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.budget-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
}

.budget-number {
  width: 9rem;
  padding: 0.5rem 0.625rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #0f172a;
  font-variant-numeric: tabular-nums;
}

.budget-number:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 1px;
}

.preset-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.utilization {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
  margin: -0.5rem 0 1.5rem;
}

.meter-track {
  flex: 1 1 12rem;
  height: 6px;
  background: #e2e8f0;
  border-radius: 999px;
  overflow: hidden;
}

.meter-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.2s ease;
}

.meter-ok { background: #16a34a; }
.meter-warn { background: #eab308; }

.meter-label {
  font-size: 0.813rem;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
}

.action-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem 0.75rem;
}

.hint {
  font-size: 0.813rem;
  color: #64748b;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid transparent;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}

.btn:disabled {
  cursor: not-allowed;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #cbd5e1;
}

.btn-secondary {
  background: white;
  color: #0f172a;
  border-color: #e2e8f0;
}

.btn-secondary:hover:not(:disabled) {
  background: #f1f5f9;
}

.btn-secondary[aria-pressed='true'] {
  background: #0f172a;
  border-color: #0f172a;
  color: white;
}

.spinner {
  width: 0.875rem;
  height: 0.875rem;
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.c-sku { white-space: nowrap; }

.stat-value { font-variant-numeric: tabular-nums; }

.table-container.is-refreshing tbody tr {
  opacity: 0.5;
  transition: opacity 0.15s ease;
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
  margin: 0;
  padding: 0 1.25rem 0.75rem;
  font-size: 0.813rem;
  color: #64748b;
}

.ai-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 1rem 1.25rem;
}

.ai-budget {
  font-size: 0.875rem;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}

.ai-summary {
  margin: 0;
  padding: 0 1.25rem 1rem;
  color: #0f172a;
  line-height: 1.5;
}

.skeleton-list {
  display: grid;
  gap: 0.75rem;
  padding: 0.5rem 1.25rem 1.25rem;
}

.skeleton-row {
  height: 2.5rem;
  border-radius: 6px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s ease-in-out infinite;
}

@keyframes shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .skeleton-row { animation: none; }
  .spinner { animation-duration: 2.4s; }
  .meter-fill, .table-container.is-refreshing tbody tr { transition: none; }
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

/* Mobile: each row becomes a card. display:block/grid strips native table roles,
   hence the explicit role attributes in the template. */
@media (max-width: 639px) {
  .stack-table,
  .stack-table tbody,
  .stack-table tfoot {
    display: block;
    width: 100%;
  }

  /* Visually hidden (not display:none) so column headers stay in the a11y tree. */
  .stack-table thead {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
  }

  .stack-table tbody tr {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem 1rem;
    padding: 0.875rem 1rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .stack-table tbody td {
    display: block;
    padding: 0;
    border: none;
    text-align: left;
    min-width: 0;
  }

  .stack-table tbody td::before {
    content: attr(data-label);
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 0.125rem;
  }

  /* Head of the card: SKU left, badge right, name below; no labels needed there. */
  .stack-table td.c-sku { grid-column: 1; grid-row: 1; }
  .stack-table td.c-badge { grid-column: 2; grid-row: 1; justify-self: end; }
  .stack-table td.c-name { grid-column: 1 / -1; grid-row: 2; }
  .stack-table td.c-sku::before,
  .stack-table td.c-name::before,
  .stack-table td.c-badge::before { display: none; }

  .stack-table td.num { text-align: left; }

  .stack-table td.ai-reason {
    grid-column: 1 / -1;
    min-width: 0;
  }

  .stack-table tfoot tr {
    display: flex;
    justify-content: space-between;
    padding: 0.875rem 1rem;
  }

  .stack-table tfoot td {
    display: block;
    padding: 0;
    border-top: none;
  }

  .stack-table tfoot td.tfoot-spacer { display: none; }
  .ai-card tfoot tr { border-top: 2px solid #e2e8f0; }
  .ai-card tfoot td { border-top: none; }

  .ai-footer .btn,
  .action-group .btn { width: 100%; }
  .action-group { width: 100%; }
}
</style>
