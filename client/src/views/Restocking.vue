<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const { t, currentCurrency, translateProductName } = useI18n()

// Slider is always in USD; formatCurrency converts for display
const budget = ref(10000)
const recommendation = ref(null)
const loading = ref(true)
const error = ref(null)
const submitting = ref(false)
const orderError = ref(null)
const placedOrder = ref(null)

const items = computed(() => recommendation.value?.items ?? [])
const fmt = (usd) => formatCurrency(usd, currentCurrency.value)
const days = (n) => t('restocking.days', { count: n })

// Each request gets an id; only the latest one may update state, so a slow
// response for an old slider value cannot overwrite a newer result.
let requestId = 0
let debounceTimer = null

const loadRecommendations = async () => {
  const id = ++requestId
  loading.value = true
  error.value = null
  try {
    const data = await api.getRestockRecommendations(budget.value)
    if (id !== requestId) return
    recommendation.value = data
  } catch (err) {
    if (id !== requestId) return
    error.value = t('restocking.failedToLoad') + ': ' + (err.response?.data?.detail || err.message)
    recommendation.value = null
  } finally {
    if (id === requestId) loading.value = false
  }
}

// Debounce while dragging; a previous order's banner no longer matches the new budget
const onBudgetInput = () => {
  placedOrder.value = null
  orderError.value = null
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadRecommendations, 250)
}

const placeOrder = async () => {
  if (!items.value.length || submitting.value) return
  submitting.value = true
  orderError.value = null
  placedOrder.value = null
  try {
    placedOrder.value = await api.createRestockOrder({
      budget: budget.value,
      items: items.value.map(i => ({
        sku: i.sku,
        name: i.name,
        quantity: i.quantity,
        unit_cost: i.unit_cost
      }))
    })
  } catch (err) {
    orderError.value = t('restocking.failedToOrder') + ': ' + (err.response?.data?.detail || err.message)
  } finally {
    submitting.value = false
  }
}

onMounted(loadRecommendations)
onBeforeUnmount(() => clearTimeout(debounceTimer))
</script>

<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="budget-row">
        <label for="budget-slider" class="budget-label">{{ t('restocking.budget') }}</label>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          min="0"
          max="30000"
          step="500"
          class="budget-slider"
          @input="onBudgetInput"
        />
        <span class="budget-value">{{ fmt(budget) }}</span>
      </div>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
        <button
          class="place-order-btn"
          :disabled="!items.length || submitting"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
      </div>

      <div v-if="placedOrder" class="success">
        {{ t('restocking.orderPlaced', { orderNumber: placedOrder.order_number }) }}
        <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="orderError" class="error">{{ orderError }}</div>

      <div v-if="loading && !recommendation" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="recommendation && !items.length" class="empty">{{ t('restocking.empty') }}</div>
      <div v-else-if="recommendation" class="table-container" :class="{ stale: loading }">
        <table>
          <thead>
            <tr>
              <th>{{ t('restocking.table.item') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th class="num">{{ t('restocking.table.onHand') }}</th>
              <th class="num">{{ t('restocking.table.forecast') }}</th>
              <th class="num">{{ t('restocking.table.shortfall') }}</th>
              <th class="num">{{ t('restocking.table.quantity') }}</th>
              <th class="num">{{ t('restocking.table.unitCost') }}</th>
              <th class="num">{{ t('restocking.table.lineTotal') }}</th>
              <th class="num">{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.sku">
              <td>
                <strong>{{ item.sku }}</strong>
                <div class="item-name">{{ translateProductName(item.name) }}</div>
              </td>
              <td>
                <span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span>
              </td>
              <td class="num">{{ item.quantity_on_hand }}</td>
              <td class="num">{{ item.forecasted_demand }}</td>
              <td class="num">{{ item.shortfall }}</td>
              <td class="num"><strong>{{ item.quantity }}</strong></td>
              <td class="num">{{ fmt(item.unit_cost) }}</td>
              <td class="num"><strong>{{ fmt(item.line_total) }}</strong></td>
              <td class="num">{{ days(item.lead_time_days) }}</td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td colspan="9">
                <div class="totals">
                  <span>{{ t('restocking.totalCost') }}: <strong>{{ fmt(recommendation.total_cost) }}</strong></span>
                  <span>{{ t('restocking.remainingBudget') }}: <strong>{{ fmt(recommendation.remaining_budget) }}</strong></span>
                  <span>{{ t('restocking.overallLeadTime') }}: <strong>{{ days(recommendation.lead_time_days) }}</strong></span>
                </div>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.budget-slider {
  flex: 1;
  accent-color: #2563eb;
}

.budget-value {
  min-width: 110px;
  text-align: right;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
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

.success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.938rem;
}

.success a {
  color: #2563eb;
  font-weight: 600;
  margin-left: 0.5rem;
}

.empty {
  text-align: center;
  padding: 3rem;
  color: #64748b;
  font-size: 0.938rem;
}

.stale {
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.num {
  text-align: right;
  white-space: nowrap;
}

.item-name {
  color: #64748b;
  font-size: 0.813rem;
}

tfoot td {
  background: #f8fafc;
  border-top: 2px solid #e2e8f0;
}

.totals {
  display: flex;
  justify-content: flex-end;
  gap: 2rem;
  color: #475569;
}

.totals strong {
  color: #0f172a;
}
</style>
