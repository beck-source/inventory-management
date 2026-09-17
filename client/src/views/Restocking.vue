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
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-control">
          <div class="budget-range-labels">
            <span>{{ currencySymbol }}0</span>
            <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
          </div>
          <input
            type="range"
            min="0"
            :max="maxBudget"
            step="50"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-value">{{ t('restocking.budget') }}: {{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.allocated') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ (recommendationsData?.total_allocated || 0).toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ (recommendationsData?.remaining_budget || 0).toLocaleString() }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendationsData?.recommendations?.length || 0 }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
          <button
            class="place-order-btn"
            :disabled="!recommendationsData?.recommendations?.length || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="orderResult" class="success-panel">
          <div class="success-title">{{ t('restocking.orderSuccess', { orderNumber: orderResult.order_number }) }}</div>
          <div class="success-detail">{{ t('restocking.totalCost') }}: {{ currencySymbol }}{{ orderResult.total_cost.toLocaleString() }}</div>
          <div class="success-detail">{{ t('restocking.orderSuccessDetail', { days: orderResult.lead_time_days, date: formatDate(orderResult.expected_delivery) }) }}</div>
          <div class="success-hint">{{ t('restocking.viewInOrders') }}</div>
        </div>
        <div v-if="orderError" class="error">{{ orderError }}</div>

        <div v-if="!recommendationsData?.recommendations?.length" class="loading">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.itemName') }}</th>
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.demandGap') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendationsData.recommendations" :key="rec.item_sku">
                <td><strong>{{ rec.item_sku }}</strong></td>
                <td>{{ translateProductName(rec.item_name) }}</td>
                <td>{{ rec.current_demand }}</td>
                <td>{{ rec.forecasted_demand }}</td>
                <td>{{ rec.demand_gap }}</td>
                <td>{{ currencySymbol }}{{ rec.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ rec.recommended_quantity }}</strong></td>
                <td>{{ currencySymbol }}{{ rec.line_total.toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const budget = ref(0)
    const maxBudget = ref(10000)
    const recommendationsData = ref(null)
    const submitting = ref(false)
    const orderResult = ref(null)
    const orderError = ref(null)

    const loadRecommendations = async () => {
      try {
        recommendationsData.value = await api.getRestockingRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      }
    }

    const init = async () => {
      try {
        loading.value = true
        // Fetch with an effectively unlimited budget to discover the true full-funding cost
        const fullyFunded = await api.getRestockingRecommendations(999999999)
        maxBudget.value = Math.ceil(fullyFunded.total_allocated / 100) * 100

        // Seed budget at ~30% of max, rounded to a multiple of the slider step
        const step = 50
        budget.value = Math.round((maxBudget.value * 0.3) / step) * step

        await loadRecommendations()
      } catch (err) {
        error.value = 'Failed to load restocking recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch(budget, loadRecommendations)

    const formatDate = (dateString) => {
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return new Date(dateString).toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    const placeOrder = async () => {
      if (!recommendationsData.value?.recommendations?.length || submitting.value) return

      submitting.value = true
      orderError.value = null
      orderResult.value = null

      try {
        const items = recommendationsData.value.recommendations.map(rec => ({
          item_sku: rec.item_sku,
          item_name: rec.item_name,
          quantity: rec.recommended_quantity,
          unit_cost: rec.unit_cost,
          line_total: rec.line_total
        }))

        orderResult.value = await api.createRestockingOrder({ budget: budget.value, items })
      } catch (err) {
        orderError.value = 'Failed to place order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(init)

    return {
      t,
      currencySymbol,
      loading,
      error,
      budget,
      maxBudget,
      recommendationsData,
      submitting,
      orderResult,
      orderError,
      placeOrder,
      formatDate,
      translateProductName
    }
  }
}
</script>

<style scoped>
.budget-control {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #64748b;
}

.budget-slider {
  width: 100%;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-slider::-webkit-slider-runnable-track {
  height: 6px;
  border-radius: 6px;
  background: #e2e8f0;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 6px;
  background: #2563eb;
  cursor: pointer;
  margin-top: -6px;
  border: none;
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 6px;
  background: #e2e8f0;
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 6px;
  background: #2563eb;
  cursor: pointer;
  border: none;
}

.budget-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
  flex-shrink: 0;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-panel {
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.success-title {
  font-weight: 700;
  color: #059669;
  margin-bottom: 0.375rem;
}

.success-detail {
  font-size: 0.875rem;
  margin-bottom: 0.25rem;
}

.success-hint {
  font-size: 0.813rem;
  color: #047857;
  margin-top: 0.5rem;
  font-style: italic;
}
</style>
