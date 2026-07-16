<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="budget-control">
        <label class="budget-label" for="budget-slider">
          {{ t('restocking.budget') }}: <strong>{{ currencySymbol }}{{ budget.toLocaleString() }}</strong>
        </label>
        <input
          id="budget-slider"
          type="range"
          min="0"
          max="100000"
          step="500"
          v-model.number="budget"
          class="budget-slider"
        />
      </div>
    </div>

    <div v-if="orderPlacedMessage" class="success-banner">{{ orderPlacedMessage }}</div>
    <div v-if="orderFailedMessage" class="error">{{ orderFailedMessage }}</div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.estimatedCost') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalEstimatedCost.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
        </div>
        <div v-if="recommendations.length === 0" class="no-data">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.category') }}</th>
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.estimatedCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.reason') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ rec.name }}</td>
                <td>{{ rec.category }}</td>
                <td>{{ rec.current_demand }}</td>
                <td>{{ rec.forecasted_demand }}</td>
                <td>{{ rec.demand_gap }}</td>
                <td>{{ currencySymbol }}{{ rec.unit_cost.toLocaleString() }}</td>
                <td>{{ rec.recommended_quantity }}</td>
                <td><strong>{{ currencySymbol }}{{ rec.estimated_cost.toLocaleString() }}</strong></td>
                <td>{{ t('restocking.table.leadTimeDays', { days: rec.lead_time_days }) }}</td>
                <td>{{ rec.reason }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="place-order-row">
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

defineOptions({ name: 'Restocking' })

const { t, currentCurrency } = useI18n()

const currencySymbol = computed(() => {
  return currentCurrency.value === 'JPY' ? '¥' : '$'
})

const budget = ref(25000)
const recommendations = ref([])
const loading = ref(true)
const error = ref(null)
const submitting = ref(false)
const orderPlacedMessage = ref(null)
const orderFailedMessage = ref(null)

let debounceTimer = null

const totalEstimatedCost = computed(() => {
  return recommendations.value.reduce((sum, rec) => sum + rec.estimated_cost, 0)
})

const remainingBudget = computed(() => {
  return budget.value - totalEstimatedCost.value
})

const loadRecommendations = async () => {
  try {
    loading.value = true
    error.value = null
    recommendations.value = await api.getRestockingRecommendations(budget.value)
  } catch (err) {
    error.value = 'Failed to load restocking recommendations: ' + err.message
  } finally {
    loading.value = false
  }
}

const debouncedLoad = () => {
  orderPlacedMessage.value = null
  orderFailedMessage.value = null
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    loadRecommendations()
  }, 400)
}

const placeOrder = async () => {
  submitting.value = true
  orderPlacedMessage.value = null
  orderFailedMessage.value = null
  try {
    const payload = {
      budget: budget.value,
      items: recommendations.value.map(rec => ({
        sku: rec.sku,
        name: rec.name,
        category: rec.category,
        quantity: rec.recommended_quantity,
        unit_cost: rec.unit_cost
      }))
    }
    const order = await api.createRestockingOrder(payload)
    orderPlacedMessage.value = t('restocking.orderPlaced', {
      orderNumber: order.order_number,
      days: order.lead_time_days
    })
  } catch (err) {
    orderFailedMessage.value = t('restocking.orderFailed')
    console.error('Failed to submit restocking order:', err)
  } finally {
    submitting.value = false
  }
}

watch(budget, () => {
  debouncedLoad()
})

onMounted(loadRecommendations)

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<style scoped>
.budget-control {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.budget-label {
  font-size: 0.938rem;
  color: #334155;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.place-order-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 8px;
  font-size: 0.938rem;
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

.success-banner {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
