<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
          <span class="budget-value">{{ formatMoney(budget) }}</span>
        </div>
        <input
          v-model.number="budget"
          type="range"
          class="budget-slider"
          min="0"
          :max="maxBudget"
          step="1000"
          :aria-label="t('restocking.budget')"
        />
        <div class="slider-scale">
          <span>{{ formatMoney(0) }}</span>
          <span>{{ formatMoney(maxBudget) }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.selectedTotal') }}</div>
          <div class="stat-value">{{ formatMoney(selectedTotal, 2) }}</div>
        </div>
        <div class="stat-card" :class="remainingBudget >= 0 ? 'success' : 'danger'">
          <div class="stat-label">{{ t('restocking.remainingBudget') }}</div>
          <div class="stat-value">{{ formatMoney(remainingBudget, 2) }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }} ({{ recommendations.length }})</h3>
          <button
            type="button"
            class="place-order-button"
            :disabled="selectedItems.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="orderConfirmation" class="confirmation">
          {{ t('restocking.orderPlaced', { orderNumber: orderConfirmation }) }}
        </div>
        <div v-if="submitError" class="error">{{ submitError }}</div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noItemsFit') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th class="col-check"></th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td class="col-check">
                  <input
                    v-model="checked[item.sku]"
                    type="checkbox"
                    :aria-label="item.sku"
                  />
                </td>
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.quantity }}</td>
                <td>{{ formatMoney(item.unitCost, 2) }}</td>
                <td><strong>{{ formatMoney(item.lineCost, 2) }}</strong></td>
                <td>{{ t('restocking.days', { count: item.leadTimeDays }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import {
  useRestockingRecommendations,
  getDefaultBudget
} from '../composables/useRestockingRecommendations'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(0)
    const checked = ref({})
    const submitting = ref(false)
    const submitError = ref(null)
    const orderConfirmation = ref(null)

    const { maxBudget, recommendations } = useRestockingRecommendations(forecasts, budget)

    const selectedItems = computed(() => {
      return recommendations.value.filter(item => checked.value[item.sku])
    })

    const selectedTotal = computed(() => {
      const cents = selectedItems.value.reduce((sum, item) => sum + Math.round(item.lineCost * 100), 0)
      return cents / 100
    })

    const remainingBudget = computed(() => {
      return Math.round((budget.value - selectedTotal.value) * 100) / 100
    })

    const formatMoney = (value, decimals = 0) => {
      return formatCurrencyWithDecimals(value, currentCurrency.value, decimals)
    }

    // New recommendations (budget or data changed) start fully selected and drop stale messages.
    watch(recommendations, (items) => {
      checked.value = Object.fromEntries(items.map(item => [item.sku, true]))
      submitError.value = null
      orderConfirmation.value = null
    }, { immediate: true })

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        budget.value = getDefaultBudget(maxBudget.value)
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (submitting.value || selectedItems.value.length === 0) return

      submitting.value = true
      submitError.value = null
      orderConfirmation.value = null
      try {
        const order = await api.createRestockingOrder({
          budget: budget.value,
          items: selectedItems.value.map(item => ({ sku: item.sku, quantity: item.quantity }))
        })
        orderConfirmation.value = order.order_number
        checked.value = Object.fromEntries(recommendations.value.map(item => [item.sku, false]))
      } catch (err) {
        submitError.value = err.response?.data?.detail || t('restocking.placeOrderFailed')
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      budget,
      maxBudget,
      recommendations,
      checked,
      selectedItems,
      selectedTotal,
      remainingBudget,
      submitting,
      submitError,
      orderConfirmation,
      formatMoney,
      translateProductName,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  accent-color: #2563eb;
}

.slider-scale {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.col-check {
  width: 40px;
}

.place-order-button {
  padding: 0.5rem 1.25rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-button:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-button:disabled {
  background: #cbd5e1;
  color: #64748b;
  cursor: not-allowed;
}

.confirmation {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.938rem;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}
</style>
