<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const { t, currentCurrency, translateProductName } = useI18n()

const budget = ref(50000)
const data = ref(null)
const loading = ref(true)
const error = ref(null)

const submitting = ref(false)
const orderError = ref(null)
const confirmation = ref(null)

const money = (v) => formatCurrency(v, currentCurrency.value)
const unitMoney = (v) => formatCurrencyWithDecimals(v, currentCurrency.value, 2)

const items = computed(() => data.value?.items ?? [])
const canOrder = computed(() => items.value.length > 0 && !submitting.value && !loading.value)

// Monotonic request id: only the latest request may write state, so a slow
// earlier response can never overwrite a newer one while the slider is dragged.
let requestId = 0
let timer = null

const loadRecommendations = async () => {
  const id = ++requestId
  loading.value = true
  error.value = null
  try {
    const result = await api.getRestockRecommendations(budget.value)
    if (id !== requestId) return
    data.value = result
  } catch (err) {
    if (id !== requestId) return
    error.value = t('restocking.loadError')
    console.error('Restock load error:', err)
  } finally {
    if (id === requestId) loading.value = false
  }
}

// Debounce so dragging the slider doesn't fire a request per step.
watch(budget, () => {
  clearTimeout(timer)
  timer = setTimeout(loadRecommendations, 250)
})

onMounted(loadRecommendations)
onBeforeUnmount(() => {
  clearTimeout(timer)
  requestId++ // invalidate in-flight requests after unmount
})

const trendClass = (trend) => {
  const key = String(trend || '').toLowerCase()
  if (key === 'rising' || key === 'increasing') return 'increasing'
  if (key === 'decreasing' || key === 'falling') return 'decreasing'
  return 'stable'
}
const trendLabel = (trend) => {
  const key = String(trend || '').toLowerCase()
  const path = `restocking.trend.${key}`
  const label = t(path)
  return label === path ? trend : label // fall back to raw value for unknown trends
}

const placeOrder = async () => {
  if (!canOrder.value) return
  submitting.value = true
  orderError.value = null
  confirmation.value = null
  try {
    // Server recomputes prices; we only send what the user is looking at.
    const order = await api.createRestockOrder({
      budget: data.value.budget,
      items: items.value.map(i => ({ sku: i.sku, quantity: i.quantity }))
    })
    confirmation.value = order
    await loadRecommendations() // stock/recommendations may have changed
  } catch (err) {
    orderError.value = err.response?.data?.detail || t('restocking.orderError')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card budget-card">
      <div class="budget-label">{{ t('restocking.budget') }}</div>
      <div class="budget-value">{{ money(budget) }}</div>
      <input
        v-model.number="budget"
        type="range"
        min="0"
        max="500000"
        step="5000"
        class="budget-slider"
        :aria-label="t('restocking.budgetSlider')"
      />
      <div class="slider-scale"><span>{{ money(0) }}</span><span>{{ money(500000) }}</span></div>
    </div>

    <div v-if="confirmation" class="banner success" role="status">
      <div>
        <strong>{{ t('restocking.orderPlaced', { id: confirmation.id }) }}</strong>
        <span> {{ t('restocking.orderPlacedDetail', { days: confirmation.lead_time_days }) }}</span>
      </div>
      <router-link to="/orders" class="banner-link">{{ t('restocking.viewOrders') }}</router-link>
    </div>
    <div v-if="orderError" class="banner danger" role="alert">{{ orderError }}</div>

    <div v-if="loading && !data" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="data">
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ money(data.budget) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ money(data.total_cost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ money(data.remaining_budget) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.leadTime') }}</div>
          <div class="stat-value">{{ t('restocking.days', { count: data.lead_time_days }) }}</div>
        </div>
      </div>

      <div class="card" :class="{ stale: loading }">
        <div class="card-header header-row">
          <h3 class="card-title">
            {{ t('restocking.recommendedItems') }} ({{ items.length }})
            <span v-if="loading" class="updating">{{ t('restocking.updating') }}</span>
          </h3>
          <button class="place-order" :disabled="!canOrder" @click="placeOrder">
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="items.length === 0" class="empty">
          <strong>{{ t('restocking.emptyTitle') }}</strong>
          <p>{{ t('restocking.emptyHint') }}</p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.shortfall') }}</th>
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
                <td><span :class="['badge', trendClass(item.trend)]">{{ trendLabel(item.trend) }}</span></td>
                <td class="num">{{ item.shortfall.toLocaleString() }}</td>
                <td class="num">
                  {{ item.quantity.toLocaleString() }}
                  <span v-if="!item.fully_covered" class="badge warning partial">{{ t('restocking.partial') }}</span>
                </td>
                <td class="num">{{ unitMoney(item.unit_cost) }}</td>
                <td class="num"><strong>{{ money(item.total_cost) }}</strong></td>
                <td class="num">{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget-card { padding: 1.5rem; margin-bottom: 1.5rem; }
.budget-label { font-size: 0.875rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.budget-value { font-size: 2.5rem; font-weight: 700; color: #0f172a; margin: 0.25rem 0 1rem; }
.budget-slider { width: 100%; accent-color: #0f172a; cursor: pointer; }
.slider-scale { display: flex; justify-content: space-between; font-size: 0.813rem; color: #64748b; margin-top: 0.25rem; }
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 1rem; }
.updating { font-size: 0.813rem; font-weight: 400; color: #64748b; margin-left: 0.5rem; }
.stale { opacity: 0.6; transition: opacity 0.15s; }
.num { text-align: right; white-space: nowrap; }
.partial { margin-left: 0.5rem; }
.place-order {
  background: #0f172a; color: #fff; border: 1px solid #0f172a; border-radius: 6px;
  padding: 0.5rem 1.25rem; font-weight: 600; cursor: pointer;
}
.place-order:hover:not(:disabled) { background: #1e293b; }
.place-order:disabled { background: #e2e8f0; border-color: #e2e8f0; color: #64748b; cursor: not-allowed; }
.empty { padding: 2rem; text-align: center; color: #64748b; }
.empty strong { color: #0f172a; }
.banner {
  display: flex; justify-content: space-between; align-items: center; gap: 1rem;
  padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1.5rem; border: 1px solid;
}
.banner.success { background: #f0fdf4; border-color: #bbf7d0; color: #166534; }
.banner.danger { background: #fef2f2; border-color: #fecaca; color: #991b1b; }
.banner-link { color: inherit; font-weight: 600; text-decoration: underline; white-space: nowrap; }
</style>
