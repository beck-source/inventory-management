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
          <span class="budget-amount">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          min="0"
          :max="maxBudget"
          step="500"
          class="budget-slider"
        />
        <div class="budget-summary">
          <div>
            <div class="summary-label">{{ t('restocking.selectedTotal') }}</div>
            <div class="summary-value">{{ currencySymbol }}{{ selectedTotal.toLocaleString() }}</div>
          </div>
          <div>
            <div class="summary-label">{{ t('restocking.remaining') }}</div>
            <div class="summary-value">{{ currencySymbol }}{{ remaining.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <div v-if="orderResult" class="confirmation">
        <strong>{{ t('restocking.confirmation.title') }}</strong>
        <div>{{ t('restocking.confirmation.orderNumber') }}: {{ orderResult.order_number }}</div>
        <div>{{ t('restocking.confirmation.total') }}: {{ currencySymbol }}{{ orderResult.total_value.toLocaleString() }}</div>
        <div>{{ t('restocking.confirmation.expectedDelivery') }}: {{ orderResult.expected_delivery }}</div>
        <router-link to="/orders">{{ t('restocking.confirmation.viewOrders') }}</router-link>
      </div>
      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
          <button class="place-order-btn" :disabled="selectedItems.length === 0 || submitting" @click="placeOrder">
            {{ submitting ? t('restocking.submitting') : t('restocking.placeOrder') }}
          </button>
        </div>
        <div v-if="recommendations.length === 0" class="empty">{{ t('restocking.empty') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.select') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.item_sku">
                <td><input v-model="checked[rec.item_sku]" type="checkbox" :aria-label="t('restocking.select')" /></td>
                <td><strong>{{ rec.item_sku }}</strong></td>
                <td>{{ rec.item_name }}</td>
                <td><span :class="['badge', rec.trend]">{{ t(`trends.${rec.trend}`) }}</span></td>
                <td>{{ rec.quantity }}</td>
                <td>{{ currencySymbol }}{{ rec.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ rec.lineTotal.toLocaleString() }}</strong></td>
                <td>{{ rec.lead_time_days }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

const { t, currentCurrency } = useI18n()
const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

const loading = ref(true)
const error = ref(null)
const forecasts = ref([])
const budget = ref(0)
const checked = ref({})
const submitting = ref(false)
const submitError = ref(null)
const orderResult = ref(null)

const gapOf = (f) => f.forecasted_demand - f.current_demand

// Only increasing/stable items with a positive gap are candidates for restocking
const candidates = computed(() =>
  forecasts.value.filter(f => f.trend !== 'decreasing' && gapOf(f) > 0)
)

// Slider max = cost of fully restocking every candidate, rounded up to the next 1000
const maxBudget = computed(() => {
  const total = candidates.value.reduce((sum, f) => sum + gapOf(f) * f.unit_cost, 0)
  return Math.ceil(total / 1000) * 1000
})

/*
 * Recommendation logic (greedy, priority-ordered):
 * 1. Candidates are ranked: 'increasing' trend before 'stable', then by largest gap
 *    (forecasted - current demand) first.
 * 2. Walk the ranked list with the full budget. If the whole gap is affordable, buy all of it.
 * 3. For an item whose full gap does not fit, buy as many units as the leftover budget
 *    covers (floor(remaining / unit_cost)), if at least 1. The leftover is then
 *    spent on later (lower-priority) items, which may be cheaper and still fit.
 */
const recommendations = computed(() => {
  const ranked = [...candidates.value].sort((a, b) => {
    const rank = (f) => (f.trend === 'increasing' ? 0 : 1)
    return rank(a) - rank(b) || gapOf(b) - gapOf(a)
  })
  let remainingBudget = budget.value
  const result = []
  for (const f of ranked) {
    if (!(f.unit_cost > 0)) continue
    const gap = gapOf(f)
    const quantity = gap * f.unit_cost <= remainingBudget
      ? gap
      : Math.floor(remainingBudget / f.unit_cost)
    if (quantity < 1) continue
    const lineTotal = quantity * f.unit_cost
    remainingBudget -= lineTotal
    result.push({ ...f, quantity, lineTotal })
  }
  return result
})

// Reset every recommended row to checked whenever the recommendation changes (slider moved)
watch(recommendations, (recs) => {
  const next = {}
  for (const r of recs) next[r.item_sku] = true
  checked.value = next
}, { immediate: true })

const selectedItems = computed(() => recommendations.value.filter(r => checked.value[r.item_sku]))
const selectedTotal = computed(() => selectedItems.value.reduce((sum, r) => sum + r.lineTotal, 0))
const remaining = computed(() => budget.value - selectedTotal.value)

const loadForecasts = async () => {
  try {
    loading.value = true
    error.value = null
    forecasts.value = await api.getDemandForecasts()
    budget.value = Math.round(maxBudget.value / 2 / 500) * 500
  } catch (err) {
    error.value = t('restocking.loadFailed')
    console.error('Load error:', err)
  } finally {
    loading.value = false
  }
}

const placeOrder = async () => {
  submitting.value = true
  submitError.value = null
  orderResult.value = null
  try {
    orderResult.value = await api.placeRestockOrder({
      budget: budget.value,
      items: selectedItems.value.map(r => ({ sku: r.item_sku, quantity: r.quantity }))
    })
  } catch (err) {
    submitError.value = err.response?.data?.detail || t('restocking.submitFailed')
  } finally {
    submitting.value = false
  }
}

onMounted(loadForecasts)
</script>

<style scoped>
.budget-card {
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.budget-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}

.budget-label {
  font-weight: 600;
  color: #0f172a;
}

.budget-amount {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-slider {
  width: 100%;
}

.budget-summary {
  display: flex;
  gap: 3rem;
  margin-top: 1rem;
}

.summary-label {
  font-size: 0.813rem;
  color: #64748b;
}

.summary-value {
  font-size: 1.125rem;
  font-weight: 600;
  color: #0f172a;
}

.confirmation {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem 1.5rem;
  margin-bottom: 1rem;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  color: #166534;
}

.place-order-btn {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.empty {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}
</style>
