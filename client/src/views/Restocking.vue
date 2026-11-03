<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="loadError" class="error">{{ loadError }}</div>
    <div v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-value">{{ money(budget) }}</span>
        </div>
        <div class="budget-body">
          <input
            v-model.number="budget"
            type="range"
            class="budget-slider"
            :min="0"
            :max="MAX_BUDGET"
            :step="STEP"
            :aria-label="t('restocking.budget')"
          />
          <div class="budget-scale">
            <span>{{ money(0) }}</span>
            <span>{{ money(MAX_BUDGET) }}</span>
          </div>
          <p class="budget-hint">{{ t('restocking.budgetHint') }}</p>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ money(budget) }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.totalCost') }}</div>
          <div class="stat-value">{{ money(totalCost) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ money(remaining) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ t('restocking.itemsCount', { count: recommendations.length }) }})</h3>
          <button class="place-order-btn" :disabled="recommendations.length === 0 || submitting" @click="placeOrder">
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
        <div v-if="submitError" class="error">{{ submitError }}</div>

        <div v-if="recommendations.length === 0" class="loading">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th class="num">{{ t('restocking.table.forecastedDemand') }}</th>
                <th class="num">{{ t('restocking.table.quantity') }}</th>
                <th class="num">{{ t('restocking.table.unitCost') }}</th>
                <th class="num">{{ t('restocking.table.lineCost') }}</th>
                <th class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.id">
                <td>{{ item.item_sku }}</td>
                <td><strong>{{ translateProductName(item.item_name) }}</strong></td>
                <td>
                  <span :class="['badge', item.trend]">{{ t(`restocking.trend.${item.trend}`) }}</span>
                </td>
                <td class="num">{{ item.forecasted_demand.toLocaleString() }}</td>
                <td class="num">{{ item.quantity.toLocaleString() }}</td>
                <td class="num">{{ money(item.unit_cost) }}</td>
                <td class="num"><strong>{{ money(item.lineCost) }}</strong></td>
                <td class="num">{{ item.lead_time_days }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'

const MAX_BUDGET = 500000
const STEP = 5000

const { t, currentCurrency, translateProductName } = useI18n()

const forecasts = ref([])
const loading = ref(true)
const loadError = ref(null)
const budget = ref(100000) // USD internally
const submitting = ref(false)
const submitError = ref(null)
const successMessage = ref(null)

const money = (usd) => formatCurrency(usd, currentCurrency.value)

const recommendations = computed(() => {
  const ranked = forecasts.value
    .filter(i => i.trend !== 'decreasing')
    .map(i => ({ ...i, growth: i.forecasted_demand - i.current_demand }))
    .sort((a, b) => b.growth - a.growth)

  let remainingBudget = budget.value
  const picked = []
  for (const item of ranked) {
    const quantity = item.forecasted_demand
    const lineCost = quantity * item.unit_cost
    if (quantity > 0 && lineCost <= remainingBudget) {
      picked.push({ ...item, quantity, lineCost })
      remainingBudget -= lineCost
    }
  }
  return picked
})

const totalCost = computed(() => recommendations.value.reduce((sum, i) => sum + i.lineCost, 0))
const remaining = computed(() => budget.value - totalCost.value)

const loadForecasts = async () => {
  loading.value = true
  loadError.value = null
  try {
    forecasts.value = await api.getDemandForecasts()
  } catch (err) {
    loadError.value = t('restocking.loadError')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const placeOrder = async () => {
  if (recommendations.value.length === 0 || submitting.value) return
  submitting.value = true
  submitError.value = null
  successMessage.value = null
  try {
    const order = await api.createRestockingOrder({
      budget: budget.value,
      items: recommendations.value.map(i => ({
        sku: i.item_sku,
        name: i.item_name,
        quantity: i.quantity,
        unit_cost: i.unit_cost,
        lead_time_days: i.lead_time_days
      }))
    })
    successMessage.value = t('restocking.successMessage', {
      orderNumber: order.order_number,
      days: order.lead_time_days
    })
  } catch (err) {
    const detail = err.response?.data?.detail
    submitError.value = `${t('restocking.errorMessage')}${typeof detail === 'string' ? ': ' + detail : ''}`
    console.error(err)
  } finally {
    submitting.value = false
  }
}

onMounted(loadForecasts)
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.5rem;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text);
}

.budget-body {
  padding: 0.5rem 1rem 1rem;
}

.budget-slider {
  width: 100%;
  accent-color: #3b82f6;
  cursor: pointer;
}

.budget-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.budget-hint {
  margin-top: 0.5rem;
  font-size: 0.813rem;
  color: var(--text-muted);
}

.stats-grid {
  margin-bottom: 1.5rem;
}

.num {
  text-align: right;
}

.place-order-btn {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--accent-hover);
}

.place-order-btn:disabled {
  background: var(--border-strong);
  cursor: not-allowed;
}

.success-message {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem;
  font-size: 0.938rem;
}
</style>
