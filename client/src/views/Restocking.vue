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
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-slider-row">
          <input
            type="range"
            class="budget-slider"
            min="0"
            :max="maxBudget"
            step="100"
            v-model.number="budget"
          />
          <div class="budget-readout">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }}</h3>
        </div>
        <div v-if="recommendations.length === 0" class="no-recommendations">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.subtotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>{{ item.gap }}</td>
                <td>{{ currencySymbol }}{{ item.unitCost.toLocaleString() }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ currencySymbol }}{{ item.subtotal.toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>

          <div class="budget-summary">
            <div class="summary-row">
              <span>{{ t('restocking.totalCost') }}</span>
              <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong>
            </div>
            <div class="summary-row">
              <span>{{ t('restocking.remainingBudget') }}</span>
              <strong>{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</strong>
            </div>
          </div>
        </div>

        <div class="place-order-row">
          <button
            class="place-order-btn"
            :disabled="submitting || budget === 0 || recommendations.length === 0"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="submitError" class="error">{{ submitError }}</div>
        <div v-if="submittedOrderNumber" class="order-submitted">
          {{ t('restocking.orderSubmitted', { orderNumber: submittedOrderNumber }) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(0)
    const submitting = ref(false)
    const submitError = ref(null)
    const submittedOrderNumber = ref(null)

    const maxBudget = computed(() => {
      const total = forecasts.value.reduce((sum, f) => {
        const gap = f.forecasted_demand - f.current_demand
        return gap > 0 ? sum + gap * f.unit_cost : sum
      }, 0)
      return Math.ceil(total / 1000) * 1000
    })

    const recommendations = computed(() => {
      const candidates = forecasts.value
        .map(f => ({ ...f, gap: f.forecasted_demand - f.current_demand }))
        .filter(f => f.gap > 0)
        .sort((a, b) => b.gap - a.gap)

      let remaining = budget.value
      const result = []
      for (const item of candidates) {
        const qty = Math.min(Math.floor(remaining / item.unit_cost), item.gap)
        if (qty > 0) {
          const subtotal = qty * item.unit_cost
          result.push({
            sku: item.item_sku,
            name: item.item_name,
            gap: item.gap,
            unitCost: item.unit_cost,
            quantity: qty,
            subtotal
          })
          remaining -= subtotal
        }
      }
      return result
    })

    const totalCost = computed(() => {
      return recommendations.value.reduce((sum, r) => sum + r.subtotal, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - totalCost.value
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
        budget.value = Math.round(maxBudget.value / 2)
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      submittedOrderNumber.value = null
      try {
        const payload = recommendations.value.map(r => ({
          sku: r.sku,
          name: r.name,
          quantity: r.quantity,
          unit_price: r.unitCost
        }))
        const order = await api.submitRestockingOrder(payload)
        submittedOrderNumber.value = order.order_number
      } catch (err) {
        submitError.value = 'Failed to submit restocking order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadForecasts)

    return {
      t,
      currencySymbol,
      loading,
      error,
      budget,
      maxBudget,
      recommendations,
      totalCost,
      remainingBudget,
      submitting,
      submitError,
      submittedOrderNumber,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  appearance: none;
  outline: none;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  transition: background 0.2s;
}

.budget-slider::-webkit-slider-thumb:hover {
  background: #2563eb;
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #3b82f6;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
}

.budget-slider::-moz-range-thumb:hover {
  background: #2563eb;
}

.budget-readout {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 120px;
  text-align: right;
}

.no-recommendations {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.budget-summary {
  display: flex;
  justify-content: flex-end;
  gap: 2rem;
  padding: 1rem 0.75rem 0;
  border-top: 1px solid #e2e8f0;
  margin-top: 0.5rem;
}

.summary-row {
  display: flex;
  gap: 0.5rem;
  font-size: 0.938rem;
  color: #334155;
}

.place-order-row {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.25rem;
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s;
}

.place-order-btn:hover:not(:disabled) {
  background: #2563eb;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.order-submitted {
  margin-top: 1rem;
  padding: 1rem;
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  border-radius: 8px;
  font-size: 0.938rem;
}
</style>
