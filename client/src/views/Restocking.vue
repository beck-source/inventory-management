<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Slider Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
        </div>
        <div class="budget-slider-row">
          <input
            type="range"
            class="budget-slider"
            v-model.number="budget"
            :min="minBudget"
            :max="maxBudget"
            :step="step"
          />
          <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
        </div>
      </div>

      <!-- Recommendations Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>

        <div v-else>
          <div class="table-container">
            <table class="recommendations-table">
              <thead>
                <tr>
                  <th class="col-sku">{{ t('restocking.table.sku') }}</th>
                  <th class="col-name">{{ t('restocking.table.itemName') }}</th>
                  <th class="col-trend">{{ t('restocking.table.trend') }}</th>
                  <th class="col-demand">{{ t('restocking.table.currentDemand') }}</th>
                  <th class="col-demand">{{ t('restocking.table.forecastedDemand') }}</th>
                  <th class="col-qty">{{ t('restocking.table.onHand') }}</th>
                  <th class="col-qty">{{ t('restocking.table.recommended') }}</th>
                  <th class="col-qty">{{ t('restocking.table.funded') }}</th>
                  <th class="col-cost">{{ t('restocking.table.unitCost') }}</th>
                  <th class="col-cost">{{ t('restocking.table.lineTotal') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations" :key="item.sku">
                  <td class="col-sku"><strong>{{ item.sku }}</strong></td>
                  <td class="col-name">{{ item.item_name }}</td>
                  <td class="col-trend">
                    <span :class="['badge', item.trend]">
                      {{ t(`trends.${item.trend}`) }}
                    </span>
                  </td>
                  <td class="col-demand">{{ item.current_demand }}</td>
                  <td class="col-demand">{{ item.forecasted_demand }}</td>
                  <td class="col-qty">{{ item.quantity_on_hand }}</td>
                  <td class="col-qty">{{ item.recommended_qty }}</td>
                  <td class="col-qty" :class="{ 'qty-partial': item.funded_qty < item.recommended_qty }">
                    {{ item.funded_qty }}
                  </td>
                  <td class="col-cost">{{ currencySymbol }}{{ item.unit_cost }}</td>
                  <td class="col-cost"><strong>{{ currencySymbol }}{{ item.line_total }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Budget Summary -->
          <div class="budget-summary">
            <span>{{ t('restocking.budgetUsed') }}: <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong> / {{ currencySymbol }}{{ budget.toLocaleString() }}</span>
            <span v-if="budget > totalCost" class="budget-remaining">{{ t('restocking.remaining') }}: {{ currencySymbol }}{{ (budget - totalCost).toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <!-- Place Order Button -->
      <div class="action-bar">
        <button
          class="btn-primary"
          @click="placeOrder"
          :disabled="!canPlaceOrder"
        >
          {{ submitting ? t('common.loading') : t('restocking.placeOrder') }}
        </button>
      </div>

      <!-- Success Message -->
      <div v-if="submitSuccess" class="success-message">
        <div class="success-content">
          <h4>{{ t('restocking.orderSubmitted') }}</h4>
          <p>{{ t('restocking.orderNumber') }}: <strong>{{ submitSuccess.order_number }}</strong></p>
          <p>{{ t('restocking.leadTime') }}: {{ submitSuccess.lead_time_days }} {{ t('orders.days') }}</p>
          <p>{{ t('restocking.totalValue') }}: <strong>{{ currencySymbol }}{{ submitSuccess.total_value.toLocaleString() }}</strong></p>
          <button class="btn-secondary" @click="submitSuccess = null">{{ t('common.close') }}</button>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="submitError" class="error-message">
        {{ submitError }}
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
    const { t, currentCurrency } = useI18n()

    const budget = ref(5000)
    const minBudget = 0
    const maxBudget = 50000
    const step = 500

    const loading = ref(false)
    const error = ref(null)
    const recommendations = ref([])
    const totalCost = ref(0)
    const submitting = ref(false)
    const submitError = ref(null)
    const submitSuccess = ref(null)

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    let debounceHandle = null
    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockRecommendations(budget.value)
        recommendations.value = data.items
        totalCost.value = data.total_cost
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch(budget, () => {
      clearTimeout(debounceHandle)
      debounceHandle = setTimeout(loadRecommendations, 300)
    })

    const canPlaceOrder = computed(() =>
      recommendations.value.some(r => r.funded_qty > 0) && !submitting.value
    )

    const placeOrder = async () => {
      try {
        submitting.value = true
        submitError.value = null
        const items = recommendations.value
          .filter(r => r.funded_qty > 0)
          .map(r => ({
            sku: r.sku,
            item_name: r.item_name,
            quantity: r.funded_qty,
            unit_cost: r.unit_cost
          }))
        submitSuccess.value = await api.submitRestockOrder(items)
      } catch (err) {
        submitError.value = 'Failed to submit order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      budget,
      minBudget,
      maxBudget,
      step,
      loading,
      error,
      recommendations,
      totalCost,
      canPlaceOrder,
      placeOrder,
      submitting,
      submitError,
      submitSuccess,
      currencySymbol
    }
  }
}
</script>

<style scoped>
.budget-slider {
  width: 100%;
  accent-color: #2563eb;
  height: 6px;
  border-radius: 8px;
  background: #e2e8f0;
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.budget-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.budget-slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
}

.budget-value {
  font-weight: 600;
  color: #0f172a;
  min-width: 120px;
  text-align: right;
}

.recommendations-table {
  table-layout: fixed;
  width: 100%;
}

.col-sku {
  width: 100px;
}

.col-name {
  width: 150px;
}

.col-trend {
  width: 100px;
}

.col-demand {
  width: 100px;
}

.col-qty {
  width: 90px;
}

.col-cost {
  width: 100px;
}

.qty-partial {
  background-color: #fef3c7;
  color: #92400e;
  font-weight: 600;
}

.budget-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8fafc;
  border-top: 1px solid #e2e8f0;
  border-radius: 0 0 8px 8px;
}

.budget-remaining {
  color: #10b981;
  font-weight: 500;
}

.action-bar {
  display: flex;
  justify-content: center;
  gap: 1rem;
  padding: 2rem;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f1f5f9;
  color: #0f172a;
  border: 1px solid #e2e8f0;
  padding: 0.5rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.success-message {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-content {
  background: white;
  border: 2px solid #10b981;
  border-radius: 8px;
  padding: 2rem;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.success-content h4 {
  color: #10b981;
  margin-bottom: 1rem;
}

.success-content p {
  margin: 0.5rem 0;
  color: #475569;
}

.error-message {
  background: #fee2e2;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  border-left: 4px solid #dc2626;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}
</style>
