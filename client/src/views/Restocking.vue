<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

const { t, currentCurrency, translateProductName } = useI18n()

const STEP = 500
const DEBOUNCE_MS = 250

const loading = ref(true)
const error = ref(null)
const budget = ref(0)
const maxBudget = ref(0)
const recommendation = ref({ total_cost: 0, remaining: 0, items: [] })

const submitting = ref(false)
const orderSuccess = ref(null)
const orderError = ref(null)

let debounceTimer = null
// Monotonic id so a slow earlier response never overwrites a newer one
let requestSeq = 0

const items = computed(() => recommendation.value.items || [])
const money = (amount) => formatCurrency(amount, currentCurrency.value)
// Unit costs like $12.50 would round to $13 with no decimals, making qty x cost look wrong
const moneyExact = (amount) => formatCurrencyWithDecimals(amount, currentCurrency.value, 2)
const canOrder = computed(() => items.value.length > 0 && !submitting.value)

const fetchRecommendations = async () => {
  const seq = ++requestSeq
  try {
    const data = await api.getRestockRecommendations(budget.value)
    if (seq !== requestSeq) return // stale response, a newer request is in flight
    recommendation.value = data
    // max_budget is fixed server-side, so only the first response needs to set it
    if (maxBudget.value === 0) maxBudget.value = data.max_budget
    error.value = null
  } catch (err) {
    if (seq !== requestSeq) return
    error.value = t('restocking.loadFailed')
    console.error('Restocking load error:', err)
  } finally {
    if (seq === requestSeq) loading.value = false
  }
}

const onBudgetInput = () => {
  // Any budget change invalidates the previous order result message
  orderSuccess.value = null
  orderError.value = null
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchRecommendations, DEBOUNCE_MS)
}

const placeOrder = async () => {
  if (!canOrder.value) return
  submitting.value = true
  orderSuccess.value = null
  orderError.value = null
  // Flush any pending debounce so the order matches what the slider shows
  clearTimeout(debounceTimer)
  try {
    const order = await api.placeRestockOrder(budget.value)
    orderSuccess.value = t('restocking.orderPlaced', { id: order.id, days: order.lead_time_days })
  } catch (err) {
    orderError.value = err.response?.data?.detail || t('restocking.orderFailed')
  } finally {
    submitting.value = false
  }
}

const trendClass = (trend) => (['increasing', 'stable', 'decreasing'].includes(trend) ? trend : 'info')

onMounted(fetchRecommendations)
onBeforeUnmount(() => clearTimeout(debounceTimer))
</script>

<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error && maxBudget === 0" class="error">{{ error }}</div>
    <div v-else>
      <div class="card budget-card">
        <label class="budget-label" for="restock-budget">{{ t('restocking.budgetSlider') }}</label>
        <input
          id="restock-budget"
          v-model.number="budget"
          class="budget-slider"
          type="range"
          min="0"
          :max="maxBudget"
          :step="STEP"
          :disabled="maxBudget === 0"
          @input="onBudgetInput"
        />
        <div class="budget-scale">
          <span>{{ money(0) }}</span>
          <span>{{ money(maxBudget) }}</span>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ money(budget) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ money(recommendation.total_cost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ money(recommendation.remaining) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ items.length }})</h3>
          <button class="place-order-btn" type="button" :disabled="!canOrder" @click="placeOrder">
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="orderSuccess" class="order-message order-success" role="status">{{ orderSuccess }}</div>
        <div v-if="orderError" class="order-message order-error" role="alert">{{ orderError }}</div>

        <div v-if="items.length === 0" class="empty-state">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.supplier') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td>
                  <span :class="['badge', trendClass(item.trend)]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.supplier }}</td>
                <td class="num">{{ item.quantity.toLocaleString() }}</td>
                <td class="num">{{ moneyExact(item.unit_cost) }}</td>
                <td class="num"><strong>{{ moneyExact(item.line_cost) }}</strong></td>
                <td class="num">{{ t('restocking.days', { days: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
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

.budget-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 0.75rem;
}

.budget-slider {
  width: 100%;
  accent-color: #0f172a;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.num {
  text-align: right;
}

.place-order-btn {
  background: var(--color-text);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  height: var(--control-height);
  padding: 0 var(--space-4);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--color-text-secondary);
}

.place-order-btn:disabled {
  background: #e2e8f0;
  color: #64748b;
  cursor: not-allowed;
}

.order-message {
  margin: 0 1.5rem 1rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.order-success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.order-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.empty-state {
  padding: 2rem 1.5rem;
  text-align: center;
  color: #64748b;
}
</style>
